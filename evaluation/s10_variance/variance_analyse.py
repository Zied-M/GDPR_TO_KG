"""The variance study's analysis, per PREREGISTRATION-VARIANCE.md sections 3 and 4.

PRIMARY, and the only primary: the MODAL RELIED-PROVISION-SET SHARE. For each item, in
each arm, the count of the N runs producing the most common relied_units set, divided by
the number of usable runs. 1.0 means every run relied on the same provisions.

This file is deliberately thin. It reimplements nothing: the grouping and the modal count
come from stability_analyse, the paired test from graded_analyse. Both were built and
self-checked in S9 and neither is modified here.

It is a NEW automatic component, so per the pre-registration it produces no number until
its --selfcheck passes AND a hand-check of at least three real items across at least two
strata has been recorded. --handcheck prints exactly what that check needs.

Nothing here is written into s6_tools/.
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "s6_tools"))

from stability_analyse import group, largest_agreeing          # noqa: E402
from graded_analyse import wilcoxon, median                    # noqa: E402

MIN_USABLE = 8      # pre-registered: an item below this is excluded and listed
MIN_PAIRS = 6       # pre-registered: 2/2**5 = 0.0625 cannot reach alpha 0.05


def usable_runs(runs):
    """Drop errored repeats. A turn-cap hit is NOT dropped: it completed its turns and
    its relied set is real. Both rules are pre-registered in section 4."""
    return {r: v for r, v in runs.items() if not v.get("error")}


def item_stats(runs):
    """The per-item quantities, from the usable runs of one item in one arm."""
    keys = sorted(runs)
    sets = [tuple(sorted(runs[r]["relied_units"])) for r in keys]
    n = len(sets)
    top = largest_agreeing(sets)
    return {
        "n_usable": n,
        "modal_share": top / n,                 # PRIMARY
        "modal_count": top,
        "distinct_sets": len(set(sets)),
        "all_identical": top == n,              # S9's binary, secondary and N-dependent
        "all_empty": all(len(s) == 0 for s in sets),
        "status_modal_share": largest_agreeing([runs[r]["status"] for r in keys]) / n,
        "turn_cap_hits": sum(1 for r in keys if runs[r].get("turn_cap_hit")),
    }


def analyse(res, traces):
    by = group(res, traces)
    strata = sorted({k[1] for k in by})
    arms = sorted({k[2] for k in by})
    n_repeats = traces.get("repeats")

    out = {"n_repeats": n_repeats, "temperature": traces.get("temperature"),
           "min_usable": MIN_USABLE, "min_pairs": MIN_PAIRS,
           "excluded_items": [], "strata": {}}

    per_item = {}
    for k in sorted(by):
        runs = usable_runs(by[k])
        if len(runs) < MIN_USABLE:
            out["excluded_items"].append(
                {"id": k[0], "stratum": k[1], "arm": k[2], "usable": len(runs)})
            continue
        per_item[k] = item_stats(runs)

    for s in strata:
        blk = {"arms": {}}
        for arm in arms:
            rows = [v for k, v in per_item.items() if k[1] == s and k[2] == arm]
            shares = [r["modal_share"] for r in rows]
            blk["arms"][arm] = {
                "n_items": len(rows),
                "median_modal_share": median(shares) if shares else None,
                "mean_modal_share": (sum(shares) / len(shares)) if shares else None,
                "min_modal_share": min(shares) if shares else None,
                # the distribution is what N = 10 was chosen to expose
                "modal_count_distribution":
                    dict(sorted(Counter(r["modal_count"] for r in rows).items(),
                                reverse=True)),
                "distinct_sets_distribution":
                    dict(sorted(Counter(r["distinct_sets"] for r in rows).items())),
                "all_identical": sum(1 for r in rows if r["all_identical"]),
                # a perfectly stable emptiness is NOT evidence of a stable
                # representation and is counted apart so it cannot be read as one
                "all_empty_every_run": sum(1 for r in rows if r["all_empty"]),
                "status_median_modal_share":
                    median([r["status_modal_share"] for r in rows]) if rows else None,
                "turn_cap_hits": sum(r["turn_cap_hits"] for r in rows),
            }

        # the pre-registered arm comparison: paired Wilcoxon on graph minus text
        if "graph" in arms and "text" in arms:
            ids = sorted({k[0] for k in per_item if k[1] == s and k[2] == "graph"} &
                         {k[0] for k in per_item if k[1] == s and k[2] == "text"})
            diffs = [per_item[(i, s, "graph")]["modal_share"]
                     - per_item[(i, s, "text")]["modal_share"] for i in ids]
            nz = [d for d in diffs if d != 0]
            cmp_ = {"n_paired": len(ids), "n_nonzero_pairs": len(nz),
                    "median_paired_difference": median(diffs) if diffs else None}
            if len(nz) < MIN_PAIRS:
                # underpowered by construction. Reported, never tested, and the bound is
                # stated so a null here is not misread as an absence of effect.
                cmp_["test"] = None
                cmp_["reason_no_test"] = (
                    "%d non-zero pairs is below the pre-registered minimum of %d; the "
                    "smallest achievable two-sided p is %.4f"
                    % (len(nz), MIN_PAIRS, min(1.0, 2.0 / (2 ** len(nz))) if nz else 1.0))
            else:
                # graded_analyse.wilcoxon returns (p, n_nonzero, W_plus, method)
                p, n_nz, w_plus, method = wilcoxon(diffs)
                cmp_["test"] = {"p": p, "n_nonzero": n_nz, "W_plus": w_plus,
                                "method": method}
            blk["arm_comparison_graph_minus_text"] = cmp_
        out["strata"][s] = blk
    return out


def load_diagnostics(traces):
    """S10's load-state defect made visible. A load_duration spike marks a (re)load."""
    lds = [v.get("max_load_duration") or 0
           for r in traces["records"] for v in r["arms"].values()]
    spikes = [i for i, d in enumerate(lds) if d > 1e9]
    return {"ps_start": traces.get("ps_start"), "ps_end": traces.get("ps_end"),
            "n_units": len(traces["records"]),
            "load_spikes_over_1s": len(spikes),
            "spike_positions": spikes[:20],
            "max_load_duration_s": round(max(lds) / 1e9, 2) if lds else 0.0}


def render(out, diag):
    L = ["VARIANCE ANALYSIS (PREREGISTRATION-VARIANCE.md sections 3 and 4).",
         "temperature %s, N = %s repeats." % (out["temperature"], out["n_repeats"]),
         "",
         "PRIMARY: modal relied-provision-set share, the fraction of runs agreeing with",
         "the plurality relied_units set. STRATIFIED, NEVER POOLED. No headline number.",
         ""]
    for s, blk in out["strata"].items():
        L.append("%s" % s)
        for arm, a in blk["arms"].items():
            if not a["n_items"]:
                L.append("  %-6s no items" % arm)
                continue
            L.append("  %-6s n=%-3d median %.3f  mean %.3f  min %.3f  | all-identical %d"
                     "  | all-empty every run %d"
                     % (arm, a["n_items"], a["median_modal_share"], a["mean_modal_share"],
                        a["min_modal_share"], a["all_identical"], a["all_empty_every_run"]))
            L.append("         modal-count spread %s | distinct-set spread %s"
                     % (a["modal_count_distribution"], a["distinct_sets_distribution"]))
        c = blk.get("arm_comparison_graph_minus_text")
        if c:
            if c["test"] is None:
                L.append("  graph-text: %d paired, %d non-zero. NO TEST: %s"
                         % (c["n_paired"], c["n_nonzero_pairs"], c["reason_no_test"]))
            else:
                L.append("  graph-text: %d paired, %d non-zero, median diff %.3f, p = %s"
                         % (c["n_paired"], c["n_nonzero_pairs"],
                            c["median_paired_difference"], c["test"].get("p")))
        L.append("")
    if out["excluded_items"]:
        L.append("EXCLUDED, below %d usable repeats: %s"
                 % (out["min_usable"], out["excluded_items"]))
    else:
        L.append("EXCLUDED, below %d usable repeats: none" % out["min_usable"])
    L += ["",
          "LOAD STATE (S10). A load_duration spike marks a (re)load mid-run.",
          "  ps_start %s" % (diag["ps_start"],),
          "  ps_end   %s" % (diag["ps_end"],),
          "  spikes over 1s: %d of %d units, max %.2fs, at %s"
          % (diag["load_spikes_over_1s"], diag["n_units"],
             diag["max_load_duration_s"], diag["spike_positions"])]
    return "\n".join(L)


def handcheck(res, traces, n=3):
    """Print the raw relied sets the primary number is computed from, so a human can
    verify the modal share by eye. The pre-registration requires this on at least three
    real items across at least two strata BEFORE any number may be reported."""
    by = group(res, traces)
    seen, shown = set(), 0
    for k in sorted(by):
        if k[1] in seen and shown >= n:
            break
        if shown >= n and k[1] in seen:
            continue
        runs = usable_runs(by[k])
        if not runs:
            continue
        st = item_stats(runs)
        print("ITEM %s | stratum %s | arm %s | usable %d of %d"
              % (k[0], k[1], k[2], st["n_usable"], traces.get("repeats")))
        for r in sorted(runs):
            print("   run %2d  %s" % (r, sorted(runs[r]["relied_units"])))
        print("   -> distinct sets %d, modal count %d, MODAL SHARE %.3f"
              % (st["distinct_sets"], st["modal_count"], st["modal_share"]))
        print("   verify by hand: the most frequent list above should appear %d times "
              "of %d.\n" % (st["modal_count"], st["n_usable"]))
        seen.add(k[1])
        shown += 1


def selfcheck():
    """Hand-computable values. This is a new automatic component and the project has
    been burned twice by trusting one without a check."""
    def run(units, status="reached", error=None, cap=False):
        return {"relied_units": units, "status": status, "error": error,
                "turn_cap_hit": cap}

    # 7 runs of set A, 3 of set B -> modal share 0.7, 2 distinct, not all identical
    runs = {r: run(["u1"]) for r in range(1, 8)}
    runs.update({r: run(["u2"]) for r in range(8, 11)})
    st = item_stats(runs)
    assert st["n_usable"] == 10 and st["modal_count"] == 7, st
    assert abs(st["modal_share"] - 0.7) < 1e-12, st
    assert st["distinct_sets"] == 2 and not st["all_identical"], st

    # order within a set must not matter: ["a","b"] and ["b","a"] are the same set
    runs = {1: run(["a", "b"]), 2: run(["b", "a"]), 3: run(["a", "b"])}
    assert item_stats(runs)["modal_share"] == 1.0, "set equality is order sensitive"

    # all ten identical -> 1.0
    assert item_stats({r: run(["x"]) for r in range(1, 11)})["modal_share"] == 1.0

    # ten distinct -> 1/10, the floor of the scale
    st = item_stats({r: run(["u%d" % r]) for r in range(1, 11)})
    assert st["modal_share"] == 0.1 and st["distinct_sets"] == 10, st

    # errored repeats are dropped, turn-cap hits are NOT
    mixed = {1: run(["a"]), 2: run(["a"], error="boom"), 3: run(["b"], cap=True)}
    u = usable_runs(mixed)
    assert sorted(u) == [1, 3], u
    assert item_stats(u)["n_usable"] == 2 and item_stats(u)["turn_cap_hits"] == 1

    # an empty relied set that never changes is stable, and is flagged as empty
    st = item_stats({r: run([]) for r in range(1, 11)})
    assert st["modal_share"] == 1.0 and st["all_empty"], st

    # the minimum-pairs rule: 5 non-zero pairs must NOT be tested, 6 must be
    for npairs, expect_test in ((5, False), (6, True)):
        recs, rows = [], []
        for rep in range(1, 11):
            for i in range(npairs + 2):
                recs.append({"id": "i%d" % i, "repeat": rep})
                # graph always identical; text differs on the first npairs items
                text = ["a"] if (i >= npairs or rep <= 5) else ["b"]
                rows.append({"id": "i%d" % i, "stratum": "S",
                             "arms": {"graph": run(["a"]), "text": run(text)}})
        out = analyse({"items": rows}, {"records": recs, "repeats": 10})
        c = out["strata"]["S"]["arm_comparison_graph_minus_text"]
        assert c["n_nonzero_pairs"] == npairs, c
        assert (c["test"] is not None) == expect_test, (npairs, c)
        if not expect_test:
            assert "smallest achievable" in c["reason_no_test"]
        else:
            # assert the p value itself, not merely that a test object exists.
            # graph is identical every run and text differs on all 6 pairs in the same
            # direction, so the exact two-sided p is 2/2**6 = 0.03125.
            assert c["test"]["method"] == "exact", c["test"]
            assert abs(c["test"]["p"] - 2.0 / 2 ** 6) < 1e-12, c["test"]
            assert c["test"]["n_nonzero"] == npairs, c["test"]

    # an item below MIN_USABLE is excluded and listed rather than silently included
    recs, rows = [], []
    for rep in range(1, 11):
        recs.append({"id": "bad", "repeat": rep})
        rows.append({"id": "bad", "stratum": "S",
                     "arms": {"graph": run(["a"], error=None if rep < 8 else "boom")}})
    out = analyse({"items": rows}, {"records": recs, "repeats": 10})
    # 7 usable is below MIN_USABLE = 8, so it is excluded AND listed, never silently kept
    assert out["excluded_items"] == [
        {"id": "bad", "stratum": "S", "arm": "graph", "usable": 7}], out["excluded_items"]
    assert out["strata"]["S"]["arms"]["graph"]["n_items"] == 0, out
    print("variance_analyse.py self-check OK: modal share, set equality, the exclusion "
          "rules, the empty-set flag, and the minimum-pairs rule")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reach", nargs="?")
    ap.add_argument("traces", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--handcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    res = json.load(open(a.reach, encoding="utf-8"))
    traces = json.load(open(a.traces, encoding="utf-8"))
    if a.handcheck:
        return handcheck(res, traces)
    out = analyse(res, traces)
    diag = load_diagnostics(traces)
    text = render(out, diag)
    print(text)
    if a.out:
        json.dump({"analysis": out, "load": diag},
                  open(a.out, "w", encoding="utf-8"), indent=2)
        open(a.out.replace(".json", ".txt"), "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
