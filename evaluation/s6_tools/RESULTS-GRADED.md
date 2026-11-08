# Results: the graded-measure study, run 2026-09-16/17 (S9)

**Results record, not a draft.**

**Digest verified before any result was read:** `PREREGISTRATION-GRADED.md` =
`1a9a5f412e4ed184ea7c7edd77761f36b6a1162316227a97e20e3dd34ccb40d3`, matching its
`.sha256`, unedited. Sample `graded.frozen.json` re-verified at `d16e6499...`, seed
`20260917`, and re-asserted **disjoint from all 290 items** of the reach study and its
pilot. `PREREGISTRATION.md` and `PREREGISTRATION-STABILITY.md` also re-verified unchanged.

220 items x 2 arms = **440 generations**, 147 minutes. `qwen2.5:7b` blob
`845dbda0ea48ed74`, `num_ctx` 16384, temperature 0.0, turn cap 10.
**Turn cap hits 0, errors 0**, max `prompt_eval_count` 3365 of 16384.

---

## The pre-registered prediction, and what happened

| stratum | predicted | observed |
|---|---|---|
| Article 14 | separation | **separation, p = 1.2e-12** |
| Article 13 | separation | **separation, p = 8.5e-14** |
| Article 12 | little or none | not significant, p = 0.0625 |
| Article 46, both strata | **no separation** | **no separation. All 48 items `no_targets` in both arms** |

**Every prediction held.** Article 13, which was the load-bearing one because it failed on
the binary measure, separated decisively.

## The primary measure

Per-item fraction of target pairs surfaced. Paired Wilcoxon signed-rank, two-sided,
alpha 0.05 per stratum, no correction across strata. **Stratified, never pooled.**

| stratum | arm | n | median | mean | all targets | none | partial | p |
|---|---|---|---|---|---|---|---|---|
| APP-13 | graph | 73 | 1.000 | 1.000 | 73 | 0 | 0 | |
| APP-13 | text | 64 | **0.667** | 0.607 | **0** | 0 | 64 | **8.5e-14** |
| APP-14 | graph | 70 | 1.000 | 1.000 | 70 | 0 | 0 | |
| APP-14 | text | 61 | **0.143** | 0.136 | **0** | 10 | 51 | **1.2e-12** |
| APP-12 | graph | 9 | 0.000 | 0.222 | 2 | 7 | 0 | |
| APP-12 | text | 14 | 1.000 | 1.000 | 14 | 0 | 0 | 0.0625 |
| APP-46 | both | 0 | n/a | n/a | 0 | 0 | 0 | n/a |
| NA-46 | both | 0 | n/a | n/a | 0 | 0 | 0 | n/a |

Median paired difference: **0.333** on Article 13, **0.857** on Article 14.

---

## THE REPLICATION, WHICH IS THE MOST IMPORTANT NUMBER HERE

The graded effect was spotted **post-hoc** in the reach study. This study tested it on
**220 fresh, disjoint items**. The text arm's mean fraction:

| stratum | S9 post-hoc observation | fresh pre-registered confirmation |
|---|---|---|
| Article 13 | 0.610 (n = 59) | **0.607** (n = 64) |
| Article 14 | 0.138 (n = 83) | **0.136** (n = 61) |

**Agreement to three decimal places on both strata, on items nobody had seen.** The
post-hoc observation was not an artifact of looking after the fact.

**And the distributional fact replicated exactly.** Across both studies, the text arm
reached **all** of its target relations on **0 of 267 items**:

| study | stratum | text arm reached all targets |
|---|---|---|
| reach | APP-13 | 0 of 59 |
| reach | APP-14 | 0 of 83 |
| graded | APP-13 | 0 of 64 |
| graded | APP-14 | 0 of 61 |

---

## The structural caveat, stated before the run and confirmed by it

**The graph arm's 1.000 is the tool surface, not model behaviour.** `get_conditions`
returns the relation nodes, so once the model relies on a duty its cross-provision
relations are surfaced by the tool return itself. Section 3 of the pre-registration says
this, and it was written before the run for exactly this reason. **No draft may present the
graph arm's figure as a behavioural result.**

**The informative quantity is the text arm's fraction**, and it is the one that replicated.

## Reachability is NOT the claim, and this study confirms the caveat rather than easing it

| stratum | arm | distinct relations surfaced / targeted |
|---|---|---|
| APP-13 | graph | 4 of 4 |
| APP-13 | text | **4 of 4** |
| APP-14 | graph | 7 of 7 |
| APP-14 | text | **7 of 7** |

**The text arm reached every distinct relation in both strata.** It reached 4 of 4 on
Article 13, where the reach study had it at 3 of 4, so on fresh items it did *better* on
distinct coverage while still separating decisively on completeness. This is the constraint
that must travel with any positive sentence: **the separation is about completeness and
consistency of coverage, never about what a text baseline is capable of reaching.**

## Secondary, descriptive only and not significance-tested

| stratum | arm | appliesIf | hasException | notApplicableIf |
|---|---|---|---|---|
| APP-13 | graph | 483/483 | 243/243 | |
| APP-13 | text | 290/353 | **12/177** | |
| APP-14 | graph | 402/402 | 808/808 | 202/202 |
| APP-14 | text | **2/226** | 47/456 | 30/114 |

The text arm's weakness is concentrated on **exceptions** (12 of 177 on Article 13) and on
Article 14's `appliesIf` (2 of 226). That is the Article 14(5) exception block and the
collection trigger, which is exactly what the fanout skew predicted the study would
measure.

---

## Article 12, reported honestly because it goes the other way twice

**The graph arm did worse on Article 12 in both studies.** Here: graph median 0.000 with 7
of 9 items surfacing none, text median 1.000 on all 14. p = 0.0625, not significant, and
**0.0625 is the smallest p achievable with 5 non-zero pairs**, so this stratum is
underpowered by construction, as "little or none" anticipated.

The likely mechanism, and it is the pre-registered definition working as designed rather
than a defect: reliance is anchored at the **provision**, so relying on a provision puts
**every** duty grounded in it into the relied set, including duties whose conditions the
model never fetched. Those duties still contribute targets. On Article 12, with 1 distinct
relation and a small pool, the graph arm apparently relied broadly and fetched narrowly, so
targets were generated that its own calls did not cover. The definition inflates both arms'
target sets equally by construction, which is why it was chosen; on this stratum it bites
the graph arm. **Nothing should be read into the direction of Article 12 in either
direction**, but it is consistent across two independent samples and is recorded rather
than passed over.

---

## What may now be said, and what may not

**Earned, with pre-registered numbers on fresh data:**

> The graph store delivers the cross-provision dependencies of a relied-upon duty by
> construction. The text store cannot, so the model must find them by its own searching,
> and that searching surfaced a median **0.667** of the target relations on Article 13 and
> **0.143** on Article 14 (Wilcoxon signed-rank, p = 8.5e-14 and 1.2e-12), and surfaced
> **all** of them on **none of 267 items** across two independent samples.

Every sentence of that is pre-registered and replicated. The three clauses that must travel
with it:

1. the graph arm's 1.000 is **structural**, a property of the tool return
2. the text arm reached **every distinct relation** (4 of 4, 7 of 7), so this is
   completeness, not capability
3. the fanout is skewed: 8 nodes carry 201 of 258, and the effect concentrates on the
   Article 14(5) exception block and the collection trigger

**Still not claimed:** no pooled figure across strata; no faithfulness claim, since
reaching more is not evidence it drove the verdict; no cross-**article** claim, there being
zero such attachments in this frozen scope; the honest headroom remains 183 of 223; and
**the corpus is synthetic**, so nothing here transfers to real-world policies. Tier 2 was
not run.

## Artifacts

| file | what |
|---|---|
| `graded.traces.json` | 220 items x 2 arms, full trace per item |
| `graded.reach.json` | `reach.py` output, unmodified extractor |
| `graded.analysis.json` / `.txt` | `graded_analyse.py` output |
| `graded.frozen.json` | the frozen draw, seed `20260917`, disjoint |
