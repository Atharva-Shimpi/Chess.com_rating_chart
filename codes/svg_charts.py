import requests
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------- CONFIG ----------------

USERNAME = "Wawa_wuwa"
NGAMES_MAP = {
    "blitz": 100,
    "rapid": 60,
    "bullet": 50,
}

COLORS = {
    "blitz": "#4A3B2F",     # Umber
    "rapid": "#4F6F52",     # Moss Green
    "bullet": "#1F2A44",    # Midnight Blue
}

BG_COLOR = "#F6F3ED"       # Ivory
TEXT_COLOR = "#2A2529"     # Charcoal

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

OUTPUT_DIR = "assets/svg"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- DATA FETCH ----------------

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

        for g in r.json().get("games", []):
            if g.get("time_class") != time_class:
                continue

            side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
            rating = g.get(side, {}).get("rating")

            if rating:
                games.append(rating)

            if len(games) >= limit:
                break

        if len(games) >= limit:
            break

    return games[::-1]  # oldest → newest


# ---------------- PLOTTING ----------------

def plot_dotted_fill(ax, ratings, color):
    x = np.arange(len(ratings))
    min_y = min(ratings)
    max_y = max(ratings)

    baseline = min_y - (max_y - min_y) * 0.15
    step = (max_y - baseline) / 22

    for i, r in enumerate(ratings):
        ys = np.arange(baseline, r, step)
        xs = np.full_like(ys, i)
        ax.scatter(xs, ys, s=6, color=color, alpha=0.9)


def style_axes(ax, ratings):
    ymin = min(ratings)
    ymax = max(ratings)

    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(-2, len(ratings) + 2)
    ax.set_ylim(ymin - (ymax - ymin) * 0.2, ymax * 1.05)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.tick_params(axis="x", colors=TEXT_COLOR, labelsize=8)
    ax.tick_params(axis="y", colors=TEXT_COLOR, labelsize=8)

    ticks = np.linspace(ymin, ymax, 5)
    ax.set_yticks(np.round(ticks, -1))


def draw_header(fig, ax, mode, games, elo):
    now = datetime.now().strftime("%-I:%M %p IST").upper()

    fig.text(0.06, 0.93, f"{mode.upper()} – CHESS.COM",
             fontsize=10, color=TEXT_COLOR, alpha=0.85)

    fig.text(0.94, 0.93,
             f"{games} GAMES     {elo} ELO     {now}",
             fontsize=9, color=TEXT_COLOR,
             ha="right")

    fig.lines.append(
        plt.Line2D([0.05, 0.95], [0.89, 0.89],
                   lw=0.6, color=TEXT_COLOR, alpha=0.25,
                   transform=fig.transFigure)
    )


# ---------------- MAIN ----------------

for mode, ngames in NGAMES_MAP.items():
    ratings = get_ratings(mode, ngames)

    if len(ratings) < 2:
        print(f"[WARN] No data for {mode}")
        continue

    fig = plt.figure(figsize=(11, 4.8))
    fig.patch.set_facecolor(BG_COLOR)

    ax = fig.add_axes([0.06, 0.14, 0.88, 0.70])

    plot_dotted_fill(ax, ratings, COLORS[mode])
    style_axes(ax, ratings)
    draw_header(fig, ax, mode, len(ratings), ratings[-1])

    plt.savefig(
        f"{OUTPUT_DIR}/rating-{mode}.svg",
        format="svg",
        bbox_inches="tight",
        facecolor=BG_COLOR
    )
    plt.close()
