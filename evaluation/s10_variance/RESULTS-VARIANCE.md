# Results: the temperature-0.7 rung of the variance study, run 2026-09-17/18 (S10)

> **READ `README.md` IN THIS DIRECTORY FIRST.** This is EXPLORATION, not the frozen study.
> By the author's decision of 2026-09-20 this work earns **one or two sentences in
> *discussion* and nothing in *evaluation*. The *evaluation* section is built on
> `s6_tools/RESULTS-REACH.md` and `s6_tools/RESULTS-GRADED.md`, which this does not alter.
> **This study measured CONSISTENCY; those measured COMPLETENESS. They are different
> quantities and neither qualifies the other.**

**Results record, not a draft.** This is EXPLORATION, in `paper_draft/s10_variance/`.
Nothing is written into `s6_tools/`. The *evaluation* section stays unwritten.

**Rung 1.0 was subsequently RUN, 2026-09-18/20, and is reported in the addendum at the end
of this file.** The section below reports the 0.7 rung as written at the time; none of its
numbers are altered.

**Digest verified before any result was read:** `PREREGISTRATION-VARIANCE.md` =
`f7d0850283c565ae38f52cdd16d78a4ca5aca1238a25b04106d5eb3b94752489`, matching its
`.sha256`, unedited. The three `s6_tools/` pre-registrations were re-verified unchanged:
`eddf157f...`, `3b4b3e91...`, `1a9a5f41...`.

Sample `stability.frozen.json` reused unmodified, seed `20260916`, payload
`7b942344...`. M = 50 items, N = 10 repeats, 2 arms = **1,000 generations, 347 minutes.**
`qwen2.5:7b` blob `845dbda0ea48ed74`, `num_ctx` 16384, **temperature 0.7**, turn cap 10,
k = 5, no seed set.

## Execution

| | |
|---|---|
| turn cap hits | **0** |
| execution errors | **0** |
| items excluded, below 8 usable repeats | **0** |
| max `prompt_eval_count` | **4546 of 16384** |
| mean turns | 4.00 |

**The load-state control held, and both detectors agree.** S10 discovered that greedy
output can differ between two loads of the same blob (`FINDING-LOAD-STATE.md`), so this
run was executed on a single verified load:

- the model was explicitly unloaded and freshly loaded before the run
- **canary-start**, 10 items at temperature 0.0 across all five strata, reproduced the S9
  stability run **20 of 20** before the rung began
- **canary-end**, the same 10 items after the rung, again **20 of 20 against S9 and 20 of
  20 against canary-start**
- `ps_start` and `ps_end` are identical (`size_vram` 5,537,654,784)
- **0 load spikes over 1s in 1,000 units**, max `load_duration` 0.32s

**No reload occurred during this rung**, so its variance is attributable to sampling and
not to load state. The canary is an execution control added after the freeze; it produces
no number entering the analysis.

**The instrument paid its hand-check before producing any number**, as pre-registered.
`variance_analyse.py --selfcheck` passes, and the raw relied sets behind the modal share
were printed and verified by hand on **8 item-arms across 4 strata**, including APP-13 and
APP-14 where the result lives. Every bucket count summed to 10, every modal count matched
the largest bucket, every distinct count matched the number of buckets.

---

## The primary measure

Modal relied-provision-set share: the fraction of the 10 runs agreeing with the plurality
`relied_units` set. **Stratified, never pooled. No headline number across strata and none
may be constructed.**

| stratum | arm | n | median | mean | min | all 10 identical |
|---|---|---|---|---|---|---|
| APP-12 | graph | 5 | 0.400 | 0.420 | 0.300 | 0 |
| APP-12 | text | 5 | 0.500 | 0.460 | 0.300 | 0 |
| APP-13 | graph | 15 | 0.400 | 0.460 | 0.300 | 0 |
| APP-13 | text | 15 | 0.500 | 0.480 | 0.300 | 0 |
| APP-14 | graph | 20 | 0.500 | 0.510 | 0.300 | 0 |
| APP-14 | text | 20 | 0.600 | 0.635 | 0.200 | **4** |
| APP-46 | graph | 5 | 0.900 | 0.880 | 0.800 | 1 |
| APP-46 | text | 5 | 0.500 | 0.540 | 0.400 | 0 |
| NA-46 | graph | 5 | 0.800 | 0.740 | 0.500 | 0 |
| NA-46 | text | 5 | 0.800 | 0.780 | 0.600 | 0 |

**Across all 100 item-arms, only 5 produced the same relied-provision set on all 10 runs.**

The arm comparison, paired Wilcoxon signed-rank, two-sided, alpha 0.05 per stratum, no
correction across strata:

| stratum | n paired | non-zero pairs | median paired diff | p |
|---|---|---|---|---|
| APP-13 | 15 | 9 | 0.000 | **0.645, not significant** |
| APP-14 | 20 | 16 | 0.000 | **0.095, not significant** |
| APP-12 | 5 | 3 | | **no test**, below the 6-pair minimum; smallest achievable p 0.250 |
| APP-46 | 5 | 5 | | **no test**, below the minimum; smallest achievable p 0.0625 |
| NA-46 | 5 | 4 | | **no test**, below the minimum; smallest achievable p 0.125 |

---

## READ AGAINST THE PRE-REGISTERED PREDICTIONS

| named in advance | outcome |
|---|---|
| Hypothesis: graph more stable than text on APP-14 and APP-13 | **NOT SUPPORTED** |
| **NULL A**, no arm difference | **HOLDS on both testable strata** |
| **NULL B**, nothing moves at all | **DECISIVELY FALSIFIED** |
| **NULL C**, hypothesis reversed | **numerical direction, not significant** |
| **NULL D**, temperature does nothing monotone | **falsified so far**, 1.000 at T=0 to ~0.5 at T=0.7 |

**NULL B is falsified and this is the substantive answer to the author's concern.** At
temperature 0.7 the relied-provision set is **highly unstable in both arms**: median modal
shares of 0.400 to 0.600 on the three applicable-article strata, and only 5 of 100
item-arms fully stable. A justification's provision basis **does change between runs**, and
it changes a great deal. The S9 temperature-0 result of 1.000 everywhere was exactly the
floor `PREREGISTRATION-STABILITY.md` section 5 said it was.

**NULL A holds: the substrate does not buy consistency under sampling.** Neither testable
stratum separates. The median paired difference is **0.000 on both**.

**The candidate hypothesis offered in `KICKOFF.md` section 6 is not supported, and the
numerical direction runs the other way.** The text arm's mean modal share is **higher than
the graph arm's in four of the five strata** (APP-12 0.460 vs 0.420, APP-13 0.480 vs 0.460,
APP-14 0.635 vs 0.510, NA-46 0.780 vs 0.740), and the only all-identical items in a
testable stratum are the text arm's 4 on APP-14. **None of this reaches significance and
none of it may be reported as a reversal**; the honest statement is that the prediction
failed and the data lean the other way.

`KICKOFF.md` said the hypothesis "could equally come out flat, or reversed". It came out
flat, leaning reversed.

## The one place the graph arm looks more stable, and why it argues against a relations story

**APP-46: graph 0.880 against text 0.540.** It is the largest arm gap in the table and it
is the wrong stratum for the hypothesis: **Article 46 carries zero cross-provision
attachments**, so whatever produced that gap cannot be the representation's relations. With
n = 5 and no test permitted, nothing may be built on it. It is recorded because it cuts
against the mechanism the hypothesis proposed, not because it supports an alternative.

## Secondary lines, descriptive only, no test

**Reach-status stability is higher than relied-set stability**, as a coarser measure
should be: median status modal share 1.000 on APP-13 graph, APP-46 both arms and NA-46 both
arms, against relied-set medians of 0.400 to 0.900. A model can arrive at the same reach
verdict by different provision routes, which is the distinction the primary measure exists
to see.

**The S9 binary is reported for continuity and is N-dependent.** All-identical counts are
in the table above. A binary at N = 10 is not comparable to one at N = 5 and the two must
never be placed side by side as if they were.

## Instrument check 2, monotonicity: PASSES SO FAR, and is not complete

Temperature 0.0 gave 1.000 in every stratum and arm (S9, same 50 items, same harness,
re-verified here by both canaries). Temperature 0.7 gives 0.400 to 0.900. The ordering is
monotone decreasing everywhere. **The check is not complete until rung 1.0 runs**, since its
condition is that 1.0 must not read as *more* stable than 0.7.

---

## WHAT MAY AND MAY NOT BE SAID

**Earned, on a pre-registered primary measure with its nulls named in advance:**

> At temperature 0.7 the set of provisions an LLM relies on in reaching a compliance
> judgement is highly unstable across repeated runs on the same policy segment: on 50
> items at 10 repeats, only 5 of 100 item-arms produced the same relied-provision set every
> time, with median modal shares of 0.400 to 0.600 on the applicable-article strata.
> **The structured substrate did not reduce this.** Neither testable stratum separated the
> two arms (Wilcoxon p = 0.645 on Article 13, p = 0.095 on Article 14, median paired
> difference 0.000 on both).

**Constraints that travel with it, none softenable:**

1. **This is ONE temperature rung.** 1.0 is unrun and 0.3 was never paid for.
2. **The corpus is synthetic.** Nothing here transfers to real-world policies.
3. **Stratified, never pooled.** Three of five strata carry no test at all, by a rule fixed
   before the run rather than after.
4. **Reachability is not the claim**, and this is not a reachability measure.
5. **This does not contradict the reach or graded results.** Those measured *completeness*
   of cross-provision coverage at temperature 0; this measures *consistency* of the relied
   set under sampling. `RESULTS-GRADED.md`'s separation stands untouched, and a draft may
   not use this null to qualify it without saying they measure different quantities.
6. **The graph arm's near-1.0 coverage figures elsewhere are structural.** Nothing here
   changes that, and nothing here is evidence about coverage.
7. **`no_reliance` is not a zero**; no item was all-empty across every run in any stratum.
8. **The pre-registration has a digest but no timestamped history.** A draft may say this
   was pre-registered, which it was, but may not imply the ordering is externally
   verifiable.
9. **No headline claim is picked here.** That is the author's.

**Not claimed:** no pooled figure; no faithfulness claim; no cross-article claim; no
significance for any direction in any stratum; no reading of Article 46's arm gap; and **no
number from the final-answer citation parser**, which is still unbuilt and still owes its
hand-check.

## Artifacts

| file | what |
|---|---|
| `var07.traces.json` | 50 items x 10 repeats x 2 arms at T=0.7, full trace per run |
| `var07.traces.json.partial.jsonl` | the incremental record |
| `var07.reach.json` | `reach.py` output, extractor unmodified |
| `var07.analysis.json` / `.txt` | `variance_analyse.py` output |
| `var07.runlog.txt` | the run log |
| `canary_start.*` / `canary_end.*` | the load-state controls, 20 of 20 against S9 at both ends |
| `icheck1*.{traces,reach}.json` | the three passes that produced `FINDING-LOAD-STATE.md` |
---

# Rung 1.0, run 2026-09-18/20 (S10). THE LADDER IS NOW COMPLETE

**Digest re-verified before any result was read:** `PREREGISTRATION-VARIANCE.md` =
`f7d0850283c565ae38f52cdd16d78a4ca5aca1238a25b04106d5eb3b94752489`, unedited. The three
`s6_tools/` pre-registrations re-verified unchanged.

Same 50 items, N = 10, both arms, **temperature 1.0**, 1,000 generations. Turn cap hits
**0**. **2 execution errors**, both flagged per E8 and neither silently included: one
`chat call failed: timed out` (seg05319 text) and one truncation-guard trip
(seg02405 graph, `prompt_eval_count` 16224 within 512 of `num_ctx` 16384 on turn 6). Those
two repeats are excluded per section 4, leaving those items 9 usable repeats each.
**0 items fell below the 8-repeat threshold**, so no item was excluded.

## THE RUN WAS SPLIT ACROSS TWO CONFIGURATIONS, AND THIS IS THE LOAD CAVEAT

**The author paused the rung at 281 of 500 units and resumed it two days later.** The two
segments were produced under different runtime configurations and that is stated here rather
than discovered later.

| | segment 1, units 1 to 281 | segment 2, units 282 to 500 |
|---|---|---|
| start canary vs S9 | **PASS 20 of 20** | **FAIL 2 of 20** |
| end canary vs S9 | **FAIL 3 of 20** | **FAIL 2 of 20** |
| internal consistency | not measurable | **end canary vs resume canary: 0 of 20** |
| `size_vram` | 5,537,654,784 class | **5,025,607,680** |

**Each segment is internally consistent**; they differ from each other, and from S9, on a
small set of borderline items (`seg00949` graph, `seg01230` text, plus `seg00338` and
`seg00572` at the pause). **The `ps_start` recorded in `var10.traces.json` is segment 2's**,
because the blob is written by the process that finishes the run; segment 1's configuration
is recoverable only from `canary10_start`.

**Why this is tolerable here and must still be reported.** The quantity measured is
run-to-run variability at temperature 1.0, where median agreement is 0.30 to 0.50. A
configuration difference that flips 2 to 3 of 20 item-arms at *greedy* decoding is small
beside that. **It is not zero, it is not quantified, and no reader may be left to assume the
rung ran under one configuration.** See `FINDING-LOAD-STATE.md` and its 2026-09-19
correction.

## The primary measure at temperature 1.0

| stratum | arm | n | median | mean | min | all 10 identical |
|---|---|---|---|---|---|---|
| APP-12 | graph | 5 | 0.300 | 0.400 | 0.200 | 0 |
| APP-12 | text | 5 | 0.400 | 0.420 | 0.300 | 0 |
| APP-13 | graph | 15 | 0.300 | 0.357 | 0.200 | 0 |
| APP-13 | text | 15 | 0.400 | 0.450 | 0.300 | 0 |
| APP-14 | graph | 20 | 0.400 | 0.375 | 0.200 | 0 |
| APP-14 | text | 20 | 0.500 | 0.530 | 0.200 | 1 |
| APP-46 | graph | 5 | 0.900 | 0.880 | 0.800 | 1 |
| APP-46 | text | 5 | 0.500 | 0.520 | 0.200 | 0 |
| NA-46 | graph | 5 | 0.900 | 0.760 | 0.400 | 0 |
| NA-46 | text | 5 | 0.900 | 0.840 | 0.600 | 2 |

| stratum | n paired | non-zero | median paired diff (graph minus text) | p |
|---|---|---|---|---|
| APP-13 | 15 | 12 | **-0.100** | **0.0420, SIGNIFICANT** |
| APP-14 | 20 | 19 | **-0.150** | **0.0208, SIGNIFICANT** |
| APP-12 | 5 | 4 | | no test, smallest achievable p 0.125 |
| APP-46 | 5 | 5 | | no test, smallest achievable p 0.0625 |
| NA-46 | 5 | 4 | | no test, smallest achievable p 0.125 |

## THE OUTCOME: NULL C, AND IT IS THE PRE-REGISTERED REVERSAL

**Both testable strata separate at temperature 1.0, and both separate in FAVOUR OF THE TEXT
ARM.** The graph arm's relied-provision set is **less** stable, by a median of 0.100 on
Article 13 and 0.150 on Article 14.

`PREREGISTRATION-VARIANCE.md` section 5 named this outcome in advance as **NULL C, the
hypothesis reversed**, and called it "explicitly live". It is what happened. **The candidate
hypothesis from `KICKOFF.md` section 6 is not merely unsupported; at temperature 1.0 the
data run against it with p < 0.05 on both testable strata.**

**Read together with rung 0.7**, which was flat and leaned the same way (p = 0.645 and
0.095, both non-significant, text numerically ahead in four of five strata), the picture is
consistent across two independent rungs: **the structured substrate does not buy consistency
under sampling, and under heavier sampling it costs some.**

**Restraint on that sentence, and it is not optional.** Alpha is 0.05 per stratum with **no
correction across strata**, as pre-registered; two strata at p = 0.042 and p = 0.021 are not
a strong joint result. Three of five strata carry no test. The configuration split above is
unquantified. **This is an exploratory finding on 50 synthetic items with one model, and it
may not be stated as an established property of graph substrates.**

## The ladder, all three rungs

Mean modal share, per stratum and arm:

| stratum | arm | T = 0.0 | T = 0.7 | T = 1.0 |
|---|---|---|---|---|
| APP-12 | graph / text | 1.000 / 1.000 | 0.420 / 0.460 | 0.400 / 0.420 |
| APP-13 | graph / text | 1.000 / 1.000 | 0.460 / 0.480 | **0.357** / 0.450 |
| APP-14 | graph / text | 1.000 / 1.000 | 0.510 / 0.635 | **0.375** / 0.530 |
| APP-46 | graph / text | 1.000 / 1.000 | 0.880 / 0.540 | 0.880 / 0.520 |
| NA-46 | graph / text | 1.000 / 1.000 | 0.740 / 0.780 | **0.760 / 0.840** |

## INSTRUMENT CHECK 2, monotonicity: PASSES IN 8 OF 10, FAILS NOMINALLY IN NA-46

The check requires that stability not **rise** with temperature. It holds in **8 of the 10
arm-stratum cells**. It fails nominally in **NA-46, both arms**: graph 0.740 to 0.760 and
text 0.780 to 0.840 from 0.7 to 1.0.

**Reported as a partial failure rather than waved through.** NA-46 is an n = 5 stratum that
carries no test by the minimum-pairs rule, and a rise of 0.02 to 0.06 on five items is well
inside sampling noise at that size. **But the check was named in advance and its condition
was "must not exceed by more than sampling noise", which is a judgement this record does not
get to make in its own favour.** The honest statement: **the ladder is monotone everywhere it
is powered, and non-monotone in the one stratum too small to test.** Any reading of the
temperature gradient must carry that.

## What rung 1.0 changes, and what it does not

- **It completes the pre-registered ladder.** All three rungs exist and the design is no
  longer partly run.
- **It strengthens the answer to the author's concern.** At temperature 1.0 **not one item
  in APP-12, APP-13 or APP-14, in either arm, held the same relied-provision set across all
  ten runs** (the only all-identical items are 1 in APP-14 text, 1 in APP-46 graph and 2 in
  NA-46 text).
- **It does NOT touch the reach or graded results.** Those measure completeness of
  cross-provision coverage at temperature 0; this measures consistency under sampling.
  `RESULTS-GRADED.md` stands unaltered.
- **It does not license a claim that graphs are worse.** See the restraint paragraph above.
- **The corpus is synthetic.** Nothing here transfers to real-world policies.

## Artifacts added

| file | what |
|---|---|
| `var10.traces.json` / `.partial.jsonl` | 1,000 generations at T=1.0, across two segments |
| `var10.reach.json` | `reach.py` output, extractor unmodified |
| `var10.analysis.json` / `.txt` | `variance_analyse.py` output |
| `canary10_start.*` | segment 1 start, PASS 20 of 20 |
| `canary10_pause.*` | segment 1 end, FAIL 3 of 20 |
| `canary10_resume.*` / `canary10_resume2.*` | segment 2 start, FAIL 2 of 20, two GPU splits |
| `canary10_end.*` | segment 2 end, FAIL 2 of 20 vs S9, 0 of 20 vs the resume canary |
