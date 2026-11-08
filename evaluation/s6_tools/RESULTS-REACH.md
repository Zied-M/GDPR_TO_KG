# Results: the tool-mediated reach study, run 2026-09-15/16 (S9)

**This is a results record, not a draft.** Drafting "evaluation" is a later session and
follows the refresh trigger at the end of `05_EVAL_PLAN.md`: results first cause the
evidence pass to be re-run and `02_EVIDENCE.md` to gain rows, with contradictions recorded
rather than smoothed over, and only then is the section written.

**Digests verified before any result was read**, per `PREREGISTRATION.md`:

| file | digest | state |
|---|---|---|
| `PREREGISTRATION.md` | `eddf157fbcd42e3b3fec6805ba65521bb9c7db014655442e92bb76eb8b078cd1` | matches `PREREGISTRATION.sha256`, unedited |
| `PREREGISTRATION-STABILITY.md` | `3b4b3e91aae86806bd50b368565dc1c3ec7762ed802a4412937ff56828ac0979` | matches its `.sha256`, unedited |
| `sample.frozen.json` | payload sha256 `96cdc651...`, corpus `a9cbcdb5...` | 250 items, every index and text digest re-verified |

Model `qwen2.5:7b`, blob `845dbda0ea48ed74`, `num_ctx` 16384 explicit, temperature 0.0,
turn cap 10, k = 5. **250 items x 2 arms = 500 generations, 168 minutes.**

## Execution, per E8

| | |
|---|---|
| turn cap hits | **0** |
| execution errors | **0** |
| max `prompt_eval_count` | **5828 of 16384** (graph arm; text arm 2968) |
| items excluded from any rate | **0** |

The pilot of 40 ran first as an end-to-end harness check: 0 cap hits, 0 errors, max
`prompt_eval_count` 3198. **It produced no number that enters this analysis or a draft**,
and its reach output was deliberately not read.

---

## The primary measure, exactly as pre-registered

Per-item rate = `reached` / (`reached` + `not_reached`), per arm, per stratum.
`no_targets` and `no_reliance` sit beside it and are **never** in the denominator.
**Stratified, never pooled. There is no headline number across strata and one may not be
constructed.**

| stratum | arm | reached | not_reached | no_targets | no_reliance | rate [95% Wilson] |
|---|---|---|---|---|---|---|
| APP-12 | graph | 5 | 7 | 13 | 0 | 0.417 [0.193, 0.680] |
| APP-12 | text | 7 | 0 | 18 | 0 | 1.000 [0.646, 1.000] |
| APP-13 | graph | 74 | 0 | 0 | 1 | 1.000 [0.951, 1.000] |
| APP-13 | text | 59 | 0 | 2 | 14 | 1.000 [0.939, 1.000] |
| APP-14 | graph | 90 | 0 | 8 | 2 | 1.000 [0.959, 1.000] |
| APP-14 | text | 75 | 8 | 16 | 1 | 0.904 [0.821, 0.950] |
| APP-46 | graph | 0 | 0 | **25** | 0 | n/a, denominator 0 |
| APP-46 | text | 0 | 0 | **25** | 0 | n/a, denominator 0 |
| NA-46 | graph | 0 | 0 | **25** | 0 | n/a, denominator 0 |
| NA-46 | text | 0 | 0 | **25** | 0 | n/a, denominator 0 |

McNemar's exact test, two-sided, paired per item, alpha 0.05 per stratum, no correction
across strata. Discordant counts shown, as pre-registered.

| stratum | n paired | graph only | text only | concordant reached | p |
|---|---|---|---|---|---|
| APP-12 | 7 | 0 | 4 | 3 | 0.125, not significant |
| APP-13 | 59 | 0 | 0 | 59 | no discordant pairs, **no test possible** |
| APP-14 | 80 | **8** | **0** | 72 | **0.0078, significant** |
| APP-46 | 0 | 0 | 0 | 0 | no test possible |
| NA-46 | 0 | 0 | 0 | 0 | no test possible |

### Read against the prediction, which was fixed before the data

| stratum | predicted | observed |
|---|---|---|
| Article 14 | separation | **separation, p = 0.0078** |
| Article 13 | separation | **no separation.** Both arms at 1.000, zero discordant pairs |
| Article 12 | little or none | no significant separation, p = 0.125, and the numerical direction **favours the text arm** |
| Article 46 | **no separation** | **no separation. Every one of the 50 items landed on `no_targets` in both arms** |

**One stratum of five separates on the primary measure.** The Article 13 prediction was
not borne out; that is a result and is reported as one, not explained away.

### The instrument passed its own failure test

`PREREGISTRATION.md` section 3 names separation on Article 46 in advance as an
**instrument failure** rather than a finding. It did not occur. All 50 Article 46 items,
across both the applicable and not-applicable strata, landed on `no_targets` in both arms,
which is the pre-registered null appearing as a distinct status rather than as a
misreadable zero. The same-article control pairing behaved identically in both halves.

---

## The secondary measure, descriptive only and NOT significance-tested

Per duty-relation pair, by relation kind. Pairs are nested within items and clustered hard
by the fanout skew, so **no test is run over them and none may be added later**.

| stratum | arm | appliesIf | hasException | notApplicableIf | all |
|---|---|---|---|---|---|
| APP-12 | graph | 8/22 | | | 8/22 |
| APP-12 | text | 14/14 | | | 14/14 |
| APP-13 | graph | 483/483 | 244/244 | | **727/727** |
| APP-13 | text | 200/240 | **0/120** | | **200/360** |
| APP-14 | graph | 466/466 | 932/932 | 233/233 | **1631/1631** |
| APP-14 | text | 3/274 | 65/548 | 37/137 | **105/959** |
| APP-46 | both | | | | 0/0 |
| NA-46 | both | | | | 0/0 |

How each arm surfaced what it surfaced, from the machine provenance:

- graph arm: 2360 by relation node, 6 by provision text
- text arm: **319 by provision text, 0 by relation node**, which is the escape route
  working exactly as E3 intends

---

## FOUR CONSTRAINTS ON ANY POSITIVE READING, and none is softenable

The first three were established before the data. **The fourth is new, was found in this
run, and is the sharpest of them.**

**1. The honest headroom is 183 of 223, not 223.** Sibling expansion alone reaches 0, but
`find_duties` normally also returns the duty's own provision, which brings 40
parent-grounded relations into the text arm's reach. No sentence may imply the text arm
can reach none of them. E3's own wording is correct as written and was not edited.

**2. The fanout is severely skewed:** 8 nodes carry 201 of the 258 attachments and 32 of
the 44 have fanout 1. The study measures behaviour around the Article 14(5) exception
block and the collection trigger, and that sentence travels with any separation.

**3. There are zero cross-article relation attachments in this frozen scope.** Only the
cross-**provision** claim is supported by anything measured here.

**4. NEW, AND IT CONSTRAINS THE WORDING HARDEST. The pair counts are instances, not
distinct relations, and the distinct counts are tiny.**

| stratum | arm | distinct relations surfaced / distinct targets |
|---|---|---|
| APP-12 | graph | 1 of 1 |
| APP-12 | text | 1 of 1 |
| APP-13 | graph | 4 of 4 |
| APP-13 | text | **3 of 4** |
| APP-14 | graph | 7 of 7 |
| APP-14 | text | **7 of 7** |

**The text arm surfaced every one of the 7 distinct Article 14 relations and 3 of the 4 in
Article 13.** So 1631/1631 against 105/959 is not a statement about which relations a text
baseline can reach. It is a statement about **how often**, across items, it reaches them.
The separation is in frequency and consistency, not in reachability, and **any sentence
implying the text arm cannot reach these relations would be contradicted by this run's own
data.** Constraint 2 predicted the phenomenon would not be diverse; it is even less diverse
than the node-level figure suggests, because the study turns on 7 distinct relation nodes
in Article 14, 4 in Article 13 and 1 in Article 12.

---

## Reported alongside, none of it a headline

**`no_reliance` is asymmetric on Article 13 and this qualifies that stratum's rates.**

| stratum | arm | no_reliance | turns mean | calls mean |
|---|---|---|---|---|
| APP-12 | graph / text | 0 / 0 | 4.80 / 3.96 | 3.80 / 2.96 |
| APP-13 | graph / text | **1 / 14** | 5.28 / 3.44 | 4.28 / 2.53 |
| APP-14 | graph / text | 2 / 1 | 3.95 / 3.28 | 3.01 / 2.28 |
| APP-46 | graph / text | 0 / 0 | 4.12 / 4.84 | 3.12 / 3.84 |
| NA-46 | graph / text | 0 / 0 | 3.80 / 3.96 | 2.80 / 2.96 |

On Article 13 the text arm never called `get_conditions` on 14 of 75 items against the
graph arm's 1, so **its 1.000 is computed over 59 items and the graph arm's over 74**.
That is the pre-registered denominator rule working as written, and it means the two
Article 13 rates are not computed over the same item set. `no_reliance` occurred in both
arms, as the S7 hand-check already found, so it remains a model behaviour rather than a
text-arm artifact; but this asymmetry is large enough that it must be reported with the
Article 13 null rather than under it.

**A second interpretive caution, on Article 12.** Target sets are defined relative to each
arm's own reliance, by design, so the two arms do not have the same denominator or the same
targets. On APP-12 the text arm landed on `no_targets` for 18 of 25 items and the graph arm
for 13, which is why the graph arm has 7 `not_reached` and the text arm none. With 1
distinct relation in play and 7 paired items, **nothing should be read into the direction of
this stratum in either direction.**

Verdict disagreement between arms, from a **case-sensitive keyword scan** of the final
answer, not a hand-checked instrument, with unparsed counts shown: APP-12 1/24/0,
APP-13 20/54/1, APP-14 27/72/1, APP-46 1/24/0, NA-46 10/10/5 (disagree / agree /
unparsed). This is Part D item 2, reported free and carrying nothing.

Tokens: max `prompt_eval_count` 5828 graph, 2968 text; mean of per-item max 1798 graph,
1598 text. Cost was one of the four motivations for the tool design, so the figure is
wanted regardless.

---

## What is NOT claimed

- **No pooled or headline figure.** None is computed anywhere in `analyse.py`.
- **No faithfulness claim.** Reach is not whether what was reached drove the verdict.
- **Tier 2 (use) was not run.** Tier 1 separated on one stratum, which is the condition
  E2 sets, but tier 2 needs a judgement and therefore a validation sheet. It stays
  unbuilt and unrun, and it is explicitly not the study.
- **No support or entailment number.** Parked, per E6.
- **No aptness number.** Retired, per E6.
- **No per-class metric against LexiGen gold labels**, and no accuracy reading of the
  verdict line.
- **The corpus is synthetic.** Nothing measured here transfers to real-world policies.
  That caveat is mandatory and may not be softened.
- **The pre-registration has a digest but no timestamped history.** A draft may say the
  study was pre-registered, which it was, but may not imply the ordering is externally
  verifiable.

## Artifacts

| file | what |
|---|---|
| `study.traces.json` | 250 items x 2 arms, full trace per item |
| `study.traces.json.partial.jsonl` | the incremental record, header plus one line per unit |
| `study.reach.json` | `reach.py` output, per item and per pair |
| `study.analysis.json` / `.txt` | `analyse.py` output, the pre-registered analysis |
| `pilot.traces.json` | the 40-item harness check. **No number from it enters anything** |
