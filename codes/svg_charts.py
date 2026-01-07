import requests
import os
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    "User-Agent": "ChessRatingRefresh/1.0 atharvashimpi2005@gmail.com"
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

    return ratings[::-1]  # OLDEST → NEWEST (LEFT → RIGHT)

# -------------------- DOTTED FILL RENDER --------------------
def plot_dotted_fill(ax, ratings, color):
    x_positions = list(range(len(ratings)))

    min_rating = min(ratings)
    max_rating = max(ratings)

    # Floating effect (negative spacing intuition)
    y_floor = min_rating - (max_rating - min_rating) * 0.15
    y_ceil  = max_rating + (max_rating - min_rating) * 0.15

    dot_step = max(6, int((max_rating - min_rating) / 22))

    for x, rating in zip(x_positions, ratings):
        y_values = list(range(int(y_floor), int(rating), dot_step))
        ax.scatter(
            [x] * len(y_values),
            y_values,
            s=18,
            color=color,
            alpha=0.95,
            linewidths=0
        )

    ax.set_ylim(y_floor, y_ceil)
    ax.set_xlim(-2, len(ratings) + 1)

# -------------------- AXIS STYLE --------------------
def style_axes(ax):
    # Remove Y axis line
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Keep subtle X baseline
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
        ax.text(
            0.5, 0.5, "No data available",
            ha="center", va="center", fontsize=14
        )
        ax.axis("off")
    else:
        plot_dotted_fill(ax, ratings, cfg["color"])
        style_axes(ax)

        # Title (micro editorial style)
        ax.text(
            0.0, 1.06,
            f"{time_class.capitalize()} · Last {len(ratings)} games",
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
