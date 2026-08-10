# gdpr-kg — a GDPR knowledge graph with a reproducible verification gate

An RDF/OWL 2 DL representation of GDPR provisions with SHACL shapes and a SPARQL
competency-question suite. Five articles are instantiated: **6, 12, 13, 14, 46**.

**Read [`SPEC.md`](SPEC.md) first.** It states what this artifact is required to do, what
currently holds, and what does not. This README only tells you how to run it.

## Status

| | |
|---|---|
| Articles instantiated | 5 of the 47-article scope set, all certified |
| Verification gate | reasoner + SHACL + competency questions, all passing |
| `reviewStatus` | `draft` on every primary normative unit — no article here is a validated benchmark |
| Legal validation | deferred; not performed |
| Applicability gating | demonstrated on hypothetical scenarios, **not evaluated** (see `SPEC.md` §2) |

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python verify.py
```

Expected: three legs, all PASS, exit 0. Takes a few minutes — the OWL 2 RL closure over
the combined graph is the slow part. The reasoner leg needs a Java runtime on `PATH`.

Individual legs:

```bash
python verify.py --shacl      # pySHACL conformance + accept/reject fixtures
python verify.py --cq         # SPARQL CQs under OWL 2 RL materialisation
python verify.py --reasoner   # headless HermiT consistency
```

The competency-question leg is **prediction-locked**: expected row counts live in
`cq_sparql/expected_results.md` and were written before the runs. The runners report
PASS/CHECK against those predictions rather than just printing numbers. If you want to
audit that discipline, that file is where to look.

## Layout

```
ontology/gdpr_kg.ttl          OWL TBox + alignment axioms to reused vocabularies
ontology/shapes.ttl           SHACL shapes
ontology/shacl_test/          accept/reject fixtures for the shapes
articles/art{6,12,13,14,46}.ttl  the instantiated ABoxes
articles/catalog-v001.xml     Protege catalogue for offline import resolution
cq_sparql/*.rq                27-question competency suite, one file per answerable CQ
cq_sparql/README.md           the evaluation regime (which CQs need materialisation)
cq_sparql/expected_results.md pre-run expected counts — the fixtures
cq_sparql/run_owlrl_*.py      per-article authoritative runners
cq_sparql/demo_art46_scenarios.py  applicability demonstrator (certifies nothing)
fixtures/art46_scenarios.ttl  non-normative scenario fixture, outside the certified graph
methodology/competency_questions.json   the frozen 27-CQ set
kg/source/                    scraped GDPR text, point-level
scripts/gdpr/                 the scraper that produced it
references.bib                verified bibliography; nothing is cited that isn't here
verify.py                     runs all three gate legs
```

Runners resolve paths relative to `cq_sparql/`, so **don't restructure the tree** without
updating them.

## Vocabulary reuse

New terms are minted only for the obligation-decomposition and verdict layer. Reused:
GDPRtEXT, DPV / DPV-GDPR, GConsent, PROV-O, ELI. Alignment axioms are in the TBox.

## Provenance and attribution

- The **article scope set** (47 articles) and the **obligation-level labels** are
  inherited from **LexiGen** — prior published work by other authors, not by this
  repository's author. LexiGen follows Poplavska et al. (JURIX 2020) for the scope set.
- **Point-level decomposition** reuses the GDPRtEXT / ELI Point-SubPoint pattern
  (Pandit et al., ESWC 2018).
- The **enumeration-splitting rule** — bundled enumerations split per item into distinct
  point-level obligations — is an original design decision with no prior-art claim. It
  determines the obligation counts; see `SPEC.md` §6.2.
- GDPR text is scraped from `gdpr-info.eu`, a third-party mirror, **not** EUR-Lex. See
  `SPEC.md` §6.3.

## The applicability demonstrator

`python cq_sparql/demo_art46_scenarios.py` runs four queries over four hypothetical
transfers and returns different answers for different transfers — applicability derived
from facts, each answer traceable to an Article 46 Point.

It **certifies nothing**. The fixture it loads sits outside the certified graph
deliberately: not imported by `certify_art13_art6.ttl`, not in the catalogue, not loaded by
the CQ runner. Read `SPEC.md` §2 for the limits, including why the demonstrator refuses to
conclude "no appropriate safeguard" from an unmatched 46(2) list.

## Limitations

Nine of them, stated plainly, in [`SPEC.md`](SPEC.md) §6. Read that section before
forming a view of the artifact.
