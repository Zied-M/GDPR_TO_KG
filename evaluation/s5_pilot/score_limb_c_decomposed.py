"""Limb (c), rebuilt with per-claim decomposition. The repair of 2026-09-13.

WHY. The first construction asked the entailment model a badly posed question: premise =
one provision, hypothesis = the WHOLE justification. A justification routinely asserts more
than any single cited provision can support, so "neutral" is the mechanically correct answer
to most of those pairs, and 84.7% neutral is what came back. `ALCE` decomposes the claim
before scoring, and that is what this does.

HOW. Each justification is split into its individual claims. Each cited provision is scored
against each claim separately. The per-citation verdict then aggregates:

    entailed      the provision entails AT LEAST ONE claim
    contradicted  it contradicts at least one claim and entails none
    neutral       otherwise

The unit of judgement is still the CITATION, deliberately, so the result stays directly
comparable to the existing annotations, which are one row per citation. Changing the unit
as well as the construction would have made the two uncomparable.

Both scores are kept. `entailment` is the original whole-justification verdict and
`entailment_decomposed` is this one, so the repair can be judged rather than assumed.

Run: <LexiGen venv>/python.exe score_limb_c_decomposed.py pilot.llama3_latest.scored.json
"""
import json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_pilot import nli_scores  # noqa: E402

MIN_CLAIM_CHARS = 25
# split after . ? ! when followed by space and a capital, but not after a lone initial or
# a known abbreviation, which do occur in these justifications ("Art. 13", "e.g.")
_SPLIT = re.compile(r"(?<![A-Z])(?<!Art)(?<!art)(?<!e\.g)(?<!i\.e)[.?!]+\s+(?=[A-Z(])")


def claims(text):
    parts = [p.strip() for p in _SPLIT.split((text or "").strip()) if p.strip()]
    merged = []
    for p in parts:
        if merged and len(p) < MIN_CLAIM_CHARS:
            merged[-1] = merged[-1] + " " + p
        else:
            merged.append(p)
    return merged or ([text.strip()] if (text or "").strip() else [])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "pilot.llama3_latest.scored.json")
    pilot = json.load(open(path, encoding="utf-8"))

    pairs, index = [], []
    nclaims = []
    for rec in pilot["records"]:
        for arm, res in rec["arms"].items():
            d = res["parsed"] or {}
            cs = claims(d.get("justification"))
            nclaims.append(len(cs))
            for r in res["citations_resolved"]:
                if r["bucket"] not in ("resolved", "graph_node_id") or not r.get("text"):
                    continue
                for j, c in enumerate(cs):
                    pairs.append((r["text"], c))
                    index.append((rec["id"], arm, r["canonical"], j))

    print(f"claims per justification: mean {sum(nclaims)/len(nclaims):.1f}, "
          f"max {max(nclaims)}")
    print(f"limb (c) pairs to judge: {len(pairs)}  "
          f"(was {len(set((i[0], i[1], i[2]) for i in index))} under the old construction)")

    verdicts = nli_scores(pairs) if pairs else []
    per_cite = defaultdict(list)
    for (sid, arm, canon, j), v in zip(index, verdicts):
        per_cite[(sid, arm, canon)].append(v)

    for rec in pilot["records"]:
        for arm, res in rec["arms"].items():
            out = []
            for r in res["citations_resolved"]:
                if r["bucket"] not in ("resolved", "graph_node_id") or not r.get("text"):
                    continue
                vs = per_cite.get((rec["id"], arm, r["canonical"]), [])
                if "entailed" in vs:
                    v = "entailed"
                elif "contradicted" in vs:
                    v = "contradicted"
                else:
                    v = "neutral"
                r["entailment_decomposed"] = v
                r["entailment_per_claim"] = vs
                out.append(v)
            res["limb_c_decomposed"] = out

    pilot.setdefault("scoring", {})["limb_c_decomposed"] = {
        "construction": "premise = provision, hypothesis = each claim separately",
        "aggregation": "entailed if any claim entailed; else contradicted if any contradicted; else neutral",
        "unit": "citation, unchanged, so annotations stay comparable",
    }
    json.dump(pilot, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    old = Counter(v for rec in pilot["records"] for res in rec["arms"].values()
                  for v in res.get("limb_c", []))
    new = Counter(v for rec in pilot["records"] for res in rec["arms"].values()
                  for v in res.get("limb_c_decomposed", []))
    print(f"\nold (whole justification): {dict(old)}")
    print(f"new (per claim)          : {dict(new)}")
    t = sum(new.values())
    if t:
        print(f"neutral share: {100*old['neutral']/max(sum(old.values()),1):.1f}% -> "
              f"{100*new['neutral']/t:.1f}%")
    print(f"\nrewrote {path}")


if __name__ == "__main__":
    main()
