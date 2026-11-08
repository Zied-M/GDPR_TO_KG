"""The pre-registered stability analysis. PREREGISTRATION-STABILITY.md section 4 only.

PRIMARY, and it needs no new instrument: the relied-provision set read from the tool
trace (`relied_units`, which reach.py already computes and S7 already hand-checked). An
item is STABLE when all five runs produce the identical relied-provision set. The reach
status is reported alongside as a second, coarser stability line.

SECONDARY is GATED and is NOT implemented here. The provisions cited in the final answer
need a prose parser, which owes a hand-check on the same terms reach.py paid in S7 before
it may produce any number. It is not built, so it produces none, and it may not be swapped
in after the fact as a rescue for a disappointing primary result.

PER-ITEM RESOLUTION. Agreement across five runs on one item is an inter-rater problem with
five raters. Items are reported by HOW MANY of the five agree, not only as stable or not,
because that gradient is what N = 5 was chosen to expose.

STRATIFY, NEVER POOL. Same boundary as the reach study.

THE LIMITATION, from section 5 and not discovered afterwards: at temperature 0.0 this
measures HARNESS REPRODUCIBILITY, not generation variance. A high figure is a FLOOR, not
a finding, and no draft may present it as answering whether an LLM justification "can be
undeterministic and can change". That needs temperature above 0 and its own
pre-registration.

    .venv/Scripts/python.exe paper_draft/s6_tools/stability_analyse.py \
        stability.reach.json --traces stability.traces.json
    .venv/Scripts/python.exe paper_draft/s6_tools/stability_analyse.py --selfcheck
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse import wilson  # noqa: E402  same interval, one implementation

N_REPEATS = 5


def group(res, traces):
    """Key each scored row by (item id, repeat, arm).

    reach.py records only the id, so the repeat comes from the traces file it was scored
    from. The two are in the same order by construction; that is asserted rather than
    assumed, because a silent misalignment here would scramble every item's five runs.
    """
    recs = traces["records"]
    rows = res["items"]
    assert len(recs) == len(rows), "reach output and traces are different lengths"
    out = defaultdict(dict)
    for rec, row in zip(recs, rows):
        assert rec["id"] == row["id"], "reach output and traces are misaligned"
        for arm, scored in row["arms"].items():
            out[(row["id"], row["stratum"], arm)][rec["repeat"]] = scored
    return out


def largest_agreeing(values):
    """How many of the five runs share the most common value. 5 = fully stable."""
    return max(Counter(values).values()) if values else 0


def analyse(res, traces, n_repeats=N_REPEATS):
    by = group(res, traces)
    strata = sorted({k[1] for k in by})
    arms = sorted({k[2] for k in by})
    out = {"n_repeats": n_repeats, "strata": {}, "incomplete_items": []}

    for s in strata:
        blk = {}
        for arm in arms:
            keys = [k for k in by if k[1] == s and k[2] == arm]
            stable = partial = 0
            gradient = Counter()
            status_stable = 0
            for k in sorted(keys):
                runs = by[k]
                if len(runs) != n_repeats:
                    out["incomplete_items"].append(
                        {"id": k[0], "arm": arm, "runs": len(runs)})
                    continue
                sets = [tuple(sorted(runs[r]["relied_units"])) for r in sorted(runs)]
                agree = largest_agreeing(sets)
                gradient[agree] += 1
                if agree == n_repeats:
                    stable += 1
                else:
                    partial += 1
                sts = [runs[r]["status"] for r in sorted(runs)]
                if largest_agreeing(sts) == n_repeats:
                    status_stable += 1
            n = stable + partial
            blk[arm] = {
                "n_items": n, "stable": stable, "unstable": partial,
                "proportion": (stable / n) if n else None,
                "wilson95": wilson(stable, n),
                "gradient_runs_agreeing": dict(sorted(gradient.items(), reverse=True)),
                "status_stable": status_stable,
                "status_proportion": (status_stable / n) if n else None,
            }
        out["strata"][s] = blk
    return out


def render(out):
    L = ["PRE-REGISTERED STABILITY ANALYSIS (PREREGISTRATION-STABILITY.md section 4).",
         "",
         "PRIMARY: proportion of items whose RELIED-PROVISION SET is identical across all",
         "%d runs, per arm, per stratum, with Wilson intervals. Stratified, never pooled."
         % out["n_repeats"],
         "",
         "AT TEMPERATURE 0.0 THIS IS HARNESS REPRODUCIBILITY, NOT GENERATION VARIANCE.",
         "A high figure is a FLOOR, not a finding. It does not answer whether an LLM",
         "justification can change between runs; that needs temperature above 0.",
         ""]
    hdr = "%-8s %-6s %5s %7s %9s  %-18s %s" % (
        "stratum", "arm", "n", "stable", "unstable", "proportion [95% CI]", "status stable")
    L.append(hdr)
    L.append("-" * len(hdr))
    for s, blk in out["strata"].items():
        for arm, a in blk.items():
            ci = a["wilson95"]
            p = ("%.3f [%.3f,%.3f]" % (a["proportion"], ci[0], ci[1])) if ci else "n/a"
            L.append("%-8s %-6s %5d %7d %9d  %-18s %d/%d" % (
                s, arm, a["n_items"], a["stable"], a["unstable"], p,
                a["status_stable"], a["n_items"]))
    L.append("")
    L.append("PER-ITEM RESOLUTION: how many of the %d runs agree on the relied-provision set."
             % out["n_repeats"])
    L.append("Reported as a gradient because that is what N = %d was chosen to expose."
             % out["n_repeats"])
    L.append("")
    L.append("%-8s %-6s %s" % ("stratum", "arm", "runs agreeing -> items"))
    L.append("-" * 52)
    for s, blk in out["strata"].items():
        for arm, a in blk.items():
            L.append("%-8s %-6s %s" % (s, arm, a["gradient_runs_agreeing"]))
    if out["incomplete_items"]:
        L.append("")
        L.append("INCOMPLETE ITEMS (fewer than %d runs), excluded and reported:"
                 % out["n_repeats"])
        for i in out["incomplete_items"]:
            L.append("  %s %s: %d runs" % (i["id"], i["arm"], i["runs"]))
    L.append("")
    L.append("SECONDARY (provisions cited in the final answer): NOT COMPUTED.")
    L.append("It needs a prose parser that owes a hand-check before it may produce any")
    L.append("number. The parser is not built, so this line produces none, per section 3.")
    return "\n".join(L)


def selfcheck():
    assert largest_agreeing([1, 1, 1, 1, 1]) == 5
    assert largest_agreeing([1, 1, 1, 1, 2]) == 4
    assert largest_agreeing([1, 2, 3, 4, 5]) == 1
    assert largest_agreeing([]) == 0

    def run(units, status="reached"):
        return {"relied_units": units, "status": status}

    traces = {"records": [
        {"id": "a", "repeat": r, "stratum": "S", "arms": {}} for r in range(1, 6)
    ] + [
        {"id": "b", "repeat": r, "stratum": "S", "arms": {}} for r in range(1, 6)
    ]}
    res = {"items": [
        # item a: identical every run in graph, one deviation in text
        {"id": "a", "stratum": "S", "arms": {"graph": run(["p1", "p2"]),
                                             "text": run(["p1"])}} for _ in range(5)
    ] + [
        {"id": "b", "stratum": "S", "arms": {"graph": run(["p9"]),
                                             "text": run(["p9"])}} for _ in range(5)
    ]}
    # order matters: zip pairs traces[i] with res[i], so make a's text run 3 deviate
    res["items"][2]["arms"]["text"] = run(["p1", "pX"])
    o = analyse(res, traces)["strata"]["S"]
    assert o["graph"]["stable"] == 2 and o["graph"]["proportion"] == 1.0, o["graph"]
    assert o["text"]["stable"] == 1 and o["text"]["unstable"] == 1, o["text"]
    assert o["text"]["gradient_runs_agreeing"] == {5: 1, 4: 1}, o["text"]

    # a short item is reported, never silently averaged away
    traces2 = {"records": [{"id": "c", "repeat": r, "stratum": "S", "arms": {}}
                           for r in range(1, 4)]}
    res2 = {"items": [{"id": "c", "stratum": "S", "arms": {"graph": run(["p1"])}}
                      for _ in range(3)]}
    o2 = analyse(res2, traces2)
    assert o2["incomplete_items"] == [{"id": "c", "arm": "graph", "runs": 3}], o2
    assert o2["strata"]["S"]["graph"]["n_items"] == 0

    print("stability_analyse.py self-check OK: gradient, stable/unstable split, and the "
          "incomplete-item report")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reach", nargs="?")
    ap.add_argument("--traces", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if not a.reach or not a.traces:
        raise SystemExit("need the reach output and --traces, or --selfcheck")
    res = json.load(open(a.reach, encoding="utf-8"))
    traces = json.load(open(a.traces, encoding="utf-8"))
    out = analyse(res, traces, traces.get("repeats", N_REPEATS))
    text = render(out)
    print(text)
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2)
        open(a.out.replace(".json", ".txt"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
