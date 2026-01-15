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
# GLOBAL THEME
# ============================================================

BG_COLOR = "#F6F4EF"
TEXT_COLOR = "#2A2529"

matplotlib.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "axes.edgecolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "svg.fonttype": "path",
})

# ============================================================
# CONFIG
# ============================================================

USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

TIME_CLASSES = {
    "blitz":  {"color": "#3E2F2A"},
    "rapid":  {"color": "#3A5F3A"},
    "bullet": {"color": "#1F2A44"},
}

# ============================================================
# LAYOUT
# ============================================================

FIG_LEFT_MARGIN   = 0.075
FIG_RIGHT_MARGIN  = 0.045
FIG_BOTTOM_MARGIN = 0.10
FIG_TOP_MARGIN    = 0.30

HEADER_TEXT_Y    = 1 - FIG_TOP_MARGIN + 0.135
HEADER_DIVIDER_Y = 1 - FIG_TOP_MARGIN + 0.085

# ============================================================
# DATA
# ============================================================

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]

def get_ratings(time_class):
    games = []
    for archive in get_archives():
        r = requests.get(archive)
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
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings[::-1]

# ============================================================
# PLOT
# ============================================================

def plot_dotted_fill(ax, ratings, color):
    min_r, max_r = min(ratings), max(ratings)
    step = max(6, int((max_r - min_r) / 22))

    for x, r in enumerate(ratings):
        ys = range(min_r, r + step, step)
        ax.scatter([x]*len(ys), ys, s=18, color=color, linewidths=0)

    ax.set_xlim(-2, len(ratings) + 1)
    ax.set_ylim(min_r - (max_r-min_r)*0.16, max_r + (max_r-min_r)*0.15)

def style_axes(ax):
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_alpha(0.4)
    ax.tick_params(axis="y", length=0)
    ax.grid(False)

# ============================================================
# HEADER (FIXED)
# ============================================================

def draw_header(fig, ax, mode, ratings, color):
    games = len(ratings)
    elo = ratings[-1]

    ist = pytz.timezone("Asia/Kolkata")
    time_str = datetime.now(ist).strftime("%-I:%M %p IST")

    left_x = ax.get_position().x0
    right_x = ax.get_position().x1

    # Left cluster
    fig.text(left_x, HEADER_TEXT_Y, mode.upper(), ha="left", va="center",
             fontsize=13, color=color)

    fig.text(left_x + 0.045, HEADER_TEXT_Y, "·", ha="left", va="center",
             fontsize=14, color=TEXT_COLOR)

    fig.text(left_x + 0.055, HEADER_TEXT_Y, "CHESS.COM", ha="left", va="center",
             fontsize=13, color=TEXT_COLOR)

    # Right cluster rhythm
    x = right_x
    gap = 0.075
    dot_gap = 0.018

    # TIME
    fig.text(x, HEADER_TEXT_Y, time_str, ha="right", va="center",
             fontsize=13, color=color)

    fig.text(x - dot_gap, HEADER_TEXT_Y, "·", ha="right", va="center",
             fontsize=14, color=TEXT_COLOR)

    # ELO
    fig.text(x - gap, HEADER_TEXT_Y, f"{elo}", ha="right", va="center",
             fontsize=13, color=color)

    fig.text(x - gap + 0.008, HEADER_TEXT_Y, " ELO", ha="left", va="center",
             fontsize=13, color=TEXT_COLOR)

    fig.text(x - gap - dot_gap, HEADER_TEXT_Y, "·", ha="right", va="center",
             fontsize=14, color=TEXT_COLOR)

    # GAMES
    fig.text(x - 2*gap, HEADER_TEXT_Y, f"{games}", ha="right", va="center",
             fontsize=13, color=color)

    fig.text(x - 2*gap + 0.008, HEADER_TEXT_Y, " GAMES", ha="left", va="center",
             fontsize=13, color=TEXT_COLOR)

    # Divider
    fig.lines.append(
        plt.Line2D(
            [left_x, right_x],
            [HEADER_DIVIDER_Y, HEADER_DIVIDER_Y],
            transform=fig.transFigure,
            linewidth=1.4,
            color=TEXT_COLOR,
            alpha=0.7
        )
    )

# ============================================================
# RENDER
# ============================================================

for mode, cfg in TIME_CLASSES.items():
    ratings = get_ratings(mode)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    fig.subplots_adjust(
        left=FIG_LEFT_MARGIN,
        right=1-FIG_RIGHT_MARGIN,
        bottom=FIG_BOTTOM_MARGIN,
        top=1-FIG_TOP_MARGIN
    )

    if ratings:
        plot_dotted_fill(ax, ratings, cfg["color"])
        style_axes(ax)
        draw_header(fig, ax, mode, ratings, cfg["color"])
    else:
        ax.text(0.5, 0.5, "NO DATA", ha="center", va="center")
        ax.axis("off")

    plt.savefig(f"{OUTPUT_DIR}/rating-{mode}.svg", format="svg")
    plt.close()
