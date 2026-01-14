import os
import requests
import numpy as np

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
TEXT_COLOR = "#2A2529"    # Charcoal text / axis color

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
    "blitz":  {"color": "#3E2F2A"},  # Umber
    "rapid":  {"color": "#3A5F3A"},  # Moss Green
    "bullet": {"color": "#1F2A44"},  # Midnight Blue
}

# ============================================================
# DATA → AXIS GEOMETRY (DO NOT TIE TO MARGINS)
# ============================================================

# Horizontal distance between y-axis and first dot column
X_AXIS_LEFT_PADDING = 2
X_AXIS_RIGHT_PADDING = 1

# Vertical floating behavior (graph ↔ x-axis)
FLOAT_GAP_RATIO = 0.16
TOP_PADDING_RATIO = 0.15

# Semantic dot size in RATING UNITS (not pixels)
DOT_DIAMETER_Y = 6

# ============================================================
# PHASE 5 — EDITORIAL LAYOUT MARGINS (SAFE TO TWEAK)
# ============================================================

# These affect FIGURE layout only.
# They do NOT affect dot spacing or axis geometry.

FIG_LEFT_MARGIN   = 0.09   # recommended: 0.06 → 0.10
FIG_RIGHT_MARGIN  = 0.05   # recommended: 0.06 → 0.10

FIG_BOTTOM_MARGIN = 0.10   # recommended: 0.10 → 0.14
FIG_TOP_MARGIN    = 0.30   # recommended: 0.26 → 0.34

# ============================================================
# DATA FETCHING
# ============================================================

def get_archives():
    """Return player archive URLs (newest → oldest)."""
    r = requests.get(ARCHIVES_URL.format(user=USERNAME), headers=HEADERS)
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]


def get_ratings(time_class):
    """Fetch last NGAMES ratings for a given time control."""
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

    return ratings[::-1]  # oldest → newest


# ============================================================
# DOTTED GRAPH RENDERING
# ============================================================

def plot_dotted_fill(ax, ratings, color):
    """
    Draw a vertically-filled dotted graph with perceptual baseline alignment.
    """

    x_positions = list(range(len(ratings)))

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    dot_step = max(6, int(rating_range / 22))

    # Semantic floating base
    float_base = min_rating

    # Visual base (scatter dots are center-anchored)
    visual_dot_base = float_base - (DOT_DIAMETER_Y / 2)

    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    # Draw dots
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
    ax.set_xlim(
        -X_AXIS_LEFT_PADDING,
        len(ratings) + X_AXIS_RIGHT_PADDING
    )

    # Y-axis ticks aligned one dot-diameter above visual base
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

    ax.spines["bottom"].set_linewidth(1.2)
    ax.spines["bottom"].set_alpha(0.4)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=4, width=1, pad=6)

    ax.grid(False)


# ============================================================
# RENDER ALL CHARTS
# ============================================================

for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class)

    # Taller canvas to support header + editorial margins
    fig, ax = plt.subplots(figsize=(11, 4.8))

    # Phase-5 layout control (do NOT affect dot geometry)
    fig.subplots_adjust(
        left=FIG_LEFT_MARGIN,
        right=1 - FIG_RIGHT_MARGIN,
        bottom=FIG_BOTTOM_MARGIN,
        top=1 - FIG_TOP_MARGIN
    )

    if not ratings:
        ax.text(
            0.5, 0.5,
            "NO DATA AVAILABLE",
            ha="center",
            va="center",
            fontsize=14
        )
        ax.axis("off")
    else:
        plot_dotted_fill(ax, ratings, cfg["color"])
        style_axes(ax)

        ax.text(
            0.0, 1.04,
            f"{time_class.upper()} · LAST {len(ratings)} GAMES",
            transform=ax.transAxes,
            fontsize=13,
            ha="left",
            va="bottom"
        )

    plt.savefig(
        f"{OUTPUT_DIR}/rating-{time_class}.svg",
        format="svg"
    )
    plt.close()
