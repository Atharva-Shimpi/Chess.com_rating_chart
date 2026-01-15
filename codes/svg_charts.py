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
# EDITORIAL LAYOUT MARGINS (PHASE 5)
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
    x_positions = range(len(ratings))

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
# PHASE 6 — HEADER BLOCK
# ============================================================

def draw_header(fig, ax, time_class, ratings, color):
    game_count = len(ratings)
    latest_elo = ratings[-1]

    ist = pytz.timezone("Asia/Kolkata")
    time_str = datetime.now(ist).strftime("%-I:%M %p IST")

    header_y = 1 - FIG_TOP_MARGIN + 0.115
    divider_y = 1 - FIG_TOP_MARGIN + 0.075

    header_left_x = ax.get_position().x0
    header_right_x = ax.get_position().x1

    # LEFT CLUSTER
    fig.text(
        header_left_x,
        header_y,
        f"{time_class.upper()}",
        ha="left",
        va="center",
        fontsize=13,
        color=color
    )
    fig.text(
        header_left_x + 0.045,
        header_y,
        "·",
        ha="left",
        va="center",
        fontsize=15,
        color=TEXT_COLOR
    )
    fig.text(
        header_left_x + 0.060,
        header_y,
        "CHESS.COM",
        ha="left",
        va="center",
        fontsize=13,
        color=TEXT_COLOR
    )

    # RIGHT CLUSTER (aligned pieces)
    cursor = header_right_x

    def draw_right(text, dx, col, fs=13):
        nonlocal cursor
        cursor -= dx
        fig.text(
            cursor,
            header_y,
            text,
            ha="right",
            va="center",
            fontsize=fs,
            color=col
        )

    draw_right(time_str, 0.0, color)
    draw_right(" IST", 0.065, TEXT_COLOR)
    draw_right("·", 0.090, TEXT_COLOR, fs=15)

    draw_right(f"{latest_elo}", 0.115, color)
    draw_right(" ELO", 0.155, TEXT_COLOR)
    draw_right("·", 0.180, TEXT_COLOR, fs=15)

    draw_right(f"{game_count}", 0.205, color)
    draw_right(" GAMES", 0.255, TEXT_COLOR)

    # DIVIDER
    fig.lines.append(
        plt.Line2D(
            [header_left_x, header_right_x],
            [divider_y, divider_y],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            linewidth=1.3,
            alpha=0.65
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
