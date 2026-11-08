"""S11 sample freeze: item = (LexiGen segment, one FIXED duty). Deterministic, seeded, digested.

Per article, every duty the graph links at least one qualification to appears exactly
twice (Article 13: 21 duties -> 42 items; Article 14: 22 duties -> 44 items; the Article
14(5)(b) protective-measures duty has no encoded links and so no reference set).

Segments: every unused segment of the article first (Article 13: 30, Article 14: 1), the
rest drawn from segments already used by Study 1, its pilot and Study 2. Reuse was decided
by the author because the reference depends only on the fixed duty, never on the segment
or on the model's own duty selection. The four s6 pilot segments used for the S11
end-to-end check (smoke.sample.json) are excluded from the reuse pool.

SEED 20261107, not used by any earlier study.
"""
import hashlib
import json
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stores  # noqa: E402

SEED = 20261107
OUT = os.path.join(HERE, "fullarticle.frozen.json")
S6 = os.path.join(HERE, "..", "s6_tools")
CORPUS = r"C:\Users\ziedm\Desktop\M2_ENSI\Memoire\LexiGen-main\LexiGen-main\corpus_creation\data\LexiGen_corpus.json"
PER_DUTY = 2


def main():
    raw = open(CORPUS, encoding="utf-8").read()
    corpus_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    segs = [s for b in json.loads(raw) for s in b["segments"]]
    assert len(segs) == 8977
    prior = json.load(open(os.path.join(S6, "sample.frozen.json"), encoding="utf-8"))
    graded = json.load(open(os.path.join(S6, "graded.frozen.json"), encoding="utf-8"))
    used = ({s["id"] for s in prior["study"]} | {s["id"] for s in prior["pilot"]}
            | {s["id"] for s in graded["items"]})
    assert len(used) == 510, len(used)
    smoke = {i["segment_id"] for i in json.load(open(os.path.join(HERE, "smoke.sample.json")))["items"]}

    _, g = stores.load()
    rng = random.Random(SEED)
    items, report = [], {}
    for art in (13, 14):
        duties = sorted(d for d, v in g.duties.items()
                        if v["relations"] and any(u.startswith("art%d-" % art) for u in v["grounded_in"]))
        slots = duties * PER_DUTY
        rng.shuffle(slots)
        pool = [(i, s) for i, s in enumerate(segs) if s["gdpr_article_number"] == art
                and s["label"] in ("COMPLIANT", "NON_COMPLIANT")]
        fresh = [(i, s) for i, s in pool if "seg%05d" % i not in used]
        reuse = [(i, s) for i, s in pool if "seg%05d" % i in used and "seg%05d" % i not in smoke]
        need = len(slots) - len(fresh)
        assert need >= 0
        chosen = [(i, s, True) for i, s in fresh] + [(i, s, False) for i, s in rng.sample(reuse, need)]
        rng.shuffle(chosen)
        for (i, s, is_fresh), duty in zip(chosen, slots):
            sid = "seg%05d" % i
            items.append({"id": "%s|%s" % (sid, duty), "segment_id": sid, "global_index": i,
                          "article": art, "stratum": "ART-%d" % art, "label": s["label"],
                          "fresh_segment": is_fresh, "duty_id": duty,
                          "text_sha256_16": hashlib.sha256(s["segment"].encode("utf-8")).hexdigest()[:16]})
        report[art] = {"n_items": len(slots), "n_duties": len(duties), "fresh": len(fresh),
                       "reused": need, "reuse_pool": len(reuse)}

    ids = [it["id"] for it in items]
    assert len(set(ids)) == len(ids)
    assert len({it["segment_id"] for it in items}) == len(items), "a segment drawn twice"
    assert not ({it["segment_id"] for it in items} & smoke)
    meta = {"seed": SEED, "per_duty": PER_DUTY, "corpus_sha256": corpus_sha,
            "plan": report, "prior_used": len(used),
            "reuse_reason": "the reference set depends only on the fixed duty; author decision"}
    meta["sample_sha256"] = hashlib.sha256(json.dumps(sorted(ids), separators=(",", ":")).encode()).hexdigest()
    json.dump({"meta": meta, "items": items}, open(OUT, "w", encoding="utf-8"), indent=2, sort_keys=True)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
