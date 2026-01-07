# codes/svg_charts.py
# Generates dotted, filled-from-zero rating charts as SVGs for Blitz/Rapid/Bullet.
# Design: Ivory card, rounded corners, header area with meta text, dotted vertical columns,
# limited Y ticks (<=6), negative spacing around axes, monotone per time_class.
#
# Requires: requests, numpy, matplotlib
# Run environment: headless (matplotlib Agg backend)

import os
import re
import math
import requests
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# -----------------------
# CONFIG / DESIGN VALUES
# -----------------------

# Palette (you can swap hexes here with exact brand values)
COLOR_IVORY = "#F6F4EF"         # background card
COLOR_CHARCOAL = "#2A2529"      # text, axis
COLOR_MOSS = "#486b3a"          # rapid
COLOR_UMBER = "#594434"         # blitz
COLOR_MIDNIGHT = "#0f2640"      # bullet

TIME_CLASSES = {
    "blitz": {"color": COLOR_UMBER, "label": "BLITZ"},
    "rapid": {"color": COLOR_MOSS, "label": "RAPID"},
    "bullet": {"color": COLOR_MIDNIGHT, "label": "BULLET"},
}

USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100  # default window - this script will cap per available games

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"
OUTPUT_DIR = "assets/svg"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Figure geometry (you asked for dynamic minimum; these are sensible defaults)
FIG_W = 1200          # px target width
FIG_H = 520           # px target height
DPI = 96              # standard screen DPI
FIGSIZE = (FIG_W / DPI, FIG_H / DPI)

# Card / layout
CARD_PAD_LEFT = 0.08    # fraction of width
CARD_PAD_RIGHT = 0.06
CARD_PAD_TOP = 0.22     # room for header text
CARD_PAD_BOTTOM = 0.12
CARD_ROUNDING = 18      # px radius

# Dot/grid
DOT_DIAMETER_PX = 7      # dot diameter in px
DOT_STEP_RATING = 8      # rating units between dot rows (controls density)
DOT_EDGE_PADDING = 0.5   # x padding (in x-units) left and right (negative spacing effect)

# Axis styling
MAX_Y_TICKS = 6
AXIS_LINEWIDTH = 1.2
TICK_LABEL_SIZE = 11
HEADER_FONT_SIZE = 14
META_FONT_SIZE = 11
FOOTER_FONT_SIZE = 10

REQUEST_HEADERS = {"User-Agent": "ChessRatingRefresh/1.0 (atharvashimpi)"}  # polite


# -----------------------
#  Helper functions
# -----------------------

def get_archives_sorted(username=USERNAME):
    """Returns a list of archive URLs sorted from oldest -> newest.
       Archive URLs generally end with /YYYY/MM - we parse that to sort.
    """
    resp = requests.get(ARCHIVES_URL.format(user=username), headers=REQUEST_HEADERS, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    archives = data.get("archives", [])
    # try to sort by year/month fragment; fallback to lexicographic
    def archive_key(url):
        m = re.search(r"/(\d{4})/(\d{1,2})/?$", url)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            return (y, mo)
        # fallback: try to extract iso date
        m2 = re.search(r"(\d{4}-\d{2}-\d{2})", url)
        if m2:
            return (m2.group(1),)
        return (url,)
    try:
        sorted_archives = sorted(archives, key=archive_key)
    except Exception:
        sorted_archives = archives[::-1]
    return sorted_archives


def collect_games_for_timeclass(time_class, ngames=NGAMES, username=USERNAME):
    """Collect up to ngames for the given time_class, returning games sorted oldest->newest."""
    archives = get_archives_sorted(username)
    if not archives:
        return []

    collected = []
    for archive in archives:
        try:
            r = requests.get(archive, headers=REQUEST_HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            month_data = r.json().get("games", [])
            # sort monthly games by 'end_time' if available, else keep as is but reverse for safety
            try:
                month_data_sorted = sorted(month_data, key=lambda g: g.get("end_time", g.get("time", 0)))
            except Exception:
                month_data_sorted = month_data[::-1]
            # filter
            filtered = [g for g in month_data_sorted if g.get("time_class") == time_class and g.get("rules") == RULES]
            # extend - oldest first
            collected.extend(filtered)
            # stop if we have enough
            if len(collected) >= ngames:
                break
        except Exception:
            continue
    # keep the most recent ngames, but preserve chronological order (oldest -> newest)
    if len(collected) > ngames:
        collected = collected[-ngames:]
    return collected


def ratings_from_games(games, username=USERNAME):
    """Return list of integer ratings in chronological order (oldest -> newest)."""
    out = []
    for g in games:
        try:
            white = g.get("white", {}).get("username", "")
            # case-insensitive compare
            if str(white).lower() == username.lower():
                out.append(int(g.get("white", {}).get("rating", 0)))
            else:
                out.append(int(g.get("black", {}).get("rating", 0)))
        except Exception:
            out.append(0)
    return out


def nice_ymax(yvals):
    """Return a nice upper bound for y-axis, a small round number above max."""
    if not yvals:
        return 100
    ymax = max(yvals)
    # round up to nearest multiple of DOT_STEP_RATING * n where n ~ 4..8
    step = DOT_STEP_RATING
    # choose a round bracket
    raw = math.ceil((ymax + step) / step) * step
    # also ensure some ceiling
    return int(raw + step * 2)


# -----------------------
#  Rendering function
# -----------------------

def render_timeclass_svg(time_class, ratings, outpath):
    """
    Draw the dotted filled chart for a sequence of ratings (oldest->newest).
    """
    if not ratings:
        # create a minimal "no data" SVG card
        fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
        fig.patch.set_facecolor(COLOR_IVORY)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        fig.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=16, color=COLOR_CHARCOAL)
        fig.savefig(outpath, bbox_inches="tight", facecolor=COLOR_IVORY)
        plt.close(fig)
        return

    n = len(ratings)
    xs = np.arange(n)

    # y-range: we fill from 0 to rating
    y_min = 0
    y_max = nice_ymax(ratings)

    # dot grid vertical positions: from step/2 to y_max - step/2
    step = DOT_STEP_RATING
    dot_centers = np.arange(step / 2.0, y_max + step / 2.0, step)

    # compute number of dots per column
    dots_per_col = [int(max(0, math.floor((r - y_min) / step))) for r in ratings]

    # dynamic dot size, convert diameter px -> scatter 's' parameter in points^2:
    # matplotlib scatter s is area in points^2. Convert: 1 point ~ 1.333 px at 96dpi, but s is points^2.
    px_per_pt = DPI / 72.0
    dot_diameter_pt = DOT_DIAMETER_PX / px_per_pt
    s = (dot_diameter_pt ** 2)  # area approx (this is rough but works)
    s = max(6, s * 5)  # tune: multiply to get visible dots; ensure a min

    # figure & axes layout (we use normalized axes coords)
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(COLOR_IVORY)

    # compute axes rect in figure coordinates with padding fractions
    left = CARD_PAD_LEFT
    right = 1.0 - CARD_PAD_RIGHT
    bottom = CARD_PAD_BOTTOM
    top = 1.0 - CARD_PAD_TOP
    ax_w = right - left
    ax_h = top - bottom
    ax = fig.add_axes([left, bottom, ax_w, ax_h])

    # rounded card background inside ax area (draw on figure coordinates)
    bbox = FancyBboxPatch(
        (left, bottom), ax_w, ax_h,
        boxstyle=f"round,pad=0,rounding_size={CARD_ROUNDING}",
        transform=fig.transFigure, zorder=0,
        linewidth=0, facecolor=COLOR_IVORY
    )
    fig.patches.append(bbox)

    # plot dotted columns by scattering points for each x
    base_x_positions = np.linspace(0, n - 1, n)  # each game's column's center
    # slight x-scale with negative spacing: leave small gap so pattern doesn't touch y-axis
    x_left_edge = -DOT_EDGE_PADDING
    x_right_edge = n - 1 + DOT_EDGE_PADDING
    ax.set_xlim(x_left_edge, x_right_edge)
    ax.set_ylim(y_min - step * 0.5, y_max + step * 0.5)

    color = TIME_CLASSES.get(time_class, {}).get("color", COLOR_CHARCOAL)
    # scatter per column
    all_x = []
    all_y = []
    for xi, num in enumerate(dots_per_col):
        if num <= 0:
            continue
        # dot row centers for this column: from bottom (step/2) up to num*step
        ys = (np.arange(1, num + 1) - 0.5) * step  # .5 offset gives nice centering, starting above zero
        xs_col = np.full_like(ys, xi, dtype=float)
        all_x.append(xs_col)
        all_y.append(ys)
    if all_x:
        X = np.concatenate(all_x)
        Y = np.concatenate(all_y)
        ax.scatter(X, Y, s=s, c=color, marker='o', linewidths=0, alpha=1.0, zorder=3)

    # Axis styling - bottom spine only, left ticks but no left spine line (borderless like Type B)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # bottom spine: draw a subtle baseline
    ax.spines['bottom'].set_linewidth(AXIS_LINEWIDTH)
    ax.spines['bottom'].set_color(COLOR_CHARCOAL)
    ax.spines['bottom'].set_alpha(0.25)

    # Y ticks: at most MAX_Y_TICKS evenly spaced from 0..y_max (include zero)
    num_ticks = min(MAX_Y_TICKS, 1 + max(1, int(math.ceil(y_max / (step * 4)) * 1)))  # heuristic
    num_ticks = max(2, num_ticks)
    yticks = np.linspace(y_min, y_max, num_ticks)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(int(v)) for v in yticks], fontsize=TICK_LABEL_SIZE, color=COLOR_CHARCOAL)
    ax.tick_params(axis='y', length=0)  # hide tick lines
    # x ticks: choose 5 checkpoints (start, 25%, 50%, 75%, end)
    xt_positions = [0, int(n * 0.25), int(n * 0.5), int(n * 0.75), n - 1] if n > 4 else list(range(n))
    xt_positions = sorted(list(dict.fromkeys(xt_positions)))  # unique & sorted
    ax.set_xticks(xt_positions)
    ax.set_xticklabels([str(int(x)) for x in xt_positions], fontsize=TICK_LABEL_SIZE, color=COLOR_CHARCOAL)
    ax.tick_params(axis='x', length=6, pad=8)
    # Move x-axis baseline slightly down visually (negative spacing between x axis and start datapoint)
    ax.spines['bottom'].set_position(('data', -step * 0.25))

    # Grid lines minimal (horizontal faint bands)
    ax.yaxis.grid(False)
    ax.xaxis.grid(False)

    # header text area - place above axes inside figure space (left-aligned)
    # We'll use fig.text in normalized coordinates to ensure consistent placement.
    header_left_x = left + 0.02 * ax_w
    header_right_x = right - 0.02 * ax_w
    header_y = top + (1.0 - top) * 0.5  # a bit above the axes rect
    # Left heading: "BLITZ - CHESS.COM"
    heading_main = TIME_CLASSES.get(time_class, {}).get("label", time_class.upper())
    heading_full = f"{heading_main} - CHESS.COM"
    # Right meta: "<N> GAMES    <current rating> ELO    <timestamp>"
    current_rating = int(ratings[-1]) if ratings else 0
    # We show N games, rating, and approximate timestamp = "LATEST" placeholder (no time zone conversion here)
    meta_right = f"{n} GAMES   {current_rating} ELO   LATEST"
    fig.text(header_left_x, top + 0.04, heading_full, ha="left", va="bottom",
             fontsize=HEADER_FONT_SIZE, color=COLOR_CHARCOAL, weight='normal')
    fig.text(header_right_x, top + 0.04, meta_right, ha="right", va="bottom",
             fontsize=META_FONT_SIZE, color=COLOR_CHARCOAL, alpha=0.95)

    # subtle divider line under header area spanning the axes width
    divider_y = top - 0.02
    fig.lines.append(plt.Line2D([left + 0.01, right - 0.01], [divider_y, divider_y],
                               transform=fig.transFigure, color=COLOR_CHARCOAL, alpha=0.12, linewidth=1))

    # remove ticks/spines clutter (left invisible, etc.)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', which='major', labelcolor=COLOR_CHARCOAL)

    # ensure background of axes is also ivory
    ax.set_facecolor(COLOR_IVORY)

    # tidy layout
    plt.subplots_adjust(left=left, right=right, top=top, bottom=bottom)

    # Save as SVG
    fig.savefig(outpath, format="svg", bbox_inches="tight", facecolor=COLOR_IVORY)
    plt.close(fig)


# -----------------------
#  Main execution
# -----------------------

def main():
    for time_class in TIME_CLASSES.keys():
        # collect recent games for this time class
        games = collect_games_for_timeclass(time_class, ngames=NGAMES, username=USERNAME)
        ratings = ratings_from_games(games, username=USERNAME)
        # If there are more than NGAMES (shouldn't be), cap
        if len(ratings) > NGAMES:
            ratings = ratings[-NGAMES:]
        outfile = os.path.join(OUTPUT_DIR, f"rating-{time_class}.svg")
        try:
            render_timeclass_svg(time_class, ratings, outfile)
            print(f"Written {outfile} (games={len(ratings)})")
        except Exception as e:
            print(f"Error writing {outfile}: {e}")


if __name__ == "__main__":
    main()
