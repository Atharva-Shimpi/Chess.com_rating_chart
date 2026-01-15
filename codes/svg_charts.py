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
# AXIS GEOMETRY
# ============================================================

X_AXIS_LEFT_PADDING = 2
X_AXIS_RIGHT_PADDING = 1

FLOAT_GAP_RATIO = 0.16
TOP_PADDING_RATIO = 0.15
DOT_DIAMETER_Y = 6

# ============================================================
# LAYOUT MARGINS
# ============================================================

FIG_LEFT_MARGIN   = 0.075
FIG_RIGHT_MARGIN  = 0.045
FIG_BOTTOM_MARGIN = 0.10
FIG_TOP_MARGIN    = 0.30

# ============================================================
# HEADER CONSTANTS
# ============================================================

HEADER_Y_OFFSET  = 0.135   # [0.09 – 0.15]
DIVIDER_Y_OFFSET = 0.075   # [0.05 – 0.09]

TEXT_FONT_SIZE = 13
DOT_FONT_SIZE  = 15

DOT_GAP = 0.030   # stable spacing around middle dots

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
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings[::-1]

# ============================================================
# PLOT
# ============================================================

def plot_dotted_fill(ax, ratings, color):
    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    dot_step = max(6, int(rating_range / 22))
    float_base = min_rating
    visual_dot_base = float_base - (DOT_DIAMETER_Y / 2)

    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    for x, rating in enumerate(ratings):
        y_vals = range(float_base, rating + dot_step, dot_step)
        ax.scatter([x]*len(y_vals), y_vals, s=18, color=color, alpha=0.95, linewidths=0)

    ax.set_ylim(axis_floor, axis_ceiling)
    ax.set_xlim(-X_AXIS_LEFT_PADDING, len(ratings) + X_AXIS_RIGHT_PADDING)

    yticks = np.linspace(visual_dot_base + DOT_DIAMETER_Y, axis_ceiling, 6)
    ax.set_yticks([int(round(y)) for y in yticks])

def style_axes(ax):
    for s in ["left", "top", "right", "bottom"]:
        ax.spines[s].set_visible(False)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=4, pad=6)
    ax.grid(False)

# ============================================================
# HEADER ENGINE
# ============================================================

def measure(fig, text, size):
    t = fig.text(0, 0, text, fontsize=size)
    fig.canvas.draw()
    w = t.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    t.remove()
    return w

def draw_header(fig, ax, time_class, ratings, color):
    game_count = len(ratings)
    latest_elo = ratings[-1]

    ist = pytz.timezone("Asia/Kolkata")
    time_str = datetime.now(ist).strftime("%-I:%M %p IST")

    x_left  = ax.get_position().x0
    x_right = 1 - FIG_RIGHT_MARGIN
    y_text  = 1 - FIG_TOP_MARGIN + HEADER_Y_OFFSET
    y_div   = 1 - FIG_TOP_MARGIN + DIVIDER_Y_OFFSET

    # LEFT CLUSTER
    cursor = x_left
    left_parts = [(time_class.upper(), color), ("CHESS.COM", TEXT_COLOR)]

    for i, (txt, col) in enumerate(left_parts):
        fig.text(cursor, y_text, txt, ha="left", va="center",
                 fontsize=TEXT_FONT_SIZE, color=col)
        cursor += measure(fig, txt, TEXT_FONT_SIZE)
        if i < len(left_parts) - 1:
            fig.text(cursor + DOT_GAP/2, y_text, "·", ha="center", va="center",
                     fontsize=DOT_FONT_SIZE, color=TEXT_COLOR)
            cursor += DOT_GAP

    # RIGHT CLUSTER
    right_parts = [
        (f"{game_count} GAMES", color),
        (f"{latest_elo} ELO", color),
        (time_str, TEXT_COLOR),
    ]

    total_width = sum(measure(fig, t, TEXT_FONT_SIZE) for t, _ in right_parts) + DOT_GAP * (len(right_parts) - 1)
    cursor = x_right - total_width

    for i, (txt, col) in enumerate(right_parts):
        fig.text(cursor, y_text, txt, ha="left", va="center",
                 fontsize=TEXT_FONT_SIZE, color=col)
        cursor += measure(fig, txt, TEXT_FONT_SIZE)
        if i < len(right_parts) - 1:
            fig.text(cursor + DOT_GAP/2, y_text, "·", ha="center", va="center",
                     fontsize=DOT_FONT_SIZE, color=TEXT_COLOR)
            cursor += DOT_GAP

    # DIVIDER
    fig.lines.append(
        plt.Line2D(
            [x_left, x_right],
            [y_div, y_div],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            linewidth=1.2,
            alpha=0.8
        )
    )

def draw_custom_x_axis(fig, ax):
    x_left  = ax.get_position().x0
    x_right = 1 - FIG_RIGHT_MARGIN
    y_axis  = ax.get_position().y0

    fig.lines.append(
        plt.Line2D(
            [x_left, x_right],
            [y_axis, y_axis],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            linewidth=1.0,
            alpha=0.45
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
        draw_custom_x_axis(fig, ax)
    else:
        ax.text(0.5, 0.5, "NO DATA AVAILABLE", ha="center", va="center")
        ax.axis("off")

    plt.savefig(f"{OUTPUT_DIR}/rating-{time_class}.svg", format="svg")
    plt.close()
