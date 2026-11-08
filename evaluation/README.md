# evaluation: the three pre-registered studies behind the paper's numbers

Every evaluation number the paper reports can be traced to a file here and recomputed
from the stored traces without a model call. Each study keeps its pre-registration, the
digest that pins it, the frozen sample, the harness, the analysis scripts, the analysis
output and the results record.

**The reference in every study is the graph's own encoded duty-qualification links. It
is not legal ground truth.** The corpus is synthetic. One model, `qwen2.5:7b`, at
temperature 0. Read each `RESULTS-*.md` caveats section before quoting a number.

## The studies

| study | folder | pre-registration (sha256) | question | results |
|---|---|---|---|---|
| 1, reach | `s6_tools/` | `PREREGISTRATION.md` (`eddf157f...`) | with tools over a text store or the graph, does the model surface any cross-provision qualification of the duty it relies on? binary per item | `RESULTS-REACH.md` |
| 1, stability | `s6_tools/` | `PREREGISTRATION-STABILITY.md` (`3b4b3e91...`) | do 5 repeats at temperature 0 give the same relied-provision set? (a harness floor, not generation variance) | `RESULTS-STABILITY.md` |
| 2, graded | `s6_tools/` | `PREREGISTRATION-GRADED.md` (`1a9a5f41...`) | the same question as a per-item fraction, on 220 fresh items disjoint from Study 1 | `RESULTS-GRADED.md` |
| 3, full article | `s11_full_article/` | `PREREGISTRATION-FULLARTICLE.md` (`db2dbc99...`) | given the whole article text and a fixed duty, does the model assemble the full encoded qualification set? three conditions: `fulltext`, `graph`, `links` (secondary) | `RESULTS-FULLARTICLE.md` |

In Studies 1 and 2 the text condition's store returned the duty's provision, its
introductory paragraph and its neighbouring points, not the whole article. Study 3 exists
to remove that explanation: every condition receives the full article.

Check every digest (pre-registrations, and the S11 instruments and outputs) with:

```
python verify.py --eval
```

## Files

`s6_tools/` (Studies 1 and 2):

| file | what it is |
|---|---|
| `PREREGISTRATION*.md` / `.sha256` | the three pre-registrations and their digests |
| `freeze_sample.py` / `sample.frozen.json` | Study 1 sample: 250 study and 40 pilot items, seed `20260915` |
| `freeze_stability.py` / `stability.frozen.json` | 50 of the 250, seed `20260916` |
| `freeze_graded.py` / `graded.frozen.json` | Study 2 sample: 220 items, seed `20260917`, disjoint from the 290 above |
| `stores.py` | the shared tool surface (text store and graph store, same three functions) |
| `run_arms.py` | the harness: multi-turn tool loop, one trace per item and arm |
| `reach.py` | traces to per-item reach records (`*.reach.json`) |
| `analyse.py` / `graded_analyse.py` / `stability_analyse.py` | the pre-registered analyses |
| `study.*`, `graded.*`, `stability.*` | traces, reach records, analysis `.json` / `.txt`, run logs |
| `HANDCHECK.md`, `handcheck.*` | the extractor hand-check on 6 items of a superseded sample (instrument check, no result) |
| `RESULTS-*.md` | the results records |

`s11_full_article/` (Study 3):

| file | what it is |
|---|---|
| `PREREGISTRATION-FULLARTICLE.md` / `.sha256` | the pre-registration; the sidecar also pins the four instruments and the frozen sample |
| `freeze_fullarticle.py` / `fullarticle.frozen.json` | 88 items (42 Article 13, 46 Article 14), one fixed duty each, seed `20261107` |
| `smoke.sample.json` | the 4 end-to-end check items; read by the freeze only to exclude their segments |
| `stores.py` | copy of `s6_tools/stores.py` with `load_units` inlined |
| `run_fullarticle.py` | the harness, three conditions |
| `score.py` | scoring and the pre-registered analysis |
| `lenient_links.py` / `fullarticle.lenient_links.json` | exploratory, not pre-registered: repairs two JSON format slips in the `links` condition and rescores |
| `fullarticle.traces.json`, `.run.log`, `.analysis.json`, `.analysis.txt` | run and analysis outputs |
| `plot_recall.py` / `fullarticle_recall.png` | per-item recall figure |
| `plot_links.py` / `fig_s11_links.png` | per-qualification citation figure used in the article |
| `RESULTS-FULLARTICLE.md` / `.sha256` | the results record and the digests of the outputs it was written from |

Left out on purpose: smoke-run traces, incremental `*.partial.jsonl` records, the Study 1
pilot traces, and anything `.gitignore` excludes.

## Rerunning

Python 3 with `rdflib` (`requirements.txt`); `matplotlib` for the two plots. Run from the
repository root. **The analyses need no model and no corpus:**

```
python -B evaluation/s6_tools/stores.py
python -B evaluation/s6_tools/reach.py evaluation/s6_tools/study.traces.json --out study.reach.json
python -B evaluation/s6_tools/analyse.py evaluation/s6_tools/study.reach.json --traces evaluation/s6_tools/study.traces.json --out study.analysis.json
python -B evaluation/s6_tools/graded_analyse.py evaluation/s6_tools/graded.reach.json --out graded.analysis.json
python -B evaluation/s6_tools/stability_analyse.py evaluation/s6_tools/stability.reach.json --traces evaluation/s6_tools/stability.traces.json --out stability.analysis.json
python -B evaluation/s11_full_article/score.py evaluation/s11_full_article/fullarticle.traces.json --out fullarticle.analysis.json
python -B evaluation/s11_full_article/lenient_links.py
python -B evaluation/s11_full_article/plot_links.py evaluation/s11_full_article/fullarticle.analysis.json fig_s11_links.png
```

Each analysis script's `--out x.json` also writes `x.txt`. `reach.py` runs on all three
trace files the same way. `reach.py`, `run_arms.py`, the three analyses and `score.py`
take `--selfcheck`; `stores.py` checks itself when run. `lenient_links.py` writes into
its own folder, over the published file. The outputs above were compared with the
published ones and are byte-identical, `*.reach.json` and both PNGs included.

**Regenerating traces** needs [Ollama](https://ollama.com) serving `qwen2.5:7b` (the
traces record blob `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`;
a different blob behind the same tag is a different model) and the LexiGen corpus file.
Temperature 0 and `num_ctx` 16384 are the scripts' defaults and are set on every call.

```
python -B evaluation/s6_tools/run_arms.py --sample evaluation/s6_tools/sample.frozen.json --split study --corpus PATH --out study.traces.json
python -B evaluation/s6_tools/run_arms.py --sample evaluation/s6_tools/graded.frozen.json --split items --corpus PATH --out graded.traces.json
python -B evaluation/s6_tools/run_arms.py --sample evaluation/s6_tools/stability.frozen.json --split items --repeats 5 --corpus PATH --out stability.traces.json
python -B evaluation/s11_full_article/run_fullarticle.py --sample evaluation/s11_full_article/fullarticle.frozen.json --corpus PATH --out fullarticle.traces.json
```

`--dry-load` on either harness checks the sample against the corpus (every segment's
text digest) and stops before the first model call. Pass `--sample` to `run_arms.py`
explicitly: its default points at a superseded sample outside this repository. The four
freeze scripts reproduce the four frozen samples byte for byte from the corpus below
(`freeze_sample.py` and `freeze_graded.py` take the corpus path as their argument;
`freeze_fullarticle.py` has it as the constant `CORPUS`). Identical model output across
machines is not guaranteed even at temperature 0.

## The LexiGen corpus

The policy segments come from LexiGen (Bouhejba et al., ICAART 2026),
<https://github.com/AliBouhejba/LexiGen>, pinned at commit
`e72f014b98e4fdb4afe614d0660d512079e910f1`, file
`corpus_creation/data/LexiGen_corpus.json` (sha256
`a9cbcdb548d44b6b223052c1995c1a397b0abd76a1d72fd4cc8cd039f47ecefd`, git blob
`edfda3ab1c1b492c9518905bf897331d77b52667`). Every frozen sample records the corpus
sha256 in `meta.corpus_sha256` and, per item, the segment's position (`global_index`)
and the first 16 hex digits of its text sha256 (`text_sha256_16`).

**The corpus is not copied here.** The frozen samples carry ids, labels and hashes only.
The Study 1 and 2 traces (`s6_tools/*.traces.json`, `handcheck.traces.json`) do contain
LexiGen segment text, because the segment is part of each prompt and the model quotes
it. LexiGen's corpus is licensed CC BY 4.0 (`CC BY 4.0_LICENSE` at the pinned commit,
Copyright (c) 2025 Ali Bouhejba, <https://creativecommons.org/licenses/by/4.0/>); those
segments are redistributed unchanged under that licence, with this attribution. The
Study 3 traces record segment ids only.

## Changes from the workspace copies

Every file is byte-identical to the copy the studies ran from, except
`s6_tools/stores.py`: its import of `load_units` from an unpublished helper module is
replaced by the same function inlined, as `s11_full_article/stores.py` already does. No
logic changed; the self-check gives the same inventory (87 units, 74 duties, 258
relations, 223 cross-provision) and every output above reproduces. Workspace digest
`d6ca5433...`, published digest `11b483ca...`. Neither is pinned by a pre-registration.
Docstrings still give run paths under `paper_draft/`; the commands above are the
current ones.
