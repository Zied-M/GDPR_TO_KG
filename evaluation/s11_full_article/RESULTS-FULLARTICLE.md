# S11 results: full article text vs graph tools, fixed duty

Analysis as pre-registered in `PREREGISTRATION-FULLARTICLE.md` (sha256 `db2dbc99...`).
All six digests in `PREREGISTRATION-FULLARTICLE.sha256` checked OK before scoring.
Raw traces: `fullarticle.traces.json`. Scored output: `fullarticle.analysis.json` / `.txt`.
Figure: `fullarticle_recall.png` (script `plot_recall.py`).

**Reference = the graph's encoded links. This is not legal ground truth.** Recall means
"share of the links the graph encodes for this duty that the answer cites", scored by
provision containment (primary rule, section 5 of the preregistration).

## Run

- qwen2.5:7b via Ollama, temperature 0, num_ctx 16384, turn cap 10.
- 88 items (Article 13: 42, Article 14: 46) x 3 conditions = 264 runs.
- 0 execution errors, 0 turn-cap hits, so no exclusions. Maximum `prompt_eval_count`: 2,438 of 16,384.
- `graph` called `get_conditions` on 88 of 88 items.
  - Tool calls per item, Article 13: one call on 36 items, two calls on 5, four calls on 1.
  - Tool calls per item, Article 14: one call on all 46.
- Parse failures (an answer the frozen parser cannot read scores as an empty answer):
  - `fulltext`: 0/42 on Article 13, 0/46 on Article 14.
  - `graph`: 0/42 and 0/46.
  - `links`: 7/42 and 13/46.

## Primary result

Wilcoxon signed-rank on per-item recall, primary rule, two-sided, alpha 0.05, per article.

| | Article 13 | Article 14 |
|---|---|---|
| n paired items | 42 | 46 |
| ties (zero differences) | 1 | 0 |
| `fulltext` recall, median / mean | 0.500 / 0.512 | 0.250 / 0.208 |
| `graph` recall, median / mean | 1.000 / 0.982 | 1.000 / 1.000 |
| median paired difference (`fulltext` minus `graph`) | -0.500 | -0.750 |
| p | < 0.000001 | < 0.000001 |
| per-duty sensitivity test (n = duties) | n 21, median diff -0.500, p = 0.000043 | n 23, median diff -0.750, p = 0.000026 |

The per-duty test agrees with the primary test on both articles.

## Descriptive, primary rule

| | `fulltext` A13 | `graph` A13 | `links` A13 | `fulltext` A14 | `graph` A14 | `links` A14 |
|---|---|---|---|---|---|---|
| complete set (recall 1.0) | 0/42 | 40/42 | 5/42 | 0/46 | 46/46 | 30/46 |
| recall 0 | 0/42 | 0/42 | 7/42 | 6/46 | 0/46 | 13/46 |
| links matched / reference links | 72/142 | 139/142 | 82/142 | 71/338 | 338/338 | 235/338 |
| precision, median / mean | 1.000 / 0.929 | 1.000 / 0.919 | 1.000 / 0.990 | 1.000 / 0.736 | 1.000 / 1.000 | 1.000 / 0.990 |
| extraneous entries | 6 | 14 | 1 | 22 | 0 | 2 |
| unresolved citations | 0 | 0 | 1 | 2 | 0 | 0 |
| median input tokens per item | 1,024 | 3,054 | 1,182 | 1,326 | 4,017 | 1,806 |
| mean tool calls per item | 0 | 1.19 | 0 | 0 | 1.00 | 0 |

The 7 and 13 `links` items with recall 0 are exactly the parse failures listed above.

Two `graph` items are below 1.0, both on Article 13:
- seg03439 / 13(1)(d): recall 0.75, four tool calls.
- seg06494 / 13(1)(e): recall 0.50, two tool calls.

Both called `get_conditions`, so neither is a workflow failure in the sense of section 8.

**Which links `fulltext` misses.** Counts are items where the link was missed, over items whose reference contains it.

Article 13:
- `cond-collected-from-data-subject` (the Article 13(1) scope trigger): missed on 42/42.
- `exc-art13-4-already-has-info`: missed on 13/42.
- The paragraph's own timing condition: missed on 2/40 (13(1) and 13(2) together).

Article 14:
- `cond-14-3-b-first-communication`: missed on 44/44.
- `cond-14-3-c-first-disclosure`: missed on 44/44.
- `exc-art14-5-d-professional-secrecy`: missed on 45/46.
- `exc-art14-5-c-laid-down-by-law`: missed on 44/46.
- `cond-collected-from-data-subject`: missed on 38/46.
- `exc-art14-5-b-impossible-disproportionate`: missed on 31/46.
- `exc-art14-5-a-already-has-info`: missed on 18/46.

`fulltext` answers carry about two entries per item: 1.86 mean on Article 13, 2.02 on Article 14. The reference sets hold 3 to 4 links on Article 13 and 7 to 8 on Article 14.

## Secondary tests (no claim on their own)

| test | Article 13 | Article 14 |
|---|---|---|
| strict-rule recall, `fulltext` vs `graph` | n 42, ties 3, median diff -0.667, p < 0.000001 | n 46, ties 0, median diff -0.857, p < 0.000001 |
| cross-provision recall, `fulltext` vs `graph` | n 42, ties 0, median diff -0.333, p < 0.000001 | n 46, ties 0, median diff -0.857, p < 0.000001 |
| precision, `fulltext` vs `graph` | n 42, ties 26, median diff 0.000, p = 0.84 | n 46, ties 28, median diff 0.000, p = 0.000008 |
| recall, `fulltext` vs `links` | n 42, ties 16, median diff 0.000, p = 0.34 | n 46, ties 3, median diff -0.714, p < 0.000001 |
| primary test on parsed answers only | n 42, ties 1, median diff -0.500, p < 0.000001 | n 46, ties 0, median diff -0.750, p < 0.000001 |

Mean recall under the strict and kind rules:
- `fulltext`: 0.300 (strict) and 0.294 (kind) on Article 13; 0.183 and 0.168 on Article 14.
- `graph`: 0.935 and 0.982 on Article 13; 1.000 and 0.977 on Article 14.

## Predictions

| | Article 13 | Article 14 |
|---|---|---|
| P1 `fulltext` recall below `graph`, significant | holds | holds |
| P2 `fulltext` complete set on fewer than half of items | holds (0/42) | holds (0/46) |
| P2, Article 14 share smaller than Article 13 | | not met: both 0 |
| P3 `fulltext` mean recall below 0.9; Article 14 below Article 13 | holds (0.512) | holds (0.208 < 0.512) |
| P4 `links` mean recall within 0.10 of `graph` | fails (0.581 vs 0.982) | fails (0.700 vs 1.000) |
| P5 `fulltext` precision not above `graph` | medians equal (1.000); means 0.929 vs 0.919; test p = 0.84 | holds (0.736 vs 1.000, p = 0.000008) |

P5 on Article 13 is not a clean pass: the preregistration did not say whether "above" is judged by mean or by the test. By the test there is no difference; by the mean `fulltext` is 0.010 higher.

## Exploratory, not pre-registered: `links` parse failures

All 20 `links` parse failures have one of two format slips:
- a bare JSON array instead of the `{"qualifications": [...]}` object, or
- the object without its final closing brace.

`lenient_links.py` repairs only these two slips and rescores; output in `fullarticle.lenient_links.json`. After repair, 20 of 20 answers parse and 0 remain unreadable.

| | Article 13 | Article 14 |
|---|---|---|
| `links` mean recall, repaired | 0.704 | 0.983 |
| `links` complete set, repaired | 7/42 | 43/46 |
| `links` vs `graph`, Wilcoxon | 35 non-zero differences, p = 1.3e-7 | 3 non-zero differences, p = 0.25 |

On Article 13 the remaining `links` shortfall is mostly one link: `cond-collected-from-data-subject` is missed on 29/35 parsed items. The pre-registered P4 verdict above stands as written; this section only locates where the P4 failure comes from.

## Instrument check (pre-registered, descriptive, author-read)

Scope: the first 10 items per article in sample order, `fulltext` condition. Each matched entry's justification was read against the link it was matched to.

**Article 13.** 17 matched entries:
- 11 state the matched link.
- 6 do not. In these the justification states:
  - the duty's own applicability: 13(2)(e) statutory requirement; 13(2)(c) consent basis;
  - the 13(1) scope trigger, matched to a different link: 2 entries;
  - the transfer itself: 2 entries.

**Article 14.** 13 matched entries:
- 5 state the matched link.
- 8 do not. In 7 of these the citation names one point of 14(5) and the justification paraphrases another, for example "Article 14(5)(b)" with the 14(5)(c) "laid down by law" wording.

Reading: the primary rule credits `fulltext` with some links its answers do not state. The `fulltext` recall above is therefore, if anything, an overestimate under a content reading. `graph` answers copy the tool payload, so this check was not run on them, as pre-registered.

## Caveats

- **The reference is the graph's own encoding.** `graph` recall near 1.0 is structural: the tool returns the links being scored (preregistration section 7). The informative number is the `fulltext` one.
- **Corpus.** LexiGen segments are synthetic.
- **Model.** One 7B model, one temperature-0 decode per item and condition.
- **Segment reuse.** Most segments were reused from earlier studies: Article 13 has 30 fresh and 12 reused; Article 14 has 1 fresh and 45 reused. The reference depends only on the fixed duty, so reuse does not change what is scored.
- **Pseudo-replication.** Each duty appears twice. The per-duty test (n = 21 and 23) gives the same answer as the per-item test.

## Verdict

**Strong enough for the paper.** The pre-registered reading rule (section 8) gives the **assembly reading on both articles**:
- P1 and P2 hold on both, and the per-duty test agrees.
- With the whole article in the prompt and the duty fixed, `fulltext` never produced the complete encoded set: 0/42 and 0/46 items.
- It recovered about half of the links on Article 13 and about a fifth on Article 14.
- What it drops is mainly the cross-paragraph qualifications. These are the 13(1)/14(1) scope trigger, the 14(3)(b)-(c) timing conditions and the 14(5)(b)-(d) exceptions.
- The graph-assisted workflow recovered 139/142 and 338/338 links at roughly three times the input tokens.

How this changes the claim:
- The earlier text-condition gap is not explained by the text store failing to return the right passages. Given everything, the model still does not assemble the qualification set.
- The claim can be stated as assembly, not availability. It should be scoped to "the links this graph encodes", one 7B model and a synthetic corpus.
- The secondary result narrows what the graph adds. Handing the same links over as plain text recovers most of them on Article 14 once two format slips are repaired (exploratory), but not on Article 13 (0.70).
- So the benefit comes largely from the links being explicit and enumerated, not from the tool interface as such. This holds more clearly on Article 14 than on Article 13.
