#!/usr/bin/env python3
"""
svg_charts.py
Generates dot-filled, aesthetic SVG rating charts for Blitz / Rapid / Bullet.

Design notes (implemented):
- Ivory background (chart panel) with subtle padding to produce 'floating' chart.
- Dotted vertical columns: dots fill from baseline up to rating for each datapoint.
- Monotone colours per time-class:
    * blitz -> Umber
    * rapid -> Moss Green
    * bullet -> Midnight Blue
- X axis: visible horizontal line with tick marks.
- Y axis: labels + ticks only (no horizontal grid lines).
- Reduced y ticks for less clutter.
- Slight gap (negative spacing) between x-axis and bottom of dots so chart "floats".
- SVG output (vector), safe for embedding in README.md.
"""

import os
import math
import numpy as np
import requests
import matplotlib
matplotlib.use("Agg")             # headless
import matplotlib.pyplot as plt

# ensure vectors only (no PNG embedding)
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"  # convert text to paths for portability

# --- CONFIG ---
USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

# color palette (per your instructions)
COLORS = {
    "blitz": {
        "fill": "#5B3F32",     # Umber (blitz)
    },
    "rapid": {
        "fill": "#4A6B3A",     # Moss Green (rapid)
    },
    "bullet": {
        "fill": "#1F3350",     # Midnight Blue (bullet)
    },
    "text": "#2A2529",         # Charcoal for text
    "bg": "#F6F4ED"            # Ivory background (panel)
}

TIME_CLASSES = ["blitz", "rapid", "bullet"]
ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# visual parameters
FIG_W, FIG_H = 10.5, 3.0         # figure size per chart (inches)
N_ROWS = 22                      # number of dot rows (vertical resolution)
DOT_SIZE = 28                    # matplotlib scatter 's' (point area)
DOT_EDGEWIDTH = 0                # no border on dots for cleaner look
LEFT_PAD = 0.07
RIGHT_PAD = 0.98
TOP_PAD = 0.86
BOTTOM_PAD = 0.12

# typography
AX_FONT = {"family": "sans-serif", "weight": "600", "size": 10}
TITLE_FONT = {"family": "sans-serif", "weight": "700", "size": 11}


# ------------------------------
# Data fetching
# ------------------------------
def get_archives():
    try:
        r = requests.get(ARCHIVES_URL.format(user=USERNAME), timeout=12)
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("archives", [])[::-1]   # oldest->newest
    except Exception:
        return []


def get_ratings(time_class, ngames=NGAMES):
    """
    Returns a list of ratings ordered oldest -> newest (left->right).
    """
    games = []
    for archive in get_archives():
        try:
            r = requests.get(archive, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json().get("games", [])
        except Exception:
            continue

        # keep chronological order within the month: earliest -> latest
        filtered = [g for g in data if g.get("time_class") == time_class and g.get("rules") == RULES][::-1]
        games.extend(filtered)
        if len(games) >= ngames:
            break

    # convert to ratings (oldest->newest)
    ratings = []
    for g in games[:ngames]:
        # defensive: ensure user found
        try:
            side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
            ratings.append(int(g[side]["rating"]))
        except Exception:
            # skip broken entries
            continue

    return ratings


# ------------------------------
# Plot helpers
# ------------------------------
def dot_fill_plot(ax, ratings, color_fill, title_text, footer_text):
    """
    Draws a dotted, column-filled plot into `ax`.
    - ratings: list oldest->newest
    - color_fill: hex color for dots
    """
    if not ratings:
        # blank panel with "no data"
        ax.text(0.5, 0.5, "NO DATA AVAILABLE", ha="center", va="center", color=COLORS["text"], transform=ax.transAxes)
        ax.set_axis_off()
        return

    N = len(ratings)
    x_positions = np.arange(N)

    # determine y-range and padding (so dots don't touch edges)
    rmin = float(min(ratings))
    rmax = float(max(ratings))
    yrange = max(1.0, rmax - rmin)
    margin = yrange * 0.12   # vertical margin around dots to produce floating effect
    ymin_plot = max(0.0, rmin - margin)
    ymax_plot = rmax + margin

    # we'll create N_ROWS equally spaced horizontal positions from ymin_plot to ymax_plot
    y_grid = np.linspace(ymin_plot, ymax_plot, N_ROWS)

    # compute number of dot rows to fill for each x (proportional to rating)
    counts = []
    for r in ratings:
        frac = 0.0 if ymax_plot == ymin_plot else (r - ymin_plot) / (ymax_plot - ymin_plot)
        cnt = int(round(frac * (N_ROWS - 1)))
        counts.append(max(0, min(N_ROWS, cnt)))

    # Draw background panel
    ax.set_facecolor(COLORS["bg"])

    # For performance: build full arrays to scatter once
    xs = []
    ys = []
    for xi, cnt in zip(x_positions, counts):
        if cnt <= 0:
            continue
        # use the first cnt rows from y_grid (these are the *lowest* rows)
        ys_col = y_grid[:cnt]
        xs_col = np.full_like(ys_col, xi, dtype=float)
        xs.append(xs_col)
        ys.append(ys_col)

    if xs:
        xs = np.concatenate(xs)
        ys = np.concatenate(ys)
        ax.scatter(xs, ys, s=DOT_SIZE, c=color_fill, edgecolors=None, linewidths=DOT_EDGEWIDTH, alpha=1.0, marker="o", zorder=3)

    # Axis limits and ticks
    # Note: leave x range slightly padded so first & last columns don't stick to the edges
    xpad = 0.5
    ax.set_xlim(-xpad, N - 1 + xpad)
    ax.set_ylim(ymin_plot - 0.005 * yrange, ymax_plot + 0.02 * yrange)

    # X axis: visible line only at slightly below the lowest dot row (create a gap -> floating)
    # We'll draw a custom horizontal line rather than rely on default spine for better control.
    xaxis_y = ymin_plot - (yrange * 0.035)   # place x axis slightly below lowest dot row
    ax.hlines(xaxis_y, -xpad, N - 1 + xpad, color="#9aa0a6", linewidth=1, zorder=2)
    # X ticks (0..N spaced)
    # show around 6-10 ticks max
    max_xticks = 10
    step = max(1, int(math.ceil(N / max_xticks)))
    xticks = list(range(0, N, step))
    if xticks[-1] != N - 1:
        xticks.append(N - 1)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(t) for t in xticks], fontdict={"family": "sans-serif", "weight": "600", "size": 9}, color=COLORS["text"])
    # place x tick marks at the same y as the axis line (use custom tick positions)
    ax.tick_params(axis="x", which="both", length=6, pad=8, colors=COLORS["text"])

    # Y axis: show 4-6 ticks, labels only, no horizontal grid lines (clean)
    n_yticks = 5
    yticks = np.linspace(ymin_plot, ymax_plot, n_yticks)
    # Round yticks to sensible integers
    yticks_round = [int(round(v)) for v in yticks]
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(v).upper() for v in yticks_round], fontdict={"family": "sans-serif", "weight": "600", "size": 9}, color=COLORS["text"])
    ax.tick_params(axis="y", which="both", length=4, pad=6, colors=COLORS["text"])

    # Remove spines except left grid tick line (we draw x axis ourselves)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Titles / micro-text
    ax.text(0.01, 0.94, title_text.upper(), transform=ax.transAxes, ha="left", va="center", color=COLORS["text"], fontdict=TITLE_FONT)
    # bottom-center microtext under axis (footer)
    ax.text(0.5, -0.20, footer_text.upper(), transform=ax.transAxes, ha="center", va="center", color=COLORS["text"], fontdict={"family": "sans-serif", "weight": "600", "size": 9})

    # remove axis frame box
    ax.set_axisbelow(False)


# ------------------------------
# Main
# ------------------------------
def generate_svgs(output_dir="assets/svg"):
    os.makedirs(output_dir, exist_ok=True)

    for time_class in TIME_CLASSES:
        # request ratings
        ratings = get_ratings(time_class)
        # if NGAMES provided per-class override for display text: compute N used
        used_n = len(ratings)
        title_text = f"{time_class.capitalize()} · Last {used_n} games" if used_n else f"{time_class.capitalize()}"
        footer_text = f"LAST {used_n} GAMES"

        fig = plt.figure(figsize=(FIG_W, FIG_H))
        # adjust padding to create 'negative spacing' / floating look
        plt.subplots_adjust(left=LEFT_PAD, right=RIGHT_PAD, top=TOP_PAD, bottom=BOTTOM_PAD)
        ax = fig.add_subplot(111)
        # panel background should be ivory
        fig.patch.set_facecolor(COLORS["bg"])
        # set axis background same as panel
        ax.set_facecolor(COLORS["bg"])

        # draw dotted filled plot or "no data"
        color_fill = COLORS.get(time_class, {}).get("fill", "#333333")
        dot_fill_plot(ax, ratings, color_fill, title_text, footer_text)

        # finalize and save as SVG
        out_path = os.path.join(output_dir, f"rating-{time_class}.svg")
        # ensure tight bbox and vector output
        plt.savefig(out_path, format="svg", bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    generate_svgs()
