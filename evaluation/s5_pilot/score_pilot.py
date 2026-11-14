"""Score the S5 pilot against the Part D item 3 definition of a grounded justification.

  (a) cites at least one provision identifier          - mechanical
  (b) the identifier resolves to a real Article /
      Paragraph / Point in the digest-pinned source    - mechanical
  (c) the cited provision's text supports the
      assertion made about it                          - textual entailment

(c) is reported three ways, entailed / neutral / contradicted, never summed, per the
2026-09-05 decision. Similarity is not used and is not a fallback.

The entailment checkpoint is TehranNLP-org/bert-large-mnli, which is the one LexiGen's own
benchmark runs, so the instrument is the baseline's rather than a new one.

Run with LexiGen's venv (transformers + torch already present):
  python score_pilot.py <pilot.json>
"""
import json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NLI_MODEL = "TehranNLP-org/bert-large-mnli"
# The hub download stalls repeatedly on this connection, so a local copy of the SAME
# checkpoint is used when present. It lives OUTSIDE the project tree, because 1.3 GB of
# weights does not belong in it. Override with S5_NLI_DIR if it moves again.
_LOCAL = os.path.normpath(os.environ.get(
    "S5_NLI_DIR",
    os.path.join(ROOT, "..", "..", "..", "models", "bert-large-mnli")))
PINNED = (6, 12, 13, 14, 46)

CITE_RE = re.compile(
    r"art(?:icle|\.)?\s*(\d+)"           # Article 13
    r"(?:\s*\(\s*(\d+)\s*\))?"           # (1)
    r"(?:\s*\(\s*([a-z])\s*\))?",        # (c)
    re.I)


def load_units():
    """label -> (unit_id, text) over every pinned source, digest-verified."""
    import hashlib
    by_label, by_article = {}, defaultdict(dict)
    for art in PINNED:
        meta = json.load(open(os.path.join(ROOT, "sources", f"art{art}.units.json"), encoding="utf-8"))
        text = open(os.path.join(ROOT, "sources", f"art{art}.txt"), encoding="utf-8").read()
        assert hashlib.sha256(text.encode()).hexdigest() == meta["sha256"], f"art{art} digest"
        for u in meta["units"]:
            body = text[u["char_start"]:u["char_end"]].strip()
            by_label[u["label"]] = (u["unit_id"], body)
            by_article[art][u["label"]] = (u["unit_id"], body)
    return by_label, by_article


def canonical(cite):
    """'Art. 13(1)(c)' -> ('Article 13(1)(c)', article, depth). None if unparseable."""
    m = CITE_RE.search(cite or "")
    if not m:
        return None, None, None
    art, para, pt = m.group(1), m.group(2), m.group(3)
    s = f"Article {art}"
    depth = "article"
    if para:
        s += f"({para})"
        depth = "paragraph"
    if pt:
        s += f"({pt.lower()})"
        depth = "point"
    return s, int(art), depth


def resolve(cite, by_label, node_map=None):
    """Bucket a citation. The buckets are NOT all failures and must not be summed.

    node_map: {graph node id -> (provision label, provision text)} for the article. Arm 3
    sometimes cites the graph's own node id ("[obl-12-1-form]") instead of a provision
    reference. That is not a hallucination and not malformed: it is the model using the
    supplied structure while naming the wrong kind of identifier.

    Such a citation gets its OWN bucket and is deliberately NOT counted toward limb (b).
    Only arm 3 can produce one, because only arm 3 is shown node ids, so folding it into
    limb (b) would inflate arm 3 by construction. It IS counted as evidence that the model
    used the supplied grounding, which is a different question. See Part D item 3's
    circularity guard. Whether limb (b) should admit it is the author's call.
    """
    raw = (cite or "").strip().strip("[]")
    if node_map and raw in node_map:
        lab, text = node_map[raw]
        return {"canonical": lab, "bucket": "graph_node_id", "unit_id": raw, "text": text,
                "depth": "node", "node_id": raw}
    canon, art, depth = canonical(cite)
    if canon is None:
        return {"canonical": None, "bucket": "malformed", "unit_id": None, "text": None}
    if canon in by_label:
        uid, text = by_label[canon]
        return {"canonical": canon, "bucket": "resolved", "unit_id": uid, "text": text,
                "depth": depth}
    if art not in PINNED:
        # a real GDPR article this project pinned no source for. Not a hallucination,
        # and reporting it as one would be wrong.
        return {"canonical": canon, "bucket": "out_of_pinned_scope", "unit_id": None,
                "text": None, "depth": depth}
    if depth == "article":
        # article-level citation: there is no provision unit at that granularity. This is
        # exactly LexiGen's granularity and it is the paper's argument, not an error.
        return {"canonical": canon, "bucket": "article_level_no_unit", "unit_id": None,
                "text": None, "depth": depth}
    return {"canonical": canon, "bucket": "unresolvable_in_pinned_source", "unit_id": None,
            "text": None, "depth": depth}


def nli_scores(pairs):
    """[(premise, hypothesis)] -> ['entailed'|'neutral'|'contradicted']."""
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    src = _LOCAL if os.path.exists(os.path.join(_LOCAL, "pytorch_model.bin")) else NLI_MODEL
    # print what was ACTUALLY loaded. Printing the constant meant that overriding
    # S5_NLI_DIR put a false checkpoint name into every log line.
    print(f"NLI checkpoint: {os.path.basename(src) if src is _LOCAL else src}  [{src}]")
    tok = AutoTokenizer.from_pretrained(src)
    mdl = AutoModelForSequenceClassification.from_pretrained(src).eval()
    id2 = {int(k): v for k, v in mdl.config.id2label.items()}
    norm = {}
    for i, v in id2.items():
        v = v.lower()
        norm[i] = ("entailed" if "entail" in v else
                   "contradicted" if "contradic" in v else "neutral")
    out = []
    B = 8
    with torch.no_grad():
        for i in range(0, len(pairs), B):
            chunk = pairs[i:i + B]
            enc = tok([p for p, _ in chunk], [h for _, h in chunk],
                      truncation=True, max_length=512, padding=True, return_tensors="pt")
            logits = mdl(**enc).logits
            for row in logits.argmax(-1).tolist():
                out.append(norm[row])
    return out


def main():
    pilot = json.load(open(sys.argv[1], encoding="utf-8"))
    by_label, _ = load_units()
    payloads = json.load(open(os.path.join(HERE, "payloads.json"), encoding="utf-8"))

    node_maps, supplied_by_art = {}, {}
    for art, pay in payloads.items():
        nm, sup = {}, set()
        for u in pay["arm3_grounded"]:
            g = u["grounded_in"][0] if u["grounded_in"] else None
            if g and g.get("citation"):
                nm[u["id"]] = (g["citation"], g.get("text") or "")
                sup.add(g["citation"])
        node_maps[art], supplied_by_art[art] = nm, sup

    pairs, index = [], []
    for rec in pilot["records"]:
        art = str(rec["article"])
        for arm, res in rec["arms"].items():
            d = res["parsed"] or {}
            cites = [c for c in (d.get("citations") or []) if isinstance(c, str)]
            just = (d.get("justification") or "").strip()
            # arm 1 is never shown node ids, so it is resolved without the node map
            nm = node_maps[art] if arm == "arm3" else None
            resolved = [resolve(c, by_label, nm) for c in cites]
            res["limb_a"] = bool(cites)
            res["citations_resolved"] = resolved
            res["limb_b"] = any(r["bucket"] == "resolved" for r in resolved)
            # circularity guard: in arm 3 the graph SUPPLIES citations. Record whether the
            # model used a supplied one, so arm 3 cannot score well merely by availability.
            if arm == "arm3":
                sup = supplied_by_art[art]
                res["used_supplied_anchor"] = any(
                    r["canonical"] in sup or r["bucket"] == "graph_node_id" for r in resolved)
            for r in resolved:
                if r["bucket"] in ("resolved", "graph_node_id") and just:
                    pairs.append((r["text"], just))
                    index.append((rec["id"], arm, r["canonical"]))

    print(f"limb (c) pairs to judge: {len(pairs)}")
    verdicts = nli_scores(pairs) if pairs else []
    lut = {}
    for (sid, arm, canon), v in zip(index, verdicts):
        lut[(sid, arm, canon)] = v

    for rec in pilot["records"]:
        for arm, res in rec["arms"].items():
            per = []
            for r in res["citations_resolved"]:
                if r["bucket"] in ("resolved", "graph_node_id"):
                    r["entailment"] = lut.get((rec["id"], arm, r["canonical"]))
                    per.append(r["entailment"])
            res["limb_c"] = per
            res["grounded_auto"] = bool(res["limb_a"] and res["limb_b"]
                                        and "entailed" in per)

    pilot["scoring"] = {"nli_model": NLI_MODEL,
                        "definition": "Part D item 3 (a)/(b)/(c)",
                        "note": "automatic scores only; the reference standard is the hand labels"}
    out = sys.argv[1].replace(".json", ".scored.json")
    json.dump(pilot, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # summary, stratified, never pooled across the applicable / not-applicable boundary
    print(f"\n{'stratum':>8} {'arm':>5} {'n':>3} {'(a)':>5} {'(b)':>5} "
          f"{'entail':>7} {'neutr':>6} {'contra':>7} {'used-anchor':>12}")
    groups = defaultdict(list)
    for rec in pilot["records"]:
        for arm, res in rec["arms"].items():
            groups[(rec["stratum"], arm)].append(res)
    for k in sorted(groups):
        rs = groups[k]
        c = Counter(v for r in rs for v in r["limb_c"])
        ua = [r.get("used_supplied_anchor") for r in rs if "used_supplied_anchor" in r]
        print(f"{k[0]:>8} {k[1]:>5} {len(rs):>3} "
              f"{sum(r['limb_a'] for r in rs):>5} {sum(r['limb_b'] for r in rs):>5} "
              f"{c['entailed']:>7} {c['neutral']:>6} {c['contradicted']:>7} "
              f"{(str(sum(1 for x in ua if x)) + '/' + str(len(ua))) if ua else '-':>12}")

    print("\ncitation buckets (these are NOT all failures and must not be summed):")
    bk = Counter(r["bucket"] for rec in pilot["records"] for res in rec["arms"].values()
                 for r in res["citations_resolved"])
    for b, n in bk.most_common():
        print(f"  {b:>32} {n:>4}")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
