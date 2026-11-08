"""The reach extractor. Reads a trace, answers one question, needs no gold key.

    While relying on duty D, did the trace surface a relation the graph attaches to D
    FROM A DIFFERENT PROVISION?

Per 05_EVAL_PLAN.md E2. This is the first measure in this project that requires no
reference standard at all: relevance is defined relative to the model's own work, never
against a gold key, which is what keeps the rejected claim-to-duty matcher out of the
design.

THE THREE DEFINITIONS, and they are the whole extractor.

1. RELIANCE is anchored at the PROVISION, not at the duty id.
   A model relies on a provision when it passes that provision's handle to
   get_conditions. In the text arm the handle IS a provision; in the graph arm the
   handle is a duty id, which resolves to the provision the duty is grounded in. Both
   are then expanded downward: naming a paragraph relies on the duties in its points.
   The relied-upon duty set is every duty grounded in a relied-upon provision.

   Anchoring at the provision is the only definition computable IDENTICALLY in both
   arms, and it is neutral rather than generous: the one-to-many expansion (up to 6
   duties on one provision) inflates the graph arm's target set exactly as much as the
   text arm's. Anchoring at the duty id instead would give the graph arm a smaller and
   easier target set than the text arm's, which is a thumb on the scale.
   The direct duty ids are recorded anyway, as `relied_duties_direct`, so a later
   session can recompute under the other definition without a rerun.

2. A TARGET is a (duty, relation) pair where the graph grounds the relation in a
   different provision than the duty. Same-provision relations are excluded: reaching
   those needs no representation. 223 of the 258 attachments qualify.

3. SURFACED is read from the trace's machine provenance, never from prose. A target
   relation R is surfaced if EITHER
     (a) R was returned as a relation node  (only the graph store does this), OR
     (b) the TEXT of a provision R is grounded in was returned by any tool.
   Both tests run in both arms. (b) is the text arm's escape route and it is
   deliberate: the text arm may search for the exception directly, or meet it in a
   sibling expansion, and find it on its own. A null is therefore a live outcome.

OUTPUTS. Per item primary, per duty-relation pair secondary. Every item carries a
status so that a zero is never confused with an absence:
    reached          - at least one target relation surfaced
    not_reached      - targets existed and none surfaced
    no_targets       - the relied duties carry no cross-provision relations
                       (all Article 46 items land here: it has 0, as pre-registered)
    no_reliance      - the model never called get_conditions, so it relied on no duty
                       and the question does not arise. Reported separately, never
                       counted as a failure to reach.

    .venv/Scripts/python.exe paper_draft/s6_tools/reach.py traces.json --out reach.json
    .venv/Scripts/python.exe paper_draft/s6_tools/reach.py --selfcheck
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stores  # noqa: E402
from stores import TextStore  # noqa: E402


def relied_units(trace, corpus, graph):
    """The provisions the model leaned on: every get_conditions argument, resolved."""
    direct_duties, units = [], []
    for step in trace:
        if step.get("call") != "get_conditions":
            continue
        handle = str((step.get("args") or {}).get("duty_id", "")).strip()
        if not handle:
            continue
        d = graph.duties.get(handle)
        if d:                                   # graph arm: a duty id
            direct_duties.append(handle)
            seeds = d["grounded_in"]
        else:                                   # text arm: a provision citation
            uid = corpus.resolve(handle)
            seeds = [uid] if uid else []        # unresolved handle relies on nothing
        for s in seeds:
            for u in corpus.closure(s):
                if u not in units:
                    units.append(u)
    return sorted(units), sorted(set(direct_duties))


def surfaced_sets(trace, corpus):
    """What the trace actually put in front of the model, from provenance alone.

    Text coverage is computed over CHARACTER SPANS, not over unit ids, and the
    difference is not cosmetic. Relations ground at any level: cond-12-5-unfounded-
    excessive grounds in the paragraph art12-p5, while the text store's sibling
    expansion returns that paragraph as its four subunits. Matching on unit ids alone
    calls that unreached when the model read every word of it, which is a false
    negative AGAINST THE TEXT ARM, in a measure whose credibility rests on the
    baseline not being cheated. Spans also handle the other direction for free: a
    returned paragraph covers the point a relation grounds in.
    """
    relations, spans = set(), {}
    for step in trace:
        p = step.get("provenance") or {}
        relations.update(p.get("relations") or [])
        for uid in (p.get("units_text") or []):
            u = corpus.units.get(uid)
            if u:
                spans.setdefault(article_of(uid), []).append((u["char_start"], u["char_end"]))
    return {a: merge(v, corpus.text[int(a[3:])]) for a, v in spans.items()}, relations


def article_of(unit_id):
    return unit_id.split("-")[0]


def merge(intervals, text):
    """Adjacent units are separated by the separator character the offsets skip, so
    two returned units join when the source between them is whitespace only. Exact,
    read off the pinned source, rather than a tolerance constant."""
    out = []
    for s, e in sorted(intervals):
        if out and (s <= out[-1][1] or not text[out[-1][1]:s].strip()):
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def covered(unit_id, corpus, spans):
    """Was this provision's text returned, whole, at any granularity?"""
    u = corpus.units.get(unit_id)
    if not u:
        return False
    return any(s <= u["char_start"] and u["char_end"] <= e
               for s, e in spans.get(article_of(unit_id), []))


def score_trace(run, corpus, graph):
    trace = run.get("trace") or []
    units, direct = relied_units(trace, corpus, graph)
    duties = graph.duties_for_units(units)
    seen_spans, seen_rels = surfaced_sets(trace, corpus)

    pairs = []
    for d in duties:
        for r in graph.cross_provision_relations(d):
            by_node = r["relation_id"] in seen_rels
            by_text = any(covered(u, corpus, seen_spans) for u in r["grounded_in"])
            pairs.append({"duty_id": d, "relation_id": r["relation_id"], "kind": r["kind"],
                          "relation_cites": r["grounded_in"],
                          "surfaced": by_node or by_text,
                          "how": "relation_node" if by_node else ("provision_text" if by_text
                                                                  else None)})
    hit = sum(1 for p in pairs if p["surfaced"])
    if not units:
        status = "no_reliance"
    elif not pairs:
        status = "no_targets"
    else:
        status = "reached" if hit else "not_reached"
    return {
        "arm": run.get("arm"), "status": status,
        "relied_units": units, "relied_duties": duties, "relied_duties_direct": direct,
        "n_targets": len(pairs), "n_surfaced": hit,
        "turns": run.get("turns"), "calls": run.get("calls"),
        "turn_cap_hit": run.get("turn_cap_hit"), "error": run.get("error"),
        "pairs": pairs,
    }


def extract(traces):
    corpus, graph = stores.load()
    out = []
    for rec in traces["records"]:
        row = {"id": rec["id"], "stratum": rec["stratum"], "article": rec["article"],
               "arms": {arm: score_trace(run, corpus, graph)
                        for arm, run in rec["arms"].items()}}
        out.append(row)
    return {"source": traces.get("generated_at"), "model": traces.get("model"),
            "model_digest": traces.get("model_digest"), "num_ctx": traces.get("num_ctx"),
            "turn_cap": traces.get("turn_cap"), "k": traces.get("k"),
            "sample_file": traces.get("sample_file"), "split": traces.get("split"),
            "n_items": len(out), "items": out}


def summarise(res):
    """Per stratum per arm. Statuses are listed apart; a zero is never a null."""
    lines = []
    arms = sorted({a for it in res["items"] for a in it["arms"]})
    strata = sorted({it["stratum"] for it in res["items"]})
    lines.append("%-9s %-6s %4s  %-42s %s" % ("stratum", "arm", "n", "item status", "pairs"))
    for s in strata:
        for arm in arms:
            rows = [it["arms"][arm] for it in res["items"]
                    if it["stratum"] == s and arm in it["arms"]]
            if not rows:
                continue
            c = Counter(r["status"] for r in rows)
            t = sum(r["n_targets"] for r in rows)
            h = sum(r["n_surfaced"] for r in rows)
            lines.append("%-9s %-6s %4d  %-42s %d/%d" % (
                s, arm, len(rows),
                " ".join("%s=%d" % (k, c[k]) for k in
                         ("reached", "not_reached", "no_targets", "no_reliance") if c[k]),
                h, t))
    return "\n".join(lines)


# --------------------------------------------------------------------- self-check

def _step(call, args, units_text=(), relations=(), duties=()):
    return {"call": call, "args": args,
            "provenance": stores._prov(units_text=units_text, relations=relations,
                                       duties=duties)}


def _selfcheck():
    corpus, graph = stores.load()
    duty = graph.by_unit["art14-p1-c"][0]
    xs = graph.cross_provision_relations(duty)
    assert xs, "fixture assumes 14(1)(c)'s duty carries cross-provision relations"
    exc = [r for r in xs if r["grounded_in"] == ["art14-p5-a"]][0]

    # 1. graph arm, get_conditions returns the relation nodes -> reached by node
    r = score_trace({"arm": "graph", "trace": [
        _step("find_duties", {"topic": "categories"}, duties=[duty]),
        _step("get_conditions", {"duty_id": duty},
              relations=[x["relation_id"] for x in graph.duties[duty]["relations"]],
              duties=[duty])]}, corpus, graph)
    assert r["status"] == "reached" and r["n_surfaced"] == r["n_targets"] > 0
    assert all(p["how"] == "relation_node" for p in r["pairs"])

    # 2. text arm, sibling expansion only -> NOTHING cross-provision is reached.
    #    The fixture uses the real store's provenance, not a hand-built unit list: the
    #    expansion excludes the queried unit itself, so the union of what comes back
    #    has a hole in it and does not cover the parent paragraph. Building the list by
    #    hand got this wrong during the hand-check and made the case pass for the wrong
    #    reason. Structurally, 0 of the 223 cross-provision attachments are reachable
    #    by sibling expansion alone, which is what E3 asserts.
    _, sib_prov = TextStore(corpus, graph, 14).get_conditions("Article 14(1)(c)")
    sibs = sib_prov["units_text"]
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 14(1)(c)"}, units_text=sibs)]},
        corpus, graph)
    assert r["status"] == "not_reached", r["status"]
    assert r["n_targets"] > 0 and r["n_surfaced"] == 0

    # 2b. but find_duties normally ALSO returns the duty's own provision, which plugs
    #     the hole and covers the whole paragraph. A relation grounded in that chapeau
    #     is then genuinely reached by the text arm, and the extractor must say so.
    #     Structurally this is 40 of the 223, all of them parent-grounded; the other
    #     183 stay out of the text store's reach on any path short of the model
    #     searching for the exception itself. Found by hand-checking seg00808.
    r2 = score_trace({"arm": "text", "trace": [
        _step("find_duties", {"topic": "categories"}, units_text=["art14-p1-c"]),
        _step("get_conditions", {"duty_id": "Article 14(1)(c)"}, units_text=sibs)]},
        corpus, graph)
    assert r2["status"] == "reached" and 0 < r2["n_surfaced"] < r2["n_targets"]
    assert all(p["relation_cites"] == ["art13-p1", "art14-p1"]
               for p in r2["pairs"] if p["surfaced"])
    assert not [p for p in r2["pairs"] if p["relation_id"] == exc["relation_id"]][0]["surfaced"]
    # and the two arms must be looking at the SAME targets
    assert r["n_targets"] == score_trace({"arm": "graph", "trace": [
        _step("get_conditions", {"duty_id": duty})]}, corpus, graph)["n_targets"]

    # 3. the text arm's escape route: it finds 14(5)(a) itself -> reached by text
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 14(1)(c)"}, units_text=sibs),
        _step("get_provision", {"citation": "Article 14(5)(a)"}, units_text=["art14-p5-a"])]},
        corpus, graph)
    assert r["status"] == "reached"
    got = [p for p in r["pairs"] if p["relation_id"] == exc["relation_id"]]
    assert got and got[0]["how"] == "provision_text", got

    # 4. no get_conditions at all -> no_reliance, NOT a failure to reach
    r = score_trace({"arm": "text", "trace": [
        _step("find_duties", {"topic": "x"}, units_text=["art14-p1-c"])]}, corpus, graph)
    assert r["status"] == "no_reliance" and r["n_targets"] == 0

    # 5. Article 46 is the pre-registered null: reliance, but no targets anywhere
    d46 = graph.by_unit["art46-p2-a"][0] if "art46-p2-a" in graph.by_unit else \
        [d for d in graph.duties if graph.duties[d]["grounded_in"][0].startswith("art46-")][0]
    r = score_trace({"arm": "graph", "trace": [
        _step("get_conditions", {"duty_id": d46}, duties=[d46])]}, corpus, graph)
    assert r["status"] == "no_targets" and r["n_targets"] == 0

    # 6. an unresolvable handle relies on nothing rather than silently on everything
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 99(1)"})]}, corpus, graph)
    assert r["status"] == "no_reliance"

    # 7. reliance on a chapeau reaches the duties in its points
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 14(1)"})]}, corpus, graph)
    assert r["relied_duties"] and r["n_targets"] > 0

    # 8. span coverage, both directions. Found by eye on handcheck trace seg01511,
    #    where the text arm read all four subunits of art12-p5 and a unit-id match
    #    called the paragraph-grounded condition unreached.
    fee = graph.by_unit["art12-p5-a"][0]
    cond = graph.cross_provision_relations(fee)
    assert [r["grounded_in"] for r in cond] == [["art12-p5"]], cond
    subunits = ["art12-p5-sub1", "art12-p5-a", "art12-p5-b", "art12-p5-sub2"]
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 12(5), subparagraph 1"},
              units_text=subunits)]}, corpus, graph)
    assert r["status"] == "reached" and all(p["how"] == "provision_text" for p in r["pairs"])
    # the other direction: a returned paragraph covers the point a relation grounds in
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "Article 14(1)(c)"}, units_text=sibs),
        _step("get_provision", {"citation": "Article 14(5)"}, units_text=["art14-p5"])]},
        corpus, graph)
    assert any(p["relation_id"] == exc["relation_id"] and p["how"] == "provision_text"
               for p in r["pairs"])
    # and a PARTIAL read never counts: drop one subunit and the span no longer covers
    r = score_trace({"arm": "text", "trace": [
        _step("get_conditions", {"duty_id": "x"}, units_text=subunits[1:])]}, corpus, graph)
    assert r["status"] == "no_reliance"   # handle unresolvable, so check coverage directly
    sp, _ = surfaced_sets([_step("f", {}, units_text=subunits[1:])], corpus)
    assert not covered("art12-p5", corpus, sp)
    assert covered("art12-p5", corpus, surfaced_sets(
        [_step("f", {}, units_text=subunits)], corpus)[0])

    # 9. same-provision relations are never counted as targets
    for d in graph.duties:
        own = set(graph.duties[d]["grounded_in"])
        for x in graph.cross_provision_relations(d):
            assert not (set(x["grounded_in"]) & own)

    print("reach.py self-check OK: 10 cases")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("traces", nargs="?")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck or not a.traces:
        return _selfcheck()
    res = extract(json.load(open(a.traces, encoding="utf-8")))
    out = a.out or a.traces.replace(".json", "") + ".reach.json"
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(summarise(res))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
