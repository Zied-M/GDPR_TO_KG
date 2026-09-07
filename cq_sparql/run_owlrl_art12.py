#!/usr/bin/env python3
# =====================================================================
#  run_owlrl_art12.py — AUTHORITATIVE OWL 2 RL CQ run for Article 12
#  (the Art-12 modalities pass, over the COMBINED 4-file union).
#
#  This is the authoritative OWL 2 RL CQ run for the Art-12
#  certification gate (check 3), mirroring run_owlrl_art6.py. It is the
#  real materialised regime the reports call for; it REPLACES any
#  dev-time proxy once rdflib + owlrl are available.
#
#  Needs a networked (or pre-provisioned) machine:
#      pip install rdflib owlrl
#      python run_owlrl_art12.py
#  Run from anywhere. The graph tree is resolved as:
#      --root <dir>  >  $GDPR_KG_ROOT  >  the tree this script lives in
#  (see kg_root.py). Missing inputs exit 2, not 1, so a path failure is
#  distinguishable from a CQ failure. The TBox sha256 is printed below.
#
#  What it does (cq_sparql/README.md regime):
#    1. load the COMBINED 4-file union into ONE graph:
#         ../ontology/gdpr_kg.ttl  (TBox)
#       + ../articles/art13.ttl
#       + ../articles/art6.ttl
#       + ../articles/art12.ttl
#       print the pre-closure triple count;
#    2. materialise the OWL 2 RL closure
#       (owlrl.DeductiveClosure(owlrl.OWLRL_Semantics)) so inferred
#       rdf:type / super-type triples (e.g. every ex:perm-12-* a
#       gdprkg:Permission also a PrimaryNormativeUnit / NormativeElement
#       / GroundedConcept) become explicit; print the post-closure count;
#    3. run each Art-12 CQ .rq and print rows + PASS/CHECK against the
#       expected counts in cq_sparql/expected_results.md (§Article-12);
#    4. run the additional Art-12 fixture checks directly over the
#       materialised graph; print PASS/CHECK for each;
#    5. print the final certification SUMMARY line + exit 0/1.
#
#  REGIME NOTE (why two graphs). expected_results.md §Article-12 marks
#  every CQ except CQ-C2 and CQ-C5x as *plain* regime. CQ-C4 and CQ-C5
#  project the referenced-actor / disclosed-concept rdf:type
#  (?actorType / ?conceptType) WITHOUT restricting to the leaf class, so
#  OWL 2 RL materialisation multiplies each genuine answer row by its
#  inferred super-types (owl:Thing + intermediate classes): the DISTINCT
#  (obligation, actor) / (obligation, concept) answer set is unchanged
#  (4 / 5) but the raw row count inflates (to 12 / 21). Those two frozen
#  queries are therefore evaluated on the PLAIN (pre-closure) graph, per
#  their documented regime — this is NOT a tweak of expected numbers, it
#  is honouring the fixture's own regime column. CQ-C2 and CQ-C5x need
#  the closure and are run on the materialised graph. The remaining CQs
#  (C1/C3/C6/C7) are regime-invariant here and run on the materialised
#  graph like the run_owlrl_art6.py template. Each query prints the
#  regime it used.
# =====================================================================
import os, sys
import kg_root                      # --root / GDPR_KG_ROOT + TBox sha256 (S-B)
try:
    import rdflib
    import owlrl
except ImportError:
    sys.exit("Missing deps. Run:  pip install rdflib owlrl")

ROOT = kg_root.resolve_root()
sys.argv = kg_root.strip_root_args()

TBOX  = os.path.join(ROOT, 'ontology',  'gdpr_kg.ttl')
ART13 = os.path.join(ROOT, 'articles', 'art13.ttl')
ART6  = os.path.join(ROOT, 'articles', 'art6.ttl')
ART12 = os.path.join(ROOT, 'articles', 'art12.ttl')
kg_root.require(TBOX, ART13, ART6, ART12)
kg_root.provenance(ROOT, TBOX)
QDIR = os.path.join(ROOT, 'cq_sparql')   # .rq files come from the same tree as the data

GDPRKG = "https://w3id.org/gdprkg#"
DATA   = "https://w3id.org/gdprkg/data#"      # prefix ex:
GK  = rdflib.Namespace(GDPRKG)
EX  = rdflib.Namespace(DATA)
RDF = rdflib.RDF
OWL = rdflib.OWL

# ---------------------------------------------------------------------
# 1. load the COMBINED 4-file union (pre-closure = the PLAIN graph)
# ---------------------------------------------------------------------
g_plain = rdflib.Graph()
for f in (TBOX, ART13, ART6, ART12):
    g_plain.parse(f, format='turtle')
print("[LOAD] gdpr_kg.ttl + art13.ttl + art6.ttl + art12.ttl -> %d triples (pre-closure)"
      % len(g_plain))

# ---------------------------------------------------------------------
# 2. OWL 2 RL materialisation -> the CLOSED graph
# ---------------------------------------------------------------------
g = rdflib.Graph()
for t in g_plain:
    g.add(t)
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
print("[CLOSURE] OWL 2 RL materialised -> %d triples\n" % len(g))


def short(t):
    if isinstance(t, rdflib.URIRef):
        s = str(t)
        return s.replace(DATA, "ex:").replace(GDPRKG, "gdprkg:")
    return str(t)


def ln(u):
    s = str(u)
    return s.split('#')[-1] if '#' in s else s.rsplit('/', 1)[-1]


all_ok = True


# =====================================================================
# 3. CQ row-count checks (expected COMBINED totals, expected_results.md
#    §Article-12). "regime" selects the graph per the fixture's regime
#    column (see REGIME NOTE in the header).
# =====================================================================
# (file, label, expected, regime, note)
QUERIES = [
    ("CQ-C1_article_to_norms_grounded.rq", "CQ-C1  article -> grounded norms", 61, "materialised",
     "WORK ORDER F 2026-09-06 -- ex:cond-collected-from-data-subject. NOTE ON DISCIPLINE: unlike every other expectation moved by that unit, THESE WERE SET AFTER THE RUN, NOT BEFORE IT. The unit checked only run_owlrl_art46.py for regression and missed this runner; publish-gdpr-kg/verify.py caught it. The derivation is given so the number can be checked against reasoning rather than accepted because a runner printed it. DERIVATION 60 -> 61: one new Condition, and in THIS union only its art13-p1 grounding leg exists -- the art14-p1 leg lives in art14.ttl, which this 4-file runner does not load. Exactly +1 row. || ORIGINAL NOTE FOLLOWS: "
     "6 Permissions deliberately excluded by the frozen FILTER "
     "(Obligation/Condition/Exception only) -> recorded non-coverage, NOT a defect."),
    ("CQ-C2_uniform_grounding.rq", "CQ-C2  uniform grounding (0 = pass)", 0, "materialised",
     "materialised; 0 GroundedConcept lacks groundedIn (incl. the 6 Permissions)."),
    ("CQ-C3_bearer.rq", "CQ-C3  obligation -> bearer", 34, "materialised",
     "permission bearers excluded by frozen wording -> recorded non-coverage "
     "(bearer fact still explicit via gdprkg:grantsPermissionTo)."),
    ("CQ-C4_referenced_actor.rq", "CQ-C4  obligation -> referenced actor", 4, "plain",
     "plain regime (expected_results.md): materialisation would inflate via "
     "inferred actor super-types; distinct (obligation, actor) pairs = 4."),
    ("CQ-C5_domain_concept.rq", "CQ-C5  obligation -> disclosed concept", 5, "plain",
     "plain regime; ZERO-delta: Art-12 adds 0 disclosure concepts, stays 5 "
     "(nonzero delta vs 5 would be a DEFECT)."),
    ("CQ-C5x_cross_article_basis.rq", "CQ-C5x cross-article basis (Point-join)", 2, "materialised",
     "needs materialisation; ZERO-delta: stays 2 "
     "(nonzero delta vs 2 would be a DEFECT)."),
    ("CQ-C7_temporal.rq", "CQ-C7  temporal triggers", 21, "materialised",
     "frozen query; Art-12 contributes 0 (fixed-deadline timing, see CQ-C6/hasTimeLimit) "
     "-> all 21 are art13."),
]

for fname, label, expected, regime, note in QUERIES:
    q = open(os.path.join(QDIR, fname), encoding='utf-8').read()
    src = g if regime == "materialised" else g_plain
    rows = list(src.query(q))
    ok = (len(rows) == expected)
    all_ok = all_ok and ok
    print("=== %s ===" % label)
    print("    file=%s  regime=%s  rows=%d  expected=%d  -> %s"
          % (fname, regime, len(rows), expected, "PASS" if ok else "CHECK"))
    print("    NOTE: %s" % note)
    for r in rows:
        print("      " + "  ".join(short(x) for x in r))
    print()

# ---------------------------------------------------------------------
# CQ-C6 — provenance/review: 114 rows = 46 "direct" + 68 "inherited"
#   (the query returns a ?mode column; split on it and assert all three)
# ---------------------------------------------------------------------
print("=== CQ-C6  provenance / review (mode split) ===")
c6 = list(g.query(open(os.path.join(QDIR, "CQ-C6_provenance_review.rq"), encoding='utf-8').read()))
n_direct    = sum(1 for r in c6 if str(r["mode"]) == "direct")
n_inherited = sum(1 for r in c6 if str(r["mode"]) == "inherited")
n_total     = len(c6)
# WORK ORDER F 2026-09-06: inherited 68 -> 89 (+21, the 21 art13 appliesIf parents of the new
# shared Condition). direct unchanged at 46 -- Conditions carry no provenance of their own.
# No art14 edges in this union. SET AFTER THE RUN, not before -- see the CQ-C1 note above.
c6_ok = (n_direct == 46 and n_inherited == 89 and n_total == 135)
all_ok = all_ok and c6_ok
print("    file=CQ-C6_provenance_review.rq  regime=materialised")
print("    direct=%d (expected 46)  inherited=%d (expected 89)  total=%d (expected 135)  -> %s"
      % (n_direct, n_inherited, n_total, "PASS" if c6_ok else "CHECK"))
print("    NOTE: combined direct 46 = 21 art13 + 6 art6 + 19 art12 (13 Obl + 6 Perm); "
      "combined inherited 68 = 50 art13 + 4 art6 + 14 art12.")
print()


# =====================================================================
# 4. Additional Art-12 fixture checks (direct over the materialised graph)
#    "Art-12 node" test used: a data-namespace (ex:) subject whose IRI
#    localname startswith "art12" OR contains "12-" (covers art12- /
#    obl-12- / perm-12- / cond-12- / exc-12- and shared obl-12-*).
# =====================================================================
def is_art12(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art12") or "12-" in l


def check(name, actual, expected):
    global all_ok
    ok = (actual == expected)
    all_ok = all_ok and ok
    print("    [FIXTURE] %-58s actual=%s  expected=%s  -> %s"
          % (name, actual, expected, "PASS" if ok else "CHECK"))
    return ok


print("=== Art-12 fixture checks (materialised graph) ===")
print("    (Art-12 node = ex: subject whose localname startswith 'art12' or contains '12-')")

# gdprkg:hasTimeLimit edges = 5
htl = list(g.triples((None, GK.hasTimeLimit, None)))
check("gdprkg:hasTimeLimit edges", len(htl), 5)

# gdprkg:grantsPermissionTo edges = 6, every object = ex:actor-controller
gpt = list(g.triples((None, GK.grantsPermissionTo, None)))
check("gdprkg:grantsPermissionTo edges", len(gpt), 6)
gpt_objs = set(o for _, _, o in gpt)
check("gdprkg:grantsPermissionTo objects all = ex:actor-controller",
      (len(gpt_objs) == 1 and EX["actor-controller"] in gpt_objs), True)

# gdprkg:referencesProvision edges whose subject is an Art-12 node = 49
rp12 = [(s, o) for s, p, o in g.triples((None, GK.referencesProvision, None)) if is_art12(s)]
check("gdprkg:referencesProvision edges on Art-12 subjects", len(rp12), 49)

# forbidden edges on Art-12 nodes: each = 0
for pr in ("disclosedToDataSubject", "disclosesConcept", "notApplicableIf", "hasLegalEffect"):
    n = [(s, o) for s, p, o in g.triples((None, GK[pr], None)) if is_art12(s)]
    check("forbidden gdprkg:%s on Art-12 nodes" % pr, len(n), 0)

# every gdprkg:Permission instance (ex: data ns) infers all of
# {Permission, PrimaryNormativeUnit, NormativeElement, GroundedConcept} = 6/6
perms = sorted(set(s for s in g.subjects(RDF.type, GK.Permission) if str(s).startswith(DATA)))
need = [GK.Permission, GK.PrimaryNormativeUnit, GK.NormativeElement, GK.GroundedConcept]
perm_all4 = sum(1 for p in perms if all((p, RDF.type, t) in g for t in need))
check("ex: Permission instances", len(perms), 6)
check("ex: Permission instances inferring all 4 types "
      "{Permission,PrimaryNormativeUnit,NormativeElement,GroundedConcept}", perm_all4, 6)

# 0 owl:Nothing members
nothing = list(g.subjects(RDF.type, OWL.Nothing))
check("owl:Nothing members", len(nothing), 0)

# 0 dangling ex: object IRIs (ex: IRIs used as an object that never appear as a subject)
subjects = set(g.subjects())
dangling = set(o for _, _, o in g
               if isinstance(o, rdflib.URIRef) and str(o).startswith(DATA) and o not in subjects)
check("dangling ex: object IRIs (never a subject across the closed graph)", len(dangling), 0)
print()


# =====================================================================
# 5. Certification SUMMARY
# =====================================================================
print("=" * 68)
if all_ok:
    print("ALL ART-12 CERTIFICATION CHECKS MATCH expected_results.md §Article-12")
    sys.exit(0)
else:
    print("MISMATCH — see rows above")
    sys.exit(1)
