"""S8 sample re-freeze. Deterministic, seeded, digested.

Adapted from `s5_pilot/freeze_sample.py`, which froze the sample against a GROUNDING
measure and therefore fits a RELATIONS measure badly: it put 100 of 250 study items on
Article 46, which carries ZERO cross-provision attachments and is the pre-registered
null rather than half the study.

Draws the Part E study set and a DISJOINT pilot from LexiGen_corpus.json, under
`05_EVAL_PLAN.md` E4:
  - the shape is re-weighted onto where the relations are: Article 14 (159
    cross-provision attachments), Article 13 (62), Article 12 (2, a predicted null),
    Article 46 (0, the pre-registered null)
  - the 2026-09-13 pairing SURVIVES and is not reopened: Article 46's applicable
    segments are drawn alongside its not-applicable ones as a same-article control,
    without which a null on the not-applicable stratum cannot be told apart from
    Article 46's thin graph
  - NEW SEED. 20260913 is not reused: the strata changed, a same-seed draw is not
    comparable to the old one, and implying otherwise would be worse than a clean break.

The label-balancing, the by-construction disjointness and the digest machinery are
carried over unchanged; they were not what was wrong.

Nothing here is a result. Run with the LexiGen corpus path as argv[1].
"""
import json, sys, os, hashlib, random
from collections import Counter, defaultdict

SEED = 20260915
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sample.frozen.json")
CORPUS = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ziedm\Desktop\M2_ENSI\Memoire\LexiGen-main\LexiGen-main\corpus_creation\data\LexiGen_corpus.json"

# stratum -> (article, label(s), n_study, n_pilot). E4's shape: 100/75/25/25/25 study,
# the pilot of 40 on the same proportions. Pool headroom checked: every stratum's draw
# fits inside the 191 segments per article with room.
PLAN = [
    ("APP-14",  14, ("COMPLIANT", "NON_COMPLIANT"), 100, 16),
    ("APP-13",  13, ("COMPLIANT", "NON_COMPLIANT"),  75, 12),
    ("APP-12",  12, ("COMPLIANT", "NON_COMPLIANT"),  25,  4),
    ("APP-46",  46, ("COMPLIANT", "NON_COMPLIANT"),  25,  4),
    ("NA-46",   46, ("NOT_APPLICABLE",),             25,  4),
]


def seg_key(g):
    """Stable id: global flatten index. Digest of the text is carried beside it."""
    return f"seg{g:05d}"


def main():
    raw = open(CORPUS, encoding="utf-8").read()
    corpus_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    data = json.loads(raw)

    segs = []
    g = 0
    for b in data:
        for s in b["segments"]:
            segs.append({
                "id": seg_key(g),
                "global_index": g,
                "batch_id": b["batch_id"],
                "article": s["gdpr_article_number"],
                "label": s["label"],
                "text_sha256_16": hashlib.sha256(s["segment"].encode("utf-8")).hexdigest()[:16],
            })
            g += 1
    assert len(segs) == 8977, len(segs)

    pools = defaultdict(list)
    for s in segs:
        pools[(s["article"], s["label"])].append(s)
    for k in pools:
        pools[k].sort(key=lambda s: s["global_index"])

    rng = random.Random(SEED)
    out = {"study": [], "pilot": []}
    report = []

    for name, art, labels, n_study, n_pilot in PLAN:
        need = n_study + n_pilot
        # split the draw evenly across the labels in the stratum, remainder to the first
        per = [need // len(labels)] * len(labels)
        for i in range(need - sum(per)):
            per[i] += 1
        drawn = []
        for lab, k in zip(labels, per):
            pool = pools[(art, lab)]
            if len(pool) < k:
                raise SystemExit(f"{name}: pool {art}/{lab} has {len(pool)}, need {k}")
            drawn += rng.sample(pool, k)
        # pilot taken first from the shuffled draw, study is the disjoint remainder.
        # Disjointness is a property of this split, not something checked afterwards.
        rng.shuffle(drawn)
        pilot, study = drawn[:n_pilot], drawn[n_pilot:]
        for s in pilot:
            out["pilot"].append(dict(s, stratum=name))
        for s in study:
            out["study"].append(dict(s, stratum=name))
        report.append((name, art, "+".join(labels), len(study), len(pilot),
                       dict(Counter(s["label"] for s in study)),
                       dict(Counter(s["label"] for s in pilot))))

    study_ids = {s["id"] for s in out["study"]}
    pilot_ids = {s["id"] for s in out["pilot"]}
    assert not (study_ids & pilot_ids), "pilot and study overlap"
    assert len(study_ids) == 250 and len(pilot_ids) == 40

    out["meta"] = {
        "seed": SEED,
        "supersedes": {"path": "s5_pilot/sample.frozen.json", "seed": 20260913,
                       "reason": "frozen against a grounding measure; 100 of 250 study "
                                 "items on Article 46, which has 0 cross-provision "
                                 "attachments. Strata changed, so the seed is not reused."},
        "plan": "E4: 100 Art 14 / 75 Art 13 / 25 Art 12 / 25 Art 46 applicable / "
                "25 Art 46 not-applicable; pilot 16/12/4/4/4, disjoint",
        "corpus_sha256": corpus_sha,
        "corpus_path_basename": "LexiGen_corpus.json",
        "n_study": len(study_ids),
        "n_pilot": len(pilot_ids),
        "disjoint": True,
    }
    out["meta"]["sample_sha256"] = hashlib.sha256(
        json.dumps(sorted(study_ids) + sorted(pilot_ids), separators=(",", ":")).encode()
    ).hexdigest()
    blob = json.dumps(out, indent=2, sort_keys=True)
    open(OUT, "w", encoding="utf-8").write(blob)

    print(f"corpus sha256      {corpus_sha}")
    print(f"seed               {SEED}")
    print(f"sample sha256      {out['meta']['sample_sha256']}")
    print(f"wrote              {OUT}")
    print()
    print(f"{'stratum':>8} {'art':>4} {'labels':>28} {'study':>6} {'pilot':>6}")
    for name, art, labs, ns, np_, cs, cp in report:
        print(f"{name:>8} {art:>4} {labs:>28} {ns:>6} {np_:>6}   study={cs} pilot={cp}")
    print(f"{'TOTAL':>8} {'':>4} {'':>28} {len(study_ids):>6} {len(pilot_ids):>6}")


if __name__ == "__main__":
    main()
