#!/usr/bin/env python3
# =====================================================================
#  demo_art46_scenarios.py — NON-CERTIFYING Article-46 gate demonstrator
#  ===================================================================
#  ###                THIS SCRIPT CERTIFIES NOTHING.                ###
#
#  It is NOT part of the technical gate. It is NOT a proxy for one. It
#  does not appear in the certification commands. Its output is a
#  DEMONSTRATION and must never be reported as a gate result.
#
#  WHAT IT IS FOR. brief §2 states the honest limit of the Art-46 unit:
#  the graph has no scenario layer, so "an article-level Art-46 ABox
#  EXPRESSES the gate structure; it does not EXERCISE it." This script
#  loads the certified 6-file union PLUS the non-normative fixture
#  ../fixtures/art46_scenarios.ttl and runs four queries whose answers
#  DIFFER PER SCENARIO. That difference is the whole point: it shows
#  NOT_APPLICABLE being DERIVED from facts about a transfer rather than
#  judged from the wording of a policy.
#
#  THE PERIMETER (Zied, 2026-08-06 — not open):
#    * the fixture is NOT in articles/certify_art13_art6.ttl
#    * the fixture is NOT in articles/catalog-v001.xml
#    * the fixture is NOT loaded by run_owlrl_art46.py
#    * HermiT / pySHACL / the CQ runner certify the SIX-file union
#      WITHOUT it.
#
#  ###############################################################
#  ##  THE CLOSED-WORLD LIMIT — WHY Q3 IS SCOPED THE WAY IT IS   ##
#  ###############################################################
#  46(3) is expressly NON-EXHAUSTIVE ("in particular"); 46(2) is not.
#  So "no listed instrument matched => no appropriate safeguard" is
#  DEFENSIBLE over 46(2) and UNSOUND over 46(3).
#
#  Therefore NO query below concludes "no appropriate safeguard". Q3
#  asks the SCOPED question — "which transfers rely on no listed 46(2)
#  instrument?" — and its result column is named so it cannot be
#  misread as the stronger claim. Q3 additionally REPORTS the 46(3)
#  residue explicitly, so the unsound inference is not merely avoided
#  but visibly refused.
#
#  Usage:  cd cq_sparql && python demo_art46_scenarios.py
# =====================================================================
import os, sys
try:
    import rdflib
except ImportError:
    sys.exit("Missing deps. Run:  pip install rdflib")

BANNER = "=" * 78
print(BANNER)
print("  ARTICLE-46 GATE DEMONSTRATOR — NON-CERTIFYING, NON-NORMATIVE")
print("  Results below are a DEMONSTRATION. They are not a gate, not a")
print("  proxy for one, and must not be reported as certification evidence.")
print(BANNER)
print()

FILES = [os.path.join('..', 'ontology', 'gdpr_kg.ttl'),
         os.path.join('..', 'articles', 'art13.ttl'),
         os.path.join('..', 'articles', 'art6.ttl'),
         os.path.join('..', 'articles', 'art12.ttl'),
         os.path.join('..', 'articles', 'art14.ttl'),
         os.path.join('..', 'articles', 'art46.ttl')]
FIXTURE = os.path.join('..', 'fixtures', 'art46_scenarios.ttl')

g = rdflib.Graph()
for f in FILES:
    g.parse(f, format='turtle')
n_certified = len(g)
g.parse(FIXTURE, format='turtle')
print("[LOAD] certified 6-file union      -> %d triples" % n_certified)
print("[LOAD] + NON-NORMATIVE fixture     -> %d triples (delta %d)"
      % (len(g), len(g) - n_certified))
print()

PRE = """
PREFIX gdprkg: <https://w3id.org/gdprkg#>
PREFIX ex:     <https://w3id.org/gdprkg/data#>
PREFIX exs:    <https://w3id.org/gdprkg/scenario#>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
"""


def run(title, why, sparql, expect_n):
    rows = list(g.query(PRE + sparql))
    ok = "as expected" if len(rows) == expect_n else "!! UNEXPECTED (expected %d)" % expect_n
    print("--- %s" % title)
    print("    %s" % why)
    print("    rows = %d  (%s)" % (len(rows), ok))
    for r in rows:
        vals = []
        for v in r:
            s = str(v)
            vals.append(s.replace("https://w3id.org/gdprkg/scenario#", "exs:")
                         .replace("https://w3id.org/gdprkg/data#", "ex:"))
        print("      * " + " | ".join(vals))
    print()
    return len(rows) == expect_n


ok = True

# Q1 — the gate. This is the headline row.
ok &= run(
    "Q1  Transfers for which ARTICLE 46 DOES NOT ENGAGE",
    "An Art 45(3) adequacy decision is in force => the 46(1) permission's notApplicableIf\n"
    "        condition holds. Note this is TRUE REGARDLESS of whether any mechanism exists —\n"
    "        the gate fires first. This is applicability DERIVED FROM A FACT, not a label.",
    """
    SELECT ?transfer ?gateCondition
    WHERE {
      ?transfer exs:destinationHasAdequacyDecision true .
      ex:perm-46-1-transfer gdprkg:notApplicableIf ?gateCondition .
    }
    ORDER BY ?transfer
    """, 1)

# Q2 — engaged, satisfied through the CLOSED 46(2) list.
ok &= run(
    "Q2  Transfers ENGAGING Art 46 and relying on a 46(2) instrument (NO authorisation needed)",
    "Mechanism grounded under Article 46(2) => no supervisory-authority authorisation.",
    """
    SELECT ?transfer ?mechanism ?point
    WHERE {
      ?transfer exs:destinationHasAdequacyDecision false ;
                exs:reliesOnMechanism ?mechanism .
      ?mechanism gdprkg:groundedIn ?point .
      ?point rdfs:label ?plabel .
      FILTER(CONTAINS(STR(?plabel), "Article 46(2)"))
    }
    ORDER BY ?transfer
    """, 1)

# Q3 — THE SCOPED QUESTION. Deliberately weaker than the unsound one.
ok &= run(
    "Q3  Transfers ENGAGING Art 46 that rely on NO LISTED 46(2) INSTRUMENT",
    "SCOPED ON PURPOSE. This does NOT say 'no appropriate safeguard exists'. 46(3) is\n"
    "        non-exhaustive ('in particular'), so an unlisted instrument may still qualify,\n"
    "        and 46(1) condition (ii) is a further independent requirement not modelled here.\n"
    "        The sound claim stops at the closed 46(2) list — see Q4 for the 46(3) residue.",
    """
    SELECT ?transfer ?no_listed_46_2_mechanism
    WHERE {
      ?transfer exs:destinationHasAdequacyDecision false .
      BIND("no listed 46(2) instrument relied on - NOT a finding of no safeguard" AS ?no_listed_46_2_mechanism)
      FILTER NOT EXISTS {
        ?transfer exs:reliesOnMechanism ?m .
        ?m gdprkg:groundedIn ?p .
        ?p rdfs:label ?pl .
        FILTER(CONTAINS(STR(?pl), "Article 46(2)"))
      }
    }
    ORDER BY ?transfer
    """, 2)

# Q4 — the 46(3) route, which is exactly where the closed-world inference fails.
ok &= run(
    "Q4  Transfers relying on a 46(3) instrument (AUTHORISATION REQUIRED; 46(4) duty bites)",
    "46(3) is the NON-EXHAUSTIVE list. A transfer appearing in Q3 but here is precisely the\n"
    "        case that shows why Q3 must not be read as 'no safeguard': T4 relies on a real\n"
    "        instrument, and 46(3)'s list could not have excluded an unlisted one either way.",
    """
    SELECT ?transfer ?mechanism ?authorisation
    WHERE {
      ?transfer exs:reliesOnMechanism ?mechanism .
      ?mechanism gdprkg:groundedIn ?point .
      ?point rdfs:label ?plabel .
      FILTER(CONTAINS(STR(?plabel), "Article 46(3)"))
      BIND("supervisory-authority authorisation required; Art 46(4) consistency mechanism applies" AS ?authorisation)
    }
    ORDER BY ?transfer
    """, 1)

print(BANNER)
print("  THE POINT: Q1 and Q2/Q3/Q4 return DIFFERENT transfers. The same graph, the")
print("  same queries, different facts about the world => different applicability")
print("  answers, each traceable back to a real Article-46 Point.")
print()
print("  THE LIMIT, restated so it is not lost: this exercises the gate over FOUR")
print("  HYPOTHETICAL transfers. It is a demonstrator, not the evaluation phase, and")
print("  it is NOT evidence that the gate is correct over real policy data.")
print()
print("  T3 appears in Q3 and NOT in Q4; T4 appears in BOTH. That is not a bug — it")
print("  is the closed-world limit made visible: Q3's scoped claim is true of T4 as")
print("  well, and only Q4 shows why that claim must not be strengthened.")
print(BANNER)
sys.exit(0 if ok else 1)
