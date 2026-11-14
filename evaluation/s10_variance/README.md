# s10_variance: exploratory variance study (temperature 0.7 and 1.0)

Exploration, not one of the main studies. It backs one sentence in the paper's discussion:
at temperature 0.7, only 5 of 100 item-arms (50 items in each condition) relied on the same
set of provisions across all ten runs. Studies 1 to 3 measure **completeness** (does the
model get hold of a duty's qualifications); this study measures **consistency** (does it rely
on the same provisions when asked again). Neither result qualifies the other.

Design: the 50-item stability sample (`../s6_tools/stability.frozen.json`, seed `20260916`)
reused unchanged, both conditions (`text`, `graph`), N = 10 repeats per item, `qwen2.5:7b`,
`num_ctx` 16384, no seed. Primary outcome: the modal relied-provision-set share per item.

| file | what it is |
|---|---|
| `PREREGISTRATION-VARIANCE.md` / `.sha256` | the pre-registration and its digest, frozen before any generation |
| `variance_analyse.py` | the pre-registered analysis; imports its grouping and test from `../s6_tools/` |
| `var07.*` | the temperature 0.7 rung: traces, reach records, run log, analysis `.json` / `.txt` |
| `var10.*` | the temperature 1.0 rung, same files |
| `canary_start.*`, `canary_end.*` | execution controls for the 0.7 rung: 10 items at temperature 0.0 before and after |
| `canary10_*.*` | the same controls around the 1.0 rung |
| `RESULTS-VARIANCE.md` | the results record for both rungs |

`RESULTS-VARIANCE.md` was written in the working tree and mentions a few working notes
(`README.md`, `KICKOFF.md`, `FINDING-LOAD-STATE.md`, `icheck1*`) that are not published.
They hold process notes and an instrument-check observation withdrawn before the study ran,
not results.

## Rerunning

From the repository root, no model needed:

```
python -B evaluation/s10_variance/variance_analyse.py --selfcheck
python -B evaluation/s10_variance/variance_analyse.py evaluation/s10_variance/var07.reach.json evaluation/s10_variance/var07.traces.json --out var07.analysis.json
python -B evaluation/s10_variance/variance_analyse.py evaluation/s10_variance/var10.reach.json evaluation/s10_variance/var10.traces.json --out var10.analysis.json
python -B evaluation/s6_tools/reach.py evaluation/s10_variance/var07.traces.json --out var07.reach.json
```

Both analyses, all reach records (rungs and controls) reproduce the published files byte
for byte. The traces were generated with `../s6_tools/run_arms.py` on the stability sample
with `--repeats 10` and the rung's temperature.
