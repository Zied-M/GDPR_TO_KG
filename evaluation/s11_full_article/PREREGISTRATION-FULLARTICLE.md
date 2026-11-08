# Pre-registration: the full-article study (S11)

**Written before any generation on the frozen items. Not edited after the run.** Its digest
is in `PREREGISTRATION-FULLARTICLE.sha256`; an edited file is a failed pre-registration.
Nothing in `s5_pilot`, `s6_tools`, `s10_variance`, the graph files or `context/` is
changed by this study. The harness is copied into this folder.

---

## 1. The question

The reviewer asks why the text condition of Studies 1 and 2 did not receive the whole
article. In those studies the text store returned the introductory paragraph and the
neighbouring points of a provision, so a missing qualification can be read as
**unavailable** rather than **not assembled**. This study removes availability as an
explanation: every condition receives the full official text of the article in the prompt.

> Given the whole article and a fixed duty, does the model assemble the full set of
> qualifications the graph links to that duty, and does the graph-assisted workflow
> change that?

---

## 2. What changes from Studies 1 and 2

- **The duty is fixed before the run**, one per item, identical in every condition. The
  reference target set is therefore the same across conditions by construction. In the
  earlier studies the target set followed the model's own reliance and differed by arm.
- **Availability is equalised**: the full article text is in every prompt.
- **The outcome is the model's stated associations**, not span coverage of what a tool
  returned. Span coverage would credit the full-text condition with every target by
  construction and so would measure availability.

Unchanged: `qwen2.5:7b` via Ollama, blob digest recorded; temperature 0.0; `num_ctx` 16384
set explicitly on every call, `prompt_eval_count` asserted against it with a 512-token
margin; turn cap 10 with a per-item flag; the graph tool surface of `s6_tools/stores.py`
(copied here, changed only to inline `load_units`); source digests re-verified on load;
Ollama load state recorded at start and end.

---

## 3. Conditions

All prompts are fixed in `run_fullarticle.py`. Every condition receives the same system
instruction and the same user message: the article's full official text
(`sources/art13.txt` or `sources/art14.txt`, pinned by sha256), the policy segment as
context, and the fixed duty (its statement, its provision and its graph identifier). All
return the same JSON schema: one entry per qualification with `provision`, `kind`
(`condition`, `exception` or `not_applicable_if`) and a one-sentence `justification`.

| condition | adds | role |
|---|---|---|
| `fulltext` (A) | nothing: full article + fixed duty, no tools | primary |
| `graph` (B) | the three s6 graph tools (`find_duties`, `get_conditions`, `get_provision` over `GraphStore`) and one system sentence telling the model to call `get_conditions` with the duty identifier before answering and to check its return against the article text | primary |
| `links` (C) | the duty's encoded links written out as plain text lines (kind, statement, cited provisions), no tools. The same content `get_conditions` returns | **secondary**, separates format from content |

No `format` constraint is passed to Ollama in any condition, so decoding is identical; the
answer is parsed by the same lenient JSON reader in all three.

---

## 4. The sample, frozen before this file

`freeze_fullarticle.py` into `fullarticle.frozen.json`.

- seed `20261107`, not used by any earlier study
- sample sha256 (sorted item ids) `62ce390a50702c702c258c577132c7e54177b6f4451ee9d4be2f0d0cbbf8a091`
- file sha256 `b44b980d43d6b2f38d96fe980ddf5f0b1b135d015355b09da6680a5fb6051b0f`
- corpus sha256 `a9cbcdb548d44b6b223052c1995c1a397b0abd76a1d72fd4cc8cd039f47ecefd`

**Unit: one item = one segment x one fixed duty.** Every duty the graph links at least one
qualification to appears in exactly two items. Article 14(5)(b)'s protective-measures duty
has no encoded links, hence no reference set, and is not drawn.

| article | duties | items | fresh segments | reused segments | reference links | of which cross-provision |
|---|---|---|---|---|---|---|
| 13 | 21 | 42 | 30 | 12 | 71 | 62 |
| 14 | 23 | 46 | 1 | 45 | 169 | 159 |

Article 13 duties carry 3 or 4 links (13 and 8 duties); Article 14 duties carry 7 or 8
(15 and 8 duties). The labels are 22 COMPLIANT / 20 NON_COMPLIANT on Article 13 and
17 / 29 on Article 14.

**Segment reuse, decided by the author, and why.** After the 510 items of Studies 1 and 2
and the pilot, 30 Article 13 segments and 1 Article 14 segment are unused. Every unused
segment is included; the remainder is drawn by seed from previously used segments of the
same article. Reuse is acceptable here because the reference set depends only on the fixed
duty, never on the segment or on the model's own duty selection, and because the
full-text condition has never been run on any segment, so no earlier outcome informed the
prediction for these items. The segment is context only. The four segments used for the
end-to-end check (section 9) are excluded from the reuse pool. `fresh_segment` is recorded
on every item.

**Pseudo-replication, stated before the run.** At temperature 0 two items sharing a duty
share a reference and differ only in segment, so the effective number of independent
references is the number of duties (21 and 23). A per-duty sensitivity test is
pre-registered for this reason (section 6).

---

## 5. Reference and scoring

**The reference is the graph's encoded duty-qualification links**, the `appliesIf`,
`notApplicableIf` and `hasException` edges of the duty in `articles/art13.ttl` and
`art14.ttl`, each grounded in one or more pinned source units. **It is the graph, not
legal ground truth.** A qualification the article arguably supports but the graph does not
encode (for example the one-month period of Article 14(3)(a)) counts as extraneous. No
independently reviewed target set is used in this study.

Scoring is mechanical (`score.py`, self-checked):

1. The answer is parsed as the first JSON object with a `qualifications` list. An
   unparseable answer is scored as an **empty answer**: recall 0, precision undefined,
   counted separately.
2. Each entry's `provision` string is split into citations (commas, semicolons, `and`,
   `or`, ranges such as `14(5)(a)-(d)`, bare points inheriting the previous prefix) and
   each citation is resolved against the pinned units. Unresolvable citations and
   citations to other articles never match.
3. **Primary match rule (containment):** an entry matches a link if one of its cited
   units equals, contains or is contained in one of the link's grounding units.
4. **Matching is one-to-one**, by maximum bipartite matching: an entry credits at most one
   link and a link is credited at most once. Repeating a paragraph citation earns at most
   the links grounded under it.
5. Per item: **recall** = matched links / reference links; **precision** = matched entries
   / entries. Every unmatched entry is extraneous or wrong, whatever its cause.

Secondary rules, reported beside the primary, never substituted for it:

- **strict**: the cited unit equals a grounding unit, is its ancestor, or is a
  subparagraph of a paragraph-level grounding unit. A point does not match a
  paragraph-level link (citing the duty's own point for the Article 14(1) collection
  trigger fails here and passes the primary rule).
- **kind**: the primary rule plus agreement of the stated kind with the encoded kind
  (`condition`~`appliesIf`, `exception`~`hasException`,
  `not_applicable_if`~`notApplicableIf`). The negative polarity of the shared collection
  condition on Article 14 duties is a modelling choice of the graph; this rule is
  descriptive for that reason.
- **cross-provision recall**: recall over the links grounded in a different provision
  than the duty, the population of Studies 1 and 2.

**Known limit of the instrument, stated before the run:** matching is by provision, not by
meaning. An entry citing the right provision with a justification describing another
qualification is credited. A small instrument check is pre-registered in section 6.

---

## 6. Analysis

**Per article, never pooled.** No figure across Articles 13 and 14 is computed.

- **Primary:** per article, per-item recall under the primary rule, `fulltext` vs
  `graph`, **Wilcoxon signed-rank, two-sided, alpha 0.05 per article, no correction**,
  exact for n <= 20 non-zero differences, normal approximation with tie and continuity
  correction above (the implementation of `s6_tools/graded_analyse.py`, copied). Reported
  with n paired, ties, the median and mean per condition and the median paired difference.
- **Descriptive beside the test, always:** per condition, the number of items with
  **recall 1.0 (complete set)** and with recall 0; median and mean precision; links matched
  over reference links; extraneous entries; unresolved citations; parse failures; median
  input tokens (sum of `prompt_eval_count` over turns); mean tool calls; items where
  `get_conditions` was called.
- **Secondary, each reported with its test but carrying no claim on its own:**
  precision `fulltext` vs `graph`; recall under the strict rule; cross-provision recall;
  `fulltext` vs `links` recall; the primary test on parsed answers only; and the
  **per-duty sensitivity test**: Wilcoxon on per-duty mean recall (n = duties).
- **Instrument check, descriptive:** for 10 items per article in the `fulltext` condition,
  the first ten in sample order, each matched entry's justification is read against the
  matched link and recorded as states it / does not. Done by the study author, not
  independent; reported as an instrument check, not a result.

Exclusions: an item with an execution error or a turn-cap hit in a condition is excluded
from that condition and from any pair involving it, and reported.

---

## 7. Predictions, fixed before the data

**The graph condition's recall is expected at or near 1.0 by construction** whenever it
calls `get_conditions`, because the tool returns the encoded links. That is the tool
surface, not model behaviour. **The informative quantity is the `fulltext` condition.**

| | Article 13 | Article 14 |
|---|---|---|
| P1 primary: `fulltext` recall below `graph` recall | significant | significant |
| P2: `fulltext` complete-set items | fewer than half | fewer than half, and a smaller share than on Article 13 |
| P3: `fulltext` mean recall | below 0.9 | below Article 13's |
| P4 secondary: `links` mean recall within 0.10 of `graph` | yes | yes |
| P5 secondary: `fulltext` precision not above `graph` precision | yes | yes |

---

## 8. How the result is read, fixed before the data

- **Assembly reading supported on an article** if P1 holds and P2 holds there: with the
  whole article in context and the duty fixed, the model does not assemble the encoded
  qualification set, and the graph-assisted workflow does. The earlier text-condition gap
  is then not explained by availability alone.
- **Availability reading supported on an article** if P1 fails, or `fulltext` reaches the
  complete set on half or more of the items there: given the whole article, the model
  assembles most of the set itself, and the earlier gap was mainly a consequence of what
  the text store returned. This would narrow the paper's claim to availability, and it is
  reported as such.
- **Mixed** if the test is significant but `fulltext` completes the set on half or more of
  items, or the reverse. Both numbers are reported and neither reading is claimed alone.
- If `graph` recall is far below 1.0 because the model did not call `get_conditions` or
  dropped returned links, that is reported as a workflow failure, not as evidence about the
  representation.
- The per-duty sensitivity test disagreeing with the primary test is reported in the same
  sentence as the primary result.

---

## 9. End-to-end check, disclosed

Before this file was frozen, the harness ran end to end on four items built from s6
**pilot** segments (`smoke.sample.json`: two Article 13, two Article 14, duties chosen by
hand), in all three conditions, then once more in the `graph` condition. 0 errors, 0
turn-cap hits, maximum `prompt_eval_count` 2,496 of 16,384. **No number from it enters
the analysis**, and its segments are excluded from the sample.

What it changed, and only this: in the first pass the `graph` condition, told to use the
tools "as you see fit", made no tool call on either Article 13 item and answered from the
text. The system sentence was changed to tell the model to call `get_conditions` with the
duty identifier before answering, which is what a graph-assisted workflow is. The second
pass called it on all four. The parser was written to accept fenced JSON and
multi-citation strings, which the first pass produced.

---

## 10. Instrument digests at freeze

| file | sha256 |
|---|---|
| `stores.py` | `23a33774e84a7cce8c68ce4c3fb23d23bb1ccec077f6d524af806def058e38f6` |
| `run_fullarticle.py` | `ad6c10c0333ad280a7f64c54dd5a29493909fef2c477b8f61770fa50df6eb3cf` |
| `score.py` | `09aa1272e4168c08ced0f0d5851573064a49333a3653838177c56f45eeaf2401` |
| `freeze_fullarticle.py` | `5e5b6984bd953a3e63319defa888d93b6a8666bf86371dce5012ba9f94b4b200` |

The same digests are repeated in `PREREGISTRATION-FULLARTICLE.sha256` beside this file's
own, so a changed instrument is detectable after the run.

---

## 11. Not measured

No legal-correctness claim: the reference is the graph. No verdict accuracy against
LexiGen labels. No faithfulness claim. No claim beyond one 7B model at temperature 0. The
corpus is synthetic single-article segments generated by GPT-4.1, not real policies, and
nothing here transfers to real-world policies. The pre-registration has a digest but no
timestamped external history, so a draft may say the study was pre-registered but may not
imply the ordering is externally verifiable.
