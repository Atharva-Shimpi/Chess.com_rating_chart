# svg_charts.py
# Replace existing file with this code (copy-paste ready).
# Produces visually-refined SVG "card" charts per user spec.

import os
import math
import requests
import datetime
from datetime import timedelta

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Keep matplotlib svg vector settings (no embedded PNG/fonts)
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# ----- User / data settings (unchanged logic) -----
USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# ----- Visual design palette (as locked in) -----
PALETTE = {
    "ivory": "#F6F4EF",         # card background
    "charcoal": "#2A2529",      # text, divider
    "moss": "#4C7A4A",          # rapid
    "umber": "#6B3E2E",         # blitz
    "midnight": "#1F3A55",      # bullet
}

# Map time classes -> color
TIME_COLORS = {
    "blitz": PALETTE["umber"],
    "rapid": PALETTE["moss"],
    "bullet": PALETTE["midnight"],
}


def get_archives():
    resp = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if resp.status_code != 200:
        return []
    data = resp.json()
    return data.get("archives", [])[::-1]


def get_ratings(time_class):
    games = []

    for archive in get_archives():
        resp = requests.get(archive)
        if resp.status_code != 200:
            continue

        data = resp.json().get("games", [])

        filtered = [
            g for g in data
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ][::-1]

        games.extend(filtered)

        if len(games) >= NGAMES:
            break

    ratings = []
    for g in games[:NGAMES]:
        side = (
            "white"
            if g["white"]["username"].lower() == USERNAME.lower()
            else "black"
        )
        ratings.append(g[side]["rating"])

    return ratings


# ----------------- Helper drawing utilities -----------------

def format_time_ist():
    """Return formatted local IST time string like '5:15 PM IST'."""
    # Use UTC now and add IST offset (UTC+5:30)
    now_utc = datetime.datetime.utcnow()
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    return now_ist.strftime("%-I:%M %p IST") if hasattr(now_ist, "strftime") else now_ist.strftime("%I:%M %p IST")


def nice_ceil(x):
    """Round up to a 'nice' number for axis top padding."""
    if x <= 0:
        return 1
    magnitude = 10 ** (int(math.log10(x)))
    norm = x / magnitude
    if norm <= 1:
        nice = 1
    elif norm <= 2:
        nice = 2
    elif norm <= 5:
        nice = 5
    else:
        nice = 10
    return nice * magnitude


def compute_yticks(ymin, ymax, max_ticks=6):
    """Return an array of y-ticks with first tick at ymin (baseline)."""
    if ymax <= ymin:
        return np.array([ymin, ymin + 1])
    # try to choose up to max_ticks ticks (including ymin)
    span = ymax - ymin
    # choose number of intervals between 4..(max_ticks-1)
    for nt in range(max_ticks, 1, -1):
        step = span / (nt - 1)
        # round step to nice
        nice_step = nice_ceil(step)
        ticks = np.arange(ymin, ymin + (nice_step * nt), nice_step)
        if len(ticks) <= max_ticks + 1:
            # ensure first tick equals ymin
            ticks[0] = ymin
            return ticks
    # fallback
    return np.linspace(ymin, ymax, num=min(max_ticks, 6))


# ----------------- Core chart builder -----------------

def draw_card_chart(ratings, time_class, out_path, figsize=(11.0, 5.0)):
    """
    Draw one card-style chart and save as SVG.
    ratings : list[int] (oldest -> newest)
    time_class : "blitz"/"rapid"/"bullet"
    out_path : file path to save SVG
    figsize : inches (width, height)
    """

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    n = max(1, len(ratings))
    # define base y-range (we always fill from 0)
    y_min = 0
    y_max_data = max(ratings) if ratings else 1
    # top padding: make y_upper a little higher than the data max
    pad = max(30, int(0.06 * max(200, y_max_data)))  # stable padding
    y_max = y_max_data + pad

    # Figure and axes layout:
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0.06, 0.18, 0.88, 0.70])  # left, bottom, width, height (these create negative spacing)
    # We'll draw card background as a rounded rect on the figure (not ax) to ensure crisp corners.
    card_margin = 0.02  # fraction of figure for external padding
    card_x = card_margin
    card_y = card_margin
    card_w = 1 - 2 * card_margin
    card_h = 1 - 2 * card_margin

    # Add a rounded rectangle as card background
    # Use figure coordinates by adding a FancyBboxPatch to the figure
    bbox = FancyBboxPatch(
        (card_x, card_y),
        card_w,
        card_h,
        boxstyle="round,pad=0.02,rounding_size=20",
        transform=fig.transFigure,
        linewidth=0,
        facecolor=PALETTE["ivory"],
        mutation_aspect=1,
        zorder=0
    )
    fig.patches.append(bbox)

    # Set axis facecolor (same as card interior to appear seamless)
    ax.set_facecolor(PALETTE["ivory"])

    # Remove spine on top/right; keep subtle bottom x-axis and small ticks
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    # keep bottom spine visible but subtle
    ax.spines["bottom"].set_color(PALETTE["charcoal"])
    ax.spines["bottom"].set_linewidth(0.8)

    # X and Y limits
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(y_min, y_max)

    # Y ticks: compute upto 6 ticks, with baseline included
    yticks = compute_yticks(y_min, y_max, max_ticks=6)
    # ensure baseline tick equals y_min (0)
    if yticks[0] != y_min:
        # force baseline
        yticks = np.insert(yticks, 0, y_min)
        # trim if too many
        if len(yticks) > 6:
            yticks = yticks[0:6]
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(int(t)) for t in yticks], color=PALETTE["charcoal"], fontsize=10)
    # Minor grid lines? keep them very subtle (light horizontal lines) only at y ticks except baseline
    ax.yaxis.grid(False)
    for yy in yticks[1:]:
        ax.axhline(yy, color=PALETTE["charcoal"], linewidth=0.5, alpha=0.08, zorder=1)

    # X ticks: show some samples only (0, n/4, n/2, 3n/4, n-1)
    xticks = [0, int((n - 1) * 0.25), int((n - 1) * 0.5), int((n - 1) * 0.75), n - 1]
    xticks = sorted(list(set([int(t) for t in xticks if 0 <= t <= n - 1])))
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(t) for t in xticks], color=PALETTE["charcoal"], fontsize=10)
    ax.tick_params(axis="x", length=4, color=PALETTE["charcoal"])

    # X baseline tick marks: subtle short ticks
    ax.tick_params(axis='y', which='both', length=0)  # hide y tick marks (we show labels only)

    # Header block (use figure coordinates for placement)
    # Left: "TIMECLASS - CHESS.COM" (CHESS.COM low opacity)
    # Right: "NN GAMES   ELO   TIME IST"
    header_left = f"{time_class.upper()} \u2013 CHESS.COM"
    games_label = f"{n} GAMES"
    elo_label = f"{int(ratings[-1]) if ratings else 'N/A'} ELO"
    time_label = format_time_ist()
    header_right = f"{games_label}   {elo_label}   {time_label}"

    # Place header text inside the card area above the axes
    fig.text(0.075, 0.89, header_left, fontsize=12, fontweight='regular', color=PALETTE["charcoal"], va="center")
    # Fade CHESS.COM part slightly - we'll overlay by drawing left text in two parts
    # To get subtle opacity for CHESS.COM, draw the word with lower alpha:
    # We'll draw full left text, then redraw the "- CHESS.COM" part in lower alpha (approximate)
    if " – " in header_left:
        left_main, left_sub = header_left.split(" – ", 1)
        fig.text(0.075, 0.89, left_main + " – ", fontsize=12, color=PALETTE["charcoal"], va="center")
        fig.text(0.075 + 0.0075, 0.89, left_sub, fontsize=12, color=PALETTE["charcoal"], alpha=0.45, va="center")

    fig.text(0.92, 0.89, header_right, fontsize=11, color=PALETTE["charcoal"], ha="right", va="center")

    # Subtle divider line under header (between horizontal margins)
    fig_line_x1 = card_x + 0.03
    fig_line_x2 = card_x + card_w - 0.03
    fig_line_y = card_y + card_h - 0.195  # tuned to sit just above the axes area
    fig.lines.append(matplotlib.lines.Line2D([fig_line_x1, fig_line_x2], [fig_line_y, fig_line_y],
                                            transform=fig.transFigure,
                                            linewidth=0.8, color=PALETTE["charcoal"], alpha=0.12, zorder=2))

    # ---------------- DOTTED FILL rendering ----------------
    # We want to render vertical stacks of dots for each game index,
    # with dots starting at y=0 and filling up to rating value.

    # Decide dot spacing (vertical data units) → aim for ~30 rows maximum
    target_rows = 30
    dot_step = max(1.0, (y_max - y_min) / float(target_rows))
    # dot marker size (scatter s param = area in points^2)
    dot_area = 28  # tweakable (keeps dots small & crisp in SVG)

    # Horizontal jitter/spacing: place each column at integer x, but we can compress spacing by scaling axis.
    x_positions = np.arange(n)

    # For performance: accumulate x,y lists for scatter
    xs = []
    ys = []

    for i, r in enumerate(ratings):
        # number of dot rows for this rating
        if r <= y_min:
            rows = 0
        else:
            rows = int(math.floor((r - y_min) / dot_step))
        # produce dot centers: offset by half-step to avoid dots touching baseline exactly
        if rows > 0:
            row_heights = y_min + (np.arange(rows) + 0.5) * dot_step
            # optionally clip at y_max - tiny epsilon
            row_heights = row_heights[row_heights <= (y_max - dot_step * 0.1)]
            # same x for all dots in this column
            xs.extend([i] * len(row_heights))
            ys.extend(list(row_heights))

    # scatter dots
    color = TIME_COLORS.get(time_class, PALETTE["charcoal"])
    ax.scatter(xs, ys, s=dot_area, c=color, marker='o', linewidths=0, zorder=3)

    # slightly thicken the x-axis baseline and add small tick markers
    ax.hlines(y=y_min, xmin=-0.5, xmax=n - 0.5, colors=PALETTE["charcoal"], linewidth=0.9, alpha=0.5, zorder=2)

    # Tidy: remove top border & y grid lines we don't want, set fonts
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(10)
        label.set_color(PALETTE["charcoal"])

    # Title inside axes (small, left aligned) similar to Type A micro-head
    ax.text(0.02, 0.96, f"{time_class.capitalize()} \u00B7 Last {n} games",
            transform=ax.transAxes, fontsize=11, va='top', color=PALETTE["charcoal"])

    # Save as SVG
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)


# ----------------- Main loop -----------------

if __name__ == "__main__":
    # create assets/svg folder if not exists
    out_dir = os.path.join("assets", "svg")
    os.makedirs(out_dir, exist_ok=True)

    for t_class, color in TIME_COLORS.items():
        ratings = get_ratings(t_class)
        if not ratings:
            # write an empty placeholder svg so readme doesn't 404
            empty_path = os.path.join(out_dir, f"rating-{t_class}.svg")
            # simple empty card
            # We'll call draw_card_chart with a minimal value set so it still renders the card (no data)
            draw_card_chart([0], t_class, empty_path)
            continue

        out_file = os.path.join(out_dir, f"rating-{t_class}.svg")
        # Keep same NGAMES behavior (ratings already limited by get_ratings)
        draw_card_chart(ratings, t_class, out_file)
