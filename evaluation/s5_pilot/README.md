# s5_pilot: model screen and the abandoned entailment scorer

The pilot produced no result that enters the paper. It backs two statements in the
evaluation section: how the model was chosen, and why citation-entailment scoring was
dropped. Items come from the 40-item pilot draw in `sample.frozen.json` (seed `20260913`),
disjoint from every study sample.

## Model screen

Three open-weight models were installed locally and screened; no other was tried.

| stage | script | recorded output | result |
|---|---|---|---|
| 2, tool payload | `tool_probe.py` | `tool_probe.output.txt` | `llama3:latest` rejects the tools field (HTTP 400); `mistral:7b` and `qwen2.5:7b` both emit a call |
| 3, chaining gate | `chaining_gate.py` | `chaining_gate.run1.output.txt`, `chaining_gate.run2.output.txt` | pass = a `get_conditions` call carrying an id that `find_duties` returned. `mistral:7b` 0/10 and 0/10, `qwen2.5:7b` 10/10 and 10/10 |

Run 1 used the first ten pilot items (Article 12); run 2 (`--mixed`) used ten items across
Articles 12, 13, 14 and 46. The runs share two items, so 18 distinct items in all.
`chaining_gate.run1.first3_traces.txt` holds the calls of the first three run 1 items per
model: every `mistral:7b` duty id is a placeholder such as `find_duties_result[0].duty_id`,
every `qwen2.5:7b` id is one the tool returned. `payloads.json` is the graph-backed store the
gate used.

The two scripts are given as they ran. The only edits are paths: the pilot files are read
from this folder and the corpus path is an argument. Their JSON outputs were not kept; the
console output above is the record. Stage 2 ran once and stage 3 twice, at temperature 0.0
with `num_ctx` 8192 (stage 2) and 16384 (stage 3); neither has been re-run since.

```
python evaluation/s5_pilot/tool_probe.py
python evaluation/s5_pilot/chaining_gate.py PATH/TO/LexiGen_corpus.json [--mixed]
```

## Entailment scorer

Before the reach measure, the plan was to score whether each cited provision entails the
claim it supports, as in ALCE. The scorer was checked against an independent annotation of
100 pilot citations and did not agree with it beyond chance, so it was dropped.

| file | what it is |
|---|---|
| `score_pilot.py`, `score_limb_c_decomposed.py` | the NLI scorer (whole-claim and decomposed variants; needs `torch` and `transformers`) |
| `pilot.llama3_latest.scored.json` | the scored pilot generations |
| `subset.100.meta.json`, `labels.key.json`, `labels.sheet.100.v2.csv` | the 100-citation subset, its key and the annotation sheet |
| `agreement.py` | agreement between the scorer and the annotation |
| `agreement.json`, `agreement.entailment_decomposed.json` | Cohen's kappa 0.018 (whole claim) and the decomposed variant |

The annotator was an LLM, not a person, so this is one automatic judgement disagreeing with
another: it shows the scorer could not be trusted at scale, not that it is wrong. From the
repository root, `agreement.py` reproduces both agreement files byte for byte (it writes
into its own folder):

```
python -B evaluation/s5_pilot/agreement.py
python -B evaluation/s5_pilot/agreement.py labels.sheet.100.v2.csv "GPT ASTRA Verdict" entailment_decomposed
```

The scored file and the sheet contain LexiGen segment text, redistributed under CC BY 4.0
as described in `../README.md`.
