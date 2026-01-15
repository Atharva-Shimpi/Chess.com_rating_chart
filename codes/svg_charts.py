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

BG_COLOR = "#F6F4EF"
TEXT_COLOR = "#2A2529"

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
# PHASE 5 — EDITORIAL LAYOUT MARGINS
# ============================================================

FIG_LEFT_MARGIN   = 0.075
FIG_RIGHT_MARGIN  = 0.045

FIG_BOTTOM_MARGIN = 0.10
FIG_TOP_MARGIN    = 0.30

# ============================================================
# PHASE 6 — HEADER LAYOUT CONSTANTS
# ============================================================

HEADER_Y_OFFSET  = 0.11
DIVIDER_Y_OFFSET = 0.075

TOKEN_GAP = 0.018
DOT_FONT_SIZE = 14
TEXT_FONT_SIZE = 13

# ============================================================
# DATA FETCHING
# ============================================================

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME), headers=HEADERS)
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]


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
    x_positions = list(range(len(ratings)))

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    dot_step = max(6, int(rating_range / 22))

    float_base = min_rating
    visual_dot_base = float_base - (DOT_DIAMETER_Y / 2)

    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    for x, rating in zip(x_positions, ratings):
        y_values = range(float_base, rating + dot_step, dot_step)
        ax.scatter(
            [x] * len(y_values),
            y_values,
            s=18,
            color=color,
            alpha=0.95,
            linewidths=0
        )

    ax.set_ylim(axis_floor, axis_ceiling)
    ax.set_xlim(-X_AXIS_LEFT_PADDING, len(ratings) + X_AXIS_RIGHT_PADDING)

    yticks = np.linspace(
        visual_dot_base + DOT_DIAMETER_Y,
        axis_ceiling,
        6
    )
    ax.set_yticks([int(round(y)) for y in yticks])


def style_axes(ax):
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["bottom"].set_linewidth(1.2)
    ax.spines["bottom"].set_alpha(0.4)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=4, width=1, pad=6)

    ax.grid(False)

# ============================================================
# PHASE 6 — HEADER (FIXED)
# ============================================================

def draw_header(fig, ax, time_class, ratings, color):
    game_count = len(ratings)
    latest_elo = ratings[-1]

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    time_str = now.strftime("%-I:%M %p IST")

    # Align header to y-axis labels
    y_label_x = ax.get_position().x0

    y_text = 1 - FIG_TOP_MARGIN + HEADER_Y_OFFSET
    y_div  = 1 - FIG_TOP_MARGIN + DIVIDER_Y_OFFSET

    # LEFT CLUSTER
    fig.text(
        y_label_x,
        y_text,
        f"{time_class.upper()}",
        ha="left",
        va="center",
        fontsize=TEXT_FONT_SIZE,
        color=color
    )

    fig.text(
        y_label_x + TOKEN_GAP,
        y_text,
        "·",
        ha="left",
        va="center",
        fontsize=DOT_FONT_SIZE,
        color=TEXT_COLOR
    )

    fig.text(
        y_label_x + TOKEN_GAP * 2,
        y_text,
        "CHESS.COM",
        ha="left",
        va="center",
        fontsize=TEXT_FONT_SIZE,
        color=TEXT_COLOR
    )

    # RIGHT CLUSTER
    x_right = 1 - FIG_RIGHT_MARGIN

    fig.text(
        x_right,
        y_text,
        time_str,
        ha="right",
        va="center",
        fontsize=TEXT_FONT_SIZE,
        color=TEXT_COLOR
    )

    fig.text(
        x_right - TOKEN_GAP,
        y_text,
        "·",
        ha="right",
        va="center",
        fontsize=DOT_FONT_SIZE,
        color=TEXT_COLOR
    )

    fig.text(
        x_right - TOKEN_GAP * 2,
        y_text,
        f"{latest_elo} ELO",
        ha="right",
        va="center",
        fontsize=TEXT_FONT_SIZE,
        color=color
    )

    fig.text(
        x_right - TOKEN_GAP * 3,
        y_text,
        "·",
        ha="right",
        va="center",
        fontsize=DOT_FONT_SIZE,
        color=TEXT_COLOR
    )

    fig.text(
        x_right - TOKEN_GAP * 4,
        y_text,
        f"{game_count} GAMES",
        ha="right",
        va="center",
        fontsize=TEXT_FONT_SIZE,
        color=color
    )

    # DIVIDER
    fig.lines.append(
        plt.Line2D(
            [y_label_x, 1 - FIG_RIGHT_MARGIN],
            [y_div, y_div],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            linewidth=1.2,
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
        ax.text(0.5, 0.5, "NO DATA AVAILABLE", ha="center", va="center")
        ax.axis("off")

    plt.savefig(f"{OUTPUT_DIR}/rating-{time_class}.svg", format="svg")
    plt.close()
