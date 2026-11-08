"""The shared tool surface: three functions, identical signatures, over two stores.

Per 05_EVAL_PLAN.md Part E1. Both arms get the SAME three functions and the SAME
retrieval index. The stores differ only in what they return for a matched provision.

    find_duties(topic)         text  -> the matched provision chunks
                               graph -> the duty nodes grounded in those provisions
    get_conditions(duty_id)    text  -> the duty's chapeau and its paragraph siblings
                               graph -> the relation nodes attached to that duty
    get_provision(citation)    both  -> the pinned source text

Three boundaries carried straight from E1 and not to be relaxed:
  - the text store answers in its own currency: get_conditions returns sibling TEXT,
    never relation edges.
  - there is no get_exceptions. Splitting the function would leak the existence of
    "exception" as a category into the text arm through the schema.
  - get_provision is not optional. Both arms emit citations, so both need source.

Retrieval (E1a): ONE shared index of the article's source provision units, BM25,
k = 5 provisions, identical in both arms. find_duties is deliberately a non-variable
so that get_conditions is the only place the representation acts.

Every store method returns (payload, provenance). The payload is what the model sees.
The provenance is the machine record the reach extractor reads: which source units had
their TEXT returned, which relation nodes were returned, which duties were named. The
extractor never parses prose, which is what makes it hand-checkable.

Run the self-check from publish-gdpr-kg/ with .venv/Scripts/python.exe:
    .venv/Scripts/python.exe paper_draft/s6_tools/stores.py
"""
import json
import math
import os
import re
import sys

import rdflib
from rdflib import Namespace, RDF, RDFS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load_units(art):
    """Copied verbatim from paper_draft/s5_pilot/build_payloads.py (not published) so this
    file runs from evaluation/. The only change from the frozen instrument. Re-verifies
    art*.txt against the sha256 its units.json pins."""
    import hashlib
    p = os.path.join(ROOT, "sources", f"art{art}.units.json")
    meta = json.load(open(p, encoding="utf-8"))
    text = open(os.path.join(ROOT, "sources", f"art{art}.txt"), encoding="utf-8").read()
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != meta["sha256"]:
        raise SystemExit(f"art{art}.txt digest mismatch: {actual} != {meta['sha256']}")
    if len(text) != meta["char_length"]:
        raise SystemExit(f"art{art}.txt char_length mismatch")
    return {u["unit_id"]: dict(u, text=text[u["char_start"]:u["char_end"]].strip())
            for u in meta["units"]}, meta

G = Namespace("https://w3id.org/gdprkg#")
ARTICLES = (12, 13, 14, 46)
DUTY_CLASSES = ("Obligation", "Permission", "TransferMechanism")
RELATION_PREDICATES = (("appliesIf", G.appliesIf),
                       ("notApplicableIf", G.notApplicableIf),
                       ("hasException", G.hasException))
K = 5  # provisions returned by find_duties, fixed and identical across arms (E1a)


# --------------------------------------------------------------------------- BM25

def tokenise(s):
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if len(t) >= 3]


class BM25:
    """Okapi BM25 over one article's source provision units.

    Length normalisation is the reason this is BM25 and not term overlap: unit
    lengths run 7 to 245 words, so overlap favours chapeaux over the short
    point-level chunks the study depends on (Article 14(5)(a) is nine words).
    """

    def __init__(self, docs, k1=1.5, b=0.75):
        self.ids = list(docs)                      # insertion order, deterministic
        self.toks = {i: tokenise(docs[i]) for i in self.ids}
        self.len = {i: len(self.toks[i]) for i in self.ids}
        self.avg = (sum(self.len.values()) / len(self.ids)) if self.ids else 0.0
        self.k1, self.b = k1, b
        self.df = {}
        for i in self.ids:
            for t in set(self.toks[i]):
                self.df[t] = self.df.get(t, 0) + 1
        self.n = len(self.ids)

    def score(self, query):
        q = tokenise(query)
        out = {}
        for i in self.ids:
            tf, s = {}, 0.0
            for t in self.toks[i]:
                tf[t] = tf.get(t, 0) + 1
            for t in q:
                f = tf.get(t, 0)
                if not f:
                    continue
                idf = math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1))
                s += idf * f * (self.k1 + 1) / denom
            out[i] = s
        return out

    def top(self, query, k):
        sc = self.score(query)
        # ties break on unit_id so a rerun retrieves the same k. Part D item 4's
        # stability measure isolates the substrate; retrieval must not add noise.
        ranked = sorted(self.ids, key=lambda i: (-sc[i], i))
        return [(i, round(sc[i], 4)) for i in ranked[:k] if sc[i] > 0]


# ------------------------------------------------------------------------- corpus

def normalise_citation(s):
    """'Article 14(5)(a)' / 'Art. 14(5)(a)' / '14(5)(a)' all reduce to '14(5)(a)'."""
    s = str(s).lower().strip()
    s = re.sub(r"^art(icle)?s?\.?\s*", "", s)
    return re.sub(r"[^a-z0-9()]", "", s)


def parent_of(unit_id):
    """art14-p1-c -> art14-p1; art14-p1-sub1 -> art14-p1; art14-p1 -> art14-p1."""
    m = re.match(r"^(art\d+-p\d+)", unit_id)
    return m.group(1) if m else unit_id


class Corpus:
    """The 87 pinned source provision units plus one BM25 index per article."""

    def __init__(self, articles=ARTICLES):
        self.articles = tuple(articles)
        self.units, self.meta, self.text = {}, {}, {}
        for a in self.articles:
            u, m = load_units(a)          # verifies art{a}.txt against the pinned sha256
            self.units.update(u)
            self.meta[a] = m
            self.text[a] = open(os.path.join(ROOT, "sources", "art%d.txt" % a),
                                encoding="utf-8").read()
        self.by_article = {a: [u for u in self.units
                               if u.startswith("art%d-" % a)] for a in self.articles}
        self.index = {a: BM25({u: self.units[u]["text"] for u in self.by_article[a]})
                      for a in self.articles}
        self.by_citation = {}
        for uid, u in self.units.items():
            self.by_citation[normalise_citation(u["label"])] = uid
            self.by_citation[uid.lower()] = uid

    def digests(self):
        return {str(a): self.meta[a]["sha256"] for a in self.articles}

    def resolve(self, citation):
        return self.by_citation.get(normalise_citation(citation)) \
            or self.by_citation.get(str(citation).lower().strip())

    def children(self, unit_id):
        """Units under the same paragraph, the paragraph unit itself excluded."""
        p = parent_of(unit_id)
        return [u for u in self.by_article.get(int(re.match(r"art(\d+)", unit_id).group(1)), [])
                if parent_of(u) == p and u != p]

    def closure(self, unit_id):
        """A named unit plus, if it is a paragraph or subparagraph, its points.

        Applied identically in both arms. Asking for the conditions of Article 14(1)
        is relying on the duties 14(1) carries, and those are grounded in its points.
        Without the closure a text-arm call on a chapeau relies on nothing at all.
        """
        u = self.units.get(unit_id)
        if u is None:
            return []
        if u["kind"] == "point":
            return [unit_id]
        return sorted(set([unit_id] + [c for c in self.children(unit_id)
                                       if self.units[c]["kind"] == "point"]))


class Graph:
    """Duties and the relation nodes attached to them, from the certified ABox."""

    def __init__(self, corpus, articles=ARTICLES):
        self.corpus = corpus
        g = rdflib.Graph()
        for a in articles:
            g.parse(os.path.join(ROOT, "articles", "art%d.ttl" % a), format="turtle")
        self.g = g
        loc = lambda n: str(n).split("#")[-1]
        self.duties = {}
        for cls in DUTY_CLASSES:
            for node in sorted(g.subjects(RDF.type, G[cls]), key=str):
                stmt = g.value(node, RDFS.label)
                grounded = sorted(loc(o) for o in g.objects(node, G.groundedIn))
                if not stmt or not grounded:
                    continue
                rels = []
                for kind, pred in RELATION_PREDICATES:
                    for o in sorted(g.objects(node, pred), key=str):
                        # A shared node can ground into another article's source (the
                        # collection Condition grounds in both 13(1) and 14(1)), so the
                        # grounding is resolved against every pinned article, never just
                        # the current one. Hard won in build_payloads.py; do not narrow.
                        og = sorted(loc(x) for x in g.objects(o, G.groundedIn))
                        rels.append({"relation_id": loc(o), "kind": kind,
                                     "statement": str(g.value(o, RDFS.label) or ""),
                                     "grounded_in": og})
                self.duties[loc(node)] = {
                    "duty_id": loc(node), "type": cls, "statement": str(stmt),
                    # The article a duty belongs to is taken from its groundedIn unit id,
                    # which is uniform; node local names are NOT (obl-art13-* vs obl-12-*).
                    "grounded_in": grounded, "relations": rels,
                }
        self.by_unit = {}
        for d in self.duties.values():
            for uid in d["grounded_in"]:
                self.by_unit.setdefault(uid, []).append(d["duty_id"])
        for uid in self.by_unit:
            self.by_unit[uid].sort()

    def duties_for_units(self, unit_ids):
        """Every duty grounded in any of these units. The reach extractor's anchor."""
        out = []
        for uid in unit_ids:
            for d in self.by_unit.get(uid, []):
                if d not in out:
                    out.append(d)
        return sorted(out)

    def cross_provision_relations(self, duty_id):
        """Relations the graph attaches to this duty FROM A DIFFERENT PROVISION.

        The 86% of attachments (223 of 258) that the text store's sibling expansion
        cannot reach from the duty. Same-provision relations are excluded: reaching
        those needs no representation.
        """
        d = self.duties.get(duty_id)
        if not d:
            return []
        own = set(d["grounded_in"])
        return [r for r in d["relations"] if r["grounded_in"] and not (set(r["grounded_in"]) & own)]


# ------------------------------------------------------------------------- stores

def _prov(units_text=(), relations=(), duties=(), citations=()):
    return {"units_text": sorted(set(units_text)), "relations": sorted(set(relations)),
            "duties": sorted(set(duties)), "citations": sorted(set(citations))}


class _Store(object):
    """Shared retrieval and shared get_provision. The arms differ below this."""

    arm = None

    def __init__(self, corpus, graph, article):
        self.c, self.g, self.article = corpus, graph, article

    def _retrieve(self, topic):
        return self.c.index[self.article].top(str(topic or ""), K)

    def get_provision(self, citation):
        uid = self.c.resolve(citation)
        if not uid:
            known = [self.c.units[u]["label"] for u in self.c.by_article[self.article][:8]]
            return {"error": "no such provision", "known_citations": known}, _prov()
        u = self.c.units[uid]
        return {"citation": u["label"], "text": u["text"]}, _prov(units_text=[uid])

    def call(self, name, args):
        if not isinstance(args, dict):
            args = {}
        if name == "find_duties":
            return self.find_duties(args.get("topic", ""))
        if name == "get_conditions":
            return self.get_conditions(args.get("duty_id", ""))
        if name == "get_provision":
            return self.get_provision(args.get("citation", ""))
        return {"error": "no such tool: %s" % name}, _prov()


class TextStore(_Store):
    arm = "text"

    def find_duties(self, topic):
        hits = self._retrieve(topic)
        out = [{"duty_id": self.c.units[u]["label"], "text": self.c.units[u]["text"]}
               for u, _ in hits]
        return out, _prov(units_text=[u for u, _ in hits],
                          citations=[self.c.units[u]["label"] for u, _ in hits])

    def get_conditions(self, duty_id):
        """The duty's chapeau and its paragraph siblings, as TEXT. Never edges."""
        uid = self.c.resolve(duty_id)
        if not uid:
            return {"error": "unknown duty_id", "known_ids": [
                self.c.units[u]["label"] for u in self.c.by_article[self.article][:8]]}, _prov()
        p = parent_of(uid)
        sibs = self.c.children(uid)
        chapeau = p + "-sub1" if (p + "-sub1") in self.c.units else p
        body = [s for s in sibs if s != uid and s != chapeau]
        body.sort(key=lambda s: self.c.units[s]["char_start"])
        returned = [chapeau] + body
        return ({"chapeau": {"citation": self.c.units[chapeau]["label"],
                             "text": self.c.units[chapeau]["text"]},
                 "siblings": [{"citation": self.c.units[s]["label"],
                               "text": self.c.units[s]["text"]} for s in body]},
                _prov(units_text=returned,
                      citations=[self.c.units[s]["label"] for s in returned]))


class GraphStore(_Store):
    arm = "graph"

    def find_duties(self, topic):
        """The duty nodes grounded in the matched provisions, with their ids.

        A matched provision carrying no duties is still returned, with an empty list.
        Retrieval is identical across arms by construction; only coverage differs, and
        hiding the empty matches would make the two arms see different k.
        """
        hits = self._retrieve(topic)
        out, duties = [], []
        for u, _ in hits:
            ds = self.g.by_unit.get(u, [])
            duties += ds
            out.append({"citation": self.c.units[u]["label"],
                        "duties": [{"duty_id": d, "statement": self.g.duties[d]["statement"],
                                    "type": self.g.duties[d]["type"]} for d in ds]})
        return out, _prov(duties=duties,
                          citations=[self.c.units[u]["label"] for u, _ in hits])

    def get_conditions(self, duty_id):
        """The relation nodes attached to that duty, with the provision each cites.

        Statements and citations, not source text: text is the text store's currency
        and the model calls get_provision if it wants the words.
        """
        d = self.g.duties.get(str(duty_id).strip())
        if not d:
            known = sorted(set(sum((self.g.by_unit.get(u, [])
                                    for u in self.c.by_article[self.article]), [])))[:8]
            return {"error": "unknown duty_id", "known_ids": known}, _prov()
        rels = []
        for r in d["relations"]:
            rels.append({"kind": r["kind"], "statement": r["statement"],
                         "cites": [self.c.units[u]["label"] if u in self.c.units else u
                                   for u in r["grounded_in"]]})
        return ({"duty_id": d["duty_id"], "statement": d["statement"], "conditions": rels},
                _prov(relations=[r["relation_id"] for r in d["relations"]],
                      duties=[d["duty_id"]],
                      citations=[c for r in rels for c in r["cites"]]))


STORES = {"text": TextStore, "graph": GraphStore}

# The tool schemas the model sees. IDENTICAL in both arms, by construction: one
# definition, no arm branch. Wording stays neutral about how an answer is delivered.
TOOLS = [
    {"type": "function", "function": {
        "name": "find_duties",
        "description": "Search this GDPR article for the provisions that bear on a topic. "
                       "Returns up to 5 results, each with an identifier you can pass to "
                       "get_conditions.",
        "parameters": {"type": "object", "required": ["topic"], "properties": {
            "topic": {"type": "string",
                      "description": "a few words describing the subject matter"}}}}},
    {"type": "function", "function": {
        "name": "get_conditions",
        "description": "Given an identifier returned by find_duties, return the material "
                       "of this article that bears on when it applies: the qualifying "
                       "conditions and the exceptions.",
        "parameters": {"type": "object", "required": ["duty_id"], "properties": {
            "duty_id": {"type": "string",
                        "description": "an identifier exactly as returned by find_duties"}}}}},
    {"type": "function", "function": {
        "name": "get_provision",
        "description": "Return the official text of a GDPR provision, for example "
                       "'Article 14(5)(a)'.",
        "parameters": {"type": "object", "required": ["citation"], "properties": {
            "citation": {"type": "string", "description": "a GDPR provision reference"}}}}},
]


def load(articles=ARTICLES):
    c = Corpus(articles)
    return c, Graph(c, articles)


# --------------------------------------------------------------------- self-check

def _selfcheck():
    c, g = load()
    assert len(c.units) == 87, len(c.units)
    assert len(g.duties) == 74, len(g.duties)
    n_rel = sum(len(d["relations"]) for d in g.duties.values())
    n_x = sum(len(g.cross_provision_relations(d)) for d in g.duties)
    assert (n_rel, n_x) == (258, 223), (n_rel, n_x)          # E3's inventory
    assert len(g.by_unit) == 47, len(g.by_unit)              # E1a: 47 provisions carry duties
    assert max(len(v) for v in g.by_unit.values()) == 6      # E1a: up to 6 duties on one

    # BM25 must not hand a long chapeau the win over the short point that matches.
    hits = [u for u, _ in c.index[14].top("the data subject already has the information", K)]
    assert hits[0] == "art14-p5-a", hits
    assert len(hits) <= K

    # Retrieval is the SAME in both arms: same units, same order.
    t, gr = TextStore(c, g, 14), GraphStore(c, g, 14)
    assert [u for u, _ in t._retrieve("categories of personal data")] == \
           [u for u, _ in gr._retrieve("categories of personal data")]

    # Text get_conditions returns sibling TEXT, and no relation ever.
    pay, prov = t.get_conditions("Article 14(1)(c)")
    assert pay["chapeau"]["citation"] == "Article 14(1), subparagraph 1"
    assert {s["citation"] for s in pay["siblings"]} == {
        "Article 14(1)(%s)" % x for x in "abdef"}
    assert prov["relations"] == [] and "art14-p1-c" not in prov["units_text"]

    # Graph get_conditions returns the edges, and no source text.
    duty = g.by_unit["art14-p1-c"][0]
    pay, prov = gr.get_conditions(duty)
    assert prov["relations"] and prov["units_text"] == []
    # the worked case: 14(5)'s exceptions hang off a 14(1) duty, one hop
    assert any(r["grounded_in"][0] == "art14-p5-a"
               for r in g.duties[duty]["relations"]), g.duties[duty]["relations"]

    # get_provision is identical on both sides.
    a, pa = t.get_provision("Art. 14(5)(a)")
    b, pb = gr.get_provision("14(5)(a)")
    assert a == b and pa == pb == _prov(units_text=["art14-p5-a"])
    assert "already has the information" in a["text"]

    # unknown handles fail the same way in both arms, never with a traceback
    assert "error" in t.get_conditions("Article 99(1)")[0]
    assert "error" in gr.get_conditions("obl-nope")[0]

    # chapeau closure: relying on Article 14(1) relies on the duties in its points
    assert g.duties_for_units(c.closure("art14-p1")) != []
    assert c.closure("art14-p1-c") == ["art14-p1-c"]

    # Article 46 is the pre-registered null: no cross-provision attachments at all
    a46 = [d for d in g.duties if any(u.startswith("art46-") for u in g.duties[d]["grounded_in"])]
    assert a46 and all(not g.cross_provision_relations(d) for d in a46)

    print("stores.py self-check OK: %d units, %d duties, %d relations (%d cross-provision)"
          % (len(c.units), len(g.duties), n_rel, n_x))


if __name__ == "__main__":
    _selfcheck()
