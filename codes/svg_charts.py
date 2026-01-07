import requests
import math
from datetime import datetime

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

# ---------------- CONFIG ---------------- #

USERNAME = "Atharva-Shimpi"
RULES = "chess"

TIME_CLASSES = {
    "blitz": {
        "games": 100,
        "color": "#5B4636",      # Umber
        "label": "BLITZ"
    },
    "rapid": {
        "games": 60,
        "color": "#4E6B4A",      # Moss Green
        "label": "RAPID"
    },
    "bullet": {
        "games": 50,
        "color": "#1F2A44",      # Midnight Blue
        "label": "BULLET"
    }
}

BG_COLOR = "#F6F4EF"           # Ivory
TEXT_COLOR = "#2A2529"         # Charcoal

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# SVG rendering discipline
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# ---------------- DATA ---------------- #

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]

def get_ratings(time_class, n_games):
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
        if len(games) >= n_games:
            break

    ratings = []
    for g in games[:n_games]:
        side = (
            "white"
            if g["white"]["username"].lower() == USERNAME.lower()
            else "black"
        )
        ratings.append(g[side]["rating"])

    return ratings[::-1]  # oldest → newest (correct direction)

# ---------------- PLOT ---------------- #

def draw_chart(time_class, cfg):
    ratings = get_ratings(time_class, cfg["games"])
    if not ratings:
        return

    ratings = np.array(ratings)
    x = np.arange(len(ratings))

    # Dynamic bounds
    y_min = ratings.min()
    y_max = ratings.max()

    # Padding so graph floats (Type B)
    y_range = y_max - y_min
    y_min_plot = max(0, y_min - y_range * 0.15)
    y_max_plot = y_max + y_range * 0.12

    # SVG canvas (taller, not squashed)
    fig = plt.figure(figsize=(12, 5.2), facecolor=BG_COLOR)
    ax = fig.add_axes([0.07, 0.14, 0.86, 0.58])
    ax.set_facecolor(BG_COLOR)

    # -------- DOTTED FILL (Type A) -------- #
    dot_y_step = max(6, int(y_range / 45))

    xs, ys = [], []
    for i, r in enumerate(ratings):
        for y in range(0, int(r) + 1, dot_y_step):
            xs.append(i)
            ys.append(y)

    ax.scatter(
        xs,
        ys,
        s=10,
        color=cfg["color"],
        alpha=0.9,
        linewidths=0
    )

    # -------- AXES (Type B) -------- #
    ax.set_xlim(-3, len(ratings) + 2)
    ax.set_ylim(y_min_plot, y_max_plot)

    yticks = np.linspace(y_min_plot, y_max_plot, 6)
    ax.set_yticks(yticks.astype(int))
    ax.tick_params(axis="y", length=0, labelsize=9, colors=TEXT_COLOR)

    ax.tick_params(axis="x", labelsize=9, colors=TEXT_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_COLOR)
    ax.spines["bottom"].set_alpha(0.3)

    # -------- HEADER -------- #
    now = datetime.now().strftime("%I:%M %p IST")
    elo_now = ratings[-1]

    fig.text(
        0.07, 0.88,
        f"{cfg['label']} – CHESS.COM",
        fontsize=11,
        color=TEXT_COLOR,
        alpha=0.9
    )

    fig.text(
        0.93, 0.88,
        f"{cfg['games']} GAMES     {elo_now} ELO     {now}",
        fontsize=11,
        color=TEXT_COLOR,
        ha="right"
    )

    # Divider line
    fig.lines.append(
        plt.Line2D(
            [0.07, 0.93],
            [0.83, 0.83],
            transform=fig.transFigure,
            color=TEXT_COLOR,
            alpha=0.18,
            linewidth=1
        )
    )

    # -------- ROUNDED BORDER -------- #
    bbox = FancyBboxPatch(
        (0, 0),
        1,
        1,
        boxstyle="round,pad=0.012,rounding_size=0.03",
        transform=fig.transFigure,
        linewidth=0,
        facecolor=BG_COLOR,
        zorder=-1
    )
    fig.patches.append(bbox)

    # -------- SAVE -------- #
    plt.savefig(
        f"assets/svg/rating-{time_class}.svg",
        format="svg",
        bbox_inches="tight"
    )
    plt.close()

# ---------------- RUN ---------------- #

for tc, cfg in TIME_CLASSES.items():
    draw_chart(tc, cfg)
