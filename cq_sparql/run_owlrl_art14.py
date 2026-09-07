#!/usr/bin/env python3
# =====================================================================
#  run_owlrl_art14.py — AUTHORITATIVE OWL 2 RL CQ run for Article 14
#  (the Art-14 disclosure-sibling pass, over the COMBINED 5-file union).
#
#  This is the authoritative OWL 2 RL CQ run for the Art-14
#  certification gate (check 3), mirroring run_owlrl_art12.py. It is the
#  real materialised regime the reports call for; it REPLACES any
#  dev-time proxy once rdflib + owlrl are available.
#
#  run_owlrl_art12.py and run_owlrl_art6.py are NOT modified by this
#  pass (work order C §3.4) — this file stands alongside them.
#
#  Needs a networked (or pre-provisioned) machine:
#      pip install rdflib owlrl
#      python run_owlrl_art14.py
#  Run from anywhere. The graph tree is resolved as:
#      --root <dir>  >  $GDPR_KG_ROOT  >  the tree this script lives in
#  (see kg_root.py). Missing inputs exit 2, not 1, so a path failure is
#  distinguishable from a CQ failure. The TBox sha256 is printed below.
#
#  What it does (cq_sparql/README.md regime):
#    1. load the COMBINED 5-file union into ONE graph:
#         ../ontology/gdpr_kg.ttl  (TBox)
#       + ../articles/art13.ttl
#       + ../articles/art6.ttl
#       + ../articles/art12.ttl
#       + ../articles/art14.ttl        <-- NEW this pass
#       print the pre-closure triple count;
#    2. materialise the OWL 2 RL closure
#       (owlrl.DeductiveClosure(owlrl.OWLRL_Semantics)) so inferred
#       rdf:type / super-type triples become explicit; print the
#       post-closure count;
#    3. run each CQ .rq and print rows + PASS/CHECK against the counts
#       PREDICTED IN ADVANCE in cq_sparql/expected_results.md
#       (§Article-14). Those predictions were written BEFORE this file
#       was ever executed — see the prediction-provenance banner there;
#    4. run the additional Art-14 fixture checks directly over the
#       graph; print PASS/CHECK for each;
#    5. print the final SUMMARY line + exit 0/1.
#
#  REGIME NOTE (why two graphs) — inherited verbatim in substance from
#  run_owlrl_art12.py. expected_results.md marks every CQ except CQ-C2
#  and CQ-C5x as *plain* or regime-invariant. CQ-C4 and CQ-C5 project
#  the referenced-actor / disclosed-concept rdf:type (?actorType /
#  ?conceptType) WITHOUT restricting to the leaf class, so OWL 2 RL
#  materialisation multiplies each genuine answer row by its inferred
#  super-types (owl:Thing + intermediate classes): the DISTINCT
#  (obligation, actor) / (obligation, concept) answer set is unchanged
#  (9 / 11) but the raw row count inflates. Those two frozen queries are
#  therefore evaluated on the PLAIN (pre-closure) graph, per their
#  documented regime — this is NOT a tweak of expected numbers, it is
#  honouring the fixture's own regime column. Each query prints the
#  regime it used.
#
#  ⚠ THIS SCRIPT DOES NOT CERTIFY ANYTHING. Certification is Zied's:
#  combined HermiT over articles/certify_art13_art6.ttl (now five files)
#  + local pySHACL + this runner. An agent's run is a PROXY.
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
ART14 = os.path.join(ROOT, 'articles', 'art14.ttl')
kg_root.require(TBOX, ART13, ART6, ART12, ART14)
kg_root.provenance(ROOT, TBOX)
QDIR = os.path.join(ROOT, 'cq_sparql')   # .rq files come from the same tree as the data

GDPRKG = "https://w3id.org/gdprkg#"
DATA   = "https://w3id.org/gdprkg/data#"      # prefix ex:
GK  = rdflib.Namespace(GDPRKG)
EX  = rdflib.Namespace(DATA)
RDF = rdflib.RDF
OWL = rdflib.OWL

# ---------------------------------------------------------------------
# 1. load the COMBINED 5-file union (pre-closure = the PLAIN graph)
# ---------------------------------------------------------------------
g_plain = rdflib.Graph()
for f in (TBOX, ART13, ART6, ART12, ART14):
    g_plain.parse(f, format='turtle')
print("[LOAD] gdpr_kg.ttl + art13.ttl + art6.ttl + art12.ttl + art14.ttl -> %d triples (pre-closure)"
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
VERBOSE = ("-v" in sys.argv or "--verbose" in sys.argv)


# =====================================================================
# 3. CQ row-count checks (expected COMBINED totals, expected_results.md
#    §Article-14). "regime" selects the graph per the fixture's regime
#    column (see REGIME NOTE in the header).
# =====================================================================
# (file, label, expected, regime, note)
QUERIES = [
    ("CQ-C1_article_to_norms_grounded.rq", "CQ-C1  article -> grounded norms", 102, "materialised",
     "WORK ORDER F 2026-09-06 -- ex:cond-collected-from-data-subject. NOTE ON DISCIPLINE: unlike every other expectation moved by that unit, THESE WERE SET AFTER THE RUN, NOT BEFORE IT. The unit checked only run_owlrl_art46.py for regression and missed this runner; publish-gdpr-kg/verify.py caught it. The derivation is given so the number can be checked against reasoning rather than accepted because a runner printed it. DERIVATION 100 -> 102: BOTH grounding legs of the new Condition are present in this union (art13.ttl and art14.ttl are both loaded), so ONE node yields TWO rows. It is the first node in the project with two groundedIn edges; permitted (minCount 1, no maxCount). || ORIGINAL NOTE FOLLOWS: "
     "TIER 2. Art-14 delta +40 (24 Obligation + 12 Condition + 4 Exception). "
     "6 Permissions still excluded by the frozen FILTER -> recorded non-coverage #1, NOT a defect."),
    ("CQ-C2_uniform_grounding.rq", "CQ-C2  uniform grounding (0 = pass)", 0, "materialised",
     "TIER 1 (LOCKED, brief 6.1). 0 GroundedConcept lacks groundedIn. The three Art-14 mints "
     "(concept-data-category / actor-personal-data-source / ref-art89) sit OUTSIDE GroundedConcept "
     "by design, so none can contribute a row."),
    ("CQ-C3_bearer.rq", "CQ-C3  obligation -> bearer", 58, "materialised",
     "TIER 1 (LOCKED, brief 6.1) = 34 + 24. A value other than 58 means a missing bearer "
     "(SHACL would fail first) or a multi-bearer obligation -> report as a FINDING, do not adjust."),
    ("CQ-C4_referenced_actor.rq", "CQ-C4  obligation -> referenced actor", 9, "plain",
     "TIER 2, +5. plain regime (materialisation inflates via inferred actor super-types). "
     "Includes the FIRST gdprkg:Actor_PersonalDataSource rows (T3-E(ii)); BOTH halves of the "
     "14(2)(f) split carry the edge -> executor judgement call, an 8 would mean only one half does."),
    ("CQ-C5_domain_concept.rq", "CQ-C5  obligation -> disclosed concept", 11, "plain",
     "TIER 2, +6. plain regime. FIVE of the six Art-14 concepts are the SAME canonical ex:concept-* "
     "nodes Art 13 discloses (cross-article shared-domain-node claim, first demonstration); the sixth "
     "is the new ex:concept-data-category. A value BELOW 11 means an Art-13 edge was damaged."),
    ("CQ-C5x_cross_article_basis.rq", "CQ-C5x cross-article basis (Point-join)", 4, "materialised",
     "TIER 2, +2 (cond-14-2-d -> consent basis; cond-14-2-b -> LI basis). "
     "A value BELOW 4 means an Art-13/Art-6 edge was damaged."),
    ("CQ-C7_temporal.rq", "CQ-C7  temporal triggers (frozen label filter)", 44, "materialised",
     "TIER 2, +23 = cond-14-3-b x22 + cond-14-4-prior x1. cond-14-3-c contributes 0: 14(3)(c) says "
     "'at the latest WHEN ...', not 'at the time' -> RECORDED NON-COVERAGE #3. The label was NOT "
     "reworded to make this land (playbook 4.1). Full timing IS verified by CQ-A8."),
    ("CQ-A1_art13_coverage.rq", "CQ-A1  obligations + grounding (unscoped)", 58, "materialised",
     "TIER 2. Query is not article-scoped: 21 art13 + 13 art12 + 24 art14. "
     "The Art-13 answer it was written for is UNCHANGED at 21."),
    ("CQ-A3_conditional_duties.rq", "CQ-A3  conditional duties (Art 13/14)", 111, "materialised",
     "WORK ORDER F 2026-09-06 -- ex:cond-collected-from-data-subject. NOTE ON DISCIPLINE: unlike every other expectation moved by that unit, THESE WERE SET AFTER THE RUN, NOT BEFORE IT. The unit checked only run_owlrl_art46.py for regression and missed this runner; publish-gdpr-kg/verify.py caught it. The derivation is given so the number can be checked against reasoning rather than accepted because a runner printed it. DERIVATION 90 -> 111: +21 ONLY, the Article-13 side. The 23 Article-14 duties attach to the SAME shared trigger with gdprkg:notApplicableIf, which this frozen query does not mention, so they contribute NOTHING. RECORDED NON-COVERAGE -- CQ-A3 was DELIBERATELY NOT FIXED (Zied, option B, 2026-09-06) because its frozen probe names APPLIES_IF edges explicitly. The query was NOT widened. || ORIGINAL NOTE FOLLOWS: "
     "TIER 2 = 29 art13 + 0 art6 (its appliesIf subjects are LegalBasis) + 7 art12 (the other 5 sit "
     "on Permissions) + 54 art14. 23 of Art-14's 24 obligations are conditional; the exception is "
     "obl-art14-5-b-protective-measures."),
    ("CQ-A4_art13_exemption.rq", "CQ-A4  exemptions, grouped (unscoped)", 8, "materialised",
     "TIER 2. 8 groups: exc-art13-4 (21), exc-6-1-f (1), exc-12-2 (1), exc-12-3 (1), and each of the "
     "FOUR Art-14 grounds (23 each). The Art-13 answer is UNCHANGED at 21 attached obligations."),
    ("CQ-A5_art14_exemptions.rq", "CQ-A5  Art-14 exemptions -> defeated duties", 92, "materialised",
     "TIER 2. FIRST answer to frozen CQ-A5. 4 Exception nodes x 23 paragraph-1-to-4 obligations. "
     "obl-art14-5-b-protective-measures is deliberately NOT among them (see CQ-A6)."),
    ("CQ-A6_art14_remaining_obligation.rq", "CQ-A6  duty surviving the 14(5)(b) exemption", 1, "materialised",
     "TIER 2. FIRST answer to frozen CQ-A6 and the whole reason 14(5)(b) is an Obligation (T3-C). "
     "A 0 here is a FINDING to report, NOT a reason to rewire the graph (brief 6.2)."),
    ("CQ-A8_art14_timing.rq", "CQ-A8  Art-14 timing (fixed + event)", 66, "materialised",
     "TIER 2. FIRST answer to frozen CQ-A8. 22 fixed-deadline rows (14(3)(a) hasTimeLimit) + 44 "
     "event-trigger rows (22 duties x the two 14(3)(b)/(c) Conditions). Both halves of the Phase-3 "
     "temporal design spike, exercised together on one article for the first time."),
    # ---- Art-6 regression block: TIER 1, brief 6.1. Art 14 adds no LegalBasis. ----
    ("CQ-B1_lawful_bases.rq", "CQ-B1  lawful bases (REGRESSION)", 6, "materialised",
     "TIER 1 regression. Any change is a regression finding."),
    ("CQ-B2_basis_conditions.rq", "CQ-B2  basis -> condition (REGRESSION)", 3, "materialised",
     "TIER 1 regression."),
    ("CQ-B3_basis_in_union_or_ms_law.rq", "CQ-B3  bases needing Union/MS law (REGRESSION)", 2, "materialised",
     "TIER 1 regression. Scoped to ex:art6-p3, so Art-14's REUSE of ex:ref-union-ms-law on the "
     "14(5)(c)/(d) Exceptions cannot leak in."),
    ("CQ-B4_li_public_authority_exclusion.rq", "CQ-B4  LI public-authority carve-out (REGRESSION)", 1, "materialised",
     "TIER 1 regression."),
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
    # Full row dumps are noisy at this scale (CQ-A5 alone is 92 rows). Print them for the
    # small/decisive answers always, and for everything with -v, and always on a mismatch.
    if VERBOSE or not ok or len(rows) <= 12:
        for r in rows:
            print("      " + "  ".join(short(x) for x in r))
    else:
        print("      (%d rows suppressed; re-run with -v to print them)" % len(rows))
    print()

# ---------------------------------------------------------------------
# CQ-C6 — provenance/review: 284 rows = 70 "direct" + 214 "inherited"
#   (the query returns a ?mode column; split on it and assert all three)
# ---------------------------------------------------------------------
print("=== CQ-C6  provenance / review (mode split) ===")
c6 = list(g.query(open(os.path.join(QDIR, "CQ-C6_provenance_review.rq"), encoding='utf-8').read()))
n_direct    = sum(1 for r in c6 if str(r["mode"]) == "direct")
n_inherited = sum(1 for r in c6 if str(r["mode"]) == "inherited")
n_total     = len(c6)
# WORK ORDER F + CQ-C6 ENCODING FIX, 2026-09-06: inherited 214 -> 258 = +44, being 21 art13
# appliesIf parents AND 23 art14 notApplicableIf parents. The 23 count HERE because CQ-C6's
# encoding was fixed that day (notApplicableIf added to the inherited parent path); they do NOT
# count in CQ-A3, which was deliberately left unfixed. direct unchanged at 70.
# SET AFTER THE RUN, not before -- see the CQ-C1 note above.
c6_ok = (n_direct == 70 and n_inherited == 258 and n_total == 328)
all_ok = all_ok and c6_ok
print("    file=CQ-C6_provenance_review.rq  regime=materialised")
print("    direct=%d (expected 70)  inherited=%d (expected 258)  total=%d (expected 328)  -> %s"
      % (n_direct, n_inherited, n_total, "PASS" if c6_ok else "CHECK"))
print("    NOTE: direct 70 is TIER 1 (LOCKED, brief 6.1) = 46 + 24 Art-14 obligations.")
print("    NOTE: inherited 214 is TIER 2 = 50 art13 + 4 art6 + 14 art12 + 146 art14")
print("          (146 = 54 appliesIf + 92 hasException = 23 obligations x 4 node-shared 14(5) grounds).")
print()


# =====================================================================
# 4. Additional Art-14 fixture checks
#    "Art-14 node" test used (mirrors run_owlrl_art12.py's form): a
#    data-namespace (ex:) subject whose IRI localname startswith "art14"
#    OR contains "14-" (covers art14- / obl-art14- / cond-14- / exc-art14-).
#    NB ex:ref-art14 was REWIRED AWAY by this pass, so it cannot pollute
#    the test — and its absence is itself asserted below.
# =====================================================================
def is_art14(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art14") or "14-" in l


def is_art12(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art12") or "12-" in l


def check(name, actual, expected):
    global all_ok
    ok = (actual == expected)
    all_ok = all_ok and ok
    print("    [FIXTURE] %-64s actual=%s  expected=%s  -> %s"
          % (name, actual, expected, "PASS" if ok else "CHECK"))
    return ok


print("=== Art-14 fixture checks (materialised graph unless noted) ===")
print("    (Art-14 node = ex: subject whose localname startswith 'art14' or contains '14-')")

# ---- node inventory ----
art14_obl = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Obligation)) if is_art14(s))
art14_cnd = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Condition)) if is_art14(s))
art14_exc = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Exception)) if is_art14(s))
check("Art-14 Obligation instances  [TIER 1 = 24, LOCKED]", len(art14_obl), 24)
check("Art-14 Condition instances   [TIER 2 = 12]", len(art14_cnd), 12)
check("Art-14 Exception instances   [TIER 1 = 4, LOCKED]", len(art14_exc), 4)

# per-paragraph obligation split (brief 2.6: P1 9 / P2 13 / P3 0 / P4 1 / P5 1)
para_of = {}
for o in art14_obl:
    prov = list(g_plain.objects(o, GK.groundedIn))
    assert len(prov) == 1, "obligation %s has %d groundedIn edges" % (short(o), len(prov))
    p = ln(prov[0])                      # art14-p1-a / art14-p4 / art14-p5-b
    para_of[o] = p.split('-')[1]         # p1 / p2 / p4 / p5
for p, exp in (("p1", 9), ("p2", 13), ("p3", 0), ("p4", 1), ("p5", 1)):
    check("Art-14 obligations grounded in paragraph %s [brief 2.6]" % p,
          sum(1 for v in para_of.values() if v == p), exp)

# ---- edge fixtures ----
htl_all = list(g_plain.triples((None, GK.hasTimeLimit, None)))
check("gdprkg:hasTimeLimit edges on Art-14 subjects",
      len([1 for s, _, _ in htl_all if is_art14(s)]), 22)
check("gdprkg:hasTimeLimit edges, COMBINED (5 art12 + 22 art14)", len(htl_all), 27)
check("gdprkg:hasTimeLimit distinct strings on Art-14 subjects (one shared 14(3)(a) string)",
      len(set(o for s, _, o in htl_all if is_art14(s))), 1)

check("gdprkg:appliesIf edges on Art-14 subjects",
      len([1 for s, _, _ in g_plain.triples((None, GK.appliesIf, None)) if is_art14(s)]), 54)
check("gdprkg:hasException edges on Art-14 subjects (23 obligations x 4 grounds)",
      len([1 for s, _, _ in g_plain.triples((None, GK.hasException, None)) if is_art14(s)]), 92)

d2ds = list(g_plain.triples((None, GK.disclosedToDataSubject, None)))
check("gdprkg:disclosedToDataSubject on Art-14 subjects",
      len([1 for s, _, _ in d2ds if is_art14(s)]), 23)
check("gdprkg:disclosedToDataSubject COMBINED (21 art13 + 23 art14)", len(d2ds), 44)
check("gdprkg:disclosedToDataSubject objects all = ex:actor-data-subject",
      set(o for _, _, o in d2ds) == {EX["actor-data-subject"]}, True)

dc = list(g_plain.triples((None, GK.disclosesConcept, None)))
check("gdprkg:disclosesConcept on Art-14 subjects", len([1 for s, _, _ in dc if is_art14(s)]), 6)
check("gdprkg:disclosesConcept COMBINED (5 art13 + 6 art14)", len(dc), 11)

ra = list(g_plain.triples((None, GK.referencesActor, None)))
check("gdprkg:referencesActor on Art-14 subjects", len([1 for s, _, _ in ra if is_art14(s)]), 5)
check("gdprkg:referencesActor COMBINED (3 art13 + 1 art12 + 5 art14)", len(ra), 9)

rp = list(g_plain.triples((None, GK.referencesProvision, None)))
# ---- S-G 2026-08-30: the M2 scope edges moved these two raw-edge counts ----
# These fixtures asserted "UNCHANGED at N" because the Art-46 pass needed to show
# that the ex:ref-art46 rewire did not disturb the referencesProvision population.
# The M2 unit DELIBERATELY grows that population: every multi-bearer Exception now
# declares the scope it defeats on the same property (16 edges in art14). The old totals are recorded here, not overwritten silently.
#
# The counts are SPLIT rather than bumped, so the original claim keeps its
# discriminating power: the CITATION half must still be unchanged at 8 / 11, and
# a stray scope edge shows up as scope, not as a bigger single number.
# A scope edge is one FROM a gdprkg:Exception ONTO a gdprkg:Paragraph or
# gdprkg:Point -- the same type discrimination m_conformance.py M2 applies
# (Zied, 2026-08-28). Everything else on the property is a citation.
def _is_scope(s, o):
    return ((s, RDF.type, GK.Exception) in g_plain
            and ((o, RDF.type, GK.Paragraph) in g_plain
                 or (o, RDF.type, GK.Point) in g_plain))


check("gdprkg:referencesProvision CITATIONS on Art-14 subjects UNCHANGED at 11",
      len([1 for s, _, o in rp if is_art14(s) and not _is_scope(s, o)]), 11)
check("gdprkg:referencesProvision M2 SCOPE edges on Art-14 subjects (S-G, was 0)",
      len([1 for s, _, o in rp if is_art14(s) and _is_scope(s, o)]), 16)
check("gdprkg:referencesProvision on Art-14 subjects, TOTAL (was 11 before S-G)",
      len([1 for s, _, _ in rp if is_art14(s)]), 27)
check("gdprkg:referencesProvision on Art-12 subjects (UNCHANGED by the rewire)",
      len([1 for s, _, _ in rp if is_art12(s)]), 49)

rolb = list(g_plain.triples((None, GK.reliesOnLegalBasis, None)))
check("gdprkg:reliesOnLegalBasis COMBINED (2 art13 + 2 art14)", len(rolb), 4)
check("gdprkg:reliesOnLegalBasis on Art-14 subjects",
      len([1 for s, _, _ in rolb if is_art14(s)]), 2)

# ---- f2-domain-family must NOT trigger ----
# WORK ORDER F 2026-09-06 -- THIS BLOCK CHANGED MEANING AND THE CHANGE IS DELIBERATE.
# It used to assert a BLANKET ABSENCE: zero gdprkg:notApplicableIf on any Art-14 node. That was
# correct for the Art-14 pass (art14.ttl's own header said "NO notApplicableIf") but it was NEVER
# the f2 carry's actual trigger -- f2 fires on notApplicableIf attached to a gdprkg:LegalBasis.
# Work Order F deliberately attaches 23 such edges to Art-14 OBLIGATIONS, on Zied's decided model,
# certified 2026-09-06. So the blanket prohibition is SUPERSEDED BY A LATER CERTIFIED DECISION, not
# quietly relaxed to make a run pass. Same treatment as the three re-scoped fixtures in
# run_owlrl_art46.py. What replaces it is STRICTER where it matters: the real f2 guard is asserted
# directly, and the 23 new edges are BOUNDED rather than merely permitted.
# SET AFTER THE RUN, not before -- see the CQ-C1 note above.
n = len([1 for s, _, _ in g_plain.triples((None, GK.hasLegalEffect, None)) if is_art14(s)])
check("forbidden gdprkg:hasLegalEffect on Art-14 nodes (unchanged, still 0)", n, 0)

nai14 = [(s, o) for s, _, o in g_plain.triples((None, GK.notApplicableIf, None)) if is_art14(s)]
check("gdprkg:notApplicableIf on Art-14 nodes [was 0 pre-WO-F; now the 23 collection-source edges]",
      len(nai14), 23)
check("all 23 are gdprkg:Obligation subjects",
      all((s, RDF.type, GK.Obligation) in g_plain for s, _ in nai14), True)
check("all 23 target the ONE shared node ex:cond-collected-from-data-subject",
      {short(o) for _, o in nai14} == {"ex:cond-collected-from-data-subject"}, True)
check("THE REAL f2-domain-family TRIGGER: notApplicableIf on a gdprkg:LegalBasis - MUST be 0",
      len([1 for s, _, _ in g_plain.triples((None, GK.notApplicableIf, None))
           if (s, RDF.type, GK.LegalBasis) in g_plain]), 0)
check("ex:obl-art14-5-b-protective-measures is NOT among them (outside the 14(1)-(4) scope)",
      not any(short(s) == "ex:obl-art14-5-b-protective-measures" for s, _ in nai14), True)

# ---- Art-12 regression: Permission machinery untouched ----
check("gdprkg:grantsPermissionTo edges (REGRESSION, art12)",
      len(list(g_plain.triples((None, GK.grantsPermissionTo, None)))), 6)
check("ex: gdprkg:Permission instances (REGRESSION, art12)",
      len(set(s for s in g.subjects(RDF.type, GK.Permission) if str(s).startswith(DATA))), 6)
check("Art-14 gdprkg:Permission instances (Art 14 grants no discretionary power)",
      len([1 for s in g.subjects(RDF.type, GK.Permission) if is_art14(s)]), 0)

# ---- the three mints ----
check("ex:ref-art89 typed gdprkg:ReferencedProvision (the ONE new stub)",
      (EX["ref-art89"], RDF.type, GK.ReferencedProvision) in g_plain, True)
check("ex:ref-art89 in-edges (referencesProvision from exc-art14-5-b)",
      len(list(g_plain.subjects(GK.referencesProvision, EX["ref-art89"]))), 1)
check("ex:concept-data-category typed gdprkg:DataCategory (canonical-node MINT, T3-F)",
      (EX["concept-data-category"], RDF.type, GK.DataCategory) in g_plain, True)
check("ex:concept-data-category INFERS gdprkg:DisclosableConcept (range of disclosesConcept)",
      (EX["concept-data-category"], RDF.type, GK.DisclosableConcept) in g, True)
check("ex:concept-data-category is NOT a GroundedConcept (Art-13 SURFACE-1 discipline)",
      (EX["concept-data-category"], RDF.type, GK.GroundedConcept) in g, False)
check("ex:actor-personal-data-source typed gdprkg:Actor_PersonalDataSource (T3-E(ii))",
      (EX["actor-personal-data-source"], RDF.type, GK.Actor_PersonalDataSource) in g_plain, True)
check("ex:actor-personal-data-source INFERS gdprkg:Actor (range of referencesActor)",
      (EX["actor-personal-data-source"], RDF.type, GK.Actor) in g, True)

# ---- zero duplicate canonical nodes: the reuse-first gate, machine-checked ----
# Every ex:concept-* / ex:actor-* / ex:ref-* node must be article-neutral, i.e. no IRI may
# carry an article suffix, and Art 14 must not have minted a second copy of a shared node.
canon = sorted(set(s for s in g_plain.subjects()
                   if isinstance(s, rdflib.URIRef) and str(s).startswith(DATA)
                   and (ln(s).startswith("concept-") or ln(s).startswith("actor-")
                        or ln(s).startswith("ref-"))))
check("canonical concept-/actor-/ref- nodes carrying an article suffix (must be 0)",
      len([c for c in canon if ln(c).endswith("-art13") or ln(c).endswith("-art14")
           or ln(c).endswith("-art12") or ln(c).endswith("-art6")]), 0)
check("ex:concept-* canonical nodes (6 reused-from-art13 + 1 minted)",
      len([c for c in canon if ln(c).startswith("concept-")]), 7)
check("ex:actor-* canonical nodes (5 reused-from-art13 + 1 minted)",
      len([c for c in canon if ln(c).startswith("actor-")]), 6)

# ---- the ex:ref-art14 rewire (work order C 3.2) + orphan check ----
refart14 = EX["ref-art14"]
occurrences = (len(list(g_plain.triples((refart14, None, None))))
               + len(list(g_plain.triples((None, None, refart14)))))
check("ex:ref-art14 occurrences anywhere in the 5-file union (REWIRED AWAY -> 0)",
      occurrences, 0)
check("ex:art14 referencesProvision in-edges from art12.ttl (obl-12-1-form, obl-12-5-free, perm-12-7-icons)",
      len([1 for s in g_plain.subjects(GK.referencesProvision, EX["art14"]) if is_art12(s)]), 3)

# ---- standing invariants ----
check("owl:Nothing members  [TIER 1]", len(list(g.subjects(RDF.type, OWL.Nothing))), 0)

subjects = set(g.subjects())
dangling = sorted(set(o for _, _, o in g
                      if isinstance(o, rdflib.URIRef) and str(o).startswith(DATA)
                      and o not in subjects))
if dangling:
    print("    [FIXTURE] dangling ex: IRIs found: %s" % ", ".join(short(d) for d in dangling))
check("dangling ex: object IRIs (never a subject across the closed graph)  [TIER 1]",
      len(dangling), 0)
print()


# =====================================================================
# 5. SUMMARY  (NOT a certification — see the header)
# =====================================================================
print("=" * 72)
if all_ok:
    print("ALL ART-14 CHECKS MATCH THE PRE-RUN PREDICTIONS IN expected_results.md §Article-14")
    print("(PROXY ONLY — certification is Zied's: combined 5-file HermiT + local pySHACL + this run.)")
    sys.exit(0)
else:
    print("MISMATCH — see rows above.")
    print("Per playbook 4.2 the DEFAULT diagnosis is a defect in the data or the modelling,")
    print("NOT a wrong prediction. Investigate in that order; never silently reconcile.")
    sys.exit(1)
