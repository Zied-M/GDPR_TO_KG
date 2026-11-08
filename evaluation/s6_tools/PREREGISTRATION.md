# Pre-registration: the tool-mediated reach study

**Written 2026-09-15 (S8), BEFORE any generation. Nulls included. Not to be edited after
a run.** Its digest is recorded in `PREREGISTRATION.sha256`; a later session verifies that
digest before reading any result, and an edited file is a failed pre-registration rather
than a revised one.

Operative design: `context/05_EVAL_PLAN.md` **Part E**, stress-tested with the author
across five rounds on 2026-09-15 and settled. This file does not decide anything. It
states, in advance, what will be measured, on what, what is expected, and how it will be
read, so that none of those can be chosen after the data exists.

**Why this file exists at all.** The author's stated aim is a positive result. What a
design may legitimately optimise is **power**, the ability to detect an effect if one
exists; it may never optimise the **sign** of the outcome. Designing toward a sign is what
produced the three withdrawn directions in this project. The mechanism that separates the
two is naming the nulls in advance, which is what the table in section 3 does, and it is
the same discipline `blomqvist2012testing` supplies for the competency questions.

---

## 1. The question, and the two arms

Does representing obligations as a structured, grounded graph change whether a machine's
judgement is anchored in the source rather than in recollection?

Two arms. Both are given the **same three tool functions with identical signatures**
(`find_duties`, `get_conditions`, `get_provision`), backed by **different stores**: a
per-point text index on one side, the certified graph on the other. The interaction
pattern is therefore held constant and the representation is the only thing that varies.

**Retrieval is a non-variable.** Both arms search the same index, the 87 source provision
units, with the same scorer (BM25, local, ties broken on unit id) and the same k = 5
provisions. The stores differ only in what they return for a matched provision. A provision
that carries no duties is still returned by the graph store, with an empty duty list, so
both arms always see the same k.

**Arm 2 ("structure without grounding") is dropped**, per E4: a tool return either carries
a provision identifier or it does not, so there is no natural surface for it. Under this
design grounding is held constant and relations are the only variable. That is a different
question from Part C's 2-to-3 ablation, and the draft must say so rather than presenting
it as the same one.

Model: `qwen2.5:7b`, pinned before any run, with its Ollama blob digest recorded beside
the tag. `num_ctx` explicit at 16384, temperature 0.0, turn cap 10.

---

## 2. The measure, exactly as `reach.py` implements it

> While relying on duty D, did the model's tool trace surface a relation the graph
> attaches to D **from a different provision**?

Read **mechanically from the tool call log**, from the machine provenance each store
returns alongside its payload. The extractor never parses prose. It needs **no reference
standard of any kind**: relevance is defined relative to the model's own work, never
against a gold key. That is what keeps the claim-to-duty matcher out of the design, and
that matcher stays rejected.

Three definitions, and they are the whole measure.

- **Reliance is anchored at the PROVISION, not at the duty id.** A model relies on a
  provision when it passes that provision's handle to `get_conditions`; a graph-arm duty
  id resolves to the provision it is grounded in. A named paragraph expands down to its
  points. The relied-upon duty set is every duty grounded in a relied-upon provision.
  This is the only definition computable identically in both arms, and it is neutral
  rather than generous: the one-to-many expansion, up to six duties on one provision,
  inflates both arms' target sets equally, where anchoring at the duty id would hand the
  graph arm a smaller and easier target set. `relied_duties_direct` is recorded anyway, so
  the other definition can be recomputed without a rerun; **any such recomputation is a
  secondary analysis and must be labelled one.**
- **A target** is a (duty, relation) pair the graph grounds in a **different** provision
  than the duty. Same-provision relations are excluded: reaching those needs no
  representation. 223 of the 258 attachments qualify.
- **Surfaced** is read from the provenance. A target relation counts as surfaced if either
  it was returned as a relation node, which only the graph store does, **or** the text of
  a provision it grounds in was returned by any tool. Both tests run in both arms. Text
  coverage is computed over merged **character spans** against the pinned source, not over
  unit ids, so a provision read as its subunits counts as read and a returned parent
  covers its points.

**The text arm keeps a real escape route and it is deliberate.** It may search for the
exception directly and find Article 14(5) on its own. **A null is therefore a live
outcome and the measure is not rigged.**

### The four statuses, and none of them is a zero

| status | meaning |
|---|---|
| `reached` | at least one target relation surfaced |
| `not_reached` | targets existed and none surfaced |
| `no_targets` | the relied duties carry no cross-provision relations. Every Article 46 item is expected here |
| `no_reliance` | the model never called `get_conditions`, so it relied on no duty and the question does not arise |

**`no_reliance` is reported separately and is NEVER folded into the denominator.** Counting
a model that never used the tools as a failure to reach would measure tool-following, not
representation. It was observed in **both** arms during the S7 hand-check, so it is a model
behaviour rather than a text-arm artifact.

### The denominator, fixed here

The per-item rate is **`reached` / (`reached` + `not_reached`)**, per arm, per stratum.
`no_targets` and `no_reliance` are excluded from it and their counts are reported beside
it. Items flagged `turn_cap_hit` or carrying an execution error are **excluded from the
rate and reported separately**, per E8, never silently included.

### What the text arm's ceiling actually is

Sibling expansion alone reaches **0 of the 223** cross-provision attachments, exactly as E3
states, verified from files on disk rather than assumed. But `find_duties` normally also
returns the duty's own provision, which covers the parent chapeau and brings **40 of the
223** into the text arm's reach (Article 13: 29, Article 14: 9, Article 12: 2), all of them
parent-grounded. **The honest headroom figure for this measure is 183, not 223**, and no
sentence in this pre-registration, in any analysis of its results, or in the manuscript may
imply the text arm can reach none of them. E3's own wording is correct as written and is
not edited. See `HANDCHECK.md`.

---

## 3. The prediction

**This table is the author's, from E5, and is reproduced without alteration.**

| stratum | cross-provision attachments | prediction |
|---|---|---|
| Article 14 | 159 | separation |
| Article 13 | 62 | separation |
| Article 12 | 2 | little or none |
| Article 46 | 0 | **no separation** |

**The expected shape within a separation:** the text arm will likely **match** the graph
arm on reaching the exception *text*, and differ on **connecting it to the right duty**.

**Separation on Article 46 would be evidence the measure is picking up something other
than relations**, and catching that is what this pre-registration exists for. Article 46
has zero cross-provision attachments, so under the measure as specified every Article 46
item should land on `no_targets` in both arms. A non-trivial `reached` count in the
Article 46 strata is a **failure of the instrument**, not a finding about the
representation, and must be reported as one.

**Articles 12 and 46 are carried as predicted nulls, not as filler.** The two Article 46
strata are paired by construction: the applicable segments are drawn alongside the
not-applicable ones as a **same-article control**, without which a null on the
not-applicable stratum cannot be told apart from Article 46's thin graph. That pairing is
the author's decision of 2026-09-13 and is not reopened.

**A constraint on any positive reading, which the S6 inventory imposes and which may not
be softened.** The fanout is severely skewed: 8 nodes carry 201 of the 258 attachments and
32 of the 44 nodes have fanout 1. The study will effectively measure behaviour around the
Article 14(5) exception block and the collection trigger. **No separation may be written as
"223 relations a text baseline cannot reach" without that sentence beside it.** And there
are **zero** cross-*article* relation attachments in this frozen scope, so only the
cross-*provision* claim is supported by anything measured here.

---

## 4. The sample, fixed before any run

Frozen 2026-09-15 by `freeze_sample.py` into `sample.frozen.json`.

- **seed `20260915`.** The 2026-09-13 seed `20260913` is **not** reused: the strata
  changed, a same-seed draw is not comparable to the old one, and implying otherwise would
  be worse than a clean break.
- sample sha256 `96cdc651592ddc51f031103cb27dc7198ce8a6d06555be4abbaeac4bfbfa5a40`
- corpus sha256 `a9cbcdb548d44b6b223052c1995c1a397b0abd76a1d72fd4cc8cd039f47ecefd`

| stratum | article | labels | study | pilot |
|---|---|---|---|---|
| APP-14 | 14 | COMPLIANT + NON_COMPLIANT | 100 | 16 |
| APP-13 | 13 | COMPLIANT + NON_COMPLIANT | 75 | 12 |
| APP-12 | 12 | COMPLIANT + NON_COMPLIANT | 25 | 4 |
| APP-46 | 46 | COMPLIANT + NON_COMPLIANT | 25 | 4 |
| NA-46 | 46 | NOT_APPLICABLE | 25 | 4 |
| | | | **250** | **40** |

Study and pilot are **disjoint by construction**: each stratum is drawn once and split,
so no item can appear in both. The draw is label-balanced at the stratum level; the
study/pilot split is a shuffle, so the per-split label mix varies by a few items and is
recorded rather than forced.

The 250-item study set is the pre-registered analysis set. The 40-item pilot is for
checking the harness end to end and **produces no number that enters the analysis or a
draft**.

---

## 5. The analysis, stated before the data

**Stratify, never pool.** Every rate is reported per stratum, per arm. There is no
headline number across strata, and one may not be constructed afterwards. Pooling would
let the stratum mix drive the result, and here it would do so in a specific and misleading
direction, since Article 14 carries 159 of the 223 attachments and Article 46 carries none.

**Primary comparison: per item.** Each item is run in both arms, so the outcomes are
paired. Within each stratum, over items where both arms are in {`reached`,
`not_reached`}, the comparison is **McNemar's exact test on the discordant pairs** (an
exact binomial on the counts, no new dependency), reported with the discordant counts
themselves so a reader can see what the test is running on. Per-arm rates carry **Wilson
score intervals** (`brown2001interval`). The pre-registered alpha is **0.05, two-sided,
per stratum**, with no correction across strata because the strata are separate questions
with separate predictions rather than a family of tests hunting one effect; each is
reported with its own interval and read on its own.

**Secondary comparison: per duty-relation pair.** Surfaced pairs over total target pairs,
per stratum, per arm, per relation kind (`appliesIf`, `hasException`, `notApplicableIf`).
**This is reported descriptively and is NOT significance-tested.** Pairs are nested within
items and clustered hard by the fanout skew above, so a test over them would overstate
precision. It is there to show *what* was reached, which is the interesting half, not to
carry the claim.

**Reported alongside, all free, none of it a headline:** inter-arm verdict disagreement
(Part D item 2), `no_reliance` counts per arm, `no_targets` counts per arm, turns, tool
calls, tokens, turn-cap hits and errors.

**Tier 2 (use)**, whether the final answer *acted* on what it reached, needs a judgement
and therefore a validation sheet. Per E2 it runs **only if tier 1 separates**, on a small
slice, and is **labelled exploratory**. It is not the study and it is not pre-registered
here beyond that condition.

### What is not measured, and stays not measured

- **Support (entailment) produces no number.** Parked, not dropped. The 2026-09-13
  validation failure (best kappa 0.133 across four configurations) and the 2026-09-14
  finding that limb (c) is ambiguous between support and aptness are content for
  *discussion*, not inputs to a result.
- **Aptness is retired**, with the matcher validation sheet it owed.
- **No per-class metric against LexiGen gold labels**, and no reporting of how often an arm
  matches the corpus label. However caveated, it reads as accuracy, which evidence pass 2
  ruled out.
- **No faithfulness claim.** Measuring reach is not measuring whether what was reached
  drove the verdict, and no draft may blur them.
- **No performance, accuracy, legal-correctness or human-usefulness claim.**
- **The corpus is synthetic.** Nothing measured on it transfers to real-world policies.
  That caveat is mandatory and may not be softened.

### One parameter deliberately left unfixed

**M, the stability subsample size** (Part D item 4), is the author's and is **not chosen
here**. Part E does not override Part D item 4, so the N = 5 stability measurement remains
current and remains unrunnable until M is set. **No stability number may be produced under
this pre-registration.** When M is fixed, the stability analysis is pre-registered
separately, before its run, on the same terms as this file.

---

## 6. Conditions under which this study is reported as null

Named in advance so that a null cannot be reinterpreted afterwards.

- The arms do not separate on Articles 13 and 14. That is a result, it is reported, and
  `00_BRIEF.md` already provides for "evaluation" shrinking to ~700 words on Parts A and B.
- The arms separate on Article 46. That is an instrument failure and is reported as one;
  no separation elsewhere may be claimed on the strength of a run in which it happens.
- `no_reliance` dominates either arm. The model did not use the surface and the measure
  did not get a chance to run; the item counts are reported and no rate is claimed.

**The paper survives without this study. It does not survive this study being
overclaimed.**
