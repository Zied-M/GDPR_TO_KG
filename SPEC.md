# SPEC — what this artifact is required to do

This document states the requirements the GDPR knowledge graph in this repository is built
to satisfy, as testable claims. It contains no argument for why those requirements are
worth satisfying and no positioning against related work; both belong in the manuscript,
not here.

Read it as the bar. Everything else in the repository is either an attempt to meet that
bar or an instrument for checking whether it was met.

---

## 1. Scope

An RDF/OWL 2 DL representation of GDPR provisions, with SHACL shapes and a SPARQL
competency-question suite, covering **five instantiated articles**: 6, 12, 13, 14, 46.

The article *scope set* (which articles are eligible for the KG at all) is inherited: it
follows the LexiGen corpus, which follows Poplavska et al. (JURIX 2020) — 47 articles.
Five of those 47 are instantiated here.

Instantiation order follows cross-reference closure over the GDPR's internal reference
graph, in both directions: an article is eligible once another instantiated article either
invokes it or governs how its duties are discharged.

The KG represents the **legal source**. Compliance verdicts (`ComplianceAssessment`,
`Violation`) are modelled as optional *outputs* and kept structurally separate from the
legal-source graph. No verdict data is included.

---

## 2. Requirement A — applicability must be decidable declaratively

**R-A1.** The representation must permit a determination of whether an obligation is *in
force for a given situation* prior to, and independently of, any assessment of whether it
has been complied with.

**R-A2.** The conditions and exceptions governing that determination must be represented
as first-class, queryable nodes attached to the obligation they govern — not as free text
and not as classifier features.

**Status: EXPRESSED, and EXERCISED ON HYPOTHETICAL SCENARIOS. NOT EVALUATED.**

Articles 6, 12, 13 and 14 impose duties that are unconditionally in force for a controller
processing personal data; they *express* the gate structure without exercising it. Article
46 (transfers subject to appropriate safeguards) is the first instantiated article whose
applicability turns on facts about a situation rather than on the wording of a policy.

`cq_sparql/demo_art46_scenarios.py`, run against the non-normative fixture
`fixtures/art46_scenarios.ttl`, poses four queries over four hypothetical transfers and
returns **different answers for different transfers**. That difference is the claim: an
applicability answer derived from facts, each answer traceable to a specific Article 46
Point.

Three limits, none of them incidental:

- The fixture is **outside the certified graph** — not imported by
  `articles/certify_art13_art6.ttl`, not in `articles/catalog-v001.xml`, not loaded by
  `cq_sparql/run_owlrl_art46.py`. HermiT, pySHACL and the CQ runner certify the six-file
  union **without** it. The demonstrator is never a gate result.
- Four hypothetical transfers are not an evaluation. Nothing here shows the gate is
  correct over real policy data.
- **The closed-world limit is real and is refused rather than finessed.** Article 46(3) is
  expressly non-exhaustive ("in particular"); 46(2) is not. So "no listed instrument
  matched, therefore no appropriate safeguard" is defensible over 46(2) and unsound over
  46(3). No query in the demonstrator draws the stronger conclusion; Q3 asks only which
  transfers rely on no listed 46(2) instrument, and Q4 reports the 46(3) residue
  explicitly so the unsound step is visibly declined.

**How R-A is intended to be evaluated (not performed here).** Per-class F1 on the
NOT_APPLICABLE label against LexiGen gold labels, over the 21 articles LexiGen marks
context-dependent, against a baseline that does not reason about applicability. That
requires a policy-to-obligation matching stage which is not part of this repository. Note
also that Articles 44–49 form a block of six in that context-dependent set and only one of
them is instantiated here.

---

## 3. Requirement B — traceability must be structurally complete

**R-B1.** Every normatively-defined node carries a grounding relation to the Article /
Paragraph / Point it derives from. Uniformly — Obligation, Right, Condition, Exception,
LegalBasis and Consent alike.

**R-B2.** Grounding direction is canonical: `GROUNDED_IN` (norm to source). `SOURCE_OF` is
its `owl:inverseOf`, reasoner-inferred, never asserted.

**R-B2a.** Provision text is carried as `oa:start` / `oa:end` character offsets into
`sources/art<N>.txt`, not as a stored copy. Each source file is digest-pinned in
`sources/SOURCE.json`; `sources/art<N>.units.json` records the range per unit.

**R-B3.** Every primary normative unit (`PrimaryNormativeUnit`: Obligation, Right,
LegalBasis, Consent) carries provenance and a review status. Condition and Exception
inherit these from their parent unit rather than carrying their own.

**R-B4.** No dangling IRIs: every `ex:` IRI appearing as an object appears as a subject
somewhere in the graph.

**R-B5.** Articles share **canonical domain nodes** (one `ex:concept-purpose`, one
`ex:actor-controller`, one LegalBasis per basis) rather than holding per-file copies.

**Status: HOLDS, machine-checked.** R-B1 -> CQ-C2 returns 0. R-B3 -> CQ-C6 returns 0
missing. R-B4 -> 0 dangling, checked on the *asserted* graph (see section 6.6 for why that
distinction matters). R-B5 -> CQ-C5x joins Article 13 and Article 14 obligations through
shared nodes; Articles 13 and 14 both reference `ex:art46` directly rather than through
per-file stubs.

**Explicitly not claimed.** That this traceability is *useful to a human auditor*. That
would require a user study; none was run. R-B is a structural invariant claim only.

---

## 4. Requirement C — every non-trivial modelling decision is externally anchored

**R-C1.** Each non-trivial decision is tied to a peer-reviewed or standards source, or is
marked as an original design decision. An unmarked gap is a defect.

**R-C2.** Vocabulary is reused before it is minted. New terms exist only for the
obligation-decomposition and compliance-verdict layer. Reused: GDPRtEXT, DPV / DPV-GDPR,
GConsent, PROV-O, ELI.

**R-C3.** Citation keys resolve to `references.bib`. No citation appears that is not
verified there.

---

## 5. Verification gate

A unit is certifiable only when all three legs pass over the six-file union (TBox + five
articles), loaded via `articles/certify_art13_art6.ttl`:

| Leg | Instrument | Reproduce with |
|---|---|---|
| Reasoner consistency | HermiT | `python verify.py --reasoner` |
| Shape conformance | pySHACL, `Conforms: True` | `python verify.py --shacl` |
| Competency questions | SPARQL under OWL 2 RL materialisation | `python verify.py --cq` |

All five articles have passed all three legs. The certifying runs were performed locally
in Protégé with `owl:imports` resolved; `verify.py` reproduces the SHACL and CQ legs
exactly and the reasoner leg approximately (see 6.5).

The competency-question leg is **prediction-locked**: expected row counts are written into
`cq_sparql/expected_results.md` *before* the run, and the runners report PASS/CHECK against
them rather than merely printing results. Timestamps evidencing that predictions preceded
execution are recorded per article.

A competency question without an expected answer is not a test. The 27-question set is
frozen in `methodology/competency_questions.json`.

---

### 5.1 Which state this snapshot is

This repository is a **periodic snapshot**. The canonical graph — TBox, SHACL shapes and
article ABoxes — lives in the working tree (`gdpr-kg-foundation/`), which is upstream of
this one and is refreshed into it at milestones, not continuously. Between milestones the
two may legitimately differ.

This matters when reading a `verify.py` result. A failure here means one of two different
things, and they are not interchangeable:

- the graph in *this snapshot* genuinely fails a leg; or
- this snapshot has fallen behind the canonical tree, and the failure describes a state
  that no longer exists upstream.

To tell them apart, compare the hashes below against the ones the runners print. Every
runner emits a `[ROOT]` line and the `sha256` of the TBox it actually read, before it
loads anything, so a reported count can always be tied to the exact bytes that produced
it.

**This snapshot corresponds to the `gdpr-kg-foundation` state with canonical
`ontology/gdpr_kg.ttl` sha256 `8ab94608659ae5868bdedff894b368e2648758708a0999a70d6a771adb53815c`
and `ontology/shapes.ttl` sha256
`6abce9a50b8ed375a9f41ace8b7f42eef406b6a94a903bbd55b31409ae8a323f` (snapshot taken
2026-08-18).**

If those two hashes match what the runners report here, the snapshot is current and a
`verify.py` verdict describes the live graph. If they do not, the snapshot is stale and the
verdict describes the snapshot only. Regenerate this paragraph with
`python3 snapshot_drift_check.py --spec-line` in the canonical tree; that script is the
publish-time gate and fails loudly when the two trees have diverged.

---

## 6. Known limitations

Stated here rather than left to be discovered.

1. **`reviewStatus` is `draft` on every primary normative unit.** No article here is a
   validated benchmark. The gate is *technical* — reasoner, SHACL, CQ. Legal and doctrinal
   validation is deferred to a single review of the finished work and has not occurred.

2. **Obligation counts are consequences of a splitting rule, not settled facts.** Bundled
   enumerations are split per item into distinct point-level obligations. That rule is an
   original design decision — not inherited practice, not drawn from prior art. A different
   rule yields different counts (Article 13: 21; Article 14: 24).

3. **Source of record is `gdpr-info.eu`, not the EUR-Lex Official Journal.** The scraper
   targets a third-party mirror. Article 46's point structure was cross-checked against
   OJ L 119 and agreed, but the mirror is the operative source for the instantiated
   articles and no systematic OJ diff has been run.

4. **Applicability is demonstrated, not evaluated** — see section 2. Four hypothetical
   transfers, outside the certified graph, are not a metric.

5. **Headless HermiT is a weaker check than the Protégé run.** `verify.py --reasoner`
   strips `owl:imports` so the reasoner runs offline, meaning external vocabularies are
   *not* loaded. Treat it as a regression check, not as the certification.

6. **The dangling-IRI check is regime-sensitive.** Computed over the OWL 2 RL materialised
   closure it is close to vacuous, because materialisation gives every referenced IRI an
   `rdf:type` triple and so makes it a subject. It is meaningful only over the asserted
   graph. The per-article runners compute it post-materialisation; `verify.py` and the
   figure quoted in section 3 use the asserted graph.

7. **Boundary and negative competency questions are not drafted.** The frozen 27 bound what
   the graph *can* answer; they do not bound what it should refuse. Known non-coverage is
   recorded — CQ-C1 and CQ-C3 do not reach `Permission`; CQ-C7 cannot see fixed-deadline
   `hasTimeLimit` on Article 12 — but these were found, not predicted.

8. **Five articles is a small base.** No `Right` node is populated; `grantsRightTo` is live
   vocabulary with no instances. Article 46 breaks the notice-shaped monotony — it
   contributes the first `Permission`, the `TransferMechanism` family, and the first
   obligation borne by a supervisory authority rather than a controller — but Articles 15,
   17, 30 and 32 remain uninstantiated, so deontic variety is still thin.

9. **Some in-file version strings are stale.** `art46.ttl`'s `owl:versionInfo` still reads
   "provisional, awaiting ... certification" although Article 46 certified on 2026-08-07;
   the same is true of `art12.ttl`. The certification record is external to the TTL files.

---

## 7. What this repository is not

- Not a compliance checker. No policy ingestion, no matching stage, no verdict.
- Not a claim that LLM-based policy-to-GDPR matching is novel.
- Not a federated system. Privacy-preserving decentralisation is out of scope here.
- Not the LexiGen corpus and not a derivative of it. LexiGen is prior published work by
  other authors; this repository builds alongside it and inherits its article scope set and
  obligation-level labels by reference only.
