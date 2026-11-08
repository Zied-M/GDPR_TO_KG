"""S11 runner: one item x one FIXED duty, three conditions, full trace per condition.

Conditions (PREREGISTRATION-FULLARTICLE.md section 3):
  fulltext  the whole article text in the prompt, plus the fixed duty. No tools.
  graph     the same prompt, plus the s6 graph tools (find_duties, get_conditions,
            get_provision over GraphStore). Multi-turn, turn cap 10.
  links     SECONDARY. The same prompt, plus the duty's encoded links written out as
            plain structured text. No tools.

Every condition sees the SAME user message (article text, policy segment, fixed duty)
and the SAME answer schema. The graph condition adds tools and one system sentence
naming them; the links condition adds one block of plain text. Nothing else differs.

Execution discipline carried from s6_tools/run_arms.py: num_ctx explicit, prompt_eval_count
asserted against the ceiling with a margin on every turn, turn cap with a per-item flag,
model blob digest and the Ollama load state recorded, source digests re-verified on load,
incremental write with a header-checked --resume.

    .venv/Scripts/python.exe -B paper_draft/s11_full_article/run_fullarticle.py \
        --sample paper_draft/s11_full_article/fullarticle.frozen.json --out ...traces.json
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import stores  # noqa: E402  (the s11 copy)

OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen2.5:7b"
NUM_CTX = 16384
MARGIN = 512
TURN_CAP = 10
CONDITIONS = ("fulltext", "graph", "links")
DEFAULT_CORPUS = os.path.join(
    r"C:\Users\ziedm\Desktop\M2_ENSI\Memoire\LexiGen-main\LexiGen-main",
    "corpus_creation", "data", "LexiGen_corpus.json")

SYSTEM = (
    "You examine one duty that a GDPR article imposes on a controller. The full official "
    "text of the article is given to you. Identify EVERY qualification in the article that "
    "governs the given duty: conditions that must hold for the duty to apply (including "
    "when it must be performed), exceptions that lift the duty, and circumstances in which "
    "the duty does not apply. Answer only from the material provided, not from memory. "
    "List one entry per qualification and cite the most specific provision that states it "
    "(a paragraph, subparagraph or point, for example 'Article 14(5)(a)'). Do not list the "
    "duty itself. Reply with JSON only, in exactly this shape:\n"
    '{"qualifications": [{"provision": "Article N(x)(y)", '
    '"kind": "condition" | "exception" | "not_applicable_if", '
    '"justification": "one short sentence"}]}')

SYSTEM_TOOLS = (
    " You also have tools over a knowledge graph of this article: get_conditions takes the "
    "duty identifier given below and returns the qualifications the graph links to it; "
    "find_duties and get_provision are also available. Call get_conditions with the duty "
    "identifier before you answer, check what it returns against the article text, then "
    "give your JSON answer.")


def user_message(article, article_text, segment, duty_label, duty_statement, duty_id):
    return ("GDPR ARTICLE %d, FULL OFFICIAL TEXT:\n%s\n\n"
            "POLICY SEGMENT UNDER REVIEW (context):\n%s\n\n"
            "DUTY UNDER EXAMINATION: %s (%s). Duty identifier: %s"
            % (article, article_text, segment, duty_statement, duty_label, duty_id))


def links_block(store, duty_id):
    """The duty's encoded links as plain structured text: the same content the graph
    tool returns for get_conditions, written out as lines, no tool and no JSON."""
    pay, _ = store.get_conditions(duty_id)
    lines = ["ENCODED LINKS FOR THIS DUTY (from the knowledge graph):"]
    for r in pay["conditions"]:
        lines.append("- %s | %s | cites: %s" % (r["kind"], r["statement"], ", ".join(r["cites"])))
    return "\n".join(lines)


def post(path, body, timeout=900):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ps_snapshot(model):
    try:
        d = json.loads(urllib.request.urlopen(OLLAMA + "/api/ps", timeout=60).read())
    except Exception:
        return None
    for m in d.get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return {k: m.get(k) for k in ("size", "size_vram", "context_length")}
    return None


def model_digest(model):
    tags = json.loads(urllib.request.urlopen(OLLAMA + "/api/tags", timeout=60).read())
    for m in tags.get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return m.get("digest")
    raise SystemExit("model %s is not pulled in Ollama" % model)


def run_condition(cond, model, store, umsg, extra, num_ctx, turn_cap, temperature):
    system = SYSTEM + (SYSTEM_TOOLS if cond == "graph" else "")
    content = umsg + ("\n\n" + extra if extra else "")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": content}]
    trace, final, turns, t0 = [], None, 0, time.time()
    prompt_evals, evals, err = [], [], None
    while turns < turn_cap:
        turns += 1
        body = {"model": model, "messages": msgs, "stream": False,
                "options": {"temperature": temperature, "num_ctx": num_ctx}}
        if cond == "graph":
            body["tools"] = stores.TOOLS
        try:
            out = post("/api/chat", body)
        except Exception as e:
            err = "chat call failed: %s" % str(e)[:300]
            break
        pe = out.get("prompt_eval_count")
        prompt_evals.append(pe)
        evals.append(out.get("eval_count"))
        if pe is not None and pe > num_ctx - MARGIN:
            err = "prompt_eval_count %s within %d of num_ctx %d on turn %d" % (
                pe, MARGIN, num_ctx, turns)
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
            trace.append({"turn": turns, "call": fn, "args": args, "returned": payload,
                          "returned_chars": len(ret), "provenance": prov})
            msgs.append({"role": "tool", "content": ret})
    pes = [p for p in prompt_evals if p is not None]
    return {"condition": cond, "turns": turns,
            "turn_cap_hit": turns >= turn_cap and final is None and err is None,
            "calls": len(trace), "final": final, "trace": trace,
            "prompt_eval_counts": prompt_evals, "eval_counts": evals,
            "input_tokens_total": sum(pes), "max_prompt_eval": max(pes or [0]),
            "user_chars": len(content), "error": err,
            "seconds": round(time.time() - t0, 1)}


def resume_partial(path, header):
    if not os.path.exists(path):
        return []
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
    if not lines:
        return []
    old = json.loads(lines[0]).get("header")
    if old is None:
        raise SystemExit("%s has no header line; refusing to resume" % path)
    differs = [k for k in header if old.get(k) != header[k]]
    if differs:
        raise SystemExit("%s is a different run (differs on %s)" % (path, ", ".join(sorted(differs))))
    recs, seen = [], set()
    for line in lines[1:]:
        try:
            r = json.loads(line)
        except Exception:
            continue                       # torn last line: rerun that unit
        if r["id"] not in seen:
            seen.add(r["id"])
            recs.append(r)
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--split", default="items")
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--num-ctx", type=int, default=NUM_CTX)
    ap.add_argument("--turn-cap", type=int, default=TURN_CAP)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-load", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    corpus, graph = stores.load()
    sample = json.load(open(a.sample, encoding="utf-8"))
    segs = [s for b in json.load(open(a.corpus, encoding="utf-8")) for s in b["segments"]]
    items = sample[a.split]
    conds = [x.strip() for x in a.conditions.split(",") if x.strip()]
    for it in items:
        seg = segs[it["global_index"]]
        assert hashlib.sha256(seg["segment"].encode()).hexdigest()[:16] == it["text_sha256_16"], it["id"]
        assert seg["gdpr_article_number"] == it["article"], it["id"]
        assert it["duty_id"] in graph.duties and graph.duties[it["duty_id"]]["relations"], it["duty_id"]
    if a.dry_load:
        print("dry load OK: %d items, digests re-verify, every fixed duty resolves" % len(items))
        return

    digest = model_digest(a.model)
    header = {"partial_of": os.path.basename(a.out), "model": a.model, "model_digest": digest,
              "num_ctx": a.num_ctx, "turn_cap": a.turn_cap, "temperature": a.temperature,
              "conditions": conds, "sample_file": os.path.basename(a.sample), "split": a.split,
              "sample_sha256": sample.get("meta", {}).get("sample_sha256"), "n_items": len(items)}
    partial = a.out + ".partial.jsonl"
    records = resume_partial(partial, header) if a.resume else []
    done = {r["id"] for r in records}
    fh = open(partial, "a" if records else "w", encoding="utf-8")
    if not records:
        fh.write(json.dumps({"header": header}) + "\n")
        fh.flush()
    ps_start = ps_snapshot(a.model)
    t0 = time.time()
    for i, it in enumerate(items, 1):
        if it["id"] in done:
            continue
        seg = segs[it["global_index"]]["segment"]
        st = stores.GraphStore(corpus, graph, it["article"])
        d = graph.duties[it["duty_id"]]
        dlabel = corpus.units[d["grounded_in"][0]]["label"]
        umsg = user_message(it["article"], corpus.text[it["article"]], seg, dlabel,
                            d["statement"], it["duty_id"])
        rec = {"id": it["id"], "segment_id": it["segment_id"], "article": it["article"],
               "stratum": it["stratum"], "duty_id": it["duty_id"], "conditions": {}}
        for cond in conds:
            extra = links_block(st, it["duty_id"]) if cond == "links" else ""
            rec["conditions"][cond] = run_condition(cond, a.model, st, umsg, extra,
                                                    a.num_ctx, a.turn_cap, a.temperature)
        records.append(rec)
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        print("[%3d/%d] %s art%d %s | %s | %.1fm" % (
            i, len(items), it["id"], it["article"], it["duty_id"],
            " ".join("%s:%dcalls%s" % (k, v["calls"], "!CAP" if v["turn_cap_hit"] else
                                       "!ERR" if v["error"] else "")
                     for k, v in rec["conditions"].items()),
            (time.time() - t0) / 60), flush=True)
    fh.close()
    blob = dict(header, k=stores.K, source_digests=corpus.digests(),
                corpus_sha256=sample.get("meta", {}).get("corpus_sha256"),
                ps_start=ps_start, ps_end=ps_snapshot(a.model),
                generated_at=time.strftime("%Y-%m-%d %H:%M:%S"), records=records)
    json.dump(blob, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    errs = sum(1 for r in records for v in r["conditions"].values() if v["error"])
    caps = sum(1 for r in records for v in r["conditions"].values() if v["turn_cap_hit"])
    mpe = max(v["max_prompt_eval"] for r in records for v in r["conditions"].values())
    print("wrote %s: %d items x %d conditions | errors %d | cap hits %d | max prompt_eval %d of %d"
          % (a.out, len(records), len(conds), errs, caps, mpe, a.num_ctx))


if __name__ == "__main__":
    main()
