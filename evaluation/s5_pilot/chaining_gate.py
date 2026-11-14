"""Model screen, stage 3: can a 7B model run a multi-turn tool loop, not just emit one call?

Pass criterion, decided before the run:
  a get_conditions call whose duty_id is an id returned by a preceding find_duties call.

A floor check, not a model comparison. Items come from the 40-item pilot sample, disjoint
from the study sample. Run 1 used the first ten pilot items (all Article 12); run 2 used a
mix across Articles 12, 13, 14 and 46 (--mixed). The recorded outputs are in
chaining_gate.run1.output.txt and chaining_gate.run2.output.txt.

    python chaining_gate.py PATH/TO/LexiGen_corpus.json [--mixed]
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CHAT = "http://127.0.0.1:11434/api/chat"
NUM_CTX = 16384
CORPUS = sys.argv[1]
MIXED = "--mixed" in sys.argv[2:]

payloads = json.load(open(os.path.join(HERE, "payloads.json"), encoding="utf-8"))
sample = json.load(open(os.path.join(HERE, "sample.frozen.json"), encoding="utf-8"))
SEGS = [x for b in json.load(open(CORPUS, encoding="utf-8")) for x in b["segments"]]


def store(art):
    units = payloads[str(art)]["arm3_grounded"]
    return {u["id"]: u for u in units}


TOOLS = [
    {"type": "function", "function": {
        "name": "find_duties",
        "description": "Search the duties of this GDPR article by topic. Returns duty ids and statements.",
        "parameters": {"type": "object", "properties": {
            "topic": {"type": "string", "description": "a few words describing the subject matter"}},
            "required": ["topic"]}}},
    {"type": "function", "function": {
        "name": "get_conditions",
        "description": "Given a duty id returned by find_duties, return the conditions that switch it on, the conditions that switch it off, and any exceptions to it.",
        "parameters": {"type": "object", "properties": {
            "duty_id": {"type": "string", "description": "a duty id exactly as returned by find_duties"}},
            "required": ["duty_id"]}}},
]


def call_tool(name, args, st):
    if name == "find_duties":
        q = str(args.get("topic", "")).lower()
        words = [w for w in q.split() if len(w) > 3]
        hits = [u for u in st.values() if any(w in u["statement"].lower() for w in words)]
        hits = hits or list(st.values())
        return json.dumps([{"duty_id": u["id"], "statement": u["statement"]} for u in hits[:6]])
    if name == "get_conditions":
        u = st.get(str(args.get("duty_id", "")))
        if not u:
            return json.dumps({"error": "unknown duty_id", "known_ids": list(st)[:6]})
        return json.dumps({
            "applies_if": [c["statement"] for c in u["applies_if"]],
            "not_applicable_if": [c["statement"] for c in u["not_applicable_if"]],
            "exceptions": [c["statement"] for c in u["has_exception"]]})
    return json.dumps({"error": "no such tool"})


def chat(model, messages):
    body = {"model": model, "messages": messages, "stream": False,
            "tools": TOOLS, "options": {"temperature": 0.0, "num_ctx": NUM_CTX}}
    req = urllib.request.Request(CHAT, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


SYS = ("You assess whether a privacy policy segment complies with one GDPR article. "
       "You do NOT know the article's contents. Use the tools to find the relevant duties, "
       "then use get_conditions on the duty ids you find to check whether any condition or "
       "exception changes the answer. Only then give a verdict of COMPLIANT, NON_COMPLIANT or "
       "NOT_APPLICABLE with a short justification.")


def run(model, item, max_turns=6):
    art = item["article"]
    st = store(art)
    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": "GDPR Article {}.\n\nPOLICY SEGMENT:\n{}".format(
                art, SEGS[item["global_index"]]["segment"])}]
    trace, returned_ids = [], set()
    chained = False
    for _ in range(max_turns):
        try:
            out = chat(model, msgs)
        except Exception as e:
            trace.append({"error": str(e)[:200]})
            break
        m = out.get("message", {})
        calls = m.get("tool_calls") or []
        msgs.append(m)
        if not calls:
            trace.append({"final": (m.get("content") or "")[:200]})
            break
        for c in calls:
            fn = c["function"]["name"]
            args = c["function"]["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            if fn == "get_conditions" and str(args.get("duty_id")) in returned_ids:
                chained = True
            res = call_tool(fn, args, st)
            trace.append({"call": fn, "args": args, "ret_chars": len(res)})
            if fn == "find_duties":
                for d in json.loads(res):
                    returned_ids.add(d["duty_id"])
            msgs.append({"role": "tool", "content": res})
    return {"turns": len([t for t in trace if "call" in t]), "chained": chained, "trace": trace}


def main():
    p = sample["pilot"]
    items = p[0:2] + p[10:13] + p[20:23] + p[30:32] if MIXED else p[:10]
    out = {}
    for model in ("mistral:7b", "qwen2.5:7b"):
        rows = []
        for it in items:
            r = run(model, it)
            rows.append(r)
            print("{} art{} calls={} chained={}".format(
                model, it["article"], r["turns"], r["chained"]), flush=True)
        out[model] = {"chained": sum(r["chained"] for r in rows), "n": len(rows),
                      "mean_calls": round(sum(r["turns"] for r in rows) / len(rows), 2),
                      "rows": rows}
        print(f"== {model}: chained {out[model]['chained']}/{len(rows)}, mean calls {out[model]['mean_calls']}", flush=True)
    name = "chaining_gate.run2.json" if MIXED else "chaining_gate.run1.json"
    json.dump(out, open(os.path.join(HERE, name), "w"), indent=2)


main()
