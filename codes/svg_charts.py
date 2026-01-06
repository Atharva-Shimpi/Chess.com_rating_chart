import requests
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# =========================
# CONFIG
# =========================

USERNAME = "Atharva-Shimpi"
RULES = "chess"
NGAMES = {
    "blitz": 100,
    "rapid": 60,
    "bullet": 50
}

# Color system (locked)
COLORS = {
    "background": "#F7F4EC",   # Ivory
    "text": "#2A2529",         # Charcoal
    "blitz": "#4A3B2A",        # Umber
    "rapid": "#4F6F52",        # Moss Green
    "bullet": "#24344D"        # Midnight Blue
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# =========================
# DATA
# =========================

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
        if len(games) >= NGAMES[time_class]:
            break

    ratings = []
    for g in games[:NGAMES[time_class]]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings


# =========================
# DRAWING
# =========================

def draw_dotted_column_chart(ax, ratings, color):
    baseline = min(ratings) - 25  # negative space above x-axis
    step = 12                     # vertical dot spacing

    for x, rating in enumerate(ratings):
        dots = int((rating - baseline) / step)
        for i in range(dots):
            ax.scatter(
                x,
                baseline + i * step,
                s=14,
                color=color,
                linewidths=0,
                alpha=0.95
            )


def style_axes(ax, title):
    ax.set_facecolor(COLORS["background"])

    # Only bottom axis visible
    for side in ["top", "left", "right"]:
        ax.spines[side].set_visible(False)

    ax.spines["bottom"].set_color(COLORS["text"])
    ax.spines["bottom"].set_linewidth(1.1)

    # Y-axis minimal
    ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.tick_params(axis="y", colors=COLORS["text"], labelsize=9, length=0)

    # X-axis spacing + ticks
    ax.tick_params(axis="x", colors=COLORS["text"], labelsize=9, pad=12)

    # Title
    ax.set_title(
        title.upper(),
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=COLORS["text"],
        pad=16
    )

    # Footer label
    ax.set_xlabel(
        "GAMES (MOST RECENT →)",
        fontsize=9,
        fontweight="bold",
        color=COLORS["text"],
        labelpad=18
    )


# =========================
# MAIN
# =========================

for mode in ["blitz", "rapid", "bullet"]:
    ratings = get_ratings(mode)
    if not ratings:
        continue

    fig, ax = plt.subplots(figsize=(10.8, 4.4))
    fig.patch.set_facecolor(COLORS["background"])

    draw_dotted_column_chart(ax, ratings, COLORS[mode])
    style_axes(ax, f"{mode} · last {len(ratings)} games")

    # Negative spacing (floating look)
    ax.set_xlim(-3, len(ratings) + 2)
    ax.set_ylim(min(ratings) - 40, max(ratings) + 40)

    plt.subplots_adjust(
        left=0.06,
        right=0.985,
        top=0.82,
        bottom=0.24
    )

    plt.savefig(
        f"assets/svg/rating-{mode}.svg",
        format="svg",
        bbox_inches="tight"
    )
    plt.close()
