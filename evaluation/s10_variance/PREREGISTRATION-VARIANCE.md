# Pre-registration: the temperature-above-zero variance study (S10)

**Written 2026-09-17 (S10), BEFORE any generation on the study items. Not to be edited
after a run.** Its digest is recorded in `PREREGISTRATION-VARIANCE.sha256`.

**This is EXPLORATION and it lives in `paper_draft/s10_variance/`.** It writes nothing into
`s6_tools/`. It reuses that directory's instruments by import and does not modify them.
`PREREGISTRATION.md`, `PREREGISTRATION-STABILITY.md` and `PREREGISTRATION-GRADED.md` are
frozen, were verified before this file was written, and are **not edited by this file.**

Design authority: `context/05_EVAL_PLAN.md` **Part D item 4** and **Part E**, neither
reopened. The four design parameters below were **delegated to this session by the author
on 2026-09-17, with justification required**, on the pattern of Part E item E1a.

---

## 1. Why this study exists

`PREREGISTRATION-STABILITY.md` section 5, written before its own run and confirmed by it:
at temperature 0.0, with a pinned model, deterministic BM25 retrieval and greedy decoding,
repeated runs are near-identical **by construction**, so the S9 result of 50 of 50 items
stable in both arms is **a floor, not a finding**. The author's concern was broader, that an
LLM justification **"can be undeterministic and can change"**. That concern is unanswered
and this study exists to answer it.

**Nothing in S9 is re-run, re-scored or contradicted here.** The temperature-0 result stands
as measured and keeps its stated limitation.

---

## 2. The parameters, all fixed before any run

| parameter | value | decided |
|---|---|---|
| temperature ladder | **0.7 and 1.0**, two paid rungs | session, 2026-09-17, below |
| N, repeats per item | **10** | session, 2026-09-17, below |
| sample | **`s6_tools/stability.frozen.json` reused**, M = 50 | session, 2026-09-17, below |
| arms | **both**, `text` and `graph` | session, 2026-09-17, below |
| model, `num_ctx`, turn cap, k | `qwen2.5:7b` blob `845dbda0ea48ed74`, 16384, 10, 5 | E4 and E8, unchanged |
| seed | **none set**, deliberately | section 6 |

Cost: 50 items x 10 repeats x 2 arms x 2 temperatures = **2,000 generations**. At the
0.334 minutes per generation S9 measured twice (168 min / 500, and 147 min / 440) that is
**about 11 hours**, and higher temperature may raise it if items take more turns.

### 2.1 Why the ladder is 0.7 and 1.0, and why 0.3 is not paid for

**Temperature 0.0 is already measured on these exact 50 items**, in both arms, at 1.000
everywhere. It is therefore the ladder's bottom rung **for free**, and the effective ladder
is 0.0 / 0.7 / 1.0 for the price of two rungs.

- **0.7 is the rung that makes the result relevant.** It is the conventional sampling
  temperature and the setting a practitioner would actually deploy.
- **1.0 is the stress rung**, unmodified sampling from the model's distribution. A null at
  0.7 alone invites the reply that 0.7 is mild for a constrained tool-calling task. A null
  that also holds at 1.0 is much harder to dismiss, and a separation that grows from 0.7 to
  1.0 has a shape a single rung cannot show.
- **0.3 is dropped on the cost argument, stated rather than hidden.** It sits close to
  greedy and would most likely reproduce the temperature-0 floor for 1,000 generations. If
  0.7 and 1.0 both come back flat, 0.3 would have been flat too; if they separate, 0.3 adds
  an interior point to a curve already anchored at three temperatures.

### 2.2 Why N = 10, chosen from the resolution the result must support

The per-item quantity is a share out of N (section 3), so N **is** the resolution: the grid
is 1/N and nothing finer can be seen.

**The decisive consideration is resolution at the top of the scale, because that is where
the hypothesis lives.** The graph arm is predicted near-perfect, so the study must be able
to tell "always the same" from "almost always the same". If an item's true per-run
agreement is 0.9, the probability that N runs all coincide anyway, and the item reads as
perfectly stable when it is not, is:

| N | P(item misreads as perfectly stable at true 0.9) | grid |
|---|---|---|
| 5 | **0.59** | 0.20 |
| 10 | **0.35** | 0.10 |
| 20 | 0.12 | 0.05 |

At N = 5 a genuinely imperfect item is **more likely than not** to be recorded as perfect,
which would blur exactly the comparison this study is for. **N = 10 is the smallest N at
which that misreading is less likely than not.** N = 20 buys more and costs another 11
hours, which is not worth 0.23 of misreading probability on a 50-item exploration.

**N and M remain separate knobs and are not conflated.** N is per-item resolution, fixed at
10 by the above. M is the interval and the paired-test power on the aggregate, fixed at 50
by section 2.3 and **not** adjustable by N.

### 2.3 Why the sample is reused rather than re-drawn

**`s6_tools/stability.frozen.json` is reused**, unmodified and not re-frozen: 50 items,
seed `20260916`, payload sha256 `7b942344089e2d4c1cbf42992bedd69b13b3c7a5d6cf00418ad06564ea210afa`,
strata APP-14 20, APP-13 15, APP-12 5, APP-46 5, NA-46 5.

- **It is the identical harness on identical items.** Any variance observed here cannot be
  attributed to a difference in item difficulty between two draws, because there is only
  one draw. A fresh sample would put that explanation back on the table for nothing.
- **The item-level tuning objection does not apply.** These items were frozen at seed
  `20260916` **before any generation existed**, by a session that could not have seen a
  temperature-above-0 result because none existed. Tuning requires choosing after seeing;
  nothing here could.
- **The paired-baseline argument is real but weaker than it looks, and is stated honestly.**
  The temperature-0 baseline is 1.000 on every item in both arms, and a constant does not
  need the same items to be compared against. What reuse actually buys is the two bullets
  above, not a statistical pairing.
- **The Article 46 strata are not waste here, which they would be for a reach measure.**
  All 50 Article 46 items landed on `no_targets` in both arms across two independent S9
  studies. But the primary measure below is the **relied-provision set**, which exists and
  can vary on an Article 46 item regardless of whether it has cross-provision relations.
  Those 10 items are therefore a working control and are named as an instrument check in
  section 5.

**The cost of reuse, stated before the run rather than discovered after it.** M = 50 is
fixed, so the per-stratum item counts are 20 / 15 / 5 / 5 / 5. **APP-12, APP-46 and NA-46
are underpowered by construction at n = 5** and cannot reach the pre-registered alpha under
section 4's own minimum-pairs rule. They are carried as descriptive strata, exactly as
Article 12 was in the reach and graded studies, and **no test is run on them**. The strata
that can carry a test are **APP-14 (n = 20) and APP-13 (n = 15)**.

### 2.4 Why both arms run

**Both.** A one-armed run is uninterpretable: if the text arm's relied set varies at 0.7,
nothing says whether that is the substrate or simply what sampling does to any arm. Only
the paired graph arm on the same item at the same temperature answers it. The candidate
hypothesis in `KICKOFF.md` section 6 is explicitly **asymmetric between arms**, so a design
that runs one arm cannot test it in either direction.

---

## 3. What is measured

**ONE primary measure, declared here and not swappable afterwards.**

**PRIMARY: the modal relied-provision-set share.** For each item, in each arm, at each
temperature: take the **relied-provision set** (`relied_units`, computed by `reach.py`,
already hand-checked in S7 and **not modified here**) from each of the N runs, group the N
sets by equality, and take

> modal share = (number of runs producing the most common relied-provision set) / N

which lies in [1/N, 1]. **1.0 means every run relied on the same provisions; a lower value
is the fraction of runs that agreed with the plurality.** This is the same `largest_agreeing`
quantity `stability_analyse.py` already computes for the S9 gradient, divided by N. It is
read mechanically from the tool-call log and **no prose is parsed anywhere.**

**Why this and not S9's binary "all N identical".** The binary is **N-dependent**: at any
fixed per-run variability, P(all N identical) falls as N rises, so a binary result at
N = 10 is not comparable to one at N = 5 and would misread a resolution change as an effect.
The modal share is a share and does not have that defect. The binary is **still reported**,
as a secondary line, for continuity with `RESULTS-STABILITY.md`, with its N-dependence
stated beside it.

**SECONDARY, descriptive only, no test:**

- the S9 binary, proportion of items whose relied set is identical across all N runs
- the distinct-set count per item, how many different relied sets the N runs produced
- **reach-status stability**, the coarser line, per item
- turns, calls, turn-cap hits, errors, `prompt_eval_count`

**PRODUCES NO NUMBER, and is not swappable in:** the provisions **cited in the final
answer**. That needs a prose parser, the parser was not built in S9 and is not built here,
and **it owes a hand-check on the same terms `reach.py` paid in S7 before it may produce
anything.** This project has been burned twice by an unchecked automatic component, the
entailment metric at kappa 0.133 and limb (c)'s support/aptness ambiguity. The gate stands.

**The one new automatic component is `variance_analyse.py`, and it owes its check.** It
computes the modal share from `reach.py` output and runs a paired test. It is thin by
construction, reusing `stability_analyse.group`, `stability_analyse.largest_agreeing` and
`graded_analyse.wilcoxon` rather than reimplementing them. It carries a `--selfcheck` with
hand-computable values, **and before any number from it is reported, the modal share of at
least three real items spanning at least two strata is verified by hand against the raw
relied sets printed from the traces file.** If that hand-check is not performed and
recorded, this study produces no number.

**Reported per arm, per stratum, per temperature. Stratify, never pool.** No headline
number across strata, and none may be constructed afterwards.

---

## 4. The analysis, stated before the data

- **Per-item:** modal share as above.
- **Aggregate per arm, per stratum, per temperature:** median and mean modal share, and the
  full distribution of per-item modal shares, because that distribution is what N = 10 was
  chosen to expose.
- **The arm comparison:** paired **Wilcoxon signed-rank**, two-sided, on the per-item
  difference (graph modal share minus text modal share), **alpha 0.05 per stratum, no
  correction across strata**, the same convention as the reach and graded studies.
  `graded_analyse.wilcoxon` is the instrument and is already on file.
- **MINIMUM-PAIRS RULE, fixed now.** A two-sided exact Wilcoxon cannot reach 0.05 with
  fewer than 6 non-zero paired differences, since 2/2^5 = 0.0625. **No test is run on a
  stratum with fewer than 6 non-zero pairs**; that stratum is reported descriptively with
  its pair count, and the smallest achievable p is stated beside it so an underpowered null
  is never read as an absence of effect. This is the Article 12 lesson from the graded
  study applied in advance.
- **The temperature comparison** is read off the three rungs descriptively, per arm, per
  stratum. **No test is run across temperatures** and none may be added later: the rungs are
  not independent samples of anything, they are three settings on the same 50 items.
- **Never folded into reach or into the graded measure.** Stability is reported separately,
  per the author's 2026-09-06 split, which holds.

**Exclusions, fixed now.**

- A repeat whose record carries a non-null `error` is **excluded from that item's repeat
  set**, because an errored generation is a harness event and not a different relied set.
- A repeat that **hit the turn cap is NOT excluded**. It completed its turns and its relied
  set is real. Turn-cap hits are counted and reported per item, per E8.
- An item with **fewer than 8 usable repeats of 10** is excluded from the primary aggregate
  and listed under `incomplete_items` with its usable count. The threshold is 8 and is
  fixed here.
- **`no_reliance` is not a zero.** An item whose runs never called `get_conditions` still
  has a relied set, possibly empty, and an empty set that is stable across runs **is**
  stable. But items whose relied set is empty in **every** run are reported as a separate
  count beside each stratum, because a perfectly stable emptiness is not evidence of a
  stable representation and must not be read as one.

---

## 5. The predictions, and the nulls named just as loudly

**A design may optimise POWER and never the sign of the outcome.** Designing toward a sign
is what produced the three withdrawn directions in this project. The nulls below are named
before the data and are live outcomes, not rhetorical.

**The candidate hypothesis, from `KICKOFF.md` section 6, adopted here as the alternative:**

> Above temperature 0 the graph arm's relied-provision set stays comparatively stable,
> because `get_conditions` returns the dependencies once the model relies on a duty at all,
> while the text arm's varies more, because it must *find* the relevant provisions by
> searching and there are many near-miss paths.

| stratum | n | prediction |
|---|---|---|
| APP-14 | 20 | graph modal share > text modal share |
| APP-13 | 15 | graph modal share > text modal share |
| APP-12 | 5 | **no test.** Underpowered by construction |
| APP-46 | 5 | **no test.** Underpowered by construction |
| NA-46 | 5 | **no test.** Underpowered by construction |

**THE NULLS, each a live outcome that will be reported as a result and not explained away.**

- **NULL A, no arm difference.** Neither APP-14 nor APP-13 separates at alpha 0.05. The
  substrate does not buy consistency under sampling.
- **NULL B, nothing moves at all.** Both arms stay at modal share 1.000 even at temperature
  1.0. This is a genuinely likely outcome: tool calls are emitted against a constrained
  schema over a small deterministic index, which is far less temperature-sensitive than free
  prose, and the probe of 2026-09-17 varied only prose. **If NULL B occurs it is a positive
  and useful answer to the author's concern**, namely that the relied-provision set does not
  change under sampling, and **it may not be recast as a failed study.** It would also mean
  the arms cannot separate, so NULL A and NULL B can hold together.
- **NULL C, the hypothesis reversed.** The text arm is *more* stable than the graph arm.
  This is explicitly live. `RESULTS-GRADED.md` records the graph arm doing worse on
  Article 12 in two independent studies, so a reversal is not unimaginable here.
- **NULL D, temperature does nothing monotone.** The three rungs show no ordering.

**TWO INSTRUMENT CHECKS, both of which this study would be willing to fail on.** These are
named in advance on the same terms Article 46 was named in `PREREGISTRATION.md` section 3
and passed twice.

**INSTRUMENT CHECK 1, the temperature-0 replication. Run BEFORE the paid rungs, and a
failure stops the session.** Ten of the 50 items, spanning all five strata, are re-run at
temperature 0.0, one repeat, both arms. Their relied-provision sets **must be identical to
the S9 stability run's** on the same items. If they are not, the harness is not reproducible
across sessions and **no variance measured at 0.7 or 1.0 could be attributed to
temperature**, which would invalidate the whole study. Cost: 20 generations, about 7
minutes. This check is the reason it is cheap to run and expensive to skip.

**INSTRUMENT CHECK 2, monotonicity.** Sampling temperature can only add entropy. Within an
arm and stratum, the mean modal share at 1.0 **must not exceed** the mean modal share at 0.7
by more than sampling noise, and neither may exceed the temperature-0 value of 1.000. An arm
that is measurably *more* stable at a higher temperature indicates the measure is not
tracking sampling variability, and the positive reading is withdrawn.

---

## 6. Execution discipline, per E8, applied without further decision

- **No seed is set, deliberately.** Ollama draws a fresh seed per request when none is
  given. A pinned seed would make all N repeats identical and the study would measure
  nothing. Verified on 2026-09-17 on a throwaway non-study prompt, which produced 1 distinct
  output of 3 at temperature 0.0 and 3 of 3 at both 0.7 and 1.0. **That probe touched no
  study item and produces no number.**
- `num_ctx` set **explicitly** at 16384 on every call, `prompt_eval_count` asserted against
  the ceiling with a margin, per item.
- Turn cap **10**, with a per-item `turn_cap_hit` assertion. Items hitting it are reported
  separately, never silently included.
- Model pinned as `qwen2.5:7b` with the **Ollama blob digest recorded**, verified
  `845dbda0ea48ed74` on entry. A repointed tag fails loudly.
- Source digests re-verified on every load.
- **`reach.py` and `stores.py` are NOT modified.** The measure must stay identical to S9's
  or nothing here is comparable to it. `run_arms.py` gained a `--temperature` flag that is
  **carried in the resume header**, so two runs at different temperatures cannot merge into
  one traces file undetected; what a trace **records** is unchanged and both self-checks
  re-run clean after the edit.
- **`--resume` over incremental writes**, not restarts. Ollama's process died mid-run in S9
  while the machine slept and resume saved 69 minutes of generations.
- `mistral:7b` is not re-probed. 0/10 twice at chaining tool calls.

---

## 7. Carried constraints, none softenable

- **Stratify, never pool.** No headline number across strata and none constructed afterwards.
- **`no_reliance` is not a zero** and never enters a denominator.
- **REACHABILITY IS NOT THE CLAIM.** The text arm reached every distinct relation in S9,
  4 of 4 on Article 13 and 7 of 7 on Article 14. Any finding here is about **consistency**,
  never about what a text baseline is capable of reaching.
- **The graph arm's near-1.0 on any coverage measure is STRUCTURAL**, a property of the tool
  return, and stated as such. **If the graph arm is also near-1.0 on *stability*, that is a
  different quantity and is not automatically structural** - but the possibility that it is
  downstream of the same tool-return property must be argued, not assumed, in any reading.
- The text arm's structural ceiling is 40 of 223; the honest headroom is **183, not 223**.
- **Zero cross-article attachments exist in this scope.** Cross-provision only.
- **The corpus is synthetic.** Nothing measured here transfers to real policies.
- The fanout is skewed: 8 nodes carry 201 of 258 attachments.
- **The pre-registration has a digest but no timestamped history**, `paper_draft/` being
  deliberately untracked by the author's decision of 2026-09-15. A draft may say this study
  was pre-registered, which it was, but **may not imply the ordering is externally
  verifiable.**
- **No session picks the headline claim.** This one does not, and this study is exploration.

---

## 8. Run order

1. **The gate**, all five self-checks and all three frozen digests. Passed 2026-09-17.
2. **Instrument check 1**, the temperature-0 replication on 10 items. **A failure stops the
   session.**
3. **Rung 0.7**, 50 items x 10 repeats x 2 arms, 1,000 generations, `--resume` throughout.
4. **The hand-check of `variance_analyse.py`** on at least three real items spanning at
   least two strata, before any number is reported.
5. **Rung 1.0**, 1,000 generations.
6. The results record, at `RESULTS-VARIANCE.md` in this directory. **Nothing is written into
   `s6_tools/`.**

The *evaluation* section stays unwritten, per the refresh trigger in `05_EVAL_PLAN.md`.
