import requests
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ================= CONFIG =================

USERNAME = "Atharva-Shimpi"
RULES = "chess"

TIME_CLASSES = {
    "blitz": {
        "games": 100,
        "color": "#4A3A2A",   # Umber
        "label": "BLITZ · LAST 100 GAMES",
    },
    "rapid": {
        "games": 60,
        "color": "#3F5F3A",   # Moss Green
        "label": "RAPID · LAST 60 GAMES",
    },
    "bullet": {
        "games": 50,
        "color": "#1F2F45",   # Midnight Blue
        "label": "BULLET · LAST 50 GAMES",
    },
}

IVORY = "#F6F3EB"
TEXT = "#2A2529"

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# ================= DATA =================

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]


def get_ratings(time_class, limit):
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
        if len(games) >= limit:
            break

    ratings = []
    for g in games[:limit]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    # oldest → newest
    return ratings[::-1]


# ================= PLOT =================

def dotted_fill(ax, ratings, color):
    x_vals = range(len(ratings))

    baseline = min(ratings) - 25  # floating gap above x-axis

    for x, rating in zip(x_vals, ratings):
        y_stack = range(baseline, rating, 10)
        ax.scatter(
            [x] * len(y_stack),
            y_stack,
            s=14,
            color=color,
            alpha=0.9,
            linewidths=0
        )


def style_axes(ax, title):
    ax.set_facecolor(IVORY)

    # Remove all spines except bottom
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color(TEXT)
    ax.spines["bottom"].set_linewidth(1.2)

    # Ticks
    ax.tick_params(axis="x", colors=TEXT, labelsize=9, pad=10)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9, length=0, pad=8)

    ax.yaxis.set_major_locator(MaxNLocator(5))

    # Typography
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")
        label.set_fontfamily("DejaVu Sans")

    ax.set_title(
        title,
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=TEXT,
        pad=18
    )


# ================= MAIN =================

for mode, cfg in TIME_CLASSES.items():
    ratings = get_ratings(mode, cfg["games"])
    if not ratings:
        continue

    fig = plt.figure(figsize=(11, 4.6), facecolor=IVORY)

    # Negative spacing / floating chart
    ax = fig.add_axes([0.08, 0.22, 0.86, 0.62])

    dotted_fill(ax, ratings, cfg["color"])
    style_axes(ax, cfg["label"])

    ax.set_xlim(-2, len(ratings) + 1)
    ax.set_ylim(min(ratings) - 35, max(ratings) + 30)

    # Footer micro text
    fig.text(
        0.5,
        0.08,
        "CHESS.COM RATING HISTORY",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=TEXT
    )

    plt.savefig(
        f"assets/svg/rating-{mode}.svg",
        format="svg",
        facecolor=IVORY
    )
    plt.close()
