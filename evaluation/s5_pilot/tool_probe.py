"""Model screen, stage 2: does each installed model emit a native tool call at all?

One prompt, one tool, temperature 0.0, num_ctx 8192, against a local Ollama server.
The recorded output is in tool_probe.output.txt.

    python tool_probe.py
"""
import json
import urllib.request

TOOLS = [{"type": "function", "function": {
    "name": "get_provision",
    "description": "Fetch the exact text of a GDPR provision by its identifier.",
    "parameters": {"type": "object", "properties": {"provision_id": {
        "type": "string", "description": "e.g. 'Article 13(1)(c)'"}},
        "required": ["provision_id"]}}}]
MSG = [{"role": "user", "content": "What does Article 13(1)(c) of the GDPR say? Use the tool."}]

for m in ("llama3:latest", "mistral:7b", "qwen2.5:7b"):
    body = {"model": m, "messages": MSG, "tools": TOOLS, "stream": False,
            "options": {"temperature": 0.0, "num_ctx": 8192}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        tc = r.get("message", {}).get("tool_calls")
        if tc:
            f = tc[0]["function"]
            print(f"{m:>16}  TOOL CALL -> {f['name']}({json.dumps(f.get('arguments'))})")
        else:
            print(f"{m:>16}  no tool call; replied: {r.get('message', {}).get('content', '')[:90]!r}")
    except Exception as e:
        print(f"{m:>16}  ERROR {type(e).__name__}: {str(e)[:110]}")
