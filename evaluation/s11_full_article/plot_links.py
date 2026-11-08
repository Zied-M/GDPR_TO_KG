"""Figure for the article: how often each qualification was cited, full text vs graph tools.

One row per qualification that the graph attaches to many duties (the shared,
cross-paragraph ones), plus one pooled row for the duty-specific conditions that sit in
the duty's own provision. The x value is the share of items whose reference set holds
that qualification and whose answer cited it (primary rule, score.py).
The links-as-text condition is secondary and stays in the table, not here.

Run from publish-gdpr-kg/ (needs rdflib and matplotlib):
    python -B paper_draft/s11_full_article/plot_links.py \
        paper_draft/s11_full_article/fullarticle.analysis.json \
        paper_draft/s11_full_article/fig_s11_links.png
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stores  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SHARED_MIN = 10   # a qualification on at least this many items gets its own row
LABELS = {
    "cond-collected-from-data-subject": "Data collected from the data subject [13(1) / 14(1)]",
    "exc-art13-4-already-has-info": "Exception: already has the information [13(4)]",
    "cond-13-2-at-time-obtained": "Timing: when data are obtained [13(2)]",
    "cond-13-1-at-time-obtained": "Timing: when data are obtained [13(1)]",
    "exc-art14-5-a-already-has-info": "Exception: already has the information [14(5)(a)]",
    "exc-art14-5-b-impossible-disproportionate": "Exception: impossible or disproportionate [14(5)(b)]",
    "exc-art14-5-c-laid-down-by-law": "Exception: laid down by law [14(5)(c)]",
    "exc-art14-5-d-professional-secrecy": "Exception: professional secrecy [14(5)(d)]",
    "cond-14-3-b-first-communication": "Timing: at first communication [14(3)(b)]",
    "cond-14-3-c-first-disclosure": "Timing: at first disclosure [14(3)(c)]",
}
FULL, GRAPH = ("fulltext", "Full article text", "#2a78d6"), ("graph", "Graph tools", "#eb6834")
INK, MUTED, RULE = "#1a1a1a", "#6b6a66", "#d9d8d4"


def rates(rows, graph, art):
    tot, hit = collections.Counter(), {c: collections.Counter() for c in ("fulltext", "graph")}
    for r in rows:
        if r["article"] != art:
            continue
        for rel in graph.duties[r["duty_id"]]["relations"]:
            tot[rel["relation_id"]] += 1
        for c in hit:
            for rid in r["scores"][c]["primary"]["matched_relations"]:
                hit[c][rid] += 1
    out, pooled = [], {"n": 0, "fulltext": 0, "graph": 0}
    for rid, n in tot.most_common():
        if n >= SHARED_MIN:
            out.append((LABELS.get(rid, rid), n, hit["fulltext"][rid] / n, hit["graph"][rid] / n))
        else:
            pooled["n"] += n
            for c in hit:
                pooled[c] += hit[c][rid]
    if pooled["n"]:
        out.append(("Duty's own conditions, pooled", pooled["n"],
                    pooled["fulltext"] / pooled["n"], pooled["graph"] / pooled["n"]))
    return out


def main(src, dst):
    rows = json.load(open(src, encoding="utf-8"))["items"]
    _, graph = stores.load()
    data = {a: rates(rows, graph, a) for a in (13, 14)}
    heights = [len(data[13]), len(data[14])]
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 0.42 * sum(heights) + 1.6),
                             gridspec_kw={"height_ratios": heights}, facecolor="white")
    for ax, art in zip(axes, (13, 14)):
        rs = data[art]
        n_items = sum(1 for r in rows if r["article"] == art)
        ys = list(range(len(rs)))[::-1]
        for y, (lab, n, ft, gr) in zip(ys, rs):
            ax.plot([ft, gr], [y, y], color=RULE, lw=2.2, zorder=1)
            # graph as a ring, full text as a filled dot on top: both stay visible when equal
            ax.scatter(gr, y, s=80, facecolor="white", edgecolor=GRAPH[2], linewidth=2, zorder=3)
            ax.scatter(ft, y, s=34, color=FULL[2], zorder=4)
            ax.text(-0.02, y, "%s  (n=%d)" % (lab, n), ha="right", va="center",
                    fontsize=8, color=INK)
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.6, len(rs) - 0.4)
        ax.set_yticks([])
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"],
                      fontsize=8, color=MUTED)
        for x in (0.25, 0.5, 0.75):
            ax.axvline(x, color=RULE, lw=0.6, zorder=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(RULE)
        ax.text(-0.02, len(rs) - 0.2, "Article %d duties (%d items)" % (art, n_items),
                ha="right", va="bottom", fontsize=9.5, fontweight="bold", color=INK)
    axes[-1].set_xlabel("Share of items whose answer cited the qualification", fontsize=8.5,
                        color=INK)
    handles = [plt.Line2D([], [], marker="o", ls="", color=FULL[2], label=FULL[1]),
               plt.Line2D([], [], marker="o", ls="", markerfacecolor="white",
                          markeredgecolor=GRAPH[2], markeredgewidth=2, label=GRAPH[1])]
    fig.legend(handles=handles, loc="upper right", ncol=2, frameon=False, fontsize=8.5)
    fig.subplots_adjust(left=0.52, right=0.97, top=0.9, bottom=0.12, hspace=0.45)
    fig.savefig(dst, dpi=300)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
