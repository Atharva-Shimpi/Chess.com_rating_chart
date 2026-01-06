import requests
import math
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# -------------------- CONFIG --------------------

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

# -------------------- DATA --------------------

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

    # oldest → newest (correct direction)
    return ratings[::-1]

# -------------------- PLOT --------------------

def dotted_fill_plot(ax, ratings, color):
    x = list(range(len(ratings)))

    # baseline slightly ABOVE x-axis (negative spacing illusion)
    baseline = min(ratings) - 20

    for i, r in enumerate(ratings):
        y_values = list(range(baseline, r, 10))
        x_values = [i] * len(y_values)
        ax.scatter(
            x_values,
            y_values,
            s=14,
            color=color,
            alpha=0.9,
            linewidths=0
        )

def style_axes(ax, label):
    ax.set_facecolor(IVORY)

    # Remove box
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    # X-axis only
    ax.spines["bottom"].set_color(TEXT)
    ax.spines["bottom"].set_linewidth(1.2)

    # Ticks
    ax.tick_params(axis="x", colors=TEXT, labelsize=9, pad=10)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9, length=0, pad=8)

    # Reduce Y ticks
    ax.yaxis.set_major_locator(MaxNLocator(5))

    # Labels styling
    for t in ax.get_yticklabels():
        t.set_fontweight("bold")
        t.set_fontfamily("DejaVu Sans")

    for t in ax.get_xticklabels():
        t.set_fontweight("bold")
        t.set_fontfamily("DejaVu Sans")

    ax.set_title(
        label,
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=TEXT,
        pad=18
    )

# -------------------- MAIN --------------------

for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class, cfg["games"])
    if not ratings:
        continue

    fig = plt.figure(figsize=(11, 4.6)
