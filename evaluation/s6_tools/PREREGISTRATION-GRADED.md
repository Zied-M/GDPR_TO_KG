# Pre-registration: the graded-measure study

**Written 2026-09-16 (S9), BEFORE any generation on these items. Nulls included. Not to
be edited after a run.** Its digest is recorded in `PREREGISTRATION-GRADED.sha256`; an
edited file is a failed pre-registration rather than a revised one.

**`PREREGISTRATION.md` and `PREREGISTRATION-STABILITY.md` are frozen and are NOT edited
by this file.** All three stand side by side. The reach study is complete and its result
does not depend on anything here.

Operative design: `context/05_EVAL_PLAN.md` **Part E**, unchanged. The tool surface, the
two stores, the retrieval non-variable, the model, `num_ctx`, temperature and turn cap are
all exactly as Part E fixes them and as the reach study ran them. **Nothing about the
instrument changes. Only the statistic computed over it does.**

---

## 1. Why this study exists, stated honestly

The reach study's primary measure is **binary per item**: did the trace surface *at least
one* target relation? On Articles 13 and 14 the graph arm reached on every item and the
text arm reached on almost every item, so the measure **saturated** and could not
discriminate. Article 13 returned zero discordant pairs and no test was possible.

Looking underneath that null **after the data existed**, the fraction of targets surfaced
per item separated the arms completely on both strata. **That observation is post-hoc.**
It is a real measurement of real traces, read mechanically by a frozen extractor, and it
is reported in `RESULTS-REACH.md` as an **exploratory** finding. What it cannot do is
carry an inferential claim, because a reader cannot verify how many other statistics could
have been computed before that one was chosen.

**This study exists to convert that observation into a prediction tested on data nobody
has seen.** If it confirms, the claim is earned. If it does not, the exploratory
observation still stands as what was measured in S9, qualified by this result. **Both
outcomes are reported.**

---

## 2. The one change, and everything that does not change

**Changed: the primary statistic.**

> For each item, the **fraction of its target (duty, relation) pairs that were surfaced**:
> `n_surfaced / n_targets`, which `reach.py` already records per item as `n_surfaced` and
> `n_targets`. **No new instrument is built and `reach.py` is not touched.**

**Unchanged, and none of it is reopened:** the tool surface and both stores; `find_duties`
over one shared index, BM25, k = 5; the definition of reliance, anchored at the
**provision** and not the duty id; the definition of a **target** as a (duty, relation)
pair the graph grounds in a different provision; **surfaced** read from machine provenance
and never from prose; `qwen2.5:7b` pinned with its blob digest recorded; `num_ctx` 16384
explicit; temperature **0.0**; turn cap 10 with per-item flagging; source digests
re-verified on load.

**The four statuses are unchanged and the exclusions are the same.** An item contributes a
fraction only when its status is `reached` or `not_reached`. `no_targets` has no
denominator and is excluded; `no_reliance` is excluded and **reported separately, never
folded in**. Items flagged `turn_cap_hit` or carrying an execution error are excluded from
the statistic and reported separately, per E8.

---

## 3. A structural caveat that is stated BEFORE the run, not after

**The graph arm's fraction is expected at or near 1.0 by construction, and that is not a
finding.** `get_conditions` on the graph store returns the relation nodes attached to the
duty, so once the model relies on a duty, that duty's cross-provision relations are
surfaced by the tool return itself. A graph-arm figure near 1.0 measures **the tool
surface**, not model behaviour, and **no draft may present it as a behavioural result.**

**The informative quantity is the text arm's fraction.** The text store cannot deliver
relations in its own currency, by E1's boundary, so whatever the text arm reaches, it
reaches by its own searching. The study is therefore best read as: **how much of the gap
does model effort close when the representation does not close it for you?**

This is written here so that it cannot be presented as a discovery afterwards, and so that
a large separation cannot be read as larger than it is.

---

## 4. The sample, frozen before any run

Drawn by `freeze_graded.py` into `graded.frozen.json`, **before this file was written**.

- **seed `20260917`**, a third independent stream after the study's `20260915` and the
  stability subsample's `20260916`
- graded sha256 `d16e64990f38b09fda56ddc958a04e30dc8edc4351eceec5679e8dc0d9f87694`
- corpus sha256 `a9cbcdb548d44b6b223052c1995c1a397b0abd76a1d72fd4cc8cd039f47ecefd`

**DISJOINT from every item already used**: all 250 reach-study items and all 40 pilot
items are excluded, 290 in total, asserted in the freeze rather than checked afterwards.
The effect size was estimated from the reach results, so re-using those items would be
circular and the confirmation would be worth nothing.

| stratum | article | labels | n |
|---|---|---|---|
| APP-14 | 14 | COMPLIANT + NON_COMPLIANT | 74 |
| APP-13 | 13 | COMPLIANT + NON_COMPLIANT | 74 |
| APP-12 | 12 | COMPLIANT + NON_COMPLIANT | 24 |
| APP-46 | 46 | COMPLIANT + NON_COMPLIANT | 24 |
| NA-46 | 46 | NOT_APPLICABLE | 24 |
| | | | **220** |

220 items x 2 arms = **440 generations**.

**APP-14 is pool-limited at 74 and this is a real constraint, not a choice.** Only 75
unused Article 14 segments remain after the reach study. Article 14 carries 159 of the 223
cross-provision attachments, so it is the stratum that matters most and it is the one that
could not be made larger. **No pilot is drawn:** the harness was checked end to end in S9
with 0 cap hits and 0 errors across 540 generations, and spending 40 more on a second
plumbing check would buy nothing.

---

## 5. The prediction, fixed before the data

| stratum | cross-provision attachments | prediction |
|---|---|---|
| Article 14 | 159 | **separation** |
| Article 13 | 62 | **separation** |
| Article 12 | 2 | little or none |
| Article 46 (both strata) | 0 | **no separation** |

**Article 13 is the load-bearing prediction.** It was predicted to separate in
`PREREGISTRATION.md`, did **not** separate on the binary measure, and is predicted to
separate here. That is the claim being put at risk: if the graded measure does not
separate Article 13, the binary null stands and the post-hoc observation is weakened.

**The expected shape:** the graph arm at or near 1.0 by construction (section 3), and the
text arm substantially below it, with the gap larger on Article 14 than on Article 13.

**Separation on Article 46 remains an INSTRUMENT FAILURE, not a finding.** Article 46 has
zero cross-provision attachments, so every Article 46 item should land on `no_targets` in
both arms and contribute no fraction at all, exactly as it did in the reach study. A
non-trivial number of Article 46 items producing a fraction is a failure of the
instrument and must be reported as one, and no separation elsewhere may be claimed on the
strength of a run in which it happens.

---

## 6. The analysis, stated before the data

**Stratify, never pool.** Per stratum, per arm. There is no headline number across strata
and one may not be constructed afterwards.

- **Primary:** within each stratum, over items where **both** arms produced a fraction,
  the paired per-item difference is tested with the **Wilcoxon signed-rank test, exact
  where n permits** (implemented locally, no new dependency), two-sided, **alpha 0.05 per
  stratum, no correction across strata**, for the same reason `PREREGISTRATION.md` gives:
  the strata are separate questions with separate predictions, not a family of tests
  hunting one effect.
- Reported with the test, always: **n paired, the number of ties, the median per-arm
  fraction and the median paired difference**, so a reader sees what the test ran on
  rather than a p value alone.
- **Distributional reporting, which is the interesting half:** per arm, per stratum, the
  count of items reaching **all** targets, **none**, and **partial**. The reach study's
  exploratory look separated cleanly on exactly this cut, and it is reported whether or
  not the test is significant.
- **Secondary, descriptive only and NOT significance-tested:** pooled pairs by relation
  kind (`appliesIf`, `hasException`, `notApplicableIf`), as in the reach study, and the
  **distinct-relation counts** per arm. The distinct counts are mandatory: in the reach
  study the text arm surfaced 7 of 7 distinct Article 14 relations, so a large pair-level
  gap is **not** a reachability claim, and the distinct counts are what stop it being read
  as one.
- **Reported alongside, none of it a headline:** `no_reliance` and `no_targets` counts per
  arm, turns, calls, tokens, turn-cap hits and errors.

**The binary per-item statistic of `PREREGISTRATION.md` is also reported on this sample**,
so the two measures can be compared on the same items. It is reported **descriptively**;
the reach study's pre-registered test is not re-run here and this sample does not revise
that study's result.

### What is not measured, and stays not measured

Unchanged from `PREREGISTRATION.md`: no support or entailment number (parked); no aptness
number (retired); no per-class metric against LexiGen gold labels and no accuracy reading
of the verdict line; **no faithfulness claim**, since reaching more is not evidence that
what was reached drove the verdict; no performance, legal-correctness or human-usefulness
claim. **The corpus is synthetic and nothing measured here transfers to real-world
policies**; that caveat is mandatory and may not be softened.

**Tier 2 (use) is not run under this pre-registration.**

---

## 7. Constraints on any positive result, carried forward unchanged

- **The honest headroom is 183 of 223, not 223.** Sibling expansion alone reaches 0, but
  `find_duties` normally returns the duty's own provision too, bringing 40 parent-grounded
  relations into the text arm's reach. No sentence may imply the text arm reaches none.
- **The fanout is severely skewed:** 8 nodes carry 201 of the 258 attachments and 32 of
  the 44 have fanout 1. Any separation travels with that sentence.
- **Zero cross-article relation attachments exist in this frozen scope.** Only the
  cross-provision claim is supported.
- **Reachability is not the claim.** The reach study's own distinct-relation counts show
  the text arm reaching 7 of 7 Article 14 relations and 3 of 4 in Article 13. Whatever
  this study finds, it is about **completeness and consistency of coverage**, never about
  what a text baseline is capable of reaching.
- **The pre-registrations have digests but no timestamped history.** A draft may say the
  study was pre-registered, which it was, but may not imply the ordering is externally
  verifiable.

---

## 8. Conditions under which this study is reported as null

Named in advance so a null cannot be reinterpreted afterwards.

- **The arms do not separate on Article 13.** The binary null stands, the S9 exploratory
  observation is reported as weakened by a pre-registered test that failed to confirm it,
  and no draft may present the exploratory figures as though this had not happened.
- **The arms do not separate on Article 14.** The reach study's Article 14 result stands
  on its own binary measure and the graded measure is reported as not confirming.
- **The arms separate on Article 46.** Instrument failure, reported as one, and nothing
  else in the run may be claimed on its strength.
- **`no_reliance` dominates either arm**, or `no_targets` leaves too few paired items to
  test. The counts are reported and no rate is claimed.

**The paper survives without this study. It does not survive this study being
overclaimed.**
