"""S9 graded-measure sample freeze. Deterministic, seeded, digested.

Draws a FRESH set for the graded-measure study, DISJOINT from every item already used:
the 250 study items and the 40 pilot items of `sample.frozen.json`. Disjointness is the
whole point. The graded measure's effect size was estimated by looking at the S9 reach
results, so re-running it on the same items would be circular; fresh items are what make
the confirmation worth anything.

Adapted from `freeze_sample.py`. The label balancing and digest machinery are carried
over unchanged; what changes is the exclusion set, the shape and the seed.

THE SHAPE IS POOL-LIMITED AND THAT IS RECORDED RATHER THAN HIDDEN. Only 75 unused
Article 14 segments remain (37 COMPLIANT, 38 NON_COMPLIANT), so APP-14 is 74 rather than
the reach study's 100. Article 14 is where the relations are, so this is the binding
constraint on the study and it is stated in the pre-registration too.

SEED 20260917. The study seed 20260915 and the stability seed 20260916 are not reused:
this is a third independent stream, reproducible from a single recorded number.

Nothing here is a result.
"""
import json, sys, os, hashlib, random
from collections import Counter, defaultdict

SEED = 20260917
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "graded.frozen.json")
PRIOR = os.path.join(HERE, "sample.frozen.json")
CORPUS = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ziedm\Desktop\M2_ENSI\Memoire\LexiGen-main\LexiGen-main\corpus_creation\data\LexiGen_corpus.json"

# stratum -> (article, labels, n). Pool-limited on APP-14; the three null strata are
# carried at 24 for the same reasons E4 gives, not as filler.
PLAN = [
    ("APP-14", 14, ("COMPLIANT", "NON_COMPLIANT"), 74),
    ("APP-13", 13, ("COMPLIANT", "NON_COMPLIANT"), 74),
    ("APP-12", 12, ("COMPLIANT", "NON_COMPLIANT"), 24),
    ("APP-46", 46, ("COMPLIANT", "NON_COMPLIANT"), 24),
    ("NA-46",  46, ("NOT_APPLICABLE",),            24),
]


def main():
    raw = open(CORPUS, encoding="utf-8").read()
    corpus_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    data = json.loads(raw)

    segs, g = [], 0
    for b in data:
        for s in b["segments"]:
            segs.append({
                "id": f"seg{g:05d}",
                "global_index": g,
                "batch_id": b["batch_id"],
                "article": s["gdpr_article_number"],
                "label": s["label"],
                "text_sha256_16": hashlib.sha256(s["segment"].encode("utf-8")).hexdigest()[:16],
            })
            g += 1
    assert len(segs) == 8977, len(segs)

    prior = json.load(open(PRIOR, encoding="utf-8"))
    used = {s["id"] for s in prior["study"]} | {s["id"] for s in prior["pilot"]}
    assert len(used) == 290, len(used)

    pools = defaultdict(list)
    for s in segs:
        if s["id"] in used:
            continue
        pools[(s["article"], s["label"])].append(s)
    for k in pools:
        pools[k].sort(key=lambda s: s["global_index"])

    rng = random.Random(SEED)
    out, report = {"items": []}, []
    for name, art, labels, n in PLAN:
        per = [n // len(labels)] * len(labels)
        for i in range(n - sum(per)):
            per[i] += 1
        drawn = []
        for lab, k in zip(labels, per):
            pool = pools[(art, lab)]
            if len(pool) < k:
                raise SystemExit(f"{name}: unused pool {art}/{lab} has {len(pool)}, need {k}")
            drawn += rng.sample(pool, k)
        rng.shuffle(drawn)
        for s in drawn:
            out["items"].append(dict(s, stratum=name))
        report.append((name, art, "+".join(labels), len(drawn),
                       dict(Counter(s["label"] for s in drawn))))

    ids = {s["id"] for s in out["items"]}
    assert len(ids) == sum(p[3] for p in PLAN), "duplicate draw"
    assert not (ids & used), "graded draw overlaps the reach study or its pilot"

    out["meta"] = {
        "seed": SEED,
        "purpose": "graded-measure study: per-item FRACTION of target pairs surfaced",
        "disjoint_from": {"path": "sample.frozen.json", "splits": ["study", "pilot"],
                          "n_excluded": len(used),
                          "reason": "the graded effect size was estimated from the S9 "
                                    "reach results, so the same items would be circular"},
        "pool_limited": {"APP-14": "only 75 unused Article 14 segments remain, so 74 "
                                   "rather than the reach study's 100"},
        "plan": "74 Art 14 / 74 Art 13 / 24 Art 12 / 24 Art 46 applicable / "
                "24 Art 46 not-applicable",
        "corpus_sha256": corpus_sha,
        "corpus_path_basename": "LexiGen_corpus.json",
        "n_items": len(ids),
    }
    out["meta"]["graded_sha256"] = hashlib.sha256(
        json.dumps(sorted(ids), separators=(",", ":")).encode()).hexdigest()
    open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=2, sort_keys=True))

    print(f"corpus sha256      {corpus_sha}")
    print(f"seed               {SEED}")
    print(f"graded sha256      {out['meta']['graded_sha256']}")
    print(f"excluded (prior)   {len(used)}")
    print(f"wrote              {OUT}")
    print()
    print(f"{'stratum':>8} {'art':>4} {'labels':>28} {'n':>5}")
    for name, art, labs, n, c in report:
        print(f"{name:>8} {art:>4} {labs:>28} {n:>5}   {c}")
    print(f"{'TOTAL':>8} {'':>4} {'':>28} {len(ids):>5}")


if __name__ == "__main__":
    main()
