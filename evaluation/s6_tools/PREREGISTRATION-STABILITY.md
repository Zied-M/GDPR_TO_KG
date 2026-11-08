# Pre-registration: the stability measurement

**Written 2026-09-15 (S8), BEFORE any generation. Not to be edited after a run.** Its
digest is recorded in `PREREGISTRATION-STABILITY.sha256`.

This is the separate pre-registration that `PREREGISTRATION.md` section 5 promised when M
was fixed. **`PREREGISTRATION.md` is frozen and is not edited by this file**; the two stand
side by side, and the reach study does not depend on anything here.

Design: `context/05_EVAL_PLAN.md` **Part D item 4**, which Part E does not override.
Stability is **reported separately from reach and is never folded into it**.

---

## 1. The parameters, all fixed before any run

| parameter | value | decided |
|---|---|---|
| N, repeats per item | **5** | author, 2026-09-06 |
| M, subsample size | **50** | author, 2026-09-15 |
| temperature | **0.0** | author, 2026-09-15 |
| model, `num_ctx`, turn cap | `qwen2.5:7b` pinned, 16384, 10 | E4 and E8, unchanged |

Total cost: 50 items x 5 repeats x 2 arms = **500 generations**, equal to the reach study
itself.

**N and M are separate knobs and conflating them is the easy error.** N controls per-item
resolution: at N = 3 a single deviation is 33% and cannot be told from noise, at N = 5 it
is 20%, which separates "always identical" from "mostly" from "unstable". M controls the
confidence interval on the aggregate. Widening the interval is a job for M, never for N.

**Why M = 50.** At temperature 0 the stability proportion is expected at or near 1.0, so
what M buys is the **lower bound**, not a half-width. M = 50 gives a 95% Wilson interval of
[0.929, 1.000] if every item is stable, against [0.867, 1.000] at M = 25 and [0.963, 1.000]
at M = 100. Above 75 the bound moves about two points per 250 extra generations. M = 50 is
the point where the bound stops reading weaker than the finding and the cost stops being
worth it. **This number was chosen from the interval width the result needs to support, not
by eye**, which is what Part D item 4 required of it.

---

## 2. The subsample, frozen before any run

Drawn by `freeze_stability.py` into `stability.frozen.json`, from the **250 study items**
of `sample.frozen.json`. Frozen now for the same reason the pre-registration is written
now: a subsample chosen after the results exist is not a subsample, it is a selection.

- seed **`20260916`**, the study seed `20260915` plus one, so the two draws are independent
  streams reproducible from a single recorded number
- stability sha256 `7b942344089e2d4c1cbf42992bedd69b13b3c7a5d6cf00418ad06564ea210afa`
- study sample sha256 `96cdc651592ddc51f031103cb27dc7198ce8a6d06555be4abbaeac4bfbfa5a40`

**Allocation is proportional to the study strata and is forced rather than chosen:**
APP-14 20, APP-13 15, APP-12 5, APP-46 5, NA-46 5. Stability is a property of the substrate
rather than of any individual policy, so the draw is not label-balanced and the label mix
falls where it falls (31 COMPLIANT, 14 NON_COMPLIANT, 5 NOT_APPLICABLE). Forcing a label
balance would be balancing on a variable the measure does not turn on.

---

## 3. What is measured

Part D item 4's object: **does the cited provision set hold across the five runs on the
same item?** Two readings of "cited provision set" exist under the tool design, and they
are pre-registered with different standing.

**Primary, and it needs no new instrument.** The **relied-provision set read from the tool
trace** (`relied_units` in `reach.py`, already computed and already hand-checked in S7),
plus the item's **reach status**. Both are read mechanically from the tool call log. An
item is **stable** when all five runs produce the identical relied-provision set, and the
reach status is reported alongside as a second, coarser stability line.

**Secondary, and it is GATED.** The provisions the model **cites in its final answer**,
which is the literal wording of Part D item 4. Extracting those requires parsing prose,
which is a new automatic component. **It owes a hand-check on the same terms `reach.py`
paid in S7 before it may produce any number**, and this project has been burned twice by
trusting an unchecked automatic component (the entailment metric at kappa 0.133, and limb
(c)'s support/aptness ambiguity found only afterwards). **If the parser is not built and
hand-checked, this line produces no number** and the primary measure stands alone. It is
not a fallback for a disappointing primary result and may not be swapped in after the fact.

**Reported per arm, per stratum. Stratify, never pool.** Same boundary as the reach study.

---

## 4. The analysis, stated before the data

- **Per-item aggregate:** the proportion of the M items whose relied-provision set is
  identical across all five runs, with a **Wilson score interval** (`brown2001interval`),
  per arm, per stratum.
- **Per-item resolution:** agreement across five runs on one item is an inter-rater problem
  with five raters, interpreted on `landis1977agreement`'s scale. Items are reported by how
  many of the five runs agree, not only as stable or not, because that gradient is what
  N = 5 was chosen to expose.
- **Both instruments are already on file.** Neither is a new dependency.
- **Never folded into reach.** A model can cite the right provision in different words each
  run (grounded, unstable) and can cite the same wrong provision every run (stable,
  ungrounded). A result cannot be interpreted unless the two are measured apart. That is
  the author's 2026-09-06 split and it holds.

---

## 5. The limitation, stated here rather than discovered later

**At temperature 0.0 this measures harness reproducibility, not generation variance.** With
a pinned model, a deterministic retrieval layer and greedy decoding, repeated runs are close
to identical by construction, so a high stability figure is a **floor** rather than a
finding.

The author's original concern was broader: that an LLM justification "can be undeterministic
and can change". **This measurement does not answer that broader concern and no draft may
present it as if it did.** Answering it needs temperature above 0, which is a different
design decision with its own cost, and it would need its own pre-registration before its
run. The author chose temperature 0.0 on 2026-09-15 with that trade-off in front of them.

What the measurement does buy, and it is worth the 500 generations: a stated bound on
reproducibility, which is the precondition for every other number in the study being
attributable to the representation rather than to the provider.

---

## 6. When it runs

**After** the reach study, in S9 or later, and never before. It reuses the study items, so
running it first would produce generations on items whose reach results do not yet exist,
and the two would then have to be kept apart by hand. There is no analytical dependency in
either direction; this is an ordering convenience, and the stability result is reported
whatever the reach result turns out to be.
