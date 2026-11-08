"""The pre-registered graded-measure analysis. PREREGISTRATION-GRADED.md section 6 only.

PRIMARY: per item, the FRACTION of its target (duty, relation) pairs surfaced,
`n_surfaced / n_targets`, which reach.py already records. No new instrument; reach.py is
not touched. Within each stratum, over items where BOTH arms produced a fraction, the
paired per-item difference is tested with the WILCOXON SIGNED-RANK test, exact where n
permits, two-sided, alpha 0.05 per stratum, no correction across strata.

Reported with the test, always: n paired, ties, median per-arm fraction, median paired
difference. A p value alone hides what the test ran on.

DISTRIBUTIONAL REPORTING, which is the interesting half: per arm, per stratum, how many
items reached ALL targets, NONE, or PARTIAL.

STRATIFY, NEVER POOL. No headline number across strata is computed here and none may be
constructed afterwards.

THE STRUCTURAL CAVEAT, from section 3 and stated BEFORE the run: the graph arm's fraction
is expected at or near 1.0 BY CONSTRUCTION, because get_conditions returns the relation
nodes. That measures the tool surface, not model behaviour. The informative quantity is
the TEXT arm's fraction.

Exclusions are unchanged: an item contributes a fraction only when its status is `reached`
or `not_reached`. `no_targets` and `no_reliance` are excluded and reported separately.
turn_cap_hit and error items are excluded and reported separately, per E8.

    .venv/Scripts/python.exe paper_draft/s6_tools/graded_analyse.py graded.reach.json
    .venv/Scripts/python.exe paper_draft/s6_tools/graded_analyse.py --selfcheck
"""
import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse import usable, RATE_STATUSES  # noqa: E402  same exclusion rule, one source

ALPHA = 0.05
EXACT_MAX_N = 20          # 2^20 sign patterns is instant; above that use the normal approx


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _ranks(xs):
    """Average ranks, 1-based, ties averaged."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def wilcoxon(diffs):
    """Two-sided Wilcoxon signed-rank on paired differences. Zeros dropped (Wilcoxon's
    own handling). Exact by enumerating sign patterns when n is small, normal
    approximation with tie and continuity correction otherwise.

    Returns (p, n_nonzero, W_plus, method) or (None, 0, None, "no non-zero differences").
    """
    nz = [d for d in diffs if d != 0]
    n = len(nz)
    if n == 0:
        return None, 0, None, "no non-zero differences"
    ranks = _ranks([abs(d) for d in nz])
    w_plus = sum(r for d, r in zip(nz, ranks) if d > 0)

    if n <= EXACT_MAX_N:
        total = 0
        hits = 0
        target = min(w_plus, sum(ranks) - w_plus)
        for signs in product((0, 1), repeat=n):
            s = sum(r for sgn, r in zip(signs, ranks) if sgn)
            total += 1
            if s <= target or s >= sum(ranks) - target:
                hits += 1
        return min(1.0, hits / total), n, w_plus, "exact"

    mean = sum(ranks) / 2.0
    tie_counts = Counter(ranks).values()
    tie_term = sum(t ** 3 - t for t in tie_counts)
    var = (n * (n + 1) * (2 * n + 1) - tie_term / 2.0) / 24.0
    if var <= 0:
        return 1.0, n, w_plus, "normal approximation, zero variance"
    z = (abs(w_plus - mean) - 0.5) / math.sqrt(var)
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
    return min(1.0, max(0.0, p)), n, w_plus, "normal approximation"


def fraction(r):
    return r["n_surfaced"] / r["n_targets"] if r["n_targets"] else None


def analyse(res):
    items = res["items"]
    arms = sorted({a for it in items for a in it["arms"]})
    strata = sorted({it["stratum"] for it in items})
    out = {"alpha": ALPHA, "arms": arms, "n_items": len(items), "strata": {}}

    for s in strata:
        rows = [it for it in items if it["stratum"] == s]
        blk = {"n_items": len(rows), "arms": {}}

        for arm in arms:
            rs = [it["arms"][arm] for it in rows if arm in it["arms"]]
            counts = Counter(r["status"] for r in rs if usable(r))
            excl = [r for r in rs if not usable(r)]
            fr = [fraction(r) for r in rs
                  if usable(r) and r["status"] in RATE_STATUSES]
            fr = [f for f in fr if f is not None]
            blk["arms"][arm] = {
                "n_with_fraction": len(fr),
                "median_fraction": median(fr),
                "mean_fraction": (sum(fr) / len(fr)) if fr else None,
                "all_targets": sum(1 for f in fr if f == 1.0),
                "none": sum(1 for f in fr if f == 0.0),
                "partial": sum(1 for f in fr if 0.0 < f < 1.0),
                "no_targets": counts["no_targets"], "no_reliance": counts["no_reliance"],
                "excluded_turn_cap": sum(1 for r in excl if r.get("turn_cap_hit")),
                "excluded_error": sum(1 for r in excl if r.get("error")),
                # the binary statistic of PREREGISTRATION.md, reported DESCRIPTIVELY on
                # this sample so the two measures can be compared on the same items
                "binary_reached": counts["reached"],
                "binary_not_reached": counts["not_reached"],
            }

        if len(arms) == 2:
            a1, a2 = arms
            diffs, f1, f2 = [], [], []
            for it in rows:
                r1, r2 = it["arms"].get(a1), it["arms"].get(a2)
                if not r1 or not r2 or not usable(r1) or not usable(r2):
                    continue
                if r1["status"] not in RATE_STATUSES or r2["status"] not in RATE_STATUSES:
                    continue
                x, y = fraction(r1), fraction(r2)
                if x is None or y is None:
                    continue
                f1.append(x)
                f2.append(y)
                diffs.append(x - y)
            p, nnz, wp, method = wilcoxon(diffs)
            blk["primary"] = {
                "test": "Wilcoxon signed-rank, two-sided (%s)" % method,
                "pair": [a1, a2], "n_paired": len(diffs),
                "n_ties": len(diffs) - nnz, "n_nonzero": nnz, "W_plus": wp,
                "median_%s" % a1: median(f1), "median_%s" % a2: median(f2),
                "median_difference": median(diffs),
                "p": p,
                "significant_at_%.2f" % ALPHA: (p is not None and p < ALPHA),
            }

        sec = {}
        for arm in arms:
            by_kind = defaultdict(lambda: [0, 0])
            distinct_t, distinct_s = set(), set()
            for it in rows:
                r = it["arms"].get(arm)
                if not r or not usable(r):
                    continue
                for pr in r["pairs"]:
                    by_kind[pr["kind"]][1] += 1
                    distinct_t.add(pr["relation_id"])
                    if pr["surfaced"]:
                        by_kind[pr["kind"]][0] += 1
                        distinct_s.add(pr["relation_id"])
            sec[arm] = {
                "by_kind": {k: {"surfaced": v[0], "targets": v[1]}
                            for k, v in sorted(by_kind.items())},
                # MANDATORY per section 6: a large pair gap is not a reachability claim
                "distinct_relations_surfaced": len(distinct_s),
                "distinct_relations_targeted": len(distinct_t),
            }
        blk["secondary_descriptive_not_tested"] = sec
        out["strata"][s] = blk
    return out


def render(out):
    L = ["PRE-REGISTERED GRADED-MEASURE ANALYSIS (PREREGISTRATION-GRADED.md section 6).",
         "Stratified, never pooled. alpha %.2f two-sided per stratum." % out["alpha"],
         "",
         "PRIMARY: per-item FRACTION of target pairs surfaced. Paired Wilcoxon signed-rank.",
         "",
         "THE GRAPH ARM'S FRACTION IS EXPECTED AT OR NEAR 1.0 BY CONSTRUCTION (section 3):",
         "get_conditions returns the relation nodes. That is the tool surface, not model",
         "behaviour. THE INFORMATIVE QUANTITY IS THE TEXT ARM'S FRACTION.",
         ""]
    hdr = "%-8s %-6s %5s %8s %8s %6s %5s %8s %7s %7s" % (
        "stratum", "arm", "n", "median", "mean", "all", "none", "partial", "noTgt", "noRel")
    L.append(hdr)
    L.append("-" * len(hdr))
    for s, blk in out["strata"].items():
        for arm, a in blk["arms"].items():
            md = "%.3f" % a["median_fraction"] if a["median_fraction"] is not None else "n/a"
            mn = "%.3f" % a["mean_fraction"] if a["mean_fraction"] is not None else "n/a"
            L.append("%-8s %-6s %5d %8s %8s %6d %5d %8d %7d %7d" % (
                s, arm, a["n_with_fraction"], md, mn, a["all_targets"], a["none"],
                a["partial"], a["no_targets"], a["no_reliance"]))
        pr = blk.get("primary")
        if pr:
            p = pr["p"]
            L.append("%-8s   %s: n paired %d (ties %d), median diff %s, p = %s%s" % (
                s, pr["test"], pr["n_paired"], pr["n_ties"],
                ("%.3f" % pr["median_difference"]) if pr["median_difference"] is not None else "n/a",
                ("%.6f" % p) if p is not None else "n/a (no non-zero differences)",
                "  SIGNIFICANT" if pr["significant_at_0.05"] else ""))
        L.append("")
    L.append("SECONDARY, descriptive only, NOT significance-tested.")
    L.append("DISTINCT relation counts are mandatory: a large pair gap is NOT a")
    L.append("reachability claim, and these are what stop it being read as one.")
    L.append("")
    L.append("%-8s %-6s %-16s %s" % ("stratum", "arm", "kind", "surfaced/targets"))
    L.append("-" * 58)
    for s, blk in out["strata"].items():
        for arm, sec in blk["secondary_descriptive_not_tested"].items():
            for kind, v in sec["by_kind"].items():
                L.append("%-8s %-6s %-16s %d/%d" % (s, arm, kind, v["surfaced"], v["targets"]))
            L.append("%-8s %-6s %-16s %d/%d" % (
                s, arm, "DISTINCT rels", sec["distinct_relations_surfaced"],
                sec["distinct_relations_targeted"]))
    L.append("")
    L.append("The binary statistic of PREREGISTRATION.md on these same items, DESCRIPTIVE")
    L.append("only. That study's test is not re-run and its result is not revised.")
    L.append("")
    for s, blk in out["strata"].items():
        for arm, a in blk["arms"].items():
            L.append("%-8s %-6s binary reached %d / not_reached %d" % (
                s, arm, a["binary_reached"], a["binary_not_reached"]))
    return "\n".join(L)


def selfcheck():
    # Wilcoxon against values computable by hand.
    # All differences positive and distinct: the exact two-sided p is 2/2^n.
    p, n, w, m = wilcoxon([0.1, 0.2, 0.3, 0.4, 0.5])
    assert m == "exact" and n == 5 and abs(p - 2.0 / 32.0) < 1e-12, (p, n, m)
    p, n, w, m = wilcoxon([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    assert abs(p - 2.0 / 64.0) < 1e-12, p
    assert p < ALPHA                       # n = 6 all one way is significant
    p5, _, _, _ = wilcoxon([0.1, 0.2, 0.3, 0.4, 0.5])
    assert p5 > ALPHA                      # n = 5 all one way is NOT, at 0.0625
    # symmetric differences must not be significant
    p, n, w, m = wilcoxon([0.3, -0.3, 0.2, -0.2])
    assert p == 1.0, (p, w)
    # zeros are dropped, not counted
    p, n, w, m = wilcoxon([0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.0])
    assert n == 5 and abs(p - 2.0 / 32.0) < 1e-12, (p, n)
    assert wilcoxon([0.0, 0.0])[0] is None
    assert wilcoxon([])[0] is None
    # sign must not matter to the two-sided p
    assert wilcoxon([0.1, 0.2, 0.3])[0] == wilcoxon([-0.1, -0.2, -0.3])[0]
    # the normal branch runs and is sane on a clean one-way set
    big = [0.01 * i for i in range(1, 30)]
    p, n, w, m = wilcoxon(big)
    assert m == "normal approximation" and p < 1e-4, (p, m)

    assert median([1, 2, 3]) == 2 and median([1, 2, 3, 4]) == 2.5 and median([]) is None

    def row(surf, tgt, status="reached", **kw):
        return dict({"n_surfaced": surf, "n_targets": tgt, "status": status,
                     "pairs": []}, **kw)

    fake = {"items": [
        {"id": "i%d" % i, "stratum": "S", "article": 14, "arms": {
            "graph": row(4, 4), "text": row(1, 4)}} for i in range(6)
    ] + [
        {"id": "x", "stratum": "S", "article": 14, "arms": {
            "graph": row(0, 0, "no_targets"), "text": row(0, 0, "no_targets")}},
        {"id": "y", "stratum": "S", "article": 14, "arms": {
            "graph": row(2, 2, turn_cap_hit=True), "text": row(1, 2)}},
    ]}
    o = analyse(fake)["strata"]["S"]
    g, t = o["arms"]["graph"], o["arms"]["text"]
    assert g["n_with_fraction"] == 6 and g["all_targets"] == 6, g
    assert g["no_targets"] == 1 and g["excluded_turn_cap"] == 1, g
    assert t["n_with_fraction"] == 7 and t["partial"] == 7, t
    pr = o["primary"]
    assert pr["n_paired"] == 6 and pr["n_ties"] == 0, pr
    assert abs(pr["median_difference"] - 0.75) < 1e-9, pr
    assert pr["p"] is not None and pr["p"] < ALPHA, pr

    print("graded_analyse.py self-check OK: Wilcoxon exact against hand values, zeros "
          "dropped, symmetry, normal branch, and the pre-registered exclusions")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reach", nargs="?")
    ap.add_argument("--out", default="")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if not a.reach:
        raise SystemExit("give me a reach.py output file, or --selfcheck")
    out = analyse(json.load(open(a.reach, encoding="utf-8")))
    text = render(out)
    print(text)
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2)
        open(a.out.replace(".json", ".txt"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
