"""Drive the multi-turn tool loop and record the FULL trace per item.

One item, one arm, one trace. The trace is the measurement instrument: the reach
extractor reads it and nothing else, so everything the model asked for and everything
it was given is written down, including the provenance of every tool return.

Execution discipline, per 05_EVAL_PLAN.md E8, each of these a defect this project has
already paid for:
  - num_ctx set EXPLICITLY on every call. Ollama defaults it to 8192 whatever the
    model's capacity, and that silently truncated 46% of an Article 14 prompt in S5.
  - prompt_eval_count asserted against the ceiling on every turn. If a turn ever
    evaluates within MARGIN of num_ctx the item fails loudly rather than quietly.
  - turn cap 10, with a per-item assertion of whether it was hit. Items that hit it
    are flagged and reported separately, never silently included.
  - the model string pinned, and its Ollama digest recorded alongside it.
  - source digests re-verified on load (stores.py -> build_payloads.load_units).

Generations are expensive and a 500-generation run must not be lost to a crash at
item 240, so every record is appended to <out>.partial.jsonl as soon as it exists and
a re-run with --resume picks up where it stopped. The partial file carries a header
line describing the run; a resume against a different sample, split, arm set, model or
repeat count refuses rather than mixing two runs into one file.

--repeats N runs each item N times and records the repeat index on every record, which
is what the N = 5 stability measurement needs. What a trace RECORDS is otherwise
unchanged: reach.py reads the same keys it always read.

NOT the study and not a pilot. This script runs whatever sample file it is given; the
study sample is re-drawn in S8. No number it produces is a result.

    .venv/Scripts/python.exe paper_draft/s6_tools/run_arms.py \
        --sample paper_draft/s5_pilot/sample.frozen.json --items 5 --out traces.json
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stores  # noqa: E402

OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b"          # pinned, E4. mistral:7b cannot chain tool calls (0/10 twice).
NUM_CTX = 16384               # explicit, always. never left to the 8192 default.
MARGIN = 512                  # truncation reserves room for generation, so assert with slack
TURN_CAP = 10                 # E8
DEFAULT_CORPUS = os.path.join(
    r"C:\Users\ziedm\Desktop\M2_ENSI\Memoire\LexiGen-main\LexiGen-main",
    "corpus_creation", "data", "LexiGen_corpus.json")

SYSTEM = (
    "You assess whether a privacy policy segment complies with one GDPR article. "
    "You do NOT know the article's contents and must not answer from memory. Use the "
    "tools: find the provisions that bear on the segment, then use get_conditions on "
    "the identifiers you were given to check whether anything changes the answer, and "
    "get_provision when you need the exact words. Then give a verdict of COMPLIANT, "
    "NON_COMPLIANT or NOT_APPLICABLE and a short justification citing the provisions "
    "you relied on.")


def post(path, body, timeout=600):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ps_snapshot(model):
    """What Ollama currently holds loaded for this model, or None if nothing is.

    size_vram is the GPU/CPU offload split chosen at load time. S10 found that greedy
    output can differ between two loads of the same blob, so a traces file that does not
    record this is silent about a variable known to change results.
    """
    try:
        d = json.loads(urllib.request.urlopen(OLLAMA + "/api/ps", timeout=60).read())
    except Exception:
        return None
    for m in d.get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return {k: m.get(k) for k in ("size", "size_vram", "context_length")}
    return None


def model_digest(model):
    """Pin the exact blob, not just the tag. A tag can be repointed underneath a run."""
    tags = json.loads(urllib.request.urlopen(OLLAMA + "/api/tags", timeout=60).read())
    for m in tags.get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return m.get("digest")
    raise SystemExit("model %s is not pulled in Ollama" % model)


def run_item(model, store, segment, article, num_ctx, turn_cap, temperature=0.0):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "GDPR Article %d.\n\nPOLICY SEGMENT:\n%s"
                                        % (article, segment)}]
    trace, final, turns, t0 = [], None, 0, time.time()
    prompt_evals, ctx_error, load_durations = [], None, []
    while turns < turn_cap:
        turns += 1
        try:
            out = post("/api/chat", {
                "model": model, "messages": msgs, "stream": False, "tools": stores.TOOLS,
                "options": {"temperature": temperature, "num_ctx": num_ctx}})
        except Exception as e:
            ctx_error = "chat call failed: %s" % str(e)[:300]
            break
        pe = out.get("prompt_eval_count")
        prompt_evals.append(pe)
        load_durations.append(out.get("load_duration"))
        # The truncation assertion. Ollama does not expose a tokenizer, but a prompt
        # that was clipped shows up as an evaluated count pressed against the ceiling.
        if pe is not None and pe > num_ctx - MARGIN:
            ctx_error = ("prompt_eval_count %s within %d of num_ctx %d on turn %d: "
                         "the prompt may have been truncated" % (pe, MARGIN, num_ctx, turns))
            break
        m = out.get("message", {}) or {}
        calls = m.get("tool_calls") or []
        msgs.append(m)
        if not calls:
            final = m.get("content") or ""
            break
        for c in calls:
            fn = (c.get("function") or {}).get("name")
            args = (c.get("function") or {}).get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            payload, prov = store.call(fn, args)
            ret = json.dumps(payload, ensure_ascii=False)
            trace.append({"turn": turns, "call": fn, "args": args,
                          "returned": payload, "returned_chars": len(ret),
                          "provenance": prov})
            msgs.append({"role": "tool", "content": ret})
    return {
        "arm": store.arm, "article": article, "turns": turns,
        "turn_cap_hit": turns >= turn_cap and final is None and ctx_error is None,
        "calls": len(trace), "final": final, "trace": trace,
        "prompt_eval_counts": prompt_evals,
        "max_prompt_eval": max([p for p in prompt_evals if p is not None] or [0]),
        "max_load_duration": max([d for d in load_durations if d is not None] or [0]),
        "error": ctx_error, "seconds": round(time.time() - t0, 1),
    }


def resume_partial(path, header):
    """Load the records of an interrupted run, or refuse if it is a different run.

    Silently merging two runs into one traces file would be a data defect the extractor
    cannot see, so every field that makes two runs incomparable is compared first.
    """
    if not os.path.exists(path):
        return []
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
    if not lines:
        return []
    old = json.loads(lines[0]).get("header")
    if old is None:
        raise SystemExit("%s has no header line, so it cannot be resumed safely. Move it "
                         "aside and start again." % path)
    differs = [k for k in header if old.get(k) != header[k]]
    if differs:
        raise SystemExit("%s is a different run (differs on %s). Refusing to resume into it."
                         % (path, ", ".join(sorted(differs))))
    recs, seen = [], set()
    for n, line in enumerate(lines[1:], 2):
        try:
            r = json.loads(line)
        except Exception:
            # A crash mid-write leaves a truncated last line. Drop it and rerun that unit.
            print("  dropping truncated line %d of %s" % (n, os.path.basename(path)))
            continue
        key = (r["id"], r["repeat"])
        if key in seen:
            continue
        seen.add(key)
        recs.append(r)
    return recs


def selfcheck():
    """The resume path is the only non-trivial logic here, so it gets a check.

    It decides whether 240 finished generations are reused or silently mixed with a
    different run, which is exactly the class of defect the extractor cannot see.
    """
    import tempfile
    d = tempfile.mkdtemp()
    path = os.path.join(d, "t.json.partial.jsonl")
    head = {"partial_of": "t.json", "model": "qwen2.5:7b", "model_digest": "abc",
            "num_ctx": 16384, "turn_cap": 10, "arms": ["text", "graph"], "repeats": 5, "temperature": 0.7,
            "sample_file": "sample.frozen.json", "split": "items",
            "sample_sha256": "96cd", "n_units": 250}

    # 1. no file yet is not an error, it is the first run
    assert resume_partial(path, head) == []

    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"header": head}) + "\n")
        f.write(json.dumps({"id": "seg1", "repeat": 1, "arms": {}}) + "\n")
        f.write(json.dumps({"id": "seg1", "repeat": 2, "arms": {}}) + "\n")
        f.write(json.dumps({"id": "seg1", "repeat": 1, "arms": {}}) + "\n")   # dup
        f.write('{"id": "seg2", "repe')                                        # truncated

    # 2. matching header: the two distinct units come back, the duplicate is dropped
    #    once, and the half-written last line is dropped rather than crashing the resume
    recs = resume_partial(path, head)
    assert [(r["id"], r["repeat"]) for r in recs] == [("seg1", 1), ("seg1", 2)], recs

    # 3. every field that makes two runs incomparable refuses the resume
    for k, v in [("repeats", 1), ("split", "study"), ("arms", ["text"]),
                 ("model", "mistral:7b"), ("model_digest", "zzz"), ("num_ctx", 8192),
                 ("sample_sha256", "dead"), ("turn_cap", 6),
                 ("temperature", 0.0)]:
        bad = dict(head, **{k: v})
        try:
            resume_partial(path, bad)
        except SystemExit:
            pass
        else:
            raise AssertionError("resume did not refuse a run differing on %s" % k)

    # 4. a partial file predating the header refuses rather than resuming blind
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "seg1", "repeat": 1}) + "\n")
    try:
        resume_partial(path, head)
    except SystemExit:
        pass
    else:
        raise AssertionError("resume did not refuse a headerless partial file")

    print("run_arms.py self-check OK: resume reuses, deduplicates, drops a torn line, "
          "and refuses 10 kinds of mismatch")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=os.path.join(HERE, "..", "s5_pilot",
                                                     "sample.frozen.json"))
    ap.add_argument("--split", default="pilot", help="key in the sample file")
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--num-ctx", type=int, default=NUM_CTX)
    ap.add_argument("--turn-cap", type=int, default=TURN_CAP)
    ap.add_argument("--arms", default="text,graph")
    ap.add_argument("--items", type=int, default=0, help="0 = all")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="sampling temperature. Recorded in the resume header, so two "
                         "runs at different temperatures cannot merge into one file.")
    ap.add_argument("--repeats", type=int, default=1,
                    help="run each item this many times; the repeat index is recorded "
                         "on every record. N = 5 is the stability measurement")
    ap.add_argument("--resume", action="store_true",
                    help="reuse the records already in <out>.partial.jsonl and run "
                         "only what is missing. Refuses if that file is another run")
    ap.add_argument("--pick", default="", help="comma-separated indices into the split, "
                                               "for spanning strata without running a batch")
    ap.add_argument("--out", default=os.path.join(HERE, "traces.json"))
    ap.add_argument("--selfcheck", action="store_true",
                    help="check the resume logic and exit. No model call is made")
    ap.add_argument("--dry-load", action="store_true",
                    help="verify the sample loads through this runner without generating: "
                         "source digests, every global_index resolves, every text digest "
                         "re-verifies. No model call is made.")
    a = ap.parse_args()

    if a.selfcheck:
        return selfcheck()

    corpus, graph = stores.load()                      # re-verifies every source digest
    sample = json.load(open(a.sample, encoding="utf-8"))
    segs = [s for b in json.load(open(a.corpus, encoding="utf-8")) for s in b["segments"]]
    items = sample[a.split]
    if a.pick:
        items = [items[int(i)] for i in a.pick.split(",")]
    elif a.items:
        items = items[:a.items]
    if a.dry_load:
        for item in items:
            assert 0 <= item["global_index"] < len(segs), (
                "%s global_index %s does not resolve" % (item["id"], item["global_index"]))
            seg = segs[item["global_index"]]
            assert hashlib.sha256(seg["segment"].encode()).hexdigest()[:16] == item["text_sha256_16"], (
                "%s text digest mismatch - the corpus is not the frozen one" % item["id"])
            assert seg["gdpr_article_number"] == item["article"], (
                "%s article mismatch" % item["id"])
        meta = sample.get("meta", {})
        print("dry load OK: %s/%s, %d items, every global_index resolves and every "
              "text digest re-verifies" % (os.path.basename(a.sample), a.split, len(items)))
        print("  seed          %s" % meta.get("seed"))
        print("  sample sha256 %s" % meta.get("sample_sha256"))
        print("  corpus sha256 %s" % meta.get("corpus_sha256"))
        print("  strata        %s" % dict(Counter(i["stratum"] for i in items)))
        print("  sources       %s" % corpus.digests())
        return

    digest = model_digest(a.model)
    ps_start = ps_snapshot(a.model)
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]

    # The run is identified by everything that would make two partial files
    # incomparable. A resume that disagrees on any of it is refused, not merged.
    header = {"partial_of": os.path.basename(a.out), "model": a.model,
              "model_digest": digest, "num_ctx": a.num_ctx, "turn_cap": a.turn_cap,
              "arms": arms, "repeats": a.repeats, "temperature": a.temperature,
              "sample_file": os.path.basename(a.sample), "split": a.split,
              "sample_sha256": sample.get("meta", {}).get("sample_sha256"),
              "n_units": len(items) * a.repeats}
    partial = a.out + ".partial.jsonl"
    records = resume_partial(partial, header) if a.resume else []
    done = {(r["id"], r["repeat"]) for r in records}
    if a.resume:
        print("resumed %d of %d units from %s"
              % (len(records), header["n_units"], os.path.basename(partial)))
    fh = open(partial, "a" if records else "w", encoding="utf-8")
    if not records:
        fh.write(json.dumps({"header": header}, ensure_ascii=False) + "\n")
        fh.flush()

    units = [(rep, item) for rep in range(1, a.repeats + 1) for item in items]
    t0 = time.time()
    for i, (rep, item) in enumerate(units, 1):
        if (item["id"], rep) in done:
            continue
        seg = segs[item["global_index"]]
        assert hashlib.sha256(seg["segment"].encode()).hexdigest()[:16] == item["text_sha256_16"], \
            "%s text digest mismatch - the corpus is not the frozen one" % item["id"]
        rec = {"id": item["id"], "repeat": rep, "stratum": item["stratum"],
               "article": item["article"], "gold_label": item.get("label"),
               "segment": seg["segment"], "arms": {}}
        for arm in arms:
            st = stores.STORES[arm](corpus, graph, item["article"])
            rec["arms"][arm] = run_item(a.model, st, seg["segment"], item["article"],
                                        a.num_ctx, a.turn_cap, a.temperature)
        records.append(rec)
        # Written and fsynced before the next generation starts, so a crash costs one unit.
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        print("[%3d/%d] %s r%d art%-2d %s | elapsed %.1fm" % (
            i, len(units), item["id"], rep, item["article"],
            " ".join("%s:%dcalls%s" % (k, v["calls"],
                                       "!CAP" if v["turn_cap_hit"] else
                                       "!ERR" if v["error"] else "")
                     for k, v in rec["arms"].items()),
            (time.time() - t0) / 60), flush=True)
    fh.close()

    blob = {"model": a.model, "model_digest": digest, "num_ctx": a.num_ctx,
            "turn_cap": a.turn_cap, "k": stores.K, "temperature": a.temperature, "arms": arms,
            "sample_file": os.path.basename(a.sample), "split": a.split,
            "sample_sha256": sample.get("meta", {}).get("sample_sha256"),
            "corpus_sha256": sample.get("meta", {}).get("corpus_sha256"),
            "source_digests": corpus.digests(),
            "ps_start": ps_start, "ps_end": ps_snapshot(a.model),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "repeats": a.repeats,
            "n_items": len(records), "records": records}
    json.dump(blob, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    caps = [(r["id"], k) for r in records for k, v in r["arms"].items() if v["turn_cap_hit"]]
    errs = [(r["id"], k, v["error"]) for r in records for k, v in r["arms"].items() if v["error"]]
    mpe = max([v["max_prompt_eval"] for r in records for v in r["arms"].values()] or [0])
    print("\nwrote %s\n%d units (%d items x %d repeats) x %d arms | turn cap hit: %d | "
          "errors: %d | max prompt_eval_count %d of num_ctx %d"
          % (a.out, len(records), len(items), a.repeats, len(arms), len(caps), len(errs),
             mpe, a.num_ctx))
    for e in errs:
        print("  ERROR %s/%s: %s" % e)


if __name__ == "__main__":
    main()
