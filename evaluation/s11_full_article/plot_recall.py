"""Paired dot plot of per-item recall (primary rule) by article and condition.

Reads score.py's output, so it needs only matplotlib (system python, not the .venv):
    python plot_recall.py fullarticle.analysis.json fullarticle_recall.png
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONDS = [("fulltext", "Full text", "#2a78d6"), ("graph", "Graph tools", "#eb6834"),
         ("links", "Links as text\n(secondary)", "#1baf7a")]
INK, MUTED, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"


def main(src, dst):
    rows = json.load(open(src, encoding="utf-8"))["items"]
    rng = random.Random(0)                       # jitter only; fixed so the figure is reproducible
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True, facecolor=SURFACE)
    for ax, art in zip(axes, (13, 14)):
        rs = [r for r in rows if r["article"] == art]
        ax.set_facecolor(SURFACE)
        for r in rs:
            jx = rng.uniform(-0.12, 0.12)
            jy = rng.uniform(-0.012, 0.012)
            pts = [(i + jx, r["scores"][c]["primary"]["recall"] + jy)
                   for i, (c, _, _) in enumerate(CONDS) if c in r["scores"]]
            ax.plot(*zip(*pts), color=MUTED, lw=0.6, alpha=0.25, zorder=1)
            for (x, y), (c, _, col) in zip(pts, [k for k in CONDS if k[0] in r["scores"]]):
                ax.scatter(x, y, s=22, color=col, edgecolor=SURFACE, linewidth=0.8, zorder=2)
        labels = []
        for c, lab, _ in CONDS:
            v = [r["scores"][c]["primary"]["recall"] for r in rs if c in r["scores"]]
            labels.append("%s\ncomplete %d/%d" %(lab, sum(1 for x in v if x == 1.0), len(v)))
        ax.set_xticks(range(len(CONDS)), labels, fontsize=8, color=INK)
        ax.set_title("Article %d (n = %d items)" % (art, len(rs)), fontsize=9.5, color=INK, loc="left")
        ax.set_ylim(-0.08, 1.08)
        ax.set_xlim(-0.5, len(CONDS) - 0.5)
        ax.grid(axis="y", color="#e4e3df", lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#c9c8c3")
        ax.tick_params(colors=MUTED, labelsize=8)
    axes[0].set_ylabel("Recall of encoded links per item", fontsize=8.5, color=INK)
    fig.tight_layout()
    fig.savefig(dst, dpi=300, facecolor=SURFACE)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
