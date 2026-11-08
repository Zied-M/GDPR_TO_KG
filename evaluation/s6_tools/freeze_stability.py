"""S8 stability subsample freeze. Deterministic, seeded, digested.

M = 50, DECIDED 2026-09-15 by the author, closing the last open parameter in
`05_EVAL_PLAN.md` Part D item 4. Drawn from the 250 study items of
`sample.frozen.json` and frozen NOW, before any generation, for the same reason the
pre-registration is written now: a subsample chosen after the results exist is not a
subsample, it is a selection.

Allocation is PROPORTIONAL to the study strata, which is forced rather than chosen:
stability is a property of the substrate rather than of any individual policy, and
stratify-never-pool governs all five strata here as everywhere else.

    APP-14 20 | APP-13 15 | APP-12 5 | APP-46 5 | NA-46 5   = 50

Seed is the study seed plus one, so the two draws are independent streams and both are
reproducible from a single recorded number.

Nothing here is a result. No generation happens in this file.
"""
import json, os, hashlib, random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "sample.frozen.json")
OUT = os.path.join(HERE, "stability.frozen.json")

STUDY_SEED = 20260915
SEED = STUDY_SEED + 1          # 20260916, an independent stream off the same number
M = 50
N_REPEATS = 5                  # Part D item 4, decided 2026-09-06. Not reopened here.

# proportional to the study shape 100/75/25/25/25, which divides exactly by 5
ALLOC = [("APP-14", 20), ("APP-13", 15), ("APP-12", 5), ("APP-46", 5), ("NA-46", 5)]


def main():
    raw = open(SAMPLE, encoding="utf-8").read()
    sample = json.loads(raw)
    sample_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    assert sample["meta"]["seed"] == STUDY_SEED, "not the study sample this draw is defined against"

    by_stratum = {}
    for item in sample["study"]:
        by_stratum.setdefault(item["stratum"], []).append(item)
    for k in by_stratum:
        by_stratum[k].sort(key=lambda s: s["global_index"])

    rng = random.Random(SEED)
    picked = []
    for name, n in ALLOC:
        pool = by_stratum[name]
        if len(pool) < n:
            raise SystemExit(f"{name}: study stratum has {len(pool)}, need {n}")
        picked += rng.sample(pool, n)
    picked.sort(key=lambda s: s["global_index"])
    assert len(picked) == M and len({s["id"] for s in picked}) == M

    study_ids = {s["id"] for s in sample["study"]}
    assert {s["id"] for s in picked} <= study_ids, "stability item outside the study set"

    out = {
        "items": picked,
        "meta": {
            "seed": SEED,
            "derived_from_seed": STUDY_SEED,
            "M": M,
            "n_repeats": N_REPEATS,
            "temperature": 0.0,
            "drawn_from": "sample.frozen.json :: study",
            "study_sample_sha256_of_file": sample_sha,
            "study_sample_sha256": sample["meta"]["sample_sha256"],
            "corpus_sha256": sample["meta"]["corpus_sha256"],
            "allocation": dict(ALLOC),
            "frozen": "2026-09-15 (S8), before any generation",
        },
    }
    out["meta"]["stability_sha256"] = hashlib.sha256(
        json.dumps(sorted(s["id"] for s in picked), separators=(",", ":")).encode()
    ).hexdigest()
    open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=2, sort_keys=True))

    print(f"study sample sha256   {sample['meta']['sample_sha256']}")
    print(f"seed                  {SEED}  (study seed {STUDY_SEED} + 1)")
    print(f"M                     {M} items x N = {N_REPEATS} repeats x 2 arms "
          f"= {M * N_REPEATS * 2} generations")
    print(f"stability sha256      {out['meta']['stability_sha256']}")
    print(f"wrote                 {OUT}")
    print(f"strata                {dict(Counter(s['stratum'] for s in picked))}")
    print(f"labels                {dict(Counter(s['label'] for s in picked))}")


if __name__ == "__main__":
    main()
