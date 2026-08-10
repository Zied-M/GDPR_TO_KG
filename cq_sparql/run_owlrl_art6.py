#!/usr/bin/env python3
# =====================================================================
#  run_owlrl_art6.py — AUTHORITATIVE OWL 2 RL CQ run for Article 6
#  (+ the Art-6/13 cross-article facet). This is the real materialised
#  regime the reports call for; it REPLACES the dev-time proxy
#  cq_eval_art6.py once rdflib + owlrl are available.
#
#  Needs a networked (or pre-provisioned) machine:
#      pip install rdflib owlrl
#      python run_owlrl_art6.py
#  Run from the cq_sparql/ directory.
#
#  What it does (cq_sparql/README.md regime):
#    1. load ../ontology/gdpr_kg.ttl (TBox) + ../articles/art6.ttl
#       + ../articles/art13.ttl (needed only for the cross-article CQ-C5x)
#       into ONE graph;
#    2. materialise the OWL 2 RL closure so inferred rdf:type triples
#       (e.g. ex:basis-consent a gdprkg:LegalBasis, via LegalBasisConsent)
#       become explicit;
#    3. run each Art-6 .rq over the materialised graph and print rows;
#    4. print PASS/CHECK against the expected counts in
#       cq_sparql/expected_results.md (Article-6 section).
# =====================================================================
import os, sys
try:
    import rdflib
    import owlrl
except ImportError:
    sys.exit("Missing deps. Run:  pip install rdflib owlrl")

TBOX = os.path.join('..', 'ontology', 'gdpr_kg.ttl')
ART6 = os.path.join('..', 'articles', 'art6.ttl')
ART13 = os.path.join('..', 'articles', 'art13.ttl')

g = rdflib.Graph()
for f in (TBOX, ART6, ART13):
    g.parse(f, format='turtle')
print("[LOAD] gdpr_kg.ttl + art6.ttl + art13.ttl -> %d triples (pre-closure)" % len(g))

# OWL 2 RL materialisation (makes inferred rdf:type / inverse triples explicit)
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
print("[CLOSURE] OWL 2 RL materialised -> %d triples\n" % len(g))

# (query file, human label, expected row count)
QUERIES = [
    ("CQ-B1_lawful_bases.rq",              "CQ-B1  lawful bases",                 6),
    ("CQ-B2_basis_conditions.rq",          "CQ-B2  per-basis conditions",         3),
    ("CQ-B3_basis_in_union_or_ms_law.rq",  "CQ-B3  bases requiring Union/MS law",  2),
    ("CQ-B4_li_public_authority_exclusion.rq", "CQ-B4  LI public-authority exclusion", 1),
    ("CQ-C5x_cross_article_basis.rq",      "CQ-C5x cross-article (basis touched across articles)", 2),
]

def short(t):
    if isinstance(t, rdflib.URIRef):
        s = str(t)
        return s.replace("https://w3id.org/gdprkg/data#", "ex:").replace("https://w3id.org/gdprkg#", "gdprkg:")
    return str(t)

all_ok = True
for fname, label, expected in QUERIES:
    q = open(fname, encoding='utf-8').read()
    rows = list(g.query(q))
    ok = (len(rows) == expected)
    all_ok = all_ok and ok
    print("=== %s ===" % label)
    print("    file=%s  rows=%d  expected=%d  -> %s" % (fname, len(rows), expected, "PASS" if ok else "CHECK"))
    for r in rows:
        print("      " + "  ".join(short(x) for x in r))
    print()

print("=" * 60)
print("SUMMARY: %s" % ("ALL CQ ROW-COUNTS MATCH expected_results.md" if all_ok
                        else "MISMATCH — compare against cq_sparql/expected_results.md (Article-6 section)"))
print("Also confirm CQ-C1 (Art-6 = 9 grounded norms) and CQ-C2 (0 GroundedConcept lacking groundedIn)")
print("with the existing CQ-C1/CQ-C2 .rq over the same materialised graph.")
