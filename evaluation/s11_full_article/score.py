"""S11 scorer and pre-registered analysis. PREREGISTRATION-FULLARTICLE.md sections 5 and 6.

Reference: for the item's fixed duty, the qualification links the graph ENCODES
(appliesIf, notApplicableIf, hasException), each grounded in one or more source units.
The graph is the reference, not legal ground truth.

Scoring is mechanical. Each answer entry's `provision` string is split into citations
and resolved against the pinned source units. An entry MATCHES a reference link when one
of its cited units stands in the match relation to one of the link's grounding units.
Matching is one-to-one (maximum bipartite matching): one entry credits at most one link,
one link is credited at most once.

  primary match   CONTAINMENT: the cited unit equals a grounding unit, contains it, or
                  is contained in it (spans over the pinned article text).
  strict match    the cited unit equals a grounding unit, or is its ancestor, or is a
                  subparagraph of a paragraph-level grounding unit. A point does not
                  match a paragraph-level link.
  kind match      strict-or-primary as above AND the stated kind agrees with the encoded
                  kind (condition~appliesIf, exception~hasException,
                  not_applicable_if~notApplicableIf). Secondary.

Per item: recall = matched links / reference links; precision = matched entries /
entries. An unparseable answer is scored as an empty answer (recall 0, precision
undefined) and counted.

    .venv/Scripts/python.exe -B paper_draft/s11_full_article/score.py TRACES --out ANALYSIS.json
    .venv/Scripts/python.exe -B paper_draft/s11_full_article/score.py --selfcheck
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import stores  # noqa: E402

ALPHA = 0.05
EXACT_MAX_N = 20
PRIMARY_PAIR = ("fulltext", "graph")
SECONDARY_PAIR = ("fulltext", "links")
KIND = {"appliesif": "condition", "condition": "condition",
        "hasexception": "exception", "exception": "exception",
        "notapplicableif": "not_applicable_if", "not_applicable_if": "not_applicable_if",
        "notapplicable": "not_applicable_if"}


# ------------------------------------------------------------------ parsing answers

def parse_answer(text):
    """The first JSON object carrying a `qualifications` list, or None."""
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text)
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", t):
        try:
            obj, _ = dec.raw_decode(t[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("qualifications"), list):
            return [q for q in obj["qualifications"] if isinstance(q, dict)]
    return None


RANGE = re.compile(r"(\d+)\((\d+)\)\(([a-z])\)\s*(?:-|to|through|–)\s*\(([a-z])\)")


def split_citations(s):
    """'Article 13(1), Article 14(1)' -> two; 'Article 14(5)(a)-(d)' -> four;
    'Article 14(5)(a), (b)' -> two, the bare point inheriting the previous prefix."""
    s = str(s or "")
    s = RANGE.sub(lambda m: ", ".join("%s(%s)(%s)" % (m.group(1), m.group(2), chr(c))
                                      for c in range(ord(m.group(3)), ord(m.group(4)) + 1)), s)
    out, prev = [], None
    for frag in re.split(r",|;|\band\b|\bor\b|&", s):
        f = frag.strip()
        if not f:
            continue
        if f.startswith("(") and prev:
            base = re.match(r"^(.*?\d+\(\d+\))", prev)
            f = (base.group(1) if base else prev) + f
        out.append(f)
        prev = f
    return out


# ------------------------------------------------------------------ matching

def span(corpus, uid):
    u = corpus.units[uid]
    art = int(re.match(r"art(\d+)", uid).group(1))
    return art, u["char_start"], u["char_end"]


def contains(corpus, a, b):
    """Unit a's span contains unit b's span (same article)."""
    A, B = span(corpus, a), span(corpus, b)
    return A[0] == B[0] and A[1] <= B[1] and B[2] <= A[2]


def match_primary(corpus, cited, grounding):
    return cited == grounding or contains(corpus, cited, grounding) or contains(corpus, grounding, cited)


def match_strict(corpus, cited, grounding):
    if cited == grounding or contains(corpus, cited, grounding):
        return True
    g = corpus.units[grounding]
    c = corpus.units[cited]
    return g["kind"] == "paragraph" and c["kind"] != "point" and contains(corpus, grounding, cited)


def max_matching(adj, n_left):
    """adj[i] = set of right indices entry i may match. Returns the matching size and
    the pairs. Kuhn's augmenting paths; sizes here are under 20."""
    owner = {}

    def aug(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in owner or aug(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in range(n_left):
        aug(i, set())
    return len(owner), sorted((i, j) for j, i in owner.items())


def score_answer(corpus, graph, duty_id, entries):
    refs = graph.duties[duty_id]["relations"]
    own = set(graph.duties[duty_id]["grounded_in"])
    cited = []
    for e in entries or []:
        units = [corpus.resolve(c) for c in split_citations(e.get("provision"))]
        cited.append({"units": [u for u in units if u], "kind": KIND.get(
            re.sub(r"[^a-z_]", "", str(e.get("kind", "")).lower()))})
    res = {}
    for name, pred, kinded in (("primary", match_primary, False),
                               ("strict", match_strict, False),
                               ("kind", match_primary, True)):
        adj = []
        for e in cited:
            adj.append({j for j, r in enumerate(refs)
                        if any(pred(corpus, u, g) for u in e["units"] for g in r["grounded_in"])
                        and (not kinded or e["kind"] == KIND[r["kind"].lower()])})
        m, pairs = max_matching(adj, len(cited))
        matched_refs = {j for _, j in pairs}
        cross = [j for j, r in enumerate(refs) if not (set(r["grounded_in"]) & own)]
        res[name] = {"matched": m,
                     "recall": m / len(refs),
                     "precision": (m / len(cited)) if cited else None,
                     "cross_recall": (sum(1 for j in cross if j in matched_refs) / len(cross))
                     if cross else None,
                     "matched_relations": sorted(refs[j]["relation_id"] for j in matched_refs),
                     "unmatched_entries": [i for i in range(len(cited))
                                           if i not in {a for a, _ in pairs}]}
    unresolved = sum(1 for e in cited if not e["units"])
    return dict(res, n_ref=len(refs), n_entries=len(cited), n_unresolved=unresolved)


# ------------------------------------------------------------------ statistics

def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def wilcoxon(diffs):
    """Copied from s6_tools/graded_analyse.py: two-sided signed-rank, zeros dropped,
    exact for n <= 20, normal approximation with tie and continuity correction above."""
    nz = [d for d in diffs if d != 0]
    n = len(nz)
    if n == 0:
        return None, 0, None, "no non-zero differences"
    ranks = _ranks([abs(d) for d in nz])
    w_plus = sum(r for d, r in zip(nz, ranks) if d > 0)
    if n <= EXACT_MAX_N:
        total = hits = 0
        target = min(w_plus, sum(ranks) - w_plus)
        for signs in product((0, 1), repeat=n):
            s = sum(r for sgn, r in zip(signs, ranks) if sgn)
            total += 1
            if s <= target or s >= sum(ranks) - target:
                hits += 1
        return min(1.0, hits / total), n, w_plus, "exact"
    mean = sum(ranks) / 2.0
    tie_term = sum(t ** 3 - t for t in Counter(ranks).values())
    var = (n * (n + 1) * (2 * n + 1) - tie_term / 2.0) / 24.0
    if var <= 0:
        return 1.0, n, w_plus, "normal approximation, zero variance"
    z = (abs(w_plus - mean) - 0.5) / math.sqrt(var)
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
    return min(1.0, max(0.0, p)), n, w_plus, "normal approximation"


def paired(rows, a, b, key, rule="primary"):
    xs, ys = [], []
    for r in rows:
        x, y = r["scores"].get(a), r["scores"].get(b)
        if x is None or y is None:
            continue
        vx, vy = x[rule][key], y[rule][key]
        if vx is None or vy is None:
            continue
        xs.append(vx)
        ys.append(vy)
    d = [x - y for x, y in zip(xs, ys)]
    p, nnz, wp, method = wilcoxon(d)
    return {"pair": [a, b], "metric": key, "rule": rule, "n_paired": len(d),
            "n_ties": len(d) - nnz, "W_plus": wp, "test": "Wilcoxon signed-rank, two-sided (%s)" % method,
            "median_%s" % a: median(xs), "median_%s" % b: median(ys),
            "mean_%s" % a: (sum(xs) / len(xs)) if xs else None,
            "mean_%s" % b: (sum(ys) / len(ys)) if ys else None,
            "median_difference": median(d), "p": p, "significant": p is not None and p < ALPHA}


# ------------------------------------------------------------------ analysis

def score_traces(traces, corpus, graph):
    rows = []
    for rec in traces["records"]:
        row = {"id": rec["id"], "article": rec["article"], "duty_id": rec["duty_id"],
               "scores": {}, "usage": {}, "excluded": {}}
        for cond, v in rec["conditions"].items():
            row["usage"][cond] = {"input_tokens": v["input_tokens_total"], "calls": v["calls"],
                                  "turns": v["turns"],
                                  "called_get_conditions": any(c["call"] == "get_conditions"
                                                               for c in v["trace"])}
            if v["error"] or v["turn_cap_hit"]:
                row["excluded"][cond] = "error" if v["error"] else "turn_cap_hit"
                continue
            entries = parse_answer(v["final"])
            s = score_answer(corpus, graph, rec["duty_id"], entries or [])
            s["parse_ok"] = entries is not None
            row["scores"][cond] = s
        rows.append(row)
    return rows


def describe(rows, cond, rule="primary"):
    ss = [r["scores"][cond] for r in rows if cond in r["scores"]]
    rec = [s[rule]["recall"] for s in ss]
    pre = [s[rule]["precision"] for s in ss if s[rule]["precision"] is not None]
    cr = [s[rule]["cross_recall"] for s in ss if s[rule]["cross_recall"] is not None]
    us = [r["usage"][cond] for r in rows if cond in r["usage"]]
    return {"n": len(ss), "recall_median": median(rec),
            "recall_mean": (sum(rec) / len(rec)) if rec else None,
            "complete_set": sum(1 for x in rec if x == 1.0), "none": sum(1 for x in rec if x == 0.0),
            "precision_n": len(pre), "precision_median": median(pre),
            "precision_mean": (sum(pre) / len(pre)) if pre else None,
            "cross_recall_mean": (sum(cr) / len(cr)) if cr else None,
            "links_matched": sum(s[rule]["matched"] for s in ss),
            "links_reference": sum(s["n_ref"] for s in ss),
            "entries": sum(s["n_entries"] for s in ss),
            "extraneous_entries": sum(s["n_entries"] - s[rule]["matched"] for s in ss),
            "unresolved_entries": sum(s["n_unresolved"] for s in ss),
            "parse_fail": sum(1 for s in ss if not s["parse_ok"]),
            "empty_answer": sum(1 for s in ss if s["n_entries"] == 0),
            "input_tokens_median": median([u["input_tokens"] for u in us]),
            "input_tokens_mean": (sum(u["input_tokens"] for u in us) / len(us)) if us else None,
            "calls_mean": (sum(u["calls"] for u in us) / len(us)) if us else None,
            "called_get_conditions": sum(1 for u in us if u["called_get_conditions"])}


def per_duty(rows, cond):
    by = defaultdict(list)
    for r in rows:
        if cond in r["scores"]:
            by[r["duty_id"]].append(r["scores"][cond]["primary"]["recall"])
    return {d: sum(v) / len(v) for d, v in sorted(by.items())}


def analyse(rows):
    conds = sorted({c for r in rows for c in r["scores"]})
    out = {"alpha": ALPHA, "conditions": conds, "articles": {}}
    for art in sorted({r["article"] for r in rows}):
        rs = [r for r in rows if r["article"] == art]
        blk = {"n_items": len(rs),
               "excluded": dict(Counter("%s:%s" % (c, w) for r in rs for c, w in r["excluded"].items())),
               "descriptive": {c: {rule: describe(rs, c, rule) for rule in ("primary", "strict", "kind")}
                               for c in conds}}
        if all(c in conds for c in PRIMARY_PAIR):
            blk["primary_recall_test"] = paired(rs, *PRIMARY_PAIR, key="recall")
            blk["secondary"] = {
                "precision_fulltext_vs_graph": paired(rs, *PRIMARY_PAIR, key="precision"),
                "recall_strict_fulltext_vs_graph": paired(rs, *PRIMARY_PAIR, key="recall", rule="strict"),
                "cross_recall_fulltext_vs_graph": paired(rs, *PRIMARY_PAIR, key="cross_recall"),
                # Sensitivity: the primary test without items where either answer failed to parse.
                "recall_parsed_only_fulltext_vs_graph": paired(
                    [r for r in rs if all(r["scores"].get(c, {}).get("parse_ok") for c in PRIMARY_PAIR)],
                    *PRIMARY_PAIR, key="recall"),
            }
            # Sensitivity to pseudo-replication: items sharing a duty share a reference.
            da, db = per_duty(rs, PRIMARY_PAIR[0]), per_duty(rs, PRIMARY_PAIR[1])
            d = [da[k] - db[k] for k in da if k in db]
            p, nnz, wp, method = wilcoxon(d)
            blk["secondary"]["per_duty_recall_fulltext_vs_graph"] = {
                "n_duties": len(d), "n_ties": len(d) - nnz, "p": p, "test": method,
                "median_difference": median(d)}
            blk["per_duty_recall"] = {c: per_duty(rs, c) for c in conds}
        if all(c in conds for c in SECONDARY_PAIR):
            blk.setdefault("secondary", {})["recall_fulltext_vs_links"] = paired(rs, *SECONDARY_PAIR, key="recall")
        out["articles"][str(art)] = blk
    return out


def fmt(x, n=3):
    return "n/a" if x is None else ("%.*f" % (n, x) if isinstance(x, float) else str(x))


def render(out):
    L = ["S11 PRE-REGISTERED ANALYSIS (PREREGISTRATION-FULLARTICLE.md section 6).",
         "Per article, never pooled. Reference = the graph's encoded links, not legal ground truth.", ""]
    for art, blk in out["articles"].items():
        L.append("=== Article %s (n items %d) excluded %s" % (art, blk["n_items"], blk["excluded"] or "none"))
        hdr = "%-9s %-7s %4s %7s %7s %9s %5s %7s %7s %8s %6s %6s %8s %6s" % (
            "cond", "rule", "n", "rec.med", "rec.mean", "complete", "none", "pre.med", "pre.mean",
            "links", "extra", "unres", "tok.med", "calls")
        L += [hdr, "-" * len(hdr)]
        for c, rules in blk["descriptive"].items():
            for rule, d in rules.items():
                L.append("%-9s %-7s %4d %7s %7s %9s %5d %7s %7s %8s %6d %6d %8s %6s" % (
                    c, rule, d["n"], fmt(d["recall_median"]), fmt(d["recall_mean"]),
                    "%d/%d" % (d["complete_set"], d["n"]), d["none"], fmt(d["precision_median"]),
                    fmt(d["precision_mean"]), "%d/%d" % (d["links_matched"], d["links_reference"]),
                    d["extraneous_entries"], d["unresolved_entries"], fmt(d["input_tokens_median"], 0),
                    fmt(d["calls_mean"], 2)))
        for name, t in [("PRIMARY recall fulltext vs graph", blk.get("primary_recall_test"))] + \
                sorted(blk.get("secondary", {}).items()):
            if not t:
                continue
            L.append("%s: n %s, ties %s, median diff %s, p = %s%s" % (
                name, t.get("n_paired", t.get("n_duties")), t["n_ties"], fmt(t["median_difference"]),
                fmt(t["p"], 6) if t["p"] is not None else "n/a", "  SIGNIFICANT" if t.get("p") is not None and t["p"] < ALPHA else ""))
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ self-check

def selfcheck():
    c, g = stores.load()
    assert split_citations("Article 13(1), Article 14(1)") == ["Article 13(1)", "Article 14(1)"]
    assert split_citations("Article 14(5)(a)-(d)") == ["Article 14(5)(a)", "14(5)(b)", "14(5)(c)", "14(5)(d)"]
    assert split_citations("Article 14(5)(a), (b)") == ["Article 14(5)(a)", "Article 14(5)(b)"]
    assert parse_answer('```json\n{"qualifications": [{"provision": "x"}]}\n```') == [{"provision": "x"}]
    assert parse_answer("no json here") is None
    assert parse_answer('{"qualifications": []}') == []

    d = "obl-art14-1-a-controller-identity"          # 7 links: 3(b) 3(c) 14(1) 5(a-d)
    full = [{"provision": p, "kind": k} for p, k in [
        ("Article 14(3)(b)", "condition"), ("Article 14(3)(c)", "condition"),
        ("Article 14(1)", "not_applicable_if"), ("Article 14(5)(a)", "exception"),
        ("Article 14(5)(b)", "exception"), ("Article 14(5)(c)", "exception"),
        ("Article 14(5)(d)", "exception")]]
    s = score_answer(c, g, d, full)
    assert s["n_ref"] == 7 and s["primary"]["recall"] == 1.0 and s["primary"]["precision"] == 1.0, s
    assert s["kind"]["recall"] == 1.0, s
    # one-to-one: a paragraph citation repeated credits at most the links under it, once each
    s = score_answer(c, g, d, [{"provision": "Article 14(5)"}] * 6)
    assert s["primary"]["matched"] == 4 and s["primary"]["precision"] == 4 / 6, s
    # strict: an ancestor citation still matches; a point under a paragraph-level link does not
    s = score_answer(c, g, d, [{"provision": "Article 14(1)(a)"}])
    assert s["primary"]["matched"] == 1 and s["strict"]["matched"] == 0, s
    s = score_answer(c, g, d, [{"provision": "Article 14(1), subparagraph 1"}])
    assert s["strict"]["matched"] == 1, s
    # unresolvable and out-of-article citations are extraneous, never matches
    s = score_answer(c, g, d, [{"provision": "Article 6(1)(f)"}, {"provision": "Article 14(3)(a)"}])
    assert s["primary"]["matched"] == 0 and s["n_unresolved"] == 1 and s["primary"]["precision"] == 0.0, s
    # wrong kind fails only the kind rule
    s = score_answer(c, g, d, [{"provision": "Article 14(5)(a)", "kind": "condition"}])
    assert s["primary"]["matched"] == 1 and s["kind"]["matched"] == 0, s
    # empty answer: recall 0, precision undefined
    s = score_answer(c, g, d, [])
    assert s["primary"]["recall"] == 0.0 and s["primary"]["precision"] is None
    # cross-provision recall for an Article 13 duty: 13(1) links are cross for a 13(1)(d) duty
    s = score_answer(c, g, "obl-art13-1-d-legitimate-interests",
                     [{"provision": "Article 13(1)(d)"}, {"provision": "Article 13(4)"}])
    assert s["n_ref"] == 4 and s["primary"]["matched"] == 2, s
    # wilcoxon hand values, as in graded_analyse.py
    assert abs(wilcoxon([0.1, 0.2, 0.3, 0.4, 0.5])[0] - 2 / 32) < 1e-12
    assert wilcoxon([0.3, -0.3, 0.2, -0.2])[0] == 1.0 and wilcoxon([0, 0])[0] is None
    assert wilcoxon([0.01 * i for i in range(1, 30)])[0] < 1e-4
    print("score.py self-check OK: citation splitting, parsing, one-to-one matching, "
          "strict/primary/kind rules, empty answers, Wilcoxon hand values")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("traces", nargs="?")
    ap.add_argument("--out", default="")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    c, g = stores.load()
    rows = score_traces(json.load(open(a.traces, encoding="utf-8")), c, g)
    out = analyse(rows)
    text = render(out)
    print(text)
    if a.out:
        json.dump({"analysis": out, "items": rows}, open(a.out, "w", encoding="utf-8"), indent=2)
        open(a.out.replace(".json", ".txt"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
