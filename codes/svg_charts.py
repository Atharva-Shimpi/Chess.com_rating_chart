import requests
import datetime
import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

# =========================
# CONFIGURATION
# =========================

USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz": {
        "games": 100,
        "color": "#5B4636",   # Umber
    },
    "rapid": {
        "games": 60,
        "color": "#3F5D45",   # Moss Green
    },
    "bullet": {
        "games": 50,
        "color": "#24364B",   # Midnight Blue
    },
}

BG_COLOR = "#F6F4EF"        # Ivory
TEXT_COLOR = "#2A2529"      # Charcoal
DIVIDER_ALPHA = 0.18

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"


# =========================
# DATA FETCHING
# =========================

def get_archives():
    resp = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if resp.status_code != 200:
        return []
    return resp.json().get("archives", [])[::-1]


def get_ratings(time_class, ngames):
    games = []

    for archive in get_archives():
        r = requests.get(archive)
        if r.status_code != 200:
            continue

        data = r.json().get("games", [])
        filtered = [
            g for g in data
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ]

        games.extend(filtered)

        if len(games) >= ngames:
            break

    games = games[:ngames]

    ratings = []
    for g in games:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings


# =========================
# DRAWING UTILITIES
# =========================

def draw_rounded_container(fig):
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.axis("off")

    rect = FancyBboxPatch(
        (0, 0),
        1,
        1,
        boxstyle="round,pad=0.015,rounding_size=0.03",
        transform=ax_bg.transAxes,
        facecolor=BG_COLOR,
        linewidth=0,
        zorder=-1,
    )

    ax_bg.add_patch(rect)


def draw_header(fig, title, games, elo):
    ax = fig.add_axes([0.06, 0.80, 0.88, 0.16])
    ax.axis("off")

    now = datetime.datetime.now().strftime("%I:%M %p IST").upper()

    # Left text
    ax.text(
        0.0,
        0.65,
        f"{title.upper()} – ",
        fontsize=11,
        color=TEXT_COLOR,
        ha="left",
        va="center",
        transform=ax.transAxes,
    )

    ax.text(
        0.11,
        0.65,
        "CHESS.COM",
        fontsize=11,
        color=TEXT_COLOR,
        alpha=0.5,
        ha="left",
        va="center",
        transform=ax.transAxes,
    )

    # Right text
    right_text = f"{games} GAMES     {elo} ELO     {now}"
    ax.text(
        1.0,
        0.65,
        right_text,
        fontsize=11,
        color=TEXT_COLOR,
        ha="right",
        va="center",
        transform=ax.transAxes,
    )

    # Divider
    ax.plot(
        [0, 1],
        [0.15, 0.15],
        color=TEXT_COLOR,
        alpha=DIVIDER_ALPHA,
        linewidth=1,
        transform=ax.transAxes,
    )


def draw_dotted_fill(ax, ratings, color):
    x = np.arange(len(ratings))
    y_min = min(ratings)
    y_max = max(ratings)

    # Dynamic Y limits with breathing space
    y_padding = (y_max - y_min) * 0.15
    y_floor = y_min - y_padding
    y_ceil = y_max + y_padding

    ax.set_ylim(y_floor, y_ceil)

    # Dotted vertical fill
    dot_step = max((y_max - y_min) // 28, 8)

    for i, r in enumerate(ratings):
        ys = np.arange(y_floor, r, dot_step)
        xs = np.full_like(ys, i)
        ax.scatter(xs, ys, s=12, color=color, alpha=0.9)

    # Axis styling (Type B)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color(TEXT_COLOR)
    ax.spines["bottom"].set_alpha(0.4)

    ax.tick_params(axis="x", colors=TEXT_COLOR, labelsize=9)
    ax.tick_params(axis="y", colors=TEXT_COLOR, labelsize=9, length=0)

    # Y ticks: max 6
    yticks = np.linspace(y_min, y_max, 5)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{int(y)}" for y in yticks])

    ax.set_xlim(-2, len(ratings) + 1)


# =========================
# MAIN RENDER LOOP
# =========================

for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class, cfg["games"])
    if not ratings:
        continue

    fig = plt.figure(figsize=(12, 5), dpi=120)
    fig.patch.set_alpha(0)

    draw_rounded_container(fig)
    draw_header(
        fig,
        title=time_class,
        games=len(ratings),
        elo=ratings[-1],
    )

    ax = fig.add_axes([0.06, 0.12, 0.88, 0.60])
    draw_dotted_fill(ax, ratings, cfg["color"])

    plt.savefig(
        f"assets/svg/rating-{time_class}.svg",
        format="svg",
        bbox_inches="tight",
    )
    plt.close(fig)
