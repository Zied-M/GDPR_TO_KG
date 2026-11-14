"""Agreement between the automatic entailment metric and an external annotator.

WHAT THIS IS AND IS NOT. The Part C validation asks whether the automatic metric can be
trusted on this data. Its reference standard is meant to be a PERSON. The annotator here
is a strong external LLM (GPT Astra High), supplied by the author on the grounds that they
are not a domain expert. That substitution is recorded, not hidden, and it caps what this
number can support: an LLM annotator is a second automatic judgement, so a disagreement
tells you the two instruments disagree, and an agreement would NOT establish that either
is right. Nothing here validates the metric on its own.

Reported per class, and weighted back to the pilot, because the 100-row subset is
deliberately enriched for the rare classes (see make_subset.py). A raw percentage over it
is not an estimate of anything.

Run: <LexiGen venv>/python.exe agreement.py [sheet.csv] [annotator column]
"""
import csv, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = sys.argv[1] if len(sys.argv) > 1 else "labels.sheet.100.v2.csv"
COL = sys.argv[2] if len(sys.argv) > 2 else "GPT ASTRA Verdict"
FIELD = sys.argv[3] if len(sys.argv) > 3 else "entailment"   # or entailment_decomposed
LABELS = ["entailed", "neutral", "contradicted"]


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, SHEET), encoding="utf-8-sig")))
    key = {r["row_id"]: r for r in
           json.load(open(os.path.join(HERE, "labels.key.json"), encoding="utf-8"))["rows"]}
    meta = json.load(open(os.path.join(HERE, "subset.100.meta.json"), encoding="utf-8"))
    scored = json.load(open(os.path.join(HERE, "pilot.llama3_latest.scored.json"), encoding="utf-8"))

    auto = {}
    for rec in scored["records"]:
        for arm, res in rec["arms"].items():
            for r in res["citations_resolved"]:
                if r.get(FIELD):
                    auto[(rec["id"], arm, r["canonical"])] = r[FIELD]

    pairs = []
    for r in rows:
        k = key[r["row_id"]]
        a = auto.get((k["item"], k["arm"], k["cited_provision"]))
        b = (r.get(COL) or "").strip().lower()
        if a and b in LABELS:
            pairs.append((a, b, k["arm"], k["stratum"]))

    n = len(pairs)
    cm = defaultdict(int)
    for a, b, _, _ in pairs:
        cm[(a, b)] += 1
    agree = sum(cm[(l, l)] for l in LABELS)

    per_class = {}
    for a in LABELS:
        tot = sum(cm[(a, b)] for b in LABELS)
        if tot:
            per_class[a] = {"n": tot, "agreed": cm[(a, a)], "pct": round(100 * cm[(a, a)] / tot, 1)}

    w = meta["weights_to_pilot"]
    num = sum(cm[(a, a)] * w.get(a, 1) for a in LABELS)
    den = sum(cm[(a, b)] * w.get(a, 1) for a in LABELS for b in LABELS)

    ra, rb = Counter(a for a, _, _, _ in pairs), Counter(b for _, b, _, _ in pairs)
    pe = sum(ra[l] * rb[l] for l in LABELS) / (n * n)
    kappa = ((agree / n) - pe) / (1 - pe)

    out = {
        "metric_field": FIELD,
        "annotator": COL,
        "annotator_is_an_llm": True,
        "caveat": "an LLM annotator is a second automatic judgement; agreement would not "
                  "establish correctness and this does not complete the Part C validation",
        "n": n,
        "raw_agreement_enriched_subset": round(100 * agree / n, 1),
        "weighted_back_to_pilot": round(100 * num / den, 1),
        "cohens_kappa": round(kappa, 3),
        "kappa_scale": "landis1977agreement: <0.00 poor, 0.00-0.20 slight, 0.21-0.40 fair",
        "per_class_metric_vs_annotator": per_class,
        "confusion_metric_rows_annotator_cols": {a: {b: cm[(a, b)] for b in LABELS} for a in LABELS},
        "annotator_label_use": dict(rb),
        "metric_label_use": dict(ra),
    }
    suffix = "" if FIELD == "entailment" else "." + FIELD
    json.dump(out, open(os.path.join(HERE, f"agreement{suffix}.json"), "w"), indent=2)

    print(f"n = {n}   annotator = {COL}   metric field = {FIELD}")
    print(f"raw agreement on the enriched subset : {out['raw_agreement_enriched_subset']}%  (not a pilot rate)")
    print(f"weighted back to the pilot           : {out['weighted_back_to_pilot']}%")
    print(f"Cohen's kappa                        : {out['cohens_kappa']}  ({out['kappa_scale']})")
    print("\nper class, metric vs annotator:")
    for a, v in per_class.items():
        print(f"  metric said {a:>13}: annotator agreed {v['agreed']:>3}/{v['n']:<3} = {v['pct']:>5}%")
    print(f"\nlabel use  metric: {dict(ra)}\n           annot.: {dict(rb)}")
    print("\nwrote agreement.json")


if __name__ == "__main__":
    main()
