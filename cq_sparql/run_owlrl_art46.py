#!/usr/bin/env python3
# =====================================================================
#  run_owlrl_art46.py — AUTHORITATIVE OWL 2 RL CQ run for Article 46
#  (the Art-46 applicability-gating pass, over the COMBINED 6-file union).
#
#  This is the authoritative OWL 2 RL CQ run for the Art-46
#  certification gate (check 3), mirroring run_owlrl_art14.py.
#
#  run_owlrl_art14.py, run_owlrl_art12.py and run_owlrl_art6.py are NOT
#  modified by this pass (work order E §4.6) — this file stands
#  alongside them.
#
#  Needs a networked (or pre-provisioned) machine:
#      pip install rdflib owlrl
#      python run_owlrl_art46.py
#  Run from anywhere. The graph tree is resolved as:
#      --root <dir>  >  $GDPR_KG_ROOT  >  the tree this script lives in
#  (see kg_root.py). Missing inputs exit 2, not 1, so a path failure is
#  distinguishable from a CQ failure. The TBox sha256 is printed below.
#
#  What it does:
#    1. load the COMBINED 6-file union into ONE graph:
#         ../ontology/gdpr_kg.ttl  (TBox, post the TWO Art-46 mints)
#       + ../articles/art13.ttl
#       + ../articles/art6.ttl
#       + ../articles/art12.ttl
#       + ../articles/art14.ttl
#       + ../articles/art46.ttl        <-- NEW this pass
#       print the pre-closure triple count;
#    2. materialise the OWL 2 RL closure; print the post-closure count;
#    3. run each CQ .rq and print rows + PASS/CHECK against the counts
#       PREDICTED IN ADVANCE in cq_sparql/expected_results.md
#       (§Article-46). Those predictions were written BEFORE THIS FILE
#       EXISTED ON DISK — see the prediction-provenance banner there,
#       and the mtime ordering, which is checkable;
#    4. run the additional Art-46 fixture checks; print PASS/CHECK;
#    5. print the final SUMMARY line + exit 0/1.
#
#  >>> DELIBERATELY NOT LOADED: ../fixtures/art46_scenarios.ttl.
#  That file is a NON-NORMATIVE demonstrator, kept OUTSIDE the
#  certification union by decision of Zied (2026-08-06). It is exercised
#  only by demo_art46_scenarios.py, which certifies nothing. If you find
#  it loaded here, that is a defect.
#
#  REGIME NOTE (why two graphs) — inherited in substance from
#  run_owlrl_art14.py / run_owlrl_art12.py. CQ-C4 and CQ-C5 project the
#  referenced-actor / disclosed-concept rdf:type WITHOUT restricting to
#  the leaf class, so OWL 2 RL materialisation multiplies each genuine
#  answer row by its inferred super-types. The DISTINCT answer set is
#  unchanged (9 / 11) but the raw row count inflates. Those two frozen
#  queries are therefore evaluated on the PLAIN (pre-closure) graph, per
#  their documented regime — this is NOT a tweak of expected numbers.
#  Each query prints the regime it used.
#
#  ⚠ THIS SCRIPT DOES NOT CERTIFY ANYTHING. Certification is Zied's:
#  combined HermiT over articles/certify_art13_art6.ttl (now SIX files)
#  + local pySHACL ×5 + this runner. An agent's run is a PROXY.
#  For THIS unit the HermiT leg matters more than usual: two TBox terms
#  were added, so it is a genuine satisfiability question, not a
#  regression, and NO PROXY HERE COVERS IT.
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
ART46 = os.path.join(ROOT, 'articles', 'art46.ttl')
kg_root.require(TBOX, ART13, ART6, ART12, ART14, ART46)
kg_root.provenance(ROOT, TBOX)
QDIR = os.path.join(ROOT, 'cq_sparql')   # .rq files come from the same tree as the data

GDPRKG = "https://w3id.org/gdprkg#"
DATA   = "https://w3id.org/gdprkg/data#"      # prefix ex:
GK  = rdflib.Namespace(GDPRKG)
EX  = rdflib.Namespace(DATA)
RDF = rdflib.RDF
RDFS = rdflib.RDFS
OWL = rdflib.OWL

# ---------------------------------------------------------------------
# 1. load the COMBINED 6-file union (pre-closure = the PLAIN graph)
# ---------------------------------------------------------------------
g_plain = rdflib.Graph()
for f in (TBOX, ART13, ART6, ART12, ART14, ART46):
    g_plain.parse(f, format='turtle')
print("[LOAD] gdpr_kg + art13 + art6 + art12 + art14 + art46 -> %d triples (pre-closure)"
      % len(g_plain))
print("[LOAD] NOT loaded (by design): ../fixtures/art46_scenarios.ttl (non-normative demonstrator)")

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
#    §Article-46).
# =====================================================================
# (file, label, expected, regime, note)
QUERIES = [
    ("CQ-C1_article_to_norms_grounded.rq", "CQ-C1  article -> grounded norms", 107, "materialised",
     "WORK ORDER F 2026-09-06: 105 -> 107, +2 FOR ONE NODE. ex:cond-collected-from-data-subject is "
     "DUAL-GROUNDED (art13-p1 + art14-p1) and this query returns one row per groundedIn edge. It is "
     "the FIRST node in the project with two; permitted (minCount 1, NO maxCount) but previously "
     "unexercised, so this query's own header note 'every one carrying exactly one groundedIn edge' "
     "NO LONGER DESCRIBES THE WHOLE GRAPH. Predicted in expected_results.md BEFORE the run; the "
     "query itself was NOT edited. || Art-46 delta +5 (1 Obligation + 4 Conditions + 0 Exceptions). The 46(1) PERMISSION is "
     "excluded by the frozen FILTER (non-coverage #1) AND so are all 8 TransferMechanism nodes "
     "(non-coverage #4, NEW). Neither query was widened."),
    ("CQ-C2_uniform_grounding.rq", "CQ-C2  uniform grounding (0 = pass)", 0, "materialised",
     "TIER 1 (LOCKED, brief 6.2) and LOAD-BEARING this unit. All 8 TransferMechanism individuals are "
     "GroundedConcepts and must each carry groundedIn. This is the invariant the TBox delta was "
     "SHAPED to protect: widening gdprkg:Safeguard instead would have made ex:concept-safeguard an "
     "ungrounded GroundedConcept and broken art13/art14 without editing them."),
    ("CQ-C3_bearer.rq", "CQ-C3  obligation -> bearer", 59, "materialised",
     "TIER 1 (LOCKED, brief 6.2) = 58 + 1. The base is 58 (the TRIPLE count), NOT 61 (a raw string "
     "count including three commented-out template lines). THE +1 IS NOT A CONTROLLER: it is "
     "ex:actor-supervisory-authority, so this result set stops being homogeneous for the first time."),
    ("CQ-C4_referenced_actor.rq", "CQ-C4  obligation -> referenced actor", 9, "plain",
     "TIER 2 — EXPECTED ZERO DELTA. plain regime. 46(4)'s supervisory authority is the BEARER, and "
     "referencesActor is for the NON-BEARER actor a duty is about. A 10 means a referencesActor edge "
     "was drawn where the bearer edge belongs."),
    ("CQ-C5_domain_concept.rq", "CQ-C5  obligation -> disclosed concept", 11, "plain",
     "TIER 2 — EXPECTED ZERO DELTA. plain regime. Art 46 is not a disclosure article. A value BELOW "
     "11 means an Art-13/Art-14 edge was damaged by the ex:ref-art46 rewire."),
    ("CQ-C5x_cross_article_basis.rq", "CQ-C5x cross-article basis (Point-join)", 4, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA. Art 46 adds no LegalBasis and no reliesOnLegalBasis. A value "
     "BELOW 4 means an Art-13/Art-6/Art-14 edge was damaged."),
    ("CQ-C7_temporal.rq", "CQ-C7  temporal triggers (frozen label filter)", 44, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA. Art 46 states no temporal trigger. No Art-46 Condition label "
     "contains 'at the time' or 'prior to', and none was worded to attract or avoid the filter."),
    ("CQ-A1_art13_coverage.rq", "CQ-A1  obligations + grounding (unscoped)", 59, "materialised",
     "TIER 2, +1: obl-46-4-consistency-mechanism @ ex:art46-p4. Query is not article-scoped."),
    ("CQ-A3_conditional_duties.rq", "CQ-A3  conditional duties", 112, "materialised",
     "WORK ORDER F 2026-09-06: 91 -> 112, and the +21 IS THE ARTICLE-13 SIDE ONLY. The 23 Article-14 "
     "duties attach to the same shared trigger with gdprkg:notApplicableIf, which this frozen query "
     "does not mention (verified: 0 occurrences in the .rq), so they contribute NOTHING here. "
     "RECORDED NON-COVERAGE #1 of this pass. The 23 duties are NOT invisible to the query overall — "
     "distinct art14 obligations returned is 23 both before and after; what is missing is their "
     "PAIRING with this trigger. THE QUERY WAS NOT WIDENED AND NO EDGE WAS RE-POINTED TO appliesIf "
     "TO MAKE THE COUNT LAND (playbook 4.1). Zied ruled 2026-09-06 that the ENCODING mis-models the "
     "question CQ-A3 states in words (a duty switched OFF by a condition is conditional); that "
     "correction is a SEPARATE unit, deliberately not this one. Predicted in expected_results.md "
     "BEFORE the run. || Art-46 legacy note: +1 was obl-46-4, one appliesIf; the 46(1) PERMISSION's "
     "TWO appliesIf edges do NOT count - the query requires ?obligation a gdprkg:Obligation."),
    ("CQ-A4_art13_exemption.rq", "CQ-A4  exemptions, grouped (unscoped)", 8, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA. Art 46 has 0 Exceptions, so it contributes no group."),
    ("CQ-A5_art14_exemptions.rq", "CQ-A5  Art-14 exemptions -> defeated duties (REGRESSION)", 92, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA. Art 46 adds no Exception."),
    ("CQ-A6_art14_remaining_obligation.rq", "CQ-A6  duty surviving 14(5)(b) (REGRESSION)", 1, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA."),
    ("CQ-A8_art14_timing.rq", "CQ-A8  Art-14 timing (REGRESSION)", 66, "materialised",
     "TIER 2 — EXPECTED ZERO DELTA. Art 46 adds no hasTimeLimit and no timing Condition."),
    # ---- Art-6 regression block: TIER 1, brief 6.2. Art 46 adds no LegalBasis. ----
    ("CQ-B1_lawful_bases.rq", "CQ-B1  lawful bases (REGRESSION)", 6, "materialised",
     "TIER 1 regression. A 7 would mean the 46(2)/(3) instruments were typed as LegalBasis — the "
     "one construct choice that fires carry f2-domain-family and is FORBIDDEN this unit."),
    ("CQ-B2_basis_conditions.rq", "CQ-B2  basis -> condition (REGRESSION)", 3, "materialised",
     "TIER 1 regression."),
    ("CQ-B3_basis_in_union_or_ms_law.rq", "CQ-B3  bases needing Union/MS law (REGRESSION)", 2, "materialised",
     "TIER 1 regression."),
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
    if VERBOSE or not ok or len(rows) <= 12:
        for r in rows:
            print("      " + "  ".join(short(x) for x in r))
    else:
        print("      (%d rows suppressed; re-run with -v to print them)" % len(rows))
    print()

# ---------------------------------------------------------------------
# CQ-C6 - provenance/review: 318 rows = 80 "direct" + 238 "inherited"
# WORK ORDER F 2026-09-06: inherited 217 -> 238 (+21, the Art-13 appliesIf side only).
# ---------------------------------------------------------------------
print("=== CQ-C6  provenance / review (mode split) ===")
c6 = list(g.query(open(os.path.join(QDIR, "CQ-C6_provenance_review.rq"), encoding='utf-8').read()))
n_direct    = sum(1 for r in c6 if str(r["mode"]) == "direct")
n_inherited = sum(1 for r in c6 if str(r["mode"]) == "inherited")
n_total     = len(c6)
c6_ok = (n_direct == 80 and n_inherited == 262 and n_total == 342)
all_ok = all_ok and c6_ok
print("    file=CQ-C6_provenance_review.rq  regime=materialised")
print("    direct=%d (expected 80)  inherited=%d (expected 262)  total=%d (expected 342)  -> %s"
      % (n_direct, n_inherited, n_total, "PASS" if c6_ok else "CHECK"))
print("    NOTE: direct 80 = 70 + 10, and the 10 is 1 Permission + 1 Obligation + 8 TransferMechanism.")
print("          The 8 mechanisms COUNT because CQ-C6's direct branch keys on the reviewStatus/")
print("          hasProvenance TRIPLES, not on class. Their provenance is ASSERTED BUT NOT ENFORCED:")
print("          ProvenanceRequiredShape/ReviewStatusShape target PrimaryNormativeUnit, which")
print("          gdprkg:TransferMechanism deliberately is NOT. Carry art46-transfermechanism-provenance.")
print("    NOTE: inherited 217 = 214 + 3, NOT +4. RECORDED NON-COVERAGE #5: CQ-C6's inherited branch")
print("          enumerates (appliesIf|hasException) and does NOT include notApplicableIf, so")
print("          cond-46-1-adequacy-decision-exists — the 45(3) gate, the most important node in this")
print("          unit — has NO provenance path under the frozen query. The query was NOT widened and")
print("          the edge was NOT re-pointed to appliesIf to make the count land (playbook 4.1).")
print("    NOTE: ^^ THE TWO NOTES ABOVE ARE HISTORICAL AS OF 2026-09-06 - RETAINED, NOT DELETED.")
print("          CQ-C6's ENCODING WAS FIXED that day (Zied, option B): notApplicableIf was added to")
print("          the inherited parent path, because the frozen QUESTION ('for any node') and PROBE")
print("          ('Condition/Exception inherit via parent', naming no properties) were ALREADY")
print("          broader than the encoding. EXEC-9 IS RESOLVED: cond-46-1-adequacy-decision-exists")
print("          now HAS a provenance path, and Cond/Exc nodes with no provenance answer is 0.")
print("          inherited 262 = 238 + 23 Work-Order-F art14 edges + 1 the Art-46 gate itself.")
print("          CQ-A3 has the SAME blind spot and was DELIBERATELY NOT FIXED - its frozen probe")
print("          names APPLIES_IF, so that call was left open. CQ-A3 stays 112, a recorded gap.")
print("    NOTE: WORK ORDER F 2026-09-06 - inherited 238 = 217 + 21, NOT +44. The 23 Article-14")
print("          notApplicableIf edges to ex:cond-collected-from-data-subject are invisible to the")
print("          same closed (appliesIf|hasException) list. RECORDED NON-COVERAGE #2 of that pass.")
print("          BUT THIS IS **NOT** A SECOND EXEC-9: the shared node RESOLVES here via the 21")
print("          Article-13 appliesIf edges, so NO NODE IS LEFT UNPROVENANCED. Measured, Cond/Exc")
print("          nodes with no provenance answer: 1 before and 1 after, and it is art46's, unchanged.")
print("          EXEC-9 is a node with NO path at all; this is a lower row count. Different in kind.")
print()


# =====================================================================
# 4. Additional Art-46 fixture checks
#    "Art-46 node" test: a data-namespace (ex:) subject whose IRI
#    localname startswith "art46" OR contains "46-" (covers art46- /
#    obl-46- / cond-46- / perm-46- / mech-46-).
#    NB ex:ref-art46 was REWIRED AWAY by this pass, so it cannot pollute
#    the test — and its absence is itself asserted below.
# =====================================================================
def is_art46(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art46") or "46-" in l


def is_art12(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art12") or "12-" in l


def is_art13(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art13") or "13-" in l


def is_art14(node):
    if not isinstance(node, rdflib.URIRef) or not str(node).startswith(DATA):
        return False
    l = ln(node)
    return l.startswith("art14") or "14-" in l


def check(name, actual, expected):
    global all_ok
    ok = (actual == expected)
    all_ok = all_ok and ok
    print("    [FIXTURE] %-68s actual=%s  expected=%s  -> %s"
          % (name, actual, expected, "PASS" if ok else "CHECK"))
    return ok


print("=== Art-46 fixture checks (plain graph unless noted) ===")
print("    (Art-46 node = ex: subject whose localname startswith 'art46' or contains '46-')")

# ---- node inventory (TIER 1 unless marked) ----
a46_obl  = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Obligation)) if is_art46(s))
a46_perm = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Permission)) if is_art46(s))
a46_mech = sorted(s for s in set(g_plain.subjects(RDF.type, GK.TransferMechanism)) if is_art46(s))
a46_cnd  = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Condition)) if is_art46(s))
a46_exc  = sorted(s for s in set(g_plain.subjects(RDF.type, GK.Exception)) if is_art46(s))
check("Art-46 Obligation instances        [TIER 1 = 1, LOCKED]", len(a46_obl), 1)
check("Art-46 Permission instances        [TIER 1 = 1, LOCKED]", len(a46_perm), 1)
check("Art-46 TransferMechanism instances [TIER 1 = 8, LOCKED]", len(a46_mech), 8)
check("Art-46 Condition instances         [TIER 2 = 4]", len(a46_cnd), 4)
check("Art-46 Exception instances         [TIER 1 = 0, LOCKED]", len(a46_exc), 0)

# one mechanism per lettered point, each groundedIn ITS OWN point (R4)
mech_points = sorted(ln(p) for m in a46_mech for p in g_plain.objects(m, GK.groundedIn))
check("Art-46 mechanisms grounded in 8 DISTINCT points", len(set(mech_points)), 8)
check("Art-46 mechanism grounding points are exactly 46(2)(a)-(f) + 46(3)(a)-(b)",
      mech_points == ['art46-p2-a', 'art46-p2-b', 'art46-p2-c', 'art46-p2-d',
                      'art46-p2-e', 'art46-p2-f', 'art46-p3-a', 'art46-p3-b'], True)

# ---- the TWO TBox mints, exercised ----
ps = list(g_plain.triples((None, GK.providesSafeguard, None)))
check("gdprkg:providesSafeguard edges (FIRST use)", len(ps), 8)
check("gdprkg:providesSafeguard objects ALL = ex:concept-safeguard (canonical shared node)",
      set(o for _, _, o in ps) == {EX["concept-safeguard"]}, True)
check("every TransferMechanism infers gdprkg:GroundedConcept",
      all((m, RDF.type, GK.GroundedConcept) in g for m in a46_mech), True)
check("NO TransferMechanism infers gdprkg:PrimaryNormativeUnit (T3-B/U5 typing refused)",
      any((m, RDF.type, GK.PrimaryNormativeUnit) in g for m in a46_mech), False)
check("NO TransferMechanism infers gdprkg:NormativeElement (EXEC-1: seeAlso, not referencesProvision)",
      any((m, RDF.type, GK.NormativeElement) in g for m in a46_mech), False)

# ---- the applicability gate itself ----
nai = list(g_plain.triples((None, GK.notApplicableIf, None)))
# WORK ORDER F 2026-09-06 - THESE THREE FIXTURES WERE UNION-SCOPED AND ARE NOW ART-46-SCOPED.
# They were written when Art 46 held the ONLY notApplicableIf edge in the project, so "the whole
# union has exactly one, and it is Art 46's" was a true and useful Art-46 assertion. WO-F attaches
# 23 more (23 Art-14 duties -> ex:cond-collected-from-data-subject), so the union count is now 24.
# The Art-46 FACT the fixtures exist to protect is unchanged and is still asserted below, exactly:
# the 46(1) Permission still carries exactly one notApplicableIf, still to the 45(3) gate condition.
# The union total is kept as a separate fixture so a stray future edge is still caught.
# Predicted in expected_results.md BEFORE the run.
check("gdprkg:notApplicableIf edges, WHOLE UNION [was 1 pre-WO-F; 1 art46 + 23 art14]", len(nai), 24)
nai46 = [(x, o) for x, _, o in nai if short(x) == "ex:perm-46-1-transfer"]
check("Art-46 notApplicableIf edges on ex:perm-46-1-transfer [TIER 1 = 1, unchanged by WO-F]",
      len(nai46), 1)
check("that edge's object is ex:cond-46-1-adequacy-decision-exists",
      [short(o) for _, o in nai46] == ["ex:cond-46-1-adequacy-decision-exists"], True)
check("WO-F notApplicableIf edges, all subjects are art14 Obligations",
      all(short(x).startswith("ex:obl-art14") for x, _, o in nai if short(x) != "ex:perm-46-1-transfer"), True)
check("WO-F notApplicableIf edges all target ex:cond-collected-from-data-subject",
      all(short(o) == "ex:cond-collected-from-data-subject" for x, _, o in nai if short(x) != "ex:perm-46-1-transfer"), True)
check("notApplicableIf on a gdprkg:LegalBasis (carry f2-domain-family trigger) - MUST be 0",
      len([1 for x, _, _ in nai if (x, RDF.type, GK.LegalBasis) in g_plain]), 0)
check("the 46(1) Permission infers NormativeElement (F2 NOT tripped: domain is satisfied)",
      (EX["perm-46-1-transfer"], RDF.type, GK.NormativeElement) in g, True)

# ---- bearers ----
gpt = list(g_plain.triples((None, GK.grantsPermissionTo, None)))
a46_gpt = [(s, o) for s, _, o in gpt if is_art46(s)]
check("gdprkg:grantsPermissionTo on Art-46 subjects (FIRST multi-bearer norm)", len(a46_gpt), 2)
check("Art-46 permission bearers = {controller, processor}",
      set(short(o) for _, o in a46_gpt) == {"ex:actor-controller", "ex:actor-processor"}, True)
check("gdprkg:grantsPermissionTo COMBINED (6 art12 + 2 art46)", len(gpt), 8)
check("gdprkg:Permission instances COMBINED [TIER 1 = 7]",
      len(set(s for s in g.subjects(RDF.type, GK.Permission) if str(s).startswith(DATA))), 7)

ioo = list(g_plain.triples((None, GK.imposesObligationOn, None)))
check("imposesObligationOn -> ex:actor-supervisory-authority (FIRST non-controller bearer)",
      len([1 for _, _, o in ioo if o == EX["actor-supervisory-authority"]]), 1)
check("imposesObligationOn -> ex:actor-controller UNCHANGED at 58",
      len([1 for _, _, o in ioo if o == EX["actor-controller"]]), 58)

# ---- edges ----
check("gdprkg:appliesIf on Art-46 subjects (2 on the Permission + 1 on the Obligation)",
      len([1 for s, _, _ in g_plain.triples((None, GK.appliesIf, None)) if is_art46(s)]), 3)
rp = list(g_plain.triples((None, GK.referencesProvision, None)))
check("gdprkg:referencesProvision on Art-46 subjects (EXEC-1: the other 5 ride on seeAlso)",
      len([1 for s, _, _ in rp if is_art46(s)]), 2)
check("rdfs:seeAlso from Art-46 mechanisms to stubs (EXEC-1)",
      len([1 for s, _, o in g_plain.triples((None, RDFS.seeAlso, None))
           if is_art46(s) and str(o).startswith(DATA)]), 5)

# ---- forbidden / expected-absent edges ----
for pr, lbl in (("hasLegalEffect", "T3-D declined LegalEffect's first use"),
                ("disclosesConcept", "not a disclosure article"),
                ("disclosedToDataSubject", "not a disclosure article"),
                ("hasTimeLimit", "no deadline in Art 46"),
                ("referencesActor", "the supervisory authority is the BEARER, not a referenced actor")):
    n = len([1 for s, _, _ in g_plain.triples((None, GK[pr], None)) if is_art46(s)])
    check("expected-ABSENT gdprkg:%s on Art-46 nodes (%s)" % (pr, lbl), n, 0)
check("gdprkg:LegalEffect instances, WHOLE UNION [TIER 1 = 0]",
      len(set(g.subjects(RDF.type, GK.LegalEffect))), 0)
check("gdprkg:LegalBasis instances, WHOLE UNION (unchanged at 6; a 7th = the forbidden typing)",
      len(set(s for s in g.subjects(RDF.type, GK.LegalBasis) if str(s).startswith(DATA))), 6)

# ---- stubs + reuse-first ----
stubs = sorted(set(s for s in g_plain.subjects(RDF.type, GK.ReferencedProvision)))
# AMENDED 2026-08-07 after the first run: predicted 22, observed 21. The prediction was
# wrong, the data is correct — the ex:ref-art46 rewire DELETES a declaration from the same
# population the five new stubs join (17 - 1 + 5 = 21). Recorded permanently in
# expected_results.md §Article-46 with the original prediction left visible (playbook §4.2).
# THE ONLY DEVIATION IN THIS UNIT; every Tier-1 value passed unchanged.
check("ReferencedProvision individuals COMBINED (17 - 1 rewired away + 5 new)", len(stubs), 21)
for st in ("ref-art45-3", "ref-art93-2", "ref-art40", "ref-art42", "ref-art63"):
    check("new stub ex:%s declared" % st, (EX[st], RDF.type, GK.ReferencedProvision) in g_plain, True)
check("ex:ref-art47 REUSED, declared exactly ONCE across the union (zero duplicate stubs)",
      len(list(g_plain.triples((EX["ref-art47"], RDF.type, GK.ReferencedProvision)))), 1)
check("ex:actor-processor typed gdprkg:Processor (instance mint, NOT a TBox change)",
      (EX["actor-processor"], RDF.type, GK.Processor) in g_plain, True)
check("ex:actor-processor INFERS gdprkg:Actor", (EX["actor-processor"], RDF.type, GK.Actor) in g, True)

canon = sorted(set(s for s in g_plain.subjects()
                   if isinstance(s, rdflib.URIRef) and str(s).startswith(DATA)
                   and (ln(s).startswith("concept-") or ln(s).startswith("actor-"))))
check("ex:concept-* canonical nodes (UNCHANGED at 7 — Art 46 minted none)",
      len([c for c in canon if ln(c).startswith("concept-")]), 7)
check("ex:actor-* canonical nodes (6 + ex:actor-processor)",
      len([c for c in canon if ln(c).startswith("actor-")]), 7)
check("canonical concept-/actor- nodes carrying an article suffix (must be 0)",
      len([c for c in canon if any(ln(c).endswith(x) for x in
           ("-art13", "-art14", "-art12", "-art6", "-art46"))]), 0)

# ---- the ex:ref-art46 rewire (work order E §4.3: 3 sites / 2 files) + orphan check ----
refart46 = EX["ref-art46"]
occurrences = (len(list(g_plain.triples((refart46, None, None))))
               + len(list(g_plain.triples((None, None, refart46)))))
check("ex:ref-art46 occurrences anywhere in the 6-file union (REWIRED AWAY -> 0)", occurrences, 0)
a46_in = sorted(short(s) for s in g_plain.subjects(GK.referencesProvision, EX["art46"]))
check("ex:art46 referencesProvision in-edges (the rewire, from the other side)", len(a46_in), 2)
check("ex:art46 in-edge subjects are the two 1(f) Conditions",
      a46_in == ["ex:cond-13-1-f-transfer-safeguarded", "ex:cond-14-1-f-transfer-safeguarded"], True)
# ---- S-G 2026-08-30: the M2 scope edges moved these two raw-edge counts ----
# These fixtures asserted "UNCHANGED at N" because the Art-46 pass needed to show
# that the ex:ref-art46 rewire did not disturb the referencesProvision population.
# The M2 unit DELIBERATELY grows that population: every multi-bearer Exception now
# declares the scope it defeats on the same property (3 edges in art13, 16 in
# art14, 19 total). The old totals are recorded here, not overwritten silently.
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


check("referencesProvision CITATIONS on Art-13 subjects UNCHANGED at 8",
      len([1 for s, _, o in rp if is_art13(s) and not _is_scope(s, o)]), 8)
check("referencesProvision M2 SCOPE edges on Art-13 subjects (S-G, was 0)",
      len([1 for s, _, o in rp if is_art13(s) and _is_scope(s, o)]), 3)
check("referencesProvision on Art-13 subjects, TOTAL (was 8 before S-G)",
      len([1 for s, _, _ in rp if is_art13(s)]), 11)
check("referencesProvision on Art-12 subjects UNCHANGED at 49",
      len([1 for s, _, _ in rp if is_art12(s)]), 49)
check("referencesProvision CITATIONS on Art-14 subjects UNCHANGED at 11",
      len([1 for s, _, o in rp if is_art14(s) and not _is_scope(s, o)]), 11)
check("referencesProvision M2 SCOPE edges on Art-14 subjects (S-G, was 0)",
      len([1 for s, _, o in rp if is_art14(s) and _is_scope(s, o)]), 16)
check("referencesProvision on Art-14 subjects, TOTAL (was 11 before S-G)",
      len([1 for s, _, _ in rp if is_art14(s)]), 27)

# ---- the demonstrator must NOT be in this union ----
check("fixtures/art46_scenarios.ttl NOT loaded (0 exs: scenario IRIs present)",
      len([1 for s in set(g_plain.subjects())
           if isinstance(s, rdflib.URIRef) and str(s).startswith("https://w3id.org/gdprkg/scenario#")]), 0)

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
print("=" * 76)
if all_ok:
    print("ALL ART-46 CHECKS MATCH THE PRE-RUN PREDICTIONS IN expected_results.md §Article-46")
    print("(PROXY ONLY — certification is Zied's: combined 6-file HermiT + local pySHACL x5 + this run.)")
    print("The HermiT leg is a GENUINE SATISFIABILITY QUESTION this unit, not a regression:")
    print("two TBox terms were added. Nothing here covers it.")
    print("WORK ORDER F (2026-09-06) NOW ALSO RIDES ON THIS RUNNER, AND ITS HermiT LEG IS THE")
    print("OPPOSITE CASE: WO-F added ZERO TBox axioms, so for that pass the consistency run is a")
    print("REGRESSION, not a satisfiability question. Do not read the Art-46 sentence above as")
    print("describing it. Both legs are still Zied's to run; nothing here covers either.")
    sys.exit(0)
else:
    print("MISMATCH — see rows above.")
    print("Per playbook 4.2 the DEFAULT diagnosis is a defect in the data or the modelling,")
    print("NOT a wrong prediction. Investigate in that order; never silently reconcile.")
    sys.exit(1)
