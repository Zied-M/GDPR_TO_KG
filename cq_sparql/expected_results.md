# CQ expected-result fixtures — Article 13 (`articles/art13.ttl`)

**Added 2026-07-08 (I2 remediation).** A competency question functions as a *test* only if it
has an expected answer to measure against; the evaluation correctly flagged these were absent.
Grounding: Grüninger & Fox [gruninger1995methodology] (CQs as a requirements/evaluation device).

**Evaluation regime.** Row counts below assume the CQ evaluation protocol in
`cq_sparql/README.md`: compute the **OWL 2 RL** materialised closure over
`../ontology/gdpr_kg.ttl` + `../articles/art13.ttl`, then run the `.rq` over the materialised
graph [w3c2013sparqlentailment; w3c2012owl2]. Queries that need the closure are marked
**(needs materialisation)**; the rest are correct on a plain graph. These are **expected**
values for Zied's local `owlrl`/rdflib run to reproduce — the in-sandbox `cq_eval.py` is a
dependency-free proxy, not authoritative.

| CQ | Query file | Expected result | Regime |
|---|---|---|---|
| **CQ-A1** | `CQ-A1_art13_coverage.rq` | 21 Obligations, all grounded; per-point split 13(1)(a)=2, 13(1)(c)=2, 13(1)(f)=2, 13(2)(b)=6, others=1, 13(3)@Paragraph. | plain |
| **CQ-A3** | `CQ-A3_conditional_duties.rq` | 21/21 Obligations conditional (≥1 Condition each). | plain |
| **CQ-A4** | `CQ-A4_art13_exemption.rq` | 1 Exception, grounded 13(4), attached to 21 Obligations. | plain |
| **CQ-A7a** | `CQ-A7a_substantive_right_nodes.rq` | **0** substantive Right nodes. | plain |
| **CQ-A7b** | `CQ-A7b_rights_information_obligations.rq` | **6** Obligations grounded in `art13-p2-b`. | plain |
| **CQ-C1** | `CQ-C1_article_to_norms_grounded.rq` | **33** rows (21 Obligation + 11 Condition + 1 Exception), each grounded. | plain |
| **CQ-C2** | `CQ-C2_uniform_grounding.rq` | **0** rows (no GroundedConcept lacks `groundedIn`). | **needs materialisation** (or the closure-free fallback in the file) |
| **CQ-C3** | `CQ-C3_bearer.rq` | 21 Obligations → bearer `actor-controller`; 0 orphans. | plain |
| **CQ-C4** | `CQ-C4_referenced_actor.rq` | **3** Obligations → typed referenced actor (representative / DPO / supervisory-authority). | plain |
| **CQ-C5** | `CQ-C5_domain_concept.rq` | **5** Obligations → disclosed concept: Purpose, Recipient, Transfer, Safeguard, RetentionPeriod (I1: now the `ex:concept-*` canonical nodes). Cross-article facet pending Art 14/6/7. | plain |
| **CQ-C6** | `CQ-C6_provenance_review.rq` | **21 "direct"** rows (one per Obligation) **+ "inherited"** rows for each Condition/Exception resolved via each parent (the single 13(4) Exception → 21 inherited rows; each Condition via the Obligations whose `appliesIf` reaches it). Every grounded node's provenance is resolvable. | plain |
| **CQ-C7** | `CQ-C7_temporal.rq` | Temporal triggers reachable: 9 / 11 / 1 Obligations (the 3 temporal Conditions). | plain |

## Not answerable by the Art-13 graph alone (legitimate phase deferrals)

| CQ | Why deferred |
|---|---|
| **CQ-A9** (Art 13 vs 14 diff) | evaluation-level; needs the Art-14 graph. |
| **CQ-C5 cross-article facet** | "same concept across articles" needs Art 14/6/7 sharing the canonical `ex:concept-*` nodes (I1 makes this possible; not exercised until they are instantiated). |
| **CQ-C8** (source coverage) | evaluation-level coverage procedure over `source_units`. |

## Additional demonstrated edges (not CQs, but fixtures for regression)

| Edge | Expected over art13.ttl |
|---|---|
| `gdprkg:referencesProvision` | **8** edges (UPDATED 2026-07-10, Art-6 pass): **5** to out-of-scope stubs (Art 46/47/49, Art 9(2)(a), Art 22) **+ 3 in-scope Art-6 refs now WIRED** — `cond-13-1-d-based-on-li → ex:art6-p1-f`, `cond-13-2-c-consent-basis → ex:art6-p1-a`, `obl-art13-1-c-legal-basis → ex:art6`. (Art-6 targets are defined in `art6.ttl`; in an art13-only run they appear as bare IRIs.) Closes the S6 in-scope follow-up. |
| `gdprkg:disclosedToDataSubject` (I5) | **21** edges (one per Obligation → `ex:actor-data-subject`). |
| `gdprkg:transferredTo` (I6) | **1** edge: `ex:concept-transfer → ex:concept-third-country` (a `TransferDestination`, NOT the recipient). |
| `gdprkg:reliesOnLegalBasis` (SURFACE-C resolution, 2026-07-12) | **2** edges: `cond-13-1-d-based-on-li → ex:basis-legitimate-interests`, `cond-13-2-c-consent-basis → ex:basis-consent`. Direct condition→basis traceability ALONGSIDE the kept referencesProvision→Point edges. Targets live in `art6.ttl` — meaningful only under the COMBINED 3-file load; in an art13-only run they appear as bare IRIs. `obl-art13-1-c-legal-basis` deliberately has NO such edge (SURFACE-A). |

---

# CQ expected-result fixtures — Article 6 (`articles/art6.ttl`)

**Added 2026-07-10 (Article-6 instantiation pass).** Article 6 is a set of **lawful bases**, not
disclosure obligations: the primary normative unit is `gdprkg:LegalBasis`. Six canonical, DPV-GDPR-
aligned (`eugdpr:A6-1-a…f`), GDPRtEXT-grounded basis nodes, each with provenance + `reviewStatus="draft"`.

**Evaluation regime.** Same as Art 13: OWL 2 RL materialised closure over
`../ontology/gdpr_kg.ttl` + `../articles/art6.ttl` (+ `../articles/art13.ttl` for the cross-article
row), then run the `.rq` [w3c2013sparqlentailment; w3c2012owl2]. Queries matching an inferred super-type
(`?b a gdprkg:LegalBasis`, since the ABox asserts the specific subclass `a gdprkg:LegalBasisConsent`
etc.) are marked **(needs materialisation)**. Proxy reproduction: `cq_sparql/cq_eval_art6.py`.

| CQ | Query file | Expected result | Regime |
|---|---|---|---|
| **CQ-B1** | `CQ-B1_lawful_bases.rq` | **6** LegalBasis nodes, each grounded in its 6(1) Point (a→art6-p1-a … f→art6-p1-f). | **needs materialisation** |
| **CQ-B2** | `CQ-B2_basis_conditions.rq` | **3** basis→Condition links: LI→`cond-6-1-f-balancing` (@art6-p1-f); legal-obligation & public-task → `cond-6-3-basis-in-union-or-ms-law` (@art6-p3). (Per-basis "necessity" wording not separately modelled — see report.) | **needs materialisation** |
| **CQ-B3** | `CQ-B3_basis_in_union_or_ms_law.rq` | **2** bases require Union/MS law: `basis-legal-obligation` (6(1)(c)) + `basis-public-task` (6(1)(e)), via the 6(3) condition → `ex:ref-union-ms-law` stub. | **needs materialisation** |
| **CQ-B4** | `CQ-B4_li_public_authority_exclusion.rq` | **1** row: `basis-legitimate-interests → exc-6-1-f-public-authority` grounded in `art6-p1-final`. | plain |
| **CQ-B5** | (deferred) | 6(4) further-processing compatibility test + factors (a)–(e) — **DEFERRED this pass (SURFACE-B)**; not answerable. | — |
| **CQ-C1** (Art 6) | `CQ-C1_article_to_norms_grounded.rq` | Art-6 contributes **9** grounded normative nodes (6 LegalBasis + 2 Condition + 1 Exception), 0 ungrounded. | plain |
| **CQ-C2** (Art 6) | `CQ-C2_uniform_grounding.rq` | **0** LegalBasis lacking `groundedIn` → the uniform-grounding invariant holds for **LegalBasis for the first time** (the headline Sprint 1-R fix, previously un-exercised — Art-13 S9). | **needs materialisation** |
| **CQ-C5** (cross-article) | `CQ-C5x_cross_article_basis.rq` | **2** rows: `basis-consent @ art6-p1-a ← cond-13-2-c-consent-basis`; `basis-legitimate-interests @ art6-p1-f ← cond-13-1-d-based-on-li`. The **consent basis shared across Art 6 and Art 13** — the integration payload. **UPDATE 2026-07-12 (SURFACE-C resolution):** the SAME 2 rows are now ALSO reachable via the direct one-hop `gdprkg:reliesOnLegalBasis` edges (no Point-join needed; `?norm gdprkg:reliesOnLegalBasis ?basis` suffices, plain regime). The Point-join query stays as-is (frozen-set operationalisation, and it independently validates the grounding-path agreement: both paths must return identical rows — a useful integrity check). | **needs materialisation** (Point-join) / plain (direct edge) |
| **CQ-C6** (Art 6) | `CQ-C6_provenance_review.rq` | 6 bases, each with provenance + `reviewStatus="draft"` (0 missing) → provenance/review exercised on **LegalBasis for the first time**. | plain |

## Not answerable by the Art-6 graph this pass (legitimate deferrals)

| CQ | Why deferred |
|---|---|
| **CQ-B5** (6(4) compatibility test) | 6(4) + factors (a)–(e) deferred with I9 (SURFACE-B); new construct (a test/duty), cross-refs Art 9/10/23. |
| **CQ-C3** (bearer/holder) | Art 6 creates no Obligation/Right this pass, so no bearer/holder edges (bases are not duties). |
| **CQ-C7** (temporal) | Art 6 has no temporal-trigger obligations this pass (6(4) deferred). |
| **CQ-B6…B10** (Art 7) | Article 7, not this pass. |

## Additional demonstrated edges (Art 6)

| Edge | Expected over art6.ttl |
|---|---|
| DPV-GDPR alignment | each of the 6 bases asserts `a eugdpr:A6-1-x` (explicit) **and** is typed with its `gdprkg:LegalBasis<X>` subclass (≡ that DPV-GDPR class). |
| `gdprkg:referencesProvision` (Art 6) | **1** edge: `cond-6-3-basis-in-union-or-ms-law → ex:ref-union-ms-law` (external Union/MS-law stub, SURFACE-E). |

---

# CQ expected-result fixtures — Article 12 (`articles/art12.ttl`)

**Added 2026-07-20 (Article-12 instantiation pass, brief v2.1 §7).** Article 12 is a **modalities**
article: 13 controller-borne Obligations + **6 `gdprkg:Permission` nodes** (the class minted this pass,
12A) with `gdprkg:grantsPermissionTo ex:actor-controller` (property minted this pass, 12I), 9 Conditions
(2 shared), 2 Exceptions, and the **first ABox use of `gdprkg:hasTimeLimit`**. All counts below were
verified against the combined 4-file load (`gdpr_kg.ttl` + `art13.ttl` + `art6.ttl` + `art12.ttl`) with
rdflib/owlrl in-sandbox — **PROVISIONAL proxies; Zied's local run is authoritative.**

**Evaluation regime.** Same as Art 13/6: OWL 2 RL materialised closure, then run the `.rq`
[w3c2013sparqlentailment; w3c2012owl2]. Plain-regime queries are correct on the un-materialised graph.

| CQ | Query file | Expected result | Regime |
|---|---|---|---|
| **CQ-C1** (Art 12) | `CQ-C1_article_to_norms_grounded.rq` | Art-12 contributes **24** rows (13 Obligation + 9 Condition + 2 Exception), each grounded. Combined 4-file total: **60** rows. **RECORDED NON-COVERAGE #1:** the frozen question asks for "obligations, rights, conditions, and exceptions" and the query FILTERs `?normType IN (Obligation, Condition, Exception)` — the **6 Permissions are OUTSIDE the frozen wording and are deliberately NOT returned**. Do NOT stretch the query; Permission grounding is machine-checked via CQ-C2 instead. | plain |
| **CQ-C2** (Art 12) | `CQ-C2_uniform_grounding.rq` | **0** rows — extends to all 30 new Art-12 GroundedConcept nodes, **including the 6 Permission instances** (Permission ⊑ PrimaryNormativeUnit ⊑ GroundedConcept), which are exercised by CQ-C2 for the first time. Verified 0 over the materialised 4-file closure. | **needs materialisation** |
| **CQ-C3** (Art 12) | `CQ-C3_bearer.rq` | **+13** rows (all 13 Art-12 Obligations → `ex:actor-controller`); combined total **34**. **RECORDED NON-COVERAGE #2 (SURFACE-12I resolved):** CQ-C3's frozen wording ("obligation…right…") does **not** cover permission bearers; the bearer fact is nonetheless explicit via `gdprkg:grantsPermissionTo` (see fixture below) and ad-hoc queryable. Do NOT edit the query; validating shape → I4/I7 batch. | plain |
| **CQ-C4** (Art 12) | `CQ-C4_referenced_actor.rq` | **+1** row: `obl-12-4-complaint → ex:actor-supervisory-authority` (`Actor_SupervisoryAuthority`). Combined total **4**. | plain |
| **CQ-C5 / CQ-C5x** | `CQ-C5_domain_concept.rq` / `CQ-C5x_cross_article_basis.rq` | **ZERO delta — asserted explicitly:** Art 12 is NOT a disclosure article (12G); it carries **0 `disclosesConcept`** and **0 `disclosedToDataSubject`** edges. CQ-C5 stays **5** rows; CQ-C5x stays **2** rows over the combined load. **A nonzero delta on either is a DEFECT of the Art-12 data.** Verified: 5 / 2. | plain / per C5x note |
| **CQ-C6** (Art 12) | `CQ-C6_provenance_review.rq` | **+19 "direct"** rows (13 Obligations + 6 Permissions, each with `hasProvenance ex:prov-art12` + `reviewStatus "draft"`) → combined direct total **46** (21 art13 + 6 art6 + 19 art12). **+14 "inherited"** rows from the actual Art-12 Condition/Exception attachment count (12 `appliesIf` in-edges: 1 no-refusal + 1 notify-extension + 1 electronic + 3 shared no-action + 1 machine-readable + 1 oral + 1 extend + 2 shared unfounded/excessive + 1 verify; plus 2 `hasException` in-edges) → combined inherited total **68** (50 art13 + 4 art6 + 14 art12). Provenance/review exercised on **Permission for the first time** (ProvenanceRequiredShape/ReviewStatusShape target PrimaryNormativeUnit → enforce on Permission automatically; NO shape edit made). | plain |
| **CQ-C7** (Art 12) | `CQ-C7_temporal.rq` | The frozen query (label-substring filter "at the time"/"prior to" on `appliesIf` Conditions) contributes **0** Art-12 rows — Art-12 timing is FIXED-deadline, not event-trigger-labelled. The temporal representation the CQ asks about IS present as the **first nonzero `gdprkg:hasTimeLimit` rows** (design-spike outcome: fixed deadlines = datatype property), **5 rows**, listed in the fixture table below. Combined frozen-query total stays **21** (all art13). | plain |

## Not answerable by the Art-12 graph (legitimate deferrals / non-coverages)

| CQ | Why |
|---|---|
| **CQ-C1 on Permissions** | Recorded non-coverage #1 (frozen wording/FILTER) — see the CQ-C1 row above. |
| **CQ-C3 on Permissions** | Recorded non-coverage #2 (frozen wording) — bearer fact explicit via `grantsPermissionTo`; see the CQ-C3 row above. |
| **CQ-A9 / CQ-C8** | evaluation-level, unchanged. |

## Additional demonstrated edges (Art 12; fixtures for regression)

| Edge | Expected over art12.ttl |
|---|---|
| `gdprkg:hasTimeLimit` (FIRST ABox use) | **5** rows: `obl-12-3-respond`, `obl-12-3-notify-extension` → `"within one month of receipt of the request"`; `obl-12-4-reasons`, `obl-12-4-complaint`, `obl-12-4-remedy` → `"without delay and at the latest within one month of receipt of the request"` (shared string ×3 nodes). |
| `gdprkg:grantsPermissionTo` (FIRST use, 12I) | **6** edges — every Permission → `ex:actor-controller`. |
| `gdprkg:referencesProvision` (Art 12) | **49** edges: obl-12-1-form → `ex:art13` + 10 stubs (14, 15–22, 34); obl-12-2-facilitate → 8 stubs (15–22); cond-12-2-art11-2-case → `ex:ref-art11`; obl-12-3-respond → 8 stubs (15–22); obl-12-5-free → `ex:art13` + 10 stubs (14, 15–22, 34); perm-12-6-verify → 7 stubs (15–21, per-article reuse) + `ex:ref-art11`; perm-12-7-icons → `ex:art13` + `ex:ref-art14`. |
| `ReferencedProvision` stubs | **11 new** (`ex:ref-art11`, `-art14`, `-art15`…`-art21`, `-art34`, `-art92`); **`ex:ref-art22` REUSED from art13.ttl** (zero duplicate stubs). `ex:ref-art92` is edge-free by design (12F: no 12(8) normative unit; `referencesProvision` domain forbids a Paragraph subject) — reachable via `rdfs:seeAlso` from `ex:art12-p8` only. |
| Forbidden edges (12G / §6) | **0** `disclosedToDataSubject`, **0** `disclosesConcept`, **0** `notApplicableIf`, **0** `hasLegalEffect` on any Art-12 node. Verified 0/0/0/0. |
| `ex:ref-art14` stub | **REWIRED AWAY 2026-08-05** (Art-14 pass, work order C §3.2). Art 14 is now in scope, so the three edges that carried `ex:ref-art14` (`obl-12-1-form`, `obl-12-5-free`, `perm-12-7-icons`) now carry **`ex:art14`**, exactly parallel to the `ex:art13` edge each already had, and the stub declaration was deleted (art13→art6 precedent). Art-12 stub count is therefore **10 new**, not 11. `gdprkg:referencesProvision` on Art-12 subjects is **unchanged at 49** (targets moved, no edge added or removed). Expected occurrences of `ex:ref-art14` across the 5-file union: **0**. |

---

# CQ expected-result fixtures — Article 14 (`articles/art14.ttl`)

**Added 2026-08-05 (Article-14 instantiation pass, work order C §3.5 / brief v3.1 §6).**

> ### ⚠ PREDICTION PROVENANCE — read this before reading any number below
>
> **Every value in this section was written BEFORE `run_owlrl_art14.py` was executed for the
> first time, and before any SPARQL, SHACL, or reasoner run was made against `art14.ttl`.**
> That is the whole point (playbook §4.2): a prediction that can be edited after seeing the
> result is not evidence of anything. The predictions are split into two tiers per brief §6.0:
>
> - **TIER 1 — locked by the orchestrator in brief §6.1, restated here VERBATIM, not re-derived
>   and not the executor's to revise.** If the run disagrees with a Tier-1 value, that is a
>   **FINDING reported beside the original prediction**, never a number that gets changed.
> - **TIER 2 — derived and locked by the executor here, pre-run**, because they depend on
>   node-sharing choices the executor legitimately makes (how many Condition nodes, how the
>   four Exceptions attach, which labels the 14(3) triggers carry).
>
> Any deviation observed at run time is recorded in this file as an amendment note that
> **keeps the original prediction visible permanently**, and is reported as a finding in
> `../../gdpr-kg-monitoring/agents/2026-08-05_workorder_C.md`. Nothing is silently reconciled.

Article 14 is the **disclosure sibling of Article 13**: 24 controller-borne point-level
Obligations, 12 Conditions, and **4 node-shared Exception nodes** (one per 14(5) ground), plus
the **second** ABox use of `gdprkg:hasTimeLimit` and the **first** exercise of
`gdprkg:Actor_PersonalDataSource` and `gdprkg:DataCategory`. It is also the first time the
canonical `ex:concept-*` domain nodes are **shared by a second disclosure article** — the
"not yet demonstrated" item in playbook §7.

**Evaluation regime.** Same as Arts 13/6/12: OWL 2 RL materialised closure over the **5-file
union** (`../ontology/gdpr_kg.ttl` + `art13.ttl` + `art6.ttl` + `art12.ttl` + `art14.ttl`), then
run the `.rq` [w3c2013sparqlentailment; w3c2012owl2]. `CQ-C4` and `CQ-C5` are evaluated on the
**PLAIN** graph, per the regime note already established by `run_owlrl_art12.py` (materialisation
inflates their un-restricted `?actorType`/`?conceptType` projections via inferred super-types
without changing the distinct answer set). Runner: `cq_sparql/run_owlrl_art14.py`.

## TIER 1 — locked in brief §6.1; restated verbatim, NOT re-derived

| CQ / fixture | Locked value | Brief §6.1 derivation (verbatim) |
|---|---|---|
| **CQ-C2** (uniform grounding) | **0** | Standing invariant: no `GroundedConcept` lacking `groundedIn`. Unconditional, every unit. |
| **CQ-C3** (obligation → bearer) | **58** | Current 4-file union = 34 (21 art13 + 13 art12 + 0 art6). `shapes.ttl:171–174` makes `imposesObligationOn` `sh:minCount 1` on every `Obligation`, and every certified obligation to date has exactly one bearer (`ex:actor-controller`). 34 + 24 = 58. A value other than 58 means either a missing bearer (SHACL would fail first) or a multi-bearer obligation — report as a finding. |
| **CQ-C6 direct** (primary units with provenance + review) | **70** | Current direct = 46 (21 art13 + 6 art6 + 19 art12). Art-14's primary units are its 24 obligations. 46 + 24 = 70. |
| **Art-14 obligation count** | **24** | §2.6. Fixed. |
| **Art-14 Exception nodes** | **4** | §2.7 + T3-D decided: one node per 14(5) ground (a)–(d), node-shared across bearers, Art-13 pattern. |
| **Regression — CQ-B1 / B2 / B3 / B4** | **6 / 3 / 2 / 1** | Art-6 values; Art 14 adds no `LegalBasis`. Any change is a regression finding. |
| **Regression — art13 / art6 / art12 pySHACL** | **`Conforms: True`** ×3 | No certified file is edited by this unit. |
| **`owl:Nothing` members** | **0** | Standing. |
| **Dangling `ex:` IRIs** | **0** | Standing; enforced by the orphan check after the `ex:ref-art14` rewire. |

> **Executor note on the last regression row.** `art12.ttl` **IS** edited by this unit — the single
> authorized `ex:ref-art14` rewire (work order §2/§3.2). Brief §6.1's parenthetical "No certified
> file is edited by this unit" is therefore inexact as written; the *prediction* (`Conforms: True`
> for art12) is unaffected, since the rewire only repoints three `referencesProvision` objects and
> deletes a stub declaration, and no shape constrains that property. **Flagged, not resolved** —
> the discrepancy is between the brief's justification text and the work order's own §3.2
> instruction, and the brief wins on substance (the value stays `Conforms: True`).

## TIER 2 — derived and locked by the executor, PRE-RUN

| CQ | Query file | Predicted result (5-file union) | Regime |
|---|---|---|---|
| **CQ-C1** | `CQ-C1_article_to_norms_grounded.rq` | Art-14 contributes **40** rows = 24 Obligation + **12 Condition** + 4 Exception, each grounded. Combined 5-file total **100** (60 + 40). The Condition count 12 is the executor-chosen structure brief §6.2 leaves open: 5 "where applicable"/qualifier conditions from 14(1), 3 from 14(2) (the 6(1)(f) basis, the 6(1)(a)/9(2)(a) basis, the 14(2)(f) "if applicable" clause), 2 event-trigger timing conditions from 14(3)(b)/(c), 2 from 14(4). **The 6 Permissions stay excluded by the frozen FILTER** (recorded non-coverage #1, unchanged from Art 12). | materialised |
| **CQ-C2** | `CQ-C2_uniform_grounding.rq` | **0** — Tier-1. Extends to all 40 new Art-14 `GroundedConcept` nodes. The three mints are deliberately **outside** `GroundedConcept` (`ex:concept-data-category` is a `DataCategory`, `ex:actor-personal-data-source` an `Actor`, `ex:ref-art89` a `ReferencedProvision`), so none of them can contribute a row — the Art-13 SURFACE-1 discipline. | materialised |
| **CQ-C3** | `CQ-C3_bearer.rq` | **58** — Tier-1. +24, all → `ex:actor-controller`. | materialised |
| **CQ-C4** | `CQ-C4_referenced_actor.rq` | **9** (current 4, **+5**). Art-14 rows: `obl-art14-1-a-representative-identity` → `actor-controller-representative`; `obl-art14-1-b-dpo-contact` → `actor-dpo`; `obl-art14-2-e-lodge-complaint` → `actor-supervisory-authority`; **`obl-art14-2-f-source` AND `obl-art14-2-f-publicly-accessible` → `ex:actor-personal-data-source`** (`gdprkg:Actor_PersonalDataSource`). **BOTH halves of the T3-E(i) 2(f) split carry the edge** — both clauses are about the source (the second qualifies its *character*). That is an executor judgement call: a reading that gave the edge only to the primary-disclosure half would make this **8**, not 9. Flagged, implemented as 9. This is the **first non-Art-13 referenced-actor TYPE** in the graph and the first exercise of a TBox class declared in Phase 3 and idle ever since. | **plain** |
| **CQ-C5** | `CQ-C5_domain_concept.rq` | **11** (current 5, **+6**). Art-14 rows: purposes→`concept-purpose`, **data-categories→`ex:concept-data-category` (NEW canonical node, T3-F)**, recipients→`concept-recipient`, transfer-fact→`concept-transfer`, transfer-safeguards→`concept-safeguard`, storage-period→`concept-retention`. **Five of the six are the SAME canonical nodes Art 13 already discloses** — the cross-article shared-domain-node claim, demonstrated for the first time. `ex:concept-data-category` is the sixth and is new. | **plain** |
| **CQ-C5x** | `CQ-C5x_cross_article_basis.rq` | **4** (current 2, **+2**): `basis-consent @ art6-p1-a ←` {`cond-13-2-c-consent-basis`, **`cond-14-2-d-consent-basis`**}; `basis-legitimate-interests @ art6-p1-f ←` {`cond-13-1-d-based-on-li`, **`cond-14-2-b-based-on-li`**}. The consent basis is now shared across **three** articles' worth of grounding (6, 13, 14). | materialised |
| **CQ-C6** | `CQ-C6_provenance_review.rq` | **70 direct** (Tier-1) **+ 214 inherited** = **284 total**. Inherited = one row per `appliesIf`/`hasException` in-edge landing on a Condition/Exception: 50 art13 + 4 art6 + 14 art12 + **146 art14**. The 146 = **54 `appliesIf`** (23 from P1 + 29 from P2 + 2 from 14(4); the two 14(3) triggers alone account for 44 of them, being node-shared across all 22 paragraph-1/2 duties) **+ 92 `hasException`** (23 obligations × the 4 node-shared 14(5) grounds). | materialised |
| **CQ-C7** | `CQ-C7_temporal.rq` | **44** (current 21, **+23**). ⚠ **THE TRAP, PREDICTED FROM THE LABELS AS WRITTEN — see the honesty note below.** Art-14 rows: `cond-14-3-b-first-communication` × its 22 obligations = 22; `cond-14-4-prior` × 1 = 1. **`cond-14-3-c-first-disclosure` contributes 0** — RECORDED NON-COVERAGE #3. | materialised |
| **CQ-A1** | `CQ-A1_art13_coverage.rq` | **58** over the union (21 art13 + 13 art12 + 24 art14; the query is not article-scoped). The Art-13 answer it was written for is **unchanged at 21**. Per-point Art-14 split: 14(1)(a)=2, 14(1)(c)=2, 14(1)(f)=2, 14(2)(c)=6, 14(2)(f)=2, others=1; 14(4) grounds at the Paragraph; 14(5)(b) grounds at the Point it shares with its exemption ground. | materialised |
| **CQ-A3** | `CQ-A3_conditional_duties.rq` | **90** = 29 art13 + 0 art6 (its `appliesIf` subjects are `LegalBasis`, not `Obligation`) + 7 art12 (the other 5 sit on Permissions) + **54 art14**. **23 of Art-14's 24 obligations are conditional**; the sole unconditional one is `obl-art14-5-b-protective-measures`. | materialised |
| **CQ-A4** | `CQ-A4_art13_exemption.rq` | **8** grouped rows (the query is not article-scoped): `exc-art13-4`→21, `exc-6-1-f-public-authority`→1, `exc-12-2-cannot-identify`→1, `exc-12-3-otherwise-requested`→1, and **each of the four Art-14 grounds→23**. The Art-13 answer it was written for is **unchanged at 21 attached obligations**. | materialised |
| **CQ-A5** *(newly operationalised)* | `CQ-A5_art14_exemptions.rq` | **92** = 4 Art-14 Exception nodes × the 23 paragraph-1-to-4 obligations each defeats. Answers the frozen CQ-A5 ("…which obligations does each of the four 14(5) exceptions defeat?") for the first time. | materialised |
| **CQ-A6** *(newly operationalised)* | `CQ-A6_art14_remaining_obligation.rq` | **1** row: `exc-art14-5-b-impossible-disproportionate` @ `ex:art14-p5-b` → `obl-art14-5-b-protective-measures`. This is the whole point of T3-C. **If it returns 0, that is a FINDING, not a reason to rewire** (brief §6.2). | materialised |
| **CQ-A8** *(newly operationalised)* | `CQ-A8_art14_timing.rq` | **66** = **22 fixed-deadline rows** (14(3)(a) → `gdprkg:hasTimeLimit` on each paragraph-1/2 duty) **+ 44 event-trigger rows** (22 duties × the two 14(3)(b)/(c) Conditions). Exercises both halves of the Phase-3 temporal design spike in one query, on one article, for the first time. | materialised |
| **CQ-B1 / B2 / B3 / B4** | `CQ-B*.rq` | **6 / 3 / 2 / 1** — Tier-1 regression, unchanged. Art 14 adds no `LegalBasis`. NB CQ-B3 is scoped to `ex:art6-p3`, so Art-14's **reuse** of `ex:ref-union-ms-law` on the 14(5)(c)/(d) Exceptions cannot leak into it. | materialised |

### On the three newly operationalised queries (CQ-A5 / CQ-A6 / CQ-A8)

These are **additional operationalisations of already-frozen competency questions**, not new
CQs. `methodology/competency_questions.json` is untouched: still 27 CQs, no question edited, no
`.rq` widened. CQ-A5, CQ-A6 and CQ-A8 are Art-14-specific questions that have had **no query
file** because no Art-14 graph existed; they become answerable for the first time with this
unit. **Precedent:** the Art-6 pass added `CQ-B1…B4_*.rq` and `CQ-C5x_*.rq` on exactly this
basis (2026-07-10), and `CQ-C5x_cross_article_basis.rq` states the rule in its own header —
*"This is an ADDITIONAL operationalisation of the FROZEN CQ-C5 (it does NOT add or edit a CQ)."*
This is a **T1 precedent-settled** call under playbook §4, reported not silent.

## Recorded non-coverages / expected-absence assertions (Article 14)

| # | What | Why, and where the fact IS verified |
|---|---|---|
| **#1** (inherited) | **CQ-C1 does not reach Permissions** | Unchanged from Art 12. Art 14 mints no Permission, so nothing new is lost. Grounding for all six is still machine-checked by CQ-C2. |
| **#2** (inherited) | **CQ-C3 does not reach permission bearers** | Unchanged from Art 12. Art 14 creates no Permission. |
| **#3 — NEW** | **CQ-C7 returns 0 rows for `cond-14-3-c-first-disclosure`**, although 14(3)(c) is unambiguously an event-triggered timing rule of exactly the kind CQ-C7 asks about. | The frozen query matches Condition labels **containing the literal substrings** `"at the time"` or `"prior to"`. 14(3)(b)'s source text says *"at the latest **at the time** of the first communication"* → its label matches. 14(3)(c)'s source text says *"at the latest **when** the personal data are first disclosed"* → its label does not. **This is a source-text wording asymmetry, not a modelling defect, and the label was NOT reworded to make the count land** (playbook §4.1 — this is the specific failure that rule exists to prevent; work order §3.5 named it in advance). The fact IS verified: the trigger is a first-class `gdprkg:Condition`, grounded in `ex:art14-p3-c`, reachable via `appliesIf` from all 22 duties, and returned by **CQ-A8** (44 event-trigger rows cover both (b) and (c)) and by **CQ-A3**. |
| **#4 — NEW** | **14(3)(a) has no normative unit grounded in it.** `ex:art14-p3-a` is a Point that no Obligation/Condition/Exception grounds into. | T3-B decided (a) is a **fixed deadline**, so its content lives as the `gdprkg:hasTimeLimit` legal string on the 22 duties it governs, not as a node. Precedent: Art-12 12F left `ex:art12-p8` with no normative unit. The fact IS verified by the `hasTimeLimit` fixture (22 rows carrying 14(3)(a)'s verbatim text) and by CQ-A8's fixed-deadline branch. |
| **#5 — NEW** | **CQ-A9 (Art 13 vs 14 structured diff) is still not delivered as a query.** | `competency_questions.json` flags CQ-A9 `eval_level: true` — it is an evaluation-level CQ, deferred by phase exactly as CQ-C8 is, not by this unit's scope. Both article graphs now exist, so it becomes *constructible*; building it is Phase-6 evaluation work, not instantiation work. Recorded so the availability is not silently lost. |
| **Absence** | **CQ-C5 / CQ-C5x may not DROP.** | Art 14 only adds; `CQ-C5 < 11` or `CQ-C5x < 4` would mean an Art-13/Art-6 edge was damaged. |
| **Absence** | **0 `gdprkg:notApplicableIf` and 0 `gdprkg:hasLegalEffect` on any Art-14 node.** | Carry `f2-domain-family` is **NOT triggered** (brief §5): nothing in Art 14 attaches a condition or legal effect to a `LegalBasis` — it cites Art-6 provisions and relies on bases via `reliesOnLegalBasis`, whose domain is `NormativeElement` and whose subjects here are Conditions. A nonzero count on either is a defect **and** a STOP (F2 first). |
| **Absence** | **0 `gdprkg:Permission` / `gdprkg:grantsPermissionTo` from Art 14**; the Art-12 counts stay **6 / 6**. | Art 14 confers no discretionary power. |
| **Absence** | **0 occurrences of `ex:ref-art14`** across the 5-file union. | The §3.2 rewire is complete only if the stub is gone everywhere. |

## Additional demonstrated edges (Article 14; fixtures for regression)

| Edge / fixture | Predicted over the 5-file union |
|---|---|
| Art-14 `gdprkg:Obligation` instances | **24** (P1:9, P2:13, P3:0, P4:1, P5:1) — Tier-1. |
| Art-14 `gdprkg:Condition` instances | **12** — Tier-2 (the number brief §6.2 leaves to the executor). |
| Art-14 `gdprkg:Exception` instances | **4** — Tier-1. |
| `gdprkg:hasTimeLimit` (2nd ABox use) | **22** Art-14 rows, all carrying 14(3)(a) verbatim: *"within a reasonable period after obtaining the personal data, but at the latest within one month, having regard to the specific circumstances in which the personal data are processed"* (one shared string × 22 nodes, the Art-12 `obl-12-4-*` pattern). **Combined total 27** (5 art12 + 22 art14). Deliberately **absent** from `obl-art14-4-further-processing-info` (14(3) governs paragraphs 1 and 2 only; 14(4) carries its own "prior to" trigger) and from `obl-art14-5-b-protective-measures`. |
| `gdprkg:appliesIf` on Art-14 subjects | **54**. |
| `gdprkg:hasException` on Art-14 subjects | **92** = 23 × 4. `obl-art14-5-b-protective-measures` carries **none** — it arises *because* ground (b) applies. |
| `gdprkg:disclosedToDataSubject` (I5) | **23** Art-14 edges → `ex:actor-data-subject`; **combined 44** (21 art13 + 23 art14). Deliberately **absent** from `obl-art14-5-b-protective-measures`, whose duty is to make information *publicly available*, not to disclose to the data subject. Art 14 **is** a disclosure article, unlike Art 12 (12G). |
| `gdprkg:disclosesConcept` | **6** Art-14 edges; **combined 11**. |
| `gdprkg:referencesActor` | **5** Art-14 edges; **combined 9**. |
| `gdprkg:referencesProvision` on Art-14 subjects | **11**: `obl-art14-1-c-legal-basis`→`ex:art6`; `cond-14-1-f-transfer-safeguarded`→`ref-art46`,`ref-art47`,`ref-art49`; `cond-14-2-b-based-on-li`→`ex:art6-p1-f`; `cond-14-2-d-consent-basis`→`ex:art6-p1-a`,`ref-art9-2-a`; `obl-art14-2-g-automated-decision`→`ref-art22`; `exc-art14-5-b`→`ref-art89`; `exc-art14-5-c`→`ref-union-ms-law`; `exc-art14-5-d`→`ref-union-ms-law`. |
| `gdprkg:referencesProvision` on Art-12 subjects | **49 — UNCHANGED** by the rewire (three objects moved from `ex:ref-art14` to `ex:art14`; no edge added or removed). Regression check on the one edited certified file. |
| `gdprkg:reliesOnLegalBasis` | **combined 4** (2 art13 + **2 art14**): `cond-14-2-b-based-on-li`→`ex:basis-legitimate-interests`, `cond-14-2-d-consent-basis`→`ex:basis-consent`. `obl-art14-1-c-legal-basis` deliberately has **none** (SURFACE-A discipline). |
| `ReferencedProvision` stubs | **1 new** (`ex:ref-art89`) — Art 89(1), cited by 14(5)(b), the only citation in Art 14's set with no existing stub. **Reused, not re-minted:** `ref-art46`, `ref-art47`, `ref-art49`, `ref-art9-2-a`, `ref-art22` (from `art13.ttl`) and `ref-union-ms-law` (from `art6.ttl`). **Zero duplicate stubs.** `ex:ref-art89` carries exactly **1** in-edge. |
| Canonical mints | **`ex:concept-data-category`** (`gdprkg:DataCategory`, which was already in `disclosesConcept`'s range → canonical-node mint, **NOT** a TBox change) and **`ex:actor-personal-data-source`** (`gdprkg:Actor_PersonalDataSource`, a Phase-3 class declared and idle until now). Both must infer their grouping supertype under the closure: `DataCategory ⊑ DisclosableConcept`, `Actor_PersonalDataSource ⊑ Actor`. |
| `ex:art14` in-edges from `art12.ttl` | **3** (`obl-12-1-form`, `obl-12-5-free`, `perm-12-7-icons`) — the §3.2 rewire, verified from the other side. |
| `owl:Nothing` members / dangling `ex:` IRIs | **0 / 0** — Tier-1, and the orphan check the rewire requires. |

---

# CQ expected-result fixtures — Article 46 (`articles/art46.ttl`)

**Added 2026-08-07 (Article-46 instantiation pass, work order E §4.7 / brief v2 §6).**

> ### ⚠ PREDICTION PROVENANCE — read this before reading any number below
>
> **Every value in this section was written BEFORE `run_owlrl_art46.py` existed on disk,
> and therefore before it was executed for the first time.** No SPARQL query, no OWL-RL
> closure and no pySHACL run had been made against `art46.ttl` at the time these numbers
> were locked. The Tier-2 values were derived **by construction** — from the node inventory
> the executor had just authored plus the *text of the frozen queries*, which were read to
> determine what each one matches — not from any observed result.
>
> - **TIER 1 — locked by the orchestrator in brief §6.2, restated here VERBATIM, not
>   re-derived and not the executor's to revise.** If the run disagrees with a Tier-1
>   value, that is a **FINDING reported beside the original prediction**, never a number
>   that gets changed.
> - **TIER 2 — derived and locked by the executor here, pre-run**, because they turn on
>   Condition-count and node-sharing choices the brief deliberately leaves open.
>
> Any deviation observed at run time is recorded as an amendment note that **keeps the
> original prediction visible permanently**, and is reported as a finding in
> `../../gdpr-kg-monitoring/agents/2026-08-06_workorder_E.md`. Nothing is silently reconciled.

Article 46 is the project's **first applicability-gating unit** and its **first
TBox-changing unit since Art 12**. It contributes 1 Permission, 1 Obligation, 8
`gdprkg:TransferMechanism` and 4 Conditions — and **zero** Exceptions, LegalBases,
LegalEffects, disclosures and time limits.

**Evaluation regime.** Same as Arts 13/6/12/14: OWL 2 RL materialised closure over the
**6-file union** (`../ontology/gdpr_kg.ttl` + `art13` + `art6` + `art12` + `art14` +
`art46`), then run the `.rq` [w3c2013sparqlentailment; w3c2012owl2]. `CQ-C4` and `CQ-C5`
are evaluated on the **PLAIN** graph, per the regime note established by
`run_owlrl_art12.py`. Runner: `cq_sparql/run_owlrl_art46.py`.
**`fixtures/art46_scenarios.ttl` is NOT part of this union** and contributes to no number
in this section (Zied, 2026-08-06).

## TIER 1 — locked in brief §6.2; restated verbatim, NOT re-derived

| CQ / fixture | Locked value | Brief §6.2 derivation (verbatim) |
|---|---|---|
| **CQ-C2** (uniform grounding) | **0** | Standing invariant. Note it is *load-bearing* this unit: all 8 `TransferMechanism` individuals must be `groundedIn` their points, and the TBox delta was shaped (§3.7) specifically so the seven existing ungrounded domain concepts stay outside `GroundedConcept`. |
| **CQ-C3** (obligation → bearer) | **59** | Current 58 (21 art13 + 0 art6 + 13 art12 + 24 art14, all → `ex:actor-controller`). Art 46 adds **exactly one** Obligation, 46(4). **The +1 is NOT a controller** — it is `ex:actor-supervisory-authority`, so the result set stops being homogeneous. |
| **Art-46 Obligations** | **1** | §3.6 |
| **Art-46 Permissions** | **1** | §3.6 — combined `Permission` instances become **7** (6 art12 + 1) |
| **Art-46 `TransferMechanism` individuals** | **8** | §3.6, one per lettered point |
| **Art-46 Exceptions** | **0** | Art 46 states no exemption grounds |
| **New `ReferencedProvision` stubs** | **5** | `ref-art45-3`, `-art93-2`, `-art40`, `-art42`, `-art63`. **No Directive stub** — under T3-D those citations ride in the 46(5) `seeAlso` |
| **`notApplicableIf` ABox edges** | **1** | first use of the property **anywhere**; on the 46(1) Permission |
| **`hasLegalEffect` ABox edges / `LegalEffect` instances** | **0 / 0** | T3-D declined `LegalEffect`'s first use for 46(5) |
| Regression **CQ-B1/B2/B3/B4** | **6 / 3 / 2 / 1** | Art 46 adds no `LegalBasis` |
| Regression **pySHACL** | **`Conforms: True`** ×5 | art46 + art13/art6/art12/art14 |
| **`owl:Nothing` members** | **0** | standing |
| **Dangling `ex:` IRIs** | **0** | standing; enforced by the orphan check after the two-file rewire |

> **Executor note on the "No Directive stub" cell.** Brief §6.2's parenthetical says those
> citations "ride in the 46(5) `seeAlso`". **On disk they do not, and cannot.** T3-E
> authorises no Directive stub, so the `seeAlso` had no target; and an external ELI IRI was
> investigated and rejected on evidence (EUR-Lex returns HTTP 200 for fabricated
> subdivisions — see recorded non-coverage **#3** below). Zied ruled 2026-08-07: **`skos:note`
> text only, no `seeAlso` edge at all.** The *locked value* (`stubs = 5`) is unaffected and
> is not revised; only the brief's justification text was inexact. **Flagged, not resolved.**

## TIER 2 — derived and locked by the executor, PRE-RUN

| CQ | Query file | Predicted result (6-file union) | Regime |
|---|---|---|---|
| **CQ-C1** | `CQ-C1_article_to_norms_grounded.rq` | **105** (current 100, **+5**). Art-46 delta = **1 Obligation + 4 Conditions + 0 Exceptions**. The Condition count **4** is the executor-chosen structure brief §3.6 leaves open, and is its stated minimum: 46(1)'s two limbs, the 45(3) gate condition, and 46(4)'s "cases referred to in paragraph 3". **The 46(1) Permission is excluded by the frozen FILTER** (non-coverage #1, inherited from Art 12) **and so are all 8 `TransferMechanism` nodes** (non-coverage #4, NEW). | materialised |
| **CQ-C2** | `CQ-C2_uniform_grounding.rq` | **0** — Tier-1, and load-bearing this unit. All 14 new Art-46 `GroundedConcept` nodes (1 Permission + 1 Obligation + 8 TransferMechanism + 4 Conditions) carry `groundedIn`. `ex:actor-processor` and the 5 new stubs sit **outside** `GroundedConcept` by design, so none can contribute a row. | materialised |
| **CQ-C3** | `CQ-C3_bearer.rq` | **59** — Tier-1. +1, and **not** to `ex:actor-controller`. | materialised |
| **CQ-C4** | `CQ-C4_referenced_actor.rq` | **9 — ZERO DELTA** (expected-absence assertion). 46(4)'s supervisory authority is the **bearer**, and `referencesActor` is for the *non-bearer* actor a duty is about. Art 46 references no third-party actor. A value of 10 means a `referencesActor` edge was drawn where the bearer edge belongs. | **plain** |
| **CQ-C5** | `CQ-C5_domain_concept.rq` | **11 — ZERO DELTA** (expected-absence). Art 46 is not a disclosure article: `disclosesConcept` has domain `Obligation` and 46(4) discloses nothing. **A value below 11 means an Art-13/14 edge was damaged by the rewire.** | **plain** |
| **CQ-C5x** | `CQ-C5x_cross_article_basis.rq` | **4 — ZERO DELTA** (expected-absence). Art 46 introduces no `reliesOnLegalBasis` edge and no `LegalBasis`. **A value below 4 means an Art-13/Art-6/Art-14 edge was damaged.** | materialised |
| **CQ-C6** | `CQ-C6_provenance_review.rq` | **80 direct + 217 inherited = 297 total.** **Direct = 70 + 10**, and the 10 is the consequential number: 1 Permission + 1 Obligation + **8 TransferMechanism**. The mechanisms count because CQ-C6's direct branch keys on the `reviewStatus`/`hasProvenance` **triples**, not on class — verified by reading the query, not assumed. **Inherited = 214 + 3 only**, NOT +4 — see non-coverage **#5**, which is the most important recorded gap in this unit. | materialised |
| **CQ-C7** | `CQ-C7_temporal.rq` | **44 — ZERO DELTA** (expected-absence). Art 46 contains no temporal trigger; no Art-46 Condition label contains the literal `"at the time"` or `"prior to"`, and none was worded to avoid or to attract the filter. | materialised |
| **CQ-A1** | `CQ-A1_art13_coverage.rq` | **59** (current 58, **+1**): `obl-46-4-consistency-mechanism` @ `ex:art46-p4`. The query is not article-scoped. | materialised |
| **CQ-A3** | `CQ-A3_conditional_duties.rq` | **91** (current 90, **+1**): `obl-46-4-consistency-mechanism` carries exactly one `appliesIf`. The 46(1) Permission's **two** `appliesIf` edges do **not** count — the query requires `?obligation a gdprkg:Obligation`. | materialised |
| **CQ-A4** | `CQ-A4_art13_exemption.rq` | **8 — ZERO DELTA** (expected-absence). Art 46 has 0 Exceptions, so it contributes no group. | materialised |
| **CQ-A5 / CQ-A6 / CQ-A8** | `CQ-A5/A6/A8_art14_*.rq` | **92 / 1 / 66 — ZERO DELTA** each. Art 46 adds no Exception (A5), no 14(5)(b)-shaped surviving duty (A6), and no `hasTimeLimit` or timing Condition (A8). Regression only. | materialised |
| **CQ-B1 / B2 / B3 / B4** | `CQ-B*.rq` | **6 / 3 / 2 / 1** — Tier-1 regression, unchanged. Art 46 adds no `LegalBasis`. | materialised |

## Recorded non-coverages / expected-absence assertions (Article 46)

| # | What | Why, and where the fact IS verified |
|---|---|---|
| **#1** (inherited) | **CQ-C1 does not reach Permissions.** | Unchanged from Art 12. Art 46's single Permission is the **gate node itself**, so this non-coverage now hides the unit's headline construct from CQ-C1. Grounding is still machine-checked by CQ-C2; the bearer facts are explicit via `grantsPermissionTo` and are asserted as fixtures below. |
| **#2** (inherited) | **CQ-C3 does not reach permission bearers.** | Unchanged from Art 12. The two `grantsPermissionTo` edges (controller **and** processor) are outside CQ-C3's frozen wording; verified by fixture instead. |
| **#3 — NEW** | **46(5)'s Directive 95/46/EC citations have NO `rdfs:seeAlso` target and no stub** — the Art-12 12(8) precedent could not be followed in full. | The 12(8) precedent points a `seeAlso` at a **minted stub** (`ex:ref-art92`). T3-E authorises no Directive stub, so there was no node to point at; and `referencesProvision` cannot originate on a Paragraph (domain `NormativeElement` ⇒ the Paragraph would be entailed a `GroundedConcept` and **break CQ-C2** — the very reason 12(8) used `seeAlso`). An external ELI IRI was investigated and **rejected on evidence**: EUR-Lex returns HTTP 200 for `dir/1995/46/art_999/oj` and `art_26/par_77/oj`, i.e. for subdivisions that do not exist, so a 200 proves nothing. **Ruled by Zied 2026-08-07: `skos:note` text only.** The fact IS verified: the full 46(5) text sits in `ex:art46-p5 skos:note` with a `skos:scopeNote` recording the decision. Ledger: `art46-46-5-seealso-target`. |
| **#4 — NEW** | **CQ-C1 does not reach `gdprkg:TransferMechanism`** — all 8 nodes are invisible to it. | The frozen FILTER is `?normType IN (gdprkg:Obligation, gdprkg:Condition, gdprkg:Exception)`. A `TransferMechanism` is none of those (deliberately — T3-B/U5 decided the instruments are **not** normative units). **The query was NOT widened** (playbook §4.1); widening it would have re-imported by the back door exactly the typing the unit refuses. The fact IS verified: grounding for all 8 is checked by **CQ-C2**, provenance/review by **CQ-C6 direct**, and the inventory + `providesSafeguard` edges by the fixtures below. |
| **#5 — NEW, and the most consequential** | **CQ-C6's inherited branch does not reach a Condition attached via `gdprkg:notApplicableIf`.** `cond-46-1-adequacy-decision-exists` — the 45(3) gate, the single most important node in this unit for the applicability claim — has **no provenance path** under the frozen query. | CQ-C6's inherited branch enumerates the path `(gdprkg:appliesIf` OR `gdprkg:hasException)`. `notApplicableIf` is **not in it** — understandably, since the property had **zero ABox use anywhere** until this unit created its first. So Art 46 contributes **3** inherited rows, not 4. **The query was NOT widened and the edge was NOT re-pointed to `appliesIf` to make the count land** (playbook §4.1 — this is precisely the failure that rule exists to prevent; the Art-14 CQ-C7 case is the precedent). The fact IS verified: the Condition is a first-class `gdprkg:Condition`, `groundedIn ex:art46-p1`, reachable from `ex:perm-46-1-transfer`, counted by **CQ-C1** and **CQ-C2**, and asserted as a fixture below. **This is a genuine gap in the frozen CQ set, exposed by the first ABox use of `notApplicableIf`, and it is Zied's to resolve — not the executor's.** |
| **#6 — NEW** | **The five new stubs carry no external anchor** (no `owl:sameAs`, no `rdfs:seeAlso` to GDPRtEXT/ELI). | Reuse gate R-3 (2026-08-07) found GDPRtEXT **entirely unreachable**: `https://w3id.org/GDPRtEXT` → 503, ADAPT Centre host root → 503, `purl.org/adaptcentre/...` → 404. A 2020 GitHub mirror does contain all five anchors (`gdpr:article45-3`, `article93-2`, `article40`, `article42`, `article63`), each typed `eli:LegalResourceSubdivision` — the class `gdprkg:ReferencedProvision` is already `rdfs:subClassOf` — so the alignment would have been type-clean. **Ruled by Zied 2026-08-07: stubs stay bare; a link known to 404 inside a file about to be certified is worse than no link.** Ledger: `gdprtext-vocabulary-unreachable`. |
| **Absence** | **0 `gdprkg:hasLegalEffect` and 0 `gdprkg:LegalEffect` instances across the 6-file union.** | T3-D declined `LegalEffect`'s first use for 46(5). A nonzero count is a defect **and** a scope breach. |
| **Absence** | **0 `gdprkg:LegalBasis` contributed by Art 46**; combined stays **6**. | Typing the 46(2)/(3) instruments as `LegalBasis` is forbidden (it fires carry `f2-domain-family`). A 7th basis means that typing was taken. |
| **Absence** | **0 `disclosesConcept`, 0 `disclosedToDataSubject`, 0 `hasTimeLimit` on Art-46 subjects.** | Art 46 is not a disclosure article (Art-12 12G posture) and states no deadline. Combined totals stay 11 / 44 / 27. |
| **Absence** | **0 occurrences of `ex:ref-art46`** across the 6-file union. | The §4.3 rewire is complete only if the stub is gone from **all three** sites (two files). |
| **Absence** | **`referencesProvision` on Art-13 subjects stays 8; on Art-12 subjects stays 49; on Art-14 subjects stays 11.** | The rewire repoints one object per line and **adds/removes no edge**. Regression on the two edited certified files. |

## Additional demonstrated edges (Article 46; fixtures for regression)

| Edge / fixture | Predicted over the 6-file union |
|---|---|
| Art-46 `gdprkg:Obligation` / `Permission` / `Exception` | **1 / 1 / 0** — Tier-1. |
| Art-46 `gdprkg:TransferMechanism` instances | **8** — Tier-1, one per lettered point (46(2)(a)–(f), 46(3)(a)–(b)). |
| Art-46 `gdprkg:Condition` instances | **4** — Tier-2 (the number brief §3.6 leaves to the executor). |
| `gdprkg:providesSafeguard` edges | **8**, **all → `ex:concept-safeguard`** (the canonical node Art 13 minted and Art 14 shares). First use of the property. |
| `gdprkg:notApplicableIf` edges | **1** — Tier-1, first ABox use **anywhere**: `ex:perm-46-1-transfer` → `ex:cond-46-1-adequacy-decision-exists`. |
| `gdprkg:grantsPermissionTo` | **2** Art-46 edges (`ex:actor-controller` **and** `ex:actor-processor`) — the project's **first multi-bearer norm**. **Combined 8** (6 art12 + 2). |
| `gdprkg:Permission` instances, combined | **7** (6 art12 + 1 art46) — Tier-1. |
| `gdprkg:imposesObligationOn` → `ex:actor-supervisory-authority` | **1** — the project's first non-controller obligation. → `ex:actor-controller` stays **58**. |
| `gdprkg:appliesIf` on Art-46 subjects | **3** = 2 on the Permission (conjunctive: safeguards **AND** remedies) + 1 on the Obligation. |
| `gdprkg:referencesProvision` on Art-46 subjects | **2** only: `cond-46-1-adequacy-decision-exists` → `ex:ref-art45-3`; `obl-46-4-consistency-mechanism` → `ex:ref-art63`. **The other five citations ride on `rdfs:seeAlso` instead** — see EXEC-1: `referencesProvision` has domain `NormativeElement`, and attaching it to a `TransferMechanism` would entail the mechanism is a norm. Consequence: `ref-art93-2`, `ref-art40`, `ref-art42` carry **0** `referencesProvision` in-edges. **If Zied prefers the other side of this trade, this fixture becomes 7.** |
| `rdfs:seeAlso` from Art-46 mechanisms to stubs | **5** (b→`ref-art47`, c→`ref-art93-2`, d→`ref-art93-2`, e→`ref-art40`, f→`ref-art42`). |
| `ReferencedProvision` individuals, combined | ~~**22** (17 before this pass + 5 new)~~ → **AMENDED TO 21.** See the deviation note directly below; the original prediction is left visible per playbook §4.2. **`ex:ref-art47` REUSED, not re-minted.** |

> ### ⚠ THE ONE PREDICTION THAT DEVIATED — recorded permanently, not silently reconciled
>
> **Original prediction: 22. Observed: 21. The prediction was wrong; the data is correct.**
>
> **Diagnosis, run in playbook §4.2 order (data → modelling → prediction).** The graph was
> checked first: all 21 individuals are present and correct, the five new stubs are all
> declared, `ex:ref-art47` is declared exactly once, and there are no duplicates. Nothing is
> missing. The arithmetic in the prediction was the defect.
>
> **Why it was wrong.** I wrote "17 before this pass **+ 5 new**" and omitted the
> subtraction: the `ex:ref-art46` rewire **deletes a `ReferencedProvision` declaration from
> the same population it adds to** (work order E §4.3, site 1 of 3 — `art13.ttl:123`). The
> correct arithmetic is **17 − 1 + 5 = 21**. This is the first pass in which the stub
> population both grows and shrinks, because it is the first pass whose rewire target had
> its declaration inside a *certified* file rather than being comment-only; the Art-14
> precedent removed `ex:ref-art14` from `art12.ttl` the same way, but no Art-14 fixture
> counted the global stub population, so the interaction was never exercised.
>
> **Scope of the error.** It is confined to this one regression fixture. It is **Tier 2**
> (executor-derived), **not** a Tier-1 locked value and **not** a frozen CQ's expected
> result — so playbook §4.2's "adjusting a prediction is T3" clause is not triggered. **Every
> Tier-1 value passed unchanged**, and every other Tier-2 value passed as predicted.
> Flagged for Zied regardless.
| Canonical mints | **`ex:actor-processor`** only (`gdprkg:Processor`, a Phase-3 class idle until now → instance mint, **NOT** a TBox change). **Zero** new `ex:concept-*`. |
| `ex:actor-*` / `ex:concept-*` canonical nodes | **7 / 7**. `ex:concept-*` is **unchanged at 7** — Art 46 minted no domain concept and reused `ex:concept-safeguard`. |
| `ex:art46` `referencesProvision` in-edges | **2** — `cond-13-1-f-transfer-safeguarded` and `cond-14-1-f-transfer-safeguarded`, the rewire verified from the other side. |
| TBox after the pass | **453 triples / 86 classes / 39 object properties / 3 datatype properties**, `sha1 d8d6fd499ad8b02a47391accb4736131a888cbe2` (was 440 / 84 / 37 / 3, `sha1 2cdc5ac737a26339fee4a36fe32e2162cebfd838`). **Exactly two `gdprkg:` additions**; the +13 triples are those two terms plus two external weak-pointer declarations. Both `owl:AllDisjointClasses` sets **unchanged**; `gdprkg:TransferMechanism` deliberately **not** added to the 6-member normative set. |
| `ontology/shapes.ttl` | **UNCHANGED**, `sha1 c0c8963f1632869b9338e42f8dc000acdfc4ea55`, still 10 NodeShapes. |
| `methodology/competency_questions.json` | **UNCHANGED**, still 27 CQs, `sha1 b9bea058363d69541c7000652f97e4a551ac0693`. No question or `.rq` added, edited or widened. |
| `owl:Nothing` members / dangling `ex:` IRIs | **0 / 0** — Tier-1. |
