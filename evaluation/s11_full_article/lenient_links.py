"""Exploratory, NOT pre-registered: re-parse the links-condition answers that the frozen
parser (score.parse_answer) rejected, by repairing two observed format slips (a bare JSON
array, or an object missing its final closing brace), then rescore with score.score_answer.
Writes fullarticle.lenient_links.json. The pre-registered analysis is unchanged.
    python -B lenient_links.py   (needs the .venv for rdflib)
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score   # noqa: E402
import stores  # noqa: E402


def lenient(text):
    got = score.parse_answer(text)
    if got is not None:
        return got, "frozen"
    t = text.strip().strip("`").removeprefix("json").strip()
    for fix in (lambda s: '{"qualifications": %s}' % s, lambda s: s + "}"):
        got = score.parse_answer(fix(t))
        if got is not None:
            return got, "repaired"
    return None, "unparseable"


def main():
    corpus, graph = stores.load()
    traces = json.load(open(os.path.join(HERE, "fullarticle.traces.json"), encoding="utf-8"))
    rows = []
    for rec in traces["records"]:
        entries, how = lenient(rec["conditions"]["links"]["final"])
        s = score.score_answer(corpus, graph, rec["duty_id"], entries or [])
        g = score.score_answer(corpus, graph, rec["duty_id"],
                               score.parse_answer(rec["conditions"]["graph"]["final"]) or [])
        rows.append({"id": rec["id"], "article": rec["article"], "how": how,
                     "links_recall": s["primary"]["recall"], "graph_recall": g["primary"]["recall"]})
    out = {}
    for art in (13, 14):
        rs = [r for r in rows if r["article"] == art]
        lr = [r["links_recall"] for r in rs]
        out[art] = {"n": len(rs), "repaired": sum(r["how"] == "repaired" for r in rs),
                    "unparseable": sum(r["how"] == "unparseable" for r in rs),
                    "links_recall_mean": sum(lr) / len(lr), "links_recall_median": score.median(lr),
                    "links_complete": sum(1 for x in lr if x == 1.0),
                    "graph_recall_mean": sum(r["graph_recall"] for r in rs) / len(rs),
                    "wilcoxon_links_vs_graph": score.wilcoxon(
                        [r["links_recall"] - r["graph_recall"] for r in rs])}
    json.dump({"summary": out, "items": rows}, open(os.path.join(HERE, "fullarticle.lenient_links.json"),
              "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    assert lenient('[{"provision": "x"}]')[0] == [{"provision": "x"}]
    assert lenient('{"qualifications": [{"provision": "x"}]')[0] == [{"provision": "x"}]
    main()
