"""The pre-registered analysis of the reach study, and nothing else.

PREREGISTRATION.md section 5 fixes every choice made here BEFORE the data existed. This
script implements that section and may not be extended with an analysis it does not name.
Read it, and verify its digest, before reading any output of this file.

  - STRATIFY, NEVER POOL. Every rate is per stratum, per arm. There is no headline number
    across strata and this script deliberately does not compute one. Article 14 carries
    159 of the 223 cross-provision attachments and Article 46 carries none, so a pooled
    figure would be driven by the stratum mix in a specific and misleading direction.
  - THE DENOMINATOR IS FIXED IN ADVANCE: reached / (reached + not_reached).
    `no_targets` and `no_reliance` are reported BESIDE it and never folded into it.
    Counting a model that never called get_conditions as a failure to reach would measure
    tool-following rather than representation, and it occurs in both arms.
  - Items flagged turn_cap_hit or carrying an execution error are EXCLUDED from the rate
    and reported separately, per E8, never silently included.
  - PRIMARY: per item, paired across arms, McNemar's exact test on the discordant pairs
    within each stratum, reported with the discordant counts themselves. Wilson score
    intervals on the per-arm rates. Alpha 0.05 two-sided per stratum, no correction across
    strata: the strata are separate questions with separate predictions, not a family of
    tests hunting one effect.
  - SECONDARY: per duty-relation pair, by relation kind. DESCRIPTIVE ONLY and deliberately
    NOT significance-tested, because pairs are nested within items and clustered hard by
    the fanout skew (8 nodes carry 201 of the 258 attachments).

No new dependency: the exact binomial is math.comb and Wilson is a square root.

    .venv/Scripts/python.exe paper_draft/s6_tools/analyse.py study.reach.json --traces study.traces.json
    .venv/Scripts/python.exe paper_draft/s6_tools/analyse.py --selfcheck
"""
import argparse
import json
import math
import re
from collections import Counter, defaultdict

ALPHA = 0.05            # pre-registered, two-sided, per stratum, no correction across strata
RATE_STATUSES = ("reached", "not_reached")


def wilson(k, n, z=1.959963984540054):
    """Wilson score interval, brown2001interval. Returns (low, high), or None for n = 0."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b, c):
    """Two-sided exact binomial on the discordant pairs, p = 0.5. None if there are none.

    b and c are the two kinds of discordant pair. Concordant pairs carry no information
    about the difference and are not in the test, which is why the counts are reported
    beside the p value rather than only the p value.
    """
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def verdict_of(final):
    """Keyword scan of the final answer for the verdict label.

    THIS IS A KEYWORD SCAN, NOT A HAND-CHECKED INSTRUMENT. It feeds only the inter-arm
    verdict disagreement line, which PREREGISTRATION.md section 5 lists among the things
    reported alongside and explicitly not a headline. The count of answers it could not
    parse is reported beside it so the line cannot be read as cleaner than it is. It is
    NOT the gated final-answer provision parser of PREREGISTRATION-STABILITY.md section 3,
    which owes a hand-check and is not built here.

    Deliberately case-sensitive on the uppercase label the system prompt asks for, and it
    takes the FIRST one, which is the verdict rather than a restatement inside the
    justification. Lowercase prose like "it is compliant" is left UNPARSED on purpose: a
    looser scan would guess, and a guess here would be an unchecked automatic component of
    exactly the kind this project has twice been burned by. Unparsed is honest and is
    counted.
    """
    if not final:
        return None
    hits = re.findall(r"\b(NOT[_ ]APPLICABLE|NON[_ ]COMPLIANT|COMPLIANT)\b", final)
    if not hits:
        return None
    return hits[0].replace(" ", "_")


def usable(row):
    """Pre-registered exclusion: a capped or errored run produces no rate."""
    return not row.get("turn_cap_hit") and not row.get("error")


def analyse(res, traces=None):
    items = res["items"]
    arms = sorted({a for it in items for a in it["arms"]})
    strata = sorted({it["stratum"] for it in items})
    finals = {}
    if traces:
        for rec in traces["records"]:
            finals[rec["id"]] = {a: (run.get("final") or "")
                                 for a, run in rec["arms"].items()}

    out = {"alpha": ALPHA, "arms": arms, "n_items": len(items), "strata": {}}
    for s in strata:
        rows = [it for it in items if it["stratum"] == s]
        block = {"n_items": len(rows), "arms": {}}

        for arm in arms:
            rs = [it["arms"][arm] for it in rows if arm in it["arms"]]
            counts = Counter(r["status"] for r in rs if usable(r))
            excluded = [r for r in rs if not usable(r)]
            reached, not_reached = counts["reached"], counts["not_reached"]
            den = reached + not_reached
            block["arms"][arm] = {
                "reached": reached, "not_reached": not_reached,
                "no_targets": counts["no_targets"], "no_reliance": counts["no_reliance"],
                "excluded_turn_cap": sum(1 for r in excluded if r.get("turn_cap_hit")),
                "excluded_error": sum(1 for r in excluded if r.get("error")),
                "denominator": den,
                "rate": (reached / den) if den else None,
                "wilson95": wilson(reached, den),
                "turns_mean": round(sum(r.get("turns") or 0 for r in rs) / len(rs), 2) if rs else None,
                "calls_mean": round(sum(r.get("calls") or 0 for r in rs) / len(rs), 2) if rs else None,
            }

        # PRIMARY. Paired per item, over items where BOTH arms produced a rate status.
        if len(arms) == 2:
            a1, a2 = arms
            b = c = concordant_yes = concordant_no = 0
            paired = 0
            for it in rows:
                r1, r2 = it["arms"].get(a1), it["arms"].get(a2)
                if not r1 or not r2 or not usable(r1) or not usable(r2):
                    continue
                if r1["status"] not in RATE_STATUSES or r2["status"] not in RATE_STATUSES:
                    continue
                paired += 1
                x, y = r1["status"] == "reached", r2["status"] == "reached"
                if x and not y:
                    b += 1
                elif y and not x:
                    c += 1
                elif x and y:
                    concordant_yes += 1
                else:
                    concordant_no += 1
            p = mcnemar_exact(b, c)
            block["primary"] = {
                "test": "McNemar exact, two-sided", "pair": [a1, a2],
                "n_paired": paired,
                "discordant_%s_only" % a1: b, "discordant_%s_only" % a2: c,
                "concordant_both_reached": concordant_yes,
                "concordant_neither": concordant_no,
                "p": p,
                "significant_at_%.2f" % ALPHA: (p is not None and p < ALPHA),
            }

        # SECONDARY. Descriptive only. NOT significance-tested, by pre-registration.
        sec = {}
        for arm in arms:
            by_kind = defaultdict(lambda: [0, 0])
            for it in rows:
                r = it["arms"].get(arm)
                if not r or not usable(r):
                    continue
                for pr in r["pairs"]:
                    by_kind[pr["kind"]][1] += 1
                    if pr["surfaced"]:
                        by_kind[pr["kind"]][0] += 1
            tot = [sum(v[0] for v in by_kind.values()), sum(v[1] for v in by_kind.values())]
            sec[arm] = {"by_kind": {k: {"surfaced": v[0], "targets": v[1]}
                                    for k, v in sorted(by_kind.items())},
                        "all_kinds": {"surfaced": tot[0], "targets": tot[1]}}
        block["secondary_descriptive_not_tested"] = sec

        # Reported alongside, not a headline.
        if finals:
            dis = same = unparsed = 0
            for it in rows:
                f = finals.get(it["id"])
                if not f or len(arms) != 2:
                    continue
                v1, v2 = verdict_of(f.get(arms[0])), verdict_of(f.get(arms[1]))
                if v1 is None or v2 is None:
                    unparsed += 1
                elif v1 != v2:
                    dis += 1
                else:
                    same += 1
            block["verdict_disagreement_keyword_scan"] = {
                "disagree": dis, "agree": same, "unparsed": unparsed}

        out["strata"][s] = block
    return out


def render(out):
    L = []
    L.append("PRE-REGISTERED ANALYSIS. Stratified, never pooled: there is no number across")
    L.append("strata here and one may not be constructed. alpha %.2f two-sided per stratum." % out["alpha"])
    L.append("")
    L.append("PRIMARY: per-item rate = reached / (reached + not_reached), per arm, per stratum.")
    L.append("no_targets and no_reliance sit beside the rate and are NEVER in the denominator.")
    L.append("")
    hdr = "%-8s %-6s %6s %6s %6s %6s %5s %5s  %-16s %s" % (
        "stratum", "arm", "reach", "notr", "noTgt", "noRel", "cap", "err", "rate [95% CI]", "")
    L.append(hdr)
    L.append("-" * len(hdr))
    for s, blk in out["strata"].items():
        for arm, a in blk["arms"].items():
            ci = a["wilson95"]
            rate = ("%.3f [%.3f,%.3f]" % (a["rate"], ci[0], ci[1])) if ci else "n/a (den 0)"
            L.append("%-8s %-6s %6d %6d %6d %6d %5d %5d  %-16s" % (
                s, arm, a["reached"], a["not_reached"], a["no_targets"], a["no_reliance"],
                a["excluded_turn_cap"], a["excluded_error"], rate))
        pr = blk.get("primary")
        if pr:
            k1 = "discordant_%s_only" % pr["pair"][0]
            k2 = "discordant_%s_only" % pr["pair"][1]
            p = pr["p"]
            L.append("%-8s   McNemar exact: n paired %d, discordant %s %d / %s %d, "
                     "concordant %d yes %d no, p = %s%s" % (
                         s, pr["n_paired"], pr["pair"][0], pr[k1], pr["pair"][1], pr[k2],
                         pr["concordant_both_reached"], pr["concordant_neither"],
                         ("%.5f" % p) if p is not None else "n/a (no discordant pairs)",
                         "  SIGNIFICANT" if pr["significant_at_0.05"] else ""))
        vd = blk.get("verdict_disagreement_keyword_scan")
        if vd:
            L.append("%-8s   verdict disagreement (KEYWORD SCAN, not a headline): "
                     "%d disagree, %d agree, %d unparsed" % (s, vd["disagree"], vd["agree"], vd["unparsed"]))
        L.append("")
    L.append("SECONDARY, per duty-relation pair, by relation kind.")
    L.append("DESCRIPTIVE ONLY. Deliberately NOT significance-tested: pairs are nested within")
    L.append("items and clustered hard by the fanout skew (8 nodes carry 201 of 258).")
    L.append("")
    L.append("%-8s %-6s %-16s %s" % ("stratum", "arm", "kind", "surfaced/targets"))
    L.append("-" * 56)
    for s, blk in out["strata"].items():
        for arm, sec in blk["secondary_descriptive_not_tested"].items():
            for kind, v in sec["by_kind"].items():
                L.append("%-8s %-6s %-16s %d/%d" % (s, arm, kind, v["surfaced"], v["targets"]))
            t = sec["all_kinds"]
            L.append("%-8s %-6s %-16s %d/%d" % (s, arm, "ALL", t["surfaced"], t["targets"]))
    return "\n".join(L)


def selfcheck():
    # Wilson against the three intervals PREREGISTRATION-STABILITY.md section 1 states,
    # which were computed independently of this code and are therefore a real check.
    for n, want in [(50, 0.929), (25, 0.867), (100, 0.963)]:
        lo, hi = wilson(n, n)
        assert abs(lo - want) < 0.001 and abs(hi - 1.0) < 1e-9, (n, lo, hi)
    lo, hi = wilson(1, 2)
    assert abs(lo - 0.0946) < 0.001 and abs(hi - 0.9054) < 0.001, (lo, hi)
    assert wilson(0, 0) is None

    # Exact binomial. b = 10, c = 0 is 2 * 0.5^10; a tie is p = 1; no discordant pair is
    # not a p of 1 but an absent test, and conflating those would report a null that was
    # never run.
    assert abs(mcnemar_exact(10, 0) - 0.001953125) < 1e-9
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 0) is None
    assert abs(mcnemar_exact(9, 1) - 0.021484375) < 1e-9
    assert mcnemar_exact(8, 2) > ALPHA and mcnemar_exact(9, 1) < ALPHA
    assert mcnemar_exact(3, 7) == mcnemar_exact(7, 3)          # symmetric in b and c

    assert verdict_of("Verdict: NON_COMPLIANT because ...") == "NON_COMPLIANT"
    assert verdict_of("NOT APPLICABLE") == "NOT_APPLICABLE"
    assert verdict_of("VERDICT: COMPLIANT. It must stay NON_COMPLIANT free.") == "COMPLIANT"
    assert verdict_of("it is compliant") is None               # lowercase stays unparsed
    assert verdict_of("") is None and verdict_of(None) is None

    # The denominator rule, which is the one the pre-registration fixes in advance.
    fake = {"items": [
        {"id": "a", "stratum": "S", "article": 14, "arms": {
            "graph": {"status": "reached", "pairs": [], "turns": 3, "calls": 3},
            "text": {"status": "not_reached", "pairs": [], "turns": 3, "calls": 3}}},
        {"id": "b", "stratum": "S", "article": 14, "arms": {
            "graph": {"status": "no_reliance", "pairs": [], "turns": 1, "calls": 0},
            "text": {"status": "no_targets", "pairs": [], "turns": 2, "calls": 2}}},
        {"id": "c", "stratum": "S", "article": 14, "arms": {
            "graph": {"status": "reached", "pairs": [], "turn_cap_hit": True},
            "text": {"status": "reached", "pairs": [], "turns": 3, "calls": 3}}},
    ]}
    o = analyse(fake)["strata"]["S"]
    g, t = o["arms"]["graph"], o["arms"]["text"]
    assert g["denominator"] == 1 and g["rate"] == 1.0, g      # no_reliance out, capped out
    assert g["no_reliance"] == 1 and g["excluded_turn_cap"] == 1, g
    # Exclusion is PER ARM for a per-arm rate: item c's graph run was capped, but its text
    # run was clean and still counts. The paired test is where the item drops out entirely,
    # because a pair needs both halves.
    assert t["denominator"] == 2 and t["rate"] == 0.5, t      # no_targets out, capped graph
    assert t["no_targets"] == 1 and t["excluded_turn_cap"] == 0, t
    assert o["primary"]["n_paired"] == 1, o["primary"]        # b and c pairs both dropped
    assert o["primary"]["p"] is not None

    print("analyse.py self-check OK: Wilson against three independently stated intervals, "
          "exact binomial, and the pre-registered denominator")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reach", nargs="?", help="output of reach.py")
    ap.add_argument("--traces", default="", help="the traces file, for the verdict line")
    ap.add_argument("--out", default="")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if not a.reach:
        raise SystemExit("give me a reach.py output file, or --selfcheck")
    res = json.load(open(a.reach, encoding="utf-8"))
    traces = json.load(open(a.traces, encoding="utf-8")) if a.traces else None
    out = analyse(res, traces)
    text = render(out)
    print(text)
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2)
        open(a.out.replace(".json", ".txt"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
