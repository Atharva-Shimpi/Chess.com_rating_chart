import requests
import os
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# -------------------- FILE SYSTEM --------------------
os.makedirs("assets/svg", exist_ok=True)

# -------------------- MATPLOTLIB GLOBAL STYLE --------------------
BG_COLOR = "#F6F4EF"      # Ivory
TEXT_COLOR = "#2A2529"    # Charcoal

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

# -------------------- CONFIG --------------------
HEADERS = {
    "User-Agent": "ChessRatingRefresh/1.0"
}

USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

TIME_CLASSES = {
    "blitz":  {"color": "#3E2F2A"},  # Umber
    "rapid":  {"color": "#3A5F3A"},  # Moss Green
    "bullet": {"color": "#1F2A44"},  # Midnight Blue
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# -------------------- VISUAL CONSTANTS --------------------
DOT_SIZE = 18
DOT_DIAMETER = 6          # ← hard-coded, independent of DOT_SIZE
FLOAT_PADDING_RATIO = 0.15
MAX_Y_TICKS = 6

X_LEFT_PADDING = -2
X_RIGHT_PADDING = 1

# -------------------- DATA FETCH --------------------
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
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings[::-1]  # OLDEST → NEWEST

# -------------------- DOTTED FILL --------------------
def plot_dotted_fill(ax, ratings, color):
    x_vals = list(range(len(ratings)))

    min_rating = min(ratings)
    max_rating = max(ratings)
    span = max_rating - min_rating

    # Floating base (true graph floor)
    floating_base = min_rating - span * FLOAT_PADDING_RATIO

    # Dot grid resolution
    dot_step = max(DOT_DIAMETER, int(span / 22))

    # Draw dots
    for x, r in zip(x_vals, ratings):
        y_vals = np.arange(
            floating_base,
            r + 0.01,
            dot_step
        )
        ax.scatter(
            [x] * len(y_vals),
            y_vals,
            s=DOT_SIZE,
            color=color,
            alpha=0.95,
            linewidths=0
        )

    # Axis limits
    ax.set_ylim(
        floating_base,
        max_rating + span * FLOAT_PADDING_RATIO
    )
    ax.set_xlim(X_LEFT_PADDING, len(ratings) + X_RIGHT_PADDING)

    # ---- Y ticks (KEY FIX) ----
    first_tick = floating_base + DOT_DIAMETER
    y_max = max_rating + span * FLOAT_PADDING_RATIO

    y_ticks = np.linspace(
        first_tick,
        y_max,
        MAX_Y_TICKS
    )

    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{int(t)}" for t in y_ticks])

# -------------------- AXIS STYLE --------------------
def style_axes(ax):
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["bottom"].set_linewidth(1.2)
    ax.spines["bottom"].set_alpha(0.4)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=4, width=1, pad=6)

    ax.grid(False)

# -------------------- RENDER --------------------
for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class)

    fig, ax = plt.subplots(figsize=(11, 4.2))

    if not ratings:
        ax.text(0.5, 0.5, "No data available",
                ha="center", va="center", fontsize=14)
        ax.axis("off")
    else:
        plot_dotted_fill(ax, ratings, cfg["color"])
        style_axes(ax)

        ax.text(
            0.0, 1.06,
            f"{time_class.upper()} · LAST {len(ratings)} GAMES",
            transform=ax.transAxes,
            fontsize=13,
            fontweight="medium",
            ha="left",
            va="bottom"
        )

    plt.tight_layout(pad=2)
    plt.savefig(
        f"assets/svg/rating-{time_class}.svg",
        format="svg",
        bbox_inches="tight"
    )
    plt.close()
