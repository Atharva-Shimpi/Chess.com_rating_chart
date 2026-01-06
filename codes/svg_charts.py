#!/usr/bin/env python3
import os
import math
import numpy as np
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- REQUIRED FOR CHESS.COM API ----------
HEADERS = {
    "User-Agent": "ChessRatingSVG/1.0 (https://github.com/Wawa_wuwa)"
}

# ---------- CONFIG ----------
USERNAME = "Wawa_wuwa"
RULES = "chess"
NGAMES = 100

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

COLORS = {
    "blitz": "#5B3F32",     # Umber
    "rapid": "#4A6B3A",     # Moss Green
    "bullet": "#1F3350",    # Midnight Blue
    "text": "#2A2529",      # Charcoal
    "bg": "#F6F4ED"         # Ivory
}

TIME_CLASSES = ["blitz", "rapid", "bullet"]

# ---------- VISUAL TUNING ----------
FIG_W, FIG_H = 10.8, 3.2
N_ROWS = 22
DOT_SIZE = 28
LEFT_PAD, RIGHT_PAD = 0.08, 0.98
TOP_PAD, BOTTOM_PAD = 0.86, 0.16

matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# ---------- DATA ----------
def get_archives():
    r = requests.get(
        ARCHIVES_URL.format(user=USERNAME),
        headers=HEADERS,
        timeout=15
    )
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]


def get_ratings(time_class):
    ratings = []

    for archive in get_archives():
        r = requests.get(archive, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            continue

        games = r.json().get("games", [])

        filtered = [
            g for g in games
            if g.get("rules") == RULES and g.get("time_class") == time_class
        ][::-1]

        for g in filtered:
            side = (
                "white"
                if g["white"]["username"].lower() == USERNAME.lower()
                else "black"
            )
            ratings.append(int(g[side]["rating"]))

            if len(ratings) >= NGAMES:
                return ratings

    return ratings


# ---------- DRAW ----------
def draw_dotted_chart(ax, ratings, color, title, footer):
    if not ratings:
        ax.text(0.5, 0.5, "NO DATA AVAILABLE",
                ha="center", va="center",
                color=COLORS["text"],
                transform=ax.transAxes,
                fontsize=12, weight="600")
        ax.axis("off")
        return

    x = np.arange(len(ratings))
    rmin, rmax = min(ratings), max(ratings)
    yrange = max(1, rmax - rmin)
    ymin = max(0, rmin - yrange * 0.15)
    ymax = rmax + yrange * 0.15

    ygrid = np.linspace(ymin, ymax, N_ROWS)

    xs, ys = [], []
    for xi, r in zip(x, ratings):
        frac = (r - ymin) / (ymax - ymin)
        count = int(frac * (N_ROWS - 1))
        xs.extend([xi] * count)
        ys.extend(ygrid[:count])

    ax.scatter(xs, ys, s=DOT_SIZE, color=color, linewidths=0, zorder=3)

    # floating x-axis
    axis_y = ymin - yrange * 0.05
    ax.hlines(axis_y, -0.5, len(x) - 0.5, color="#9A9A9A", lw=1)

    ax.set_xlim(-0.5, len(x) - 0.5)
    ax.set_ylim(axis_y - yrange * 0.02, ymax)

    # ticks
    ax.set_yticks(np.linspace(ymin, ymax, 5))
    ax.set_yticklabels(
        [str(int(v)) for v in np.linspace(ymin, ymax, 5)],
        fontsize=9, weight="600", color=COLORS["text"]
    )

    xticks = np.linspace(0, len(x) - 1, 8, dtype=int)
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        [str(v) for v in xticks],
        fontsize=9, weight="600", color=COLORS["text"]
    )

    # cleanup
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=4, color=COLORS["text"])

    ax.text(0.01, 0.95, title.upper(),
            transform=ax.transAxes,
            fontsize=11, weight="700",
            color=COLORS["text"])

    ax.text(0.5, -0.22, footer.upper(),
            transform=ax.transAxes,
            ha="center",
            fontsize=9, weight="600",
            color=COLORS["text"])


# ---------- MAIN ----------
def generate():
    os.makedirs("assets/svg", exist_ok=True)

    for tc in TIME_CLASSES:
        ratings = get_ratings(tc)

        fig = plt.figure(figsize=(FIG_W, FIG_H))
        fig.patch.set_facecolor(COLORS["bg"])
        plt.subplots_adjust(
            left=LEFT_PAD, right=RIGHT_PAD,
            top=TOP_PAD, bottom=BOTTOM_PAD
        )

        ax = plt.gca()
        ax.set_facecolor(COLORS["bg"])

        draw_dotted_chart(
            ax,
            ratings,
            COLORS[tc],
            f"{tc.capitalize()} · Last {len(ratings)} Games",
            f"LAST {len(ratings)} GAMES"
        )

        plt.savefig(
            f"assets/svg/rating-{tc}.svg",
            format="svg",
            bbox_inches="tight",
            facecolor=COLORS["bg"]
        )
        plt.close()


if __name__ == "__main__":
    generate()
