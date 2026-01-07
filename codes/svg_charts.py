import requests
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ------------------ GLOBAL STYLE ------------------
IVORY = "#F6F4EF"
CHARCOAL = "#2A2529"

COLORS = {
    "blitz": "#5C3A2E",        # Umber
    "rapid": "#3E5F45",       # Moss Green
    "bullet": "#1F2A44",      # Midnight Blue
}

matplotlib.rcParams.update({
    "figure.facecolor": IVORY,
    "axes.facecolor": IVORY,
    "axes.edgecolor": CHARCOAL,
    "axes.labelcolor": CHARCOAL,
    "xtick.color": CHARCOAL,
    "ytick.color": CHARCOAL,
    "text.color": CHARCOAL,
    "font.weight": "bold",
    "font.size": 11,
    "svg.fonttype": "path",
})

# ------------------ CONFIG ------------------
USERNAME = "Atharva-Shimpi"
RULES = "chess"
NGAMES = {
    "blitz": 100,
    "rapid": 60,
    "bullet": 50,
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# ------------------ DATA FETCH ------------------
def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
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
        ][::-1]

        games.extend(filtered)
        if len(games) >= limit:
            break

    ratings = []
    for g in games[:limit]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings[::-1]  # OLDEST → NEWEST

# ------------------ DOT FILL CHART ------------------
def plot_dotted_fill(ax, ratings, color):
    x_vals = np.arange(len(ratings))
    y_min = min(ratings)
    y_max = max(ratings)

    baseline = y_min - 20  # NEGATIVE SPACE ABOVE X-AXIS
    dot_step = 10

    for x, rating in zip(x_vals, ratings):
        y_dots = np.arange(baseline, rating, dot_step)
        ax.scatter(
            np.full_like(y_dots, x),
            y_dots,
            s=10,
            color=color,
            alpha=0.9
        )

    # Limits with breathing room
    ax.set_xlim(-3, len(ratings) + 3)
    ax.set_ylim(baseline - 15, y_max + 40)

# ------------------ AXIS STYLE ------------------
def style_axes(ax, title, games):
    # X AXIS
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.spines["bottom"].set_color(CHARCOAL)

    # REMOVE OTHER BORDERS
    for side in ["top", "left", "right"]:
        ax.spines[side].set_visible(False)

    # Y TICKS (REDUCED)
    ax.yaxis.set_ticks(np.linspace(*ax.get_ylim(), 5))
    ax.tick_params(axis="y", length=0)

    # X TICKS
    ax.set_xticks([0, games // 2, games])
    ax.set_xticklabels(
        ["START", "MID", "RECENT"],
        fontsize=10,
        fontweight="bold"
    )

    # TITLE
    ax.text(
        0.01,
        0.96,
        title.upper(),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold"
    )

    # FOOTER
    ax.text(
        0.5,
        -0.18,
        f"LAST {games} GAMES",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold"
    )

# ------------------ MAIN ------------------
for mode, limit in NGAMES.items():
    ratings = get_ratings(mode, limit)
    if not ratings:
        continue

    fig = plt.figure(figsize=(12, 4.2))
    ax = fig.add_axes([0.08, 0.25, 0.84, 0.6])  # NEGATIVE SPACE MAGIC

    plot_dotted_fill(ax, ratings, COLORS[mode])
    style_axes(ax, mode, limit)

    plt.savefig(
        f"assets/svg/rating-{mode}.svg",
        format="svg",
        bbox_inches="tight"
    )
    plt.close()
