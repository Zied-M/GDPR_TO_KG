# The extractor hand-check, 2026-09-15 (S7)

**This is the gate S7 had to pass, and it is a check on an instrument, not a result.**
`reach.py` is a new automatic component and this project has been burned twice by
trusting one unchecked (the entailment metric at kappa 0.133 across four configurations,
and limb (c)'s support/aptness ambiguity found only afterwards). Reading a tool log is
not a judgement call, so the check is cheap and there was no excuse for skipping it.

**Nothing below is a number from the study.** The traces were generated on the **stale**
`s5_pilot/sample.frozen.json`, which E4 re-draws in S8, on six items picked to span the
strata rather than drawn as a batch. No verdict, rate or count here may enter a draft.

## What was read

12 traces: 6 items x 2 arms, `qwen2.5:7b`, `num_ctx` 16384, turn cap 10.
Turn cap hit 0 times, errors 0, max `prompt_eval_count` 1933 of 16384.

| item | article | stratum | read |
|---|---|---|---|
| seg01511 | 12 | APP-12 | both arms |
| seg00196 | 13 | APP-13 | both arms |
| seg00808 | 14 | APP-14 | both arms |
| seg01231 | 14 | APP-14 | both arms |
| seg05439 | 46 | APP-46 | both arms |
| seg07789 | 46 | NA-46 | both arms |

Artifacts: `handcheck.traces.json`, `handcheck.traces.reach.json`. Reproduce with the
commands in `README.md`.

## Two defects found by eye, both fixed

**1. Surfacing matched unit ids instead of character spans, and it was a false negative
against the TEXT arm.** Found on `seg01511`. The text arm called
`get_conditions("Article 12(5), subparagraph 1")` and was returned all four subunits of
Article 12(5). The condition `cond-12-5-unfounded-excessive` grounds in the **paragraph**
`art12-p5`, whose id was never in the returned list, so the extractor called it unreached
when the model had read every word of it. The extractor now merges the returned character
spans against the pinned source and asks whether the relation's provision is covered at
any granularity, in both directions. This mattered more than a rounding error: the measure
is only credible if the baseline is not quietly cheated, and this cheated it.

**2. A self-check fixture that passed for the wrong reason.** Case 2 built the sibling
list by hand rather than taking it from the store. The real `get_conditions` excludes the
queried unit itself, so its return has a hole in it and does not cover the parent
paragraph; the hand-built list had no hole and made the case pass on behaviour the store
cannot produce. The fixture now calls the real store. Structurally, **0 of the 223**
cross-provision attachments are reachable by sibling expansion alone, which is E3's claim,
verified rather than assumed.

## One structural fact found while checking, which sharpens E3 without contradicting it

Computed from files on disk, no model runs, the same class of fact as E3's inventory.

| text-store path | cross-provision attachments reachable |
|---|---|
| sibling expansion alone | **0 of 223** |
| plus the duty's own provision text, which `find_duties` normally returns too | **40 of 223** (Art 13: 29, Art 14: 9, Art 12: 2) |

All 40 are relations grounded in the duty's **parent paragraph**, whose chapeau the text
arm ends up covering once the hole is plugged. The remaining **183** stay out of the text
store's reach on any path short of the model searching for the exception itself, which is
E3's deliberate escape route.

**E3's sentence is true exactly as written** and needs no edit. What changes is what a
draft may say about headroom: the text arm's structural ceiling on this measure is 40, not
0, and **any sentence implying the text arm can reach none of the 223 would be an
overclaim**. Flagged for the author; no context file was edited on this.

## What the reading confirmed

- Retrieval is identical across arms on every item read: the same five provisions came
  back, differing only in whether the store answered with chunks or with duties. E1a's
  non-variable holds in practice, not just in the code.
- `no_reliance` occurs in **both** arms (`seg00196` text, `seg01231` graph), so it is a
  model behaviour and not a text-arm artifact. Keeping it a separate status rather than a
  zero is load bearing.
- Same-provision relations are correctly excluded: `seg00196` graph was returned four
  relations and scored three, `cond-13-2-c-consent-basis` grounding in the duty's own
  provision.
- The shared node resolves across articles: `cond-collected-from-data-subject` reports
  `['art13-p1', 'art14-p1']`, which is `build_payloads.py`'s hard-won behaviour intact.
- Both Article 46 items land on `no_targets` in both arms, which is E5's pre-registered
  null appearing as a distinct status rather than as a zero that could be misread.
- The text arm's escape route fires on its own: on `seg00808` and `seg01231` it reached
  `exc-art14-5-b` because `find_duties` happened to return `art14-p5-b` among its five.

## After the fixes

All 12 extractor verdicts match the by-eye reading, pair by pair. `reach.py --selfcheck`
covers 10 cases, including both span-coverage directions and the partial-read negative.
