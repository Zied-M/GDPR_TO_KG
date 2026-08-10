# Article-13 competency-question SPARQL suite

One `.rq` per **answerable** Article-13 competency question, plus notes on the
CQs the single-article graph cannot yet answer. Queries run over
`../articles/art13.ttl` (+ the TBox `../ontology/gdpr_kg.ttl` for class closure).

Expected per-CQ answers are recorded in **`expected_results.md`** (added I2, 2026-07-08);
a CQ only functions as a test with an expected answer [gruninger1995methodology].

**2026-07-12 update (SURFACE-C resolution — see `expected_results.md`):** CQ-C5 cross-article
(`CQ-C5x_cross_article_basis.rq`) now has a **dual path**: the original **Point-join** (norm
`referencesProvision` → Art-6 Point ← `groundedIn` basis; needs the materialised regime) and the
direct one-hop **`gdprkg:reliesOnLegalBasis`** edge (plain regime; 2 edges in `art13.ttl`). Both
paths MUST return the identical 2 rows — a grounding-path agreement/integrity check. The frozen
`.rq` file keeps the Point-join form; the direct-edge expectation is documented in
`expected_results.md` (2026-07-12 entry).

## Evaluation regime (the CQ evaluation protocol) — read before running

**Adopted regime: OWL 2 RL materialisation** [w3c2013sparqlentailment; w3c2012owl2].
The Art-13 ABox asserts only each node's DIRECT type (e.g. `a gdprkg:Obligation`); it does
NOT assert the inferred super-types (`gdprkg:GroundedConcept`, `gdprkg:NormativeElement`, …).
So any query that matches an inferred type (notably **CQ-C2**, `?n a gdprkg:GroundedConcept`)
returns the correct answer only after the type closure is made explicit. The protocol:

1. Load `../ontology/gdpr_kg.ttl` (TBox) **and** `../articles/art13.ttl` (ABox) into one graph.
2. Compute the **OWL 2 RL** closure over that graph (e.g. the `owlrl` library's RL semantics),
   materialising inferred `rdf:type` (and `owl:inverseOf` etc.) triples.
3. Run each `.rq` over the **materialised** graph.

Queries needing the closure are marked **(needs materialisation)** in `expected_results.md`;
the others are correct on a plain graph. `CQ-C2` additionally ships a **closure-free fallback**
(in the file) that only needs the TBox subclass axioms loaded, for runners without a materialiser.
The dev-time `cq_eval.py` is a dependency-free PROXY that does subclass closure in Python — it is
NOT the authoritative regime; the authoritative run is `owlrl`/rdflib on a networked machine.

## Answerable (query returns the expected answer over art13.ttl)

| File | CQ | Expected result |
|---|---|---|
| `CQ-A1_art13_coverage.rq` | CQ-A1 | 21 Obligations, all grounded; per-point split 13(1)(a)=2, 13(1)(c)=2, 13(1)(f)=2, 13(2)(b)=6, rest=1, 13(3)@Paragraph. |
| `CQ-A3_conditional_duties.rq` | CQ-A3 | all 21 obligations conditional (>=1 Condition each). |
| `CQ-A4_art13_exemption.rq` | CQ-A4 | one Exception grounded in 13(4), attached to 21 obligations. |
| `CQ-A7a_substantive_right_nodes.rq` | CQ-A7 (part a) | 0 substantive Right nodes. **T2 (2026-07-09): split into its own single-query file.** |
| `CQ-A7b_rights_information_obligations.rq` | CQ-A7 (part b) | 6 rights-information Obligations grounded in `art13-p2-b`. **T2: split into its own single-query file.** |
| `CQ-C1_article_to_norms_grounded.rq` | CQ-C1 | 33 grounded normative nodes (21 Obl + 11 Cond + 1 Exc). **Fixed I2: replaced the Cartesian-inflating body with the faithful `groundedIn` form.** |
| `CQ-C2_uniform_grounding.rq` | CQ-C2 | 0 rows (no GroundedConcept lacks groundedIn). **(needs materialisation** — or the in-file closure-free fallback).** |
| `CQ-C3_bearer.rq` | CQ-C3 | 21 obligations, bearer = controller; 0 orphans. |
| `CQ-C4_referenced_actor.rq` | CQ-C4 | **3 obligations → typed referenced actor** (representative/DPO/supervisory-authority), distinct from the controller bearer. **UNBLOCKED 2026-07-03 via `gdprkg:referencesActor` (S5).** |
| `CQ-C5_domain_concept.rq` | CQ-C5 (within-article) | **5 obligations → disclosed domain concept** (Purpose/Recipient/Transfer/Safeguard/RetentionPeriod). Obligation-side traversal **UNBLOCKED 2026-07-03 via `gdprkg:disclosesConcept` (S7).** Cross-article aggregation still pending Art 14/6/7. |
| `CQ-C6_provenance_review.rq` | CQ-C6 | 21 "direct" (Obligations) + "inherited" rows for each Condition/Exception resolved via its parent. **Fixed I2: added the inherited-via-parent UNION so it answers for ANY node, not just primary units.** |
| `CQ-C7_temporal.rq` | CQ-C7 | temporal triggers reachable: 9 / 11 / 1 obligations. |

Also demonstrated: **`gdprkg:referencesProvision`** now wires **8** cross-reference edges from Art 13
(UPDATED 2026-07-10, Art-6 pass): 5 to out-of-scope stubs (Art 46/47/49, Art 9(2)(a), Art 22) **+ 3
in-scope Art-6 refs now wired** (`cond-13-1-d → art6-p1-f`, `cond-13-2-c → art6-p1-a`,
`obl-art13-1-c → art6`) — closing the S6 in-scope follow-up.

## Article 6 queries (added 2026-07-10)

Article 6 is a set of **lawful bases**, not disclosure obligations (primary unit = `gdprkg:LegalBasis`).
The now-answerable theme-B / cross-article CQs each have a `.rq` here; expected rows in
`expected_results.md` (Article-6 section). Dev-time proxy: **`cq_eval_art6.py`** (loads `art6.ttl` +
`art13.ttl` + the hierarchy extract; the Art-13-only `cq_eval.py` is unchanged).

| File | CQ | Expected |
|---|---|---|
| `CQ-B1_lawful_bases.rq` | CQ-B1 | 6 LegalBasis nodes, each grounded in its 6(1) Point. |
| `CQ-B2_basis_conditions.rq` | CQ-B2 | 3 basis→Condition links (LI balancing; (c)&(e) 6(3)). |
| `CQ-B3_basis_in_union_or_ms_law.rq` | CQ-B3 | 2 bases require Union/MS law ((c), (e)). |
| `CQ-B4_li_public_authority_exclusion.rq` | CQ-B4 | 1: LI basis → public-authority Exception. |
| `CQ-C5x_cross_article_basis.rq` | CQ-C5 (cross-article) | 2: consent basis ← cond-13-2-c; LI basis ← cond-13-1-d. |

`CQ-B1/B2/B3` and `CQ-C5x` need the OWL 2 RL closure (`?b a gdprkg:LegalBasis` is an inferred
super-type of the asserted `a gdprkg:LegalBasisConsent` etc.). **CQ-B5 (6(4)) is deferred (SURFACE-B).**

## Flagged — still NOT answerable by the Art-13 graph alone (see report §CQ coverage)

- **CQ-A9** (Art 13 vs 14 diff): evaluation-level; needs the Art-14 graph. Deferred.
- **CQ-C5 cross-article facet**: the *within-article* traversal now works (see above), but the
  "same concept **across different articles**" aggregation needs Art 14/6/7 sharing the
  canonical domain nodes. Legitimately out this session.
- **CQ-C8** (source coverage): evaluation-level procedure over `source_units`; see report.

## Running

Authoritative (local, networked environment) — **OWL 2 RL materialised** per the regime above:
```
pip install rdflib owlrl
python - <<'PY'
import rdflib, owlrl
g = rdflib.Graph()
g.parse("../ontology/gdpr_kg.ttl", format="turtle")
g.parse("../articles/art13.ttl", format="turtle")
# materialise the OWL 2 RL closure so inferred rdf:type triples become explicit
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
for f in ["CQ-C1_article_to_norms_grounded.rq", "CQ-C2_uniform_grounding.rq",
          "CQ-C6_provenance_review.rq"]:
    print("===", f, "===")
    for row in g.query(open(f).read()):
        print(row)
PY
```
Check each result against `expected_results.md`. CQ-A7 is now two single-query files —
`CQ-A7a_substantive_right_nodes.rq` (0) and `CQ-A7b_rights_information_obligations.rq` (6).
`CQ-C2` also has a closure-free fallback (in-file) if no materialiser is available.

Dev-time (no network this session): `cq_eval.py` reuses the Phase-4 Turtle parser to
evaluate each pattern and print the actual rows/counts. It is a PROXY; the `.rq` files are
the authoritative artifacts.
