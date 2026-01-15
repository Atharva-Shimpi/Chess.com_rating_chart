import os
import requests
import numpy as np
from datetime import datetime
import pytz

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================
# FILE SYSTEM
# ============================================================

OUTPUT_DIR = "assets/svg"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# GLOBAL VISUAL THEME
# ============================================================

BG_COLOR = "#F6F4EF"       # Ivory background
TEXT_COLOR = "#2A2529"    # Neutral charcoal

matplotlib.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "axes.edgecolor": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "svg.fonttype": "path",
    "svg.image_inline": False,
})

# ============================================================
# USER / API CONFIG
# ============================================================

USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

HEADERS = {"User-Agent": "ChessRatingRefresh/1.0"}
ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

TIME_CLASSES = {
    "blitz":  {"color": "#3E2F2A"},
    "rapid":  {"color": "#3A5F3A"},
    "bullet": {"color": "#1F2A44"},
}

# ============================================================
# AXIS GEOMETRY (INDEPENDENT OF MARGINS)
# ============================================================

X_AXIS_LEFT_PADDING = 2
X_AXIS_RIGHT_PADDING = 1

FLOAT_GAP_RATIO = 0.16
TOP_PADDING_RATIO = 0.15

DOT_DIAMETER_Y = 6

# ============================================================
# EDITORIAL LAYOUT MARGINS (PHASE 5 LOCKED)
# ============================================================

FIG_LEFT_MARGIN   = 0.075
FIG_RIGHT_MARGIN  = 0.045
FIG_BOTTOM_MARGIN = 0.10
FIG_TOP_MARGIN    = 0.30

# ============================================================
# DATA FETCHING
# ============================================================

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME), headers=HEADERS)
    return r.json().get("archives", [])[::-1] if r.status_code == 200 else []


def get_ratings(time_class):
    games = []
    for archive in get_archives():
        r = requests.get(archive, headers=HEADERS)
        if r.status_code != 200:
            continue

        data = r.json().get("games", [])
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

    return ratings[::-1]

# ============================================================
# DOTTED GRAPH
# ============================================================

def plot_dotted_fill(ax, ratings, color):
    x_positions = range(len(ratings))

    min_r, max_r = min(ratings), max(ratings)
    r_range = max_r - min_r
    dot_step = max(6, int(r_range / 22))

    float_base = min_r
    visual_base = float_base - (DOT_DIAMETER_Y / 2)

    ax.set_ylim(
        visual_base - r_range * FLOAT_GAP_RATIO,
        max_r + r_range * TOP_PADDING_RATIO
    )

    ax.set_xlim(-X_AXIS_LEFT_PADDING, len(ratings) + X_AXIS_RIGHT_PADDING)

    for x, r in zip(x_positions, ratings):
        ys = range(float_base, r + dot_step, dot_step)
        ax.scatter([x]*len(ys), ys, s=18, color=color, linewidths=0)

    yticks = np.linspace(
        visual_base + DOT_DIAMETER_Y,
        ax.get_ylim()[1],
        6
    )
    ax.set_yticks([int(round(y)) for y in yticks])

# ============================================================
# AXIS STYLING
# ============================================================

def style_axes(ax):
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_alpha(0.4)
    ax.spines["bottom"].set_linewidth(1.2)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=4, width=1, pad=6)
    ax.grid(False)

# ============================================================
# PHASE 6 — HEADER BLOCK (FINAL)
# ============================================================

def draw_header(fig, ax, time_class, ratings, color):
    game_count = len(ratings)
    latest_elo = ratings[-1]

    ist = pytz.timezone("Asia/Kolkata")
    time_str = datetime.now(ist).strftime("%-I:%M %p IST")

    left_x = ax.get_position().x0
    right_x = ax.get_position().x1

    header_y = 1 - FIG_TOP_MARGIN + 0.11
    divider_y = 1 - FIG_TOP_MARGIN + 0.065

    dot = " · "

    # LEFT CLUSTER
    fig.text(left_x, header_y, time_class.upper(), ha="left", fontsize=13, color=color)
    fig.text(left_x + 0.055, header_y, dot, fontsize=14, color=TEXT_COLOR)
    fig.text(left_x + 0.070, header_y, "CHESS.COM", fontsize=13, color=TEXT_COLOR)

    # RIGHT CLUSTER (even spacing)
    cursor = right_x
    step = 0.085

    fig.text(cursor, header_y, time_str, ha="right", fontsize=13, color=TEXT_COLOR)
    cursor -= step

    fig.text(cursor, header_y, dot, ha="right", fontsize=14, color=TEXT_COLOR)
    cursor -= step

    fig.text(cursor, header_y, f"{latest_elo}", ha="right", fontsize=13, color=color)
    fig.text(cursor + 0.012, header_y, " ELO", ha="left", fontsize=13, color=TEXT_COLOR)
    cursor -= step

    fig.text(cursor, header_y, dot, ha="right", fontsize=14, color=TEXT_COLOR)
    cursor -= step

    fig.text(cursor, header_y, f"{game_count}", ha="right", fontsize=13, color=color)
    fig.text(cursor + 0.012, header_y, " GAMES", ha="left", fontsize=13, color=TEXT_COLOR)

    # DIVIDER
    fig.lines.append(
        plt.Line2D(
            [left_x, right_x],
            [divider_y, divider_y],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            linewidth=1.3,
            alpha=0.75
        )
    )

# ============================================================
# RENDER
# ============================================================

for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    fig.subplots_adjust(
        left=FIG_LEFT_MARGIN,
        right=1 - FIG_RIGHT_MARGIN,
        bottom=FIG_BOTTOM_MARGIN,
        top=1 - FIG_TOP_MARGIN
    )

    if ratings:
        plot_dotted_fill(ax, ratings, cfg["color"])
        style_axes(ax)
        draw_header(fig, ax, time_class, ratings, cfg["color"])
    else:
        ax.text(0.5, 0.5, "NO DATA", ha="center", va="center", fontsize=14)
        ax.axis("off")

    plt.savefig(f"{OUTPUT_DIR}/rating-{time_class}.svg", format="svg")
    plt.close()
