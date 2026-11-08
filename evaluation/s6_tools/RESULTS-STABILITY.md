# Results: the stability measurement, run 2026-09-16 (S9)

**Results record, not a draft.** Ran **after** the reach study, as
`PREREGISTRATION-STABILITY.md` section 6 requires.

**Digest verified before any result was read:** `PREREGISTRATION-STABILITY.md` =
`3b4b3e91aae86806bd50b368565dc1c3ec7762ed802a4412937ff56828ac0979`, matching its
`.sha256`, unedited. Subsample `stability.frozen.json` re-verified at
`7b942344089e2d4c1cbf42992bedd69b13b3c7a5d6cf00418ad06564ea210afa`, seed `20260916`.

M = 50 items, N = 5 repeats, 2 arms = **500 generations**, `qwen2.5:7b` blob
`845dbda0ea48ed74`, `num_ctx` 16384, temperature 0.0, turn cap 10.

## Execution

| | |
|---|---|
| turn cap hits | **0** |
| execution errors | **0** |
| max `prompt_eval_count` | **3207 of 16384** |
| incomplete items | **0** |

**The run died once and was resumed, and this is recorded rather than smoothed over.**
Ollama's process disappeared while the machine was asleep; the run stopped after 109 of
250 units and sat dead for about 17 hours. It was resumed from
`stability.traces.json.partial.jsonl` with `--resume`, which verified that the sample,
split, arms, model tag, **model blob digest**, `num_ctx`, turn cap and repeat count all
matched the interrupted run before reusing a single record. The torn final line was
dropped and that unit regenerated. **No generations were lost and no two runs were mixed.**
The incremental write and resume were built in this session precisely for this and were
needed within a day.

---

## The primary measure

Proportion of items whose **relied-provision set** is identical across all 5 runs, per arm,
per stratum, Wilson 95% intervals. **Stratified, never pooled.**

| stratum | arm | n | stable | unstable | proportion [95% CI] | reach status also stable |
|---|---|---|---|---|---|---|
| APP-12 | graph | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |
| APP-12 | text | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |
| APP-13 | graph | 15 | 15 | 0 | 1.000 [0.796, 1.000] | 15/15 |
| APP-13 | text | 15 | 15 | 0 | 1.000 [0.796, 1.000] | 15/15 |
| APP-14 | graph | 20 | 20 | 0 | 1.000 [0.839, 1.000] | 20/20 |
| APP-14 | text | 20 | 20 | 0 | 1.000 [0.839, 1.000] | 20/20 |
| APP-46 | graph | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |
| APP-46 | text | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |
| NA-46 | graph | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |
| NA-46 | text | 5 | 5 | 0 | 1.000 [0.566, 1.000] | 5/5 |

**Per-item resolution:** every item in every stratum in both arms sits at **5 of 5 runs
agreeing**. Not one item showed even a single deviating run, so the gradient N = 5 was
chosen to expose is entirely flat. The coarser reach-status line is identical.

---

## WHAT THIS DOES AND DOES NOT SAY

**It is a floor, not a finding, and section 5 said so before the run.** At temperature 0.0,
with a pinned model, deterministic BM25 retrieval and greedy decoding, repeated runs are
close to identical **by construction**. A result of 1.000 is what the design predicts, not
a discovery about the representation. Neither arm is more stable than the other and the
measurement was never capable of showing that here.

**It does not answer the author's original concern.** That concern, in the author's words,
was that an LLM justification "can be undeterministic and can change". A temperature-0
measurement cannot address it and **no draft may present it as if it did.** Answering it
needs temperature above 0, which is a different design with its own cost and its own
pre-registration before its run.

**What it does buy, and it is the reason the 500 generations were worth spending:** a
stated bound on reproducibility. Every number in the reach study is now attributable to
the representation rather than to provider nondeterminism, on the same items, through the
same harness. That is a precondition for the reach result, not a result beside it.

**One honest note on M.** `PREREGISTRATION-STABILITY.md` section 1 justified M = 50 from a
**pooled** interval of [0.929, 1.000] at 50 of 50 stable. Section 3 then specifies the
analysis **per stratum**, and stratified intervals over 5 to 20 items are necessarily
wider: the tightest here is [0.839, 1.000] on APP-14. The two sections are in tension, and
the binding instruction is "stratify, never pool", so **no pooled proportion is reported
here.** The consequence is that the per-stratum lower bounds are weaker than the number
used to choose M. Recorded rather than resolved, because resolving it would mean editing a
frozen pre-registration.

## The secondary measure produced no number, as gated

The provisions **cited in the final answer**, which is Part D item 4's literal wording,
need a prose parser. That parser **owes a hand-check on the same terms `reach.py` paid in
S7 before it may produce any number**. It was **not built** in this session, so this line
produces **no number** and the primary measure stands alone. It may not be swapped in
after the fact as a rescue for a disappointing primary result, and the primary result here
is not disappointing in any case: it is exactly the floor that was predicted.

## Artifacts

| file | what |
|---|---|
| `stability.traces.json` | 50 items x 5 repeats x 2 arms, full trace per run |
| `stability.traces.json.partial.jsonl` | the incremental record that survived the crash |
| `stability.reach.json` | `reach.py` output over those traces |
| `stability.analysis.json` / `.txt` | `stability_analyse.py` output |
