import requests
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import datetime
import hashlib

# ================= CONFIG =================

USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz":  {"games": 100, "color": "#4A3A2A", "label": "BLITZ · LAST 100 GAMES"},
    "rapid":  {"games": 60,  "color": "#3F5F3A", "label": "RAPID · LAST 60 GAMES"},
    "bullet": {"games": 50,  "color": "#1F2F45", "label": "BULLET · LAST 50 GAMES"},
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

    return ratings[::-1]  # oldest → newest


# ================= VISUAL =================

def dotted_fill(ax, ratings, color):
    baseline = min(ratings) - 40
    for x, rating in enumerate(ratings):
        y_stack = range(baseline, rating, 10)
        ax.scatter(
            [x] * len(y_stack),
            y_stack,
            s=14,
            color=color,
            linewidths=0,
            alpha=0.9,
        )


def style_axes(ax, title):
    ax.set_facecolor(IVORY)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color(TEXT)
    ax.spines["bottom"].set_linewidth(1.2)

    ax.tick_params(axis="x", colors=TEXT, labelsize=9, pad=10)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9, length=0, pad=8)

    ax.yaxis.set_major_locator(MaxNLocator(5))

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")

    ax.set_title(
        title,
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=TEXT,
        pad=18,
    )


# ================= MAIN =================

now = datetime.utcnow().isoformat()

for mode, cfg in TIME_CLASSES.items():
    ratings = get_ratings(mode, cfg["games"])
    if not ratings:
        continue

    # 🔒 Generate deterministic run hash (FOR GIT DIFF)
    hash_source = f"{now}-{ratings[-1]}-{mode}"
    run_hash = hashlib.sha1(hash_source.encode()).hexdigest()[:10]

    fig = plt.figure(figsize=(11, 4.8), facecolor=IVORY)
    ax = fig.add_axes([0.08, 0.26, 0.86, 0.60])

    dotted_fill(ax, ratings, cfg["color"])
    style_axes(ax, cfg["label"])

    ax.set_xlim(-2, len(ratings) + 1)
    ax.set_ylim(min(ratings) - 40, max(ratings) + 35)

    # Footer (visible, styled)
    fig.text(
        0.5,
        0.12,
        f"UPDATED · {now[:16].replace('T',' ')} UTC",
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color=TEXT,
        alpha=0.6,
    )

    output = f"assets/svg/rating-{mode}.svg"
    plt.savefig(output, format="svg", facecolor=IVORY)
    plt.close()

    # 🔒 Inject invisible metadata comment (GUARANTEED DIFF)
    with open(output, "r+", encoding="utf-8") as f:
        content = f.read()
        f.seek(0)
        f.write(f"<!-- run:{run_hash} -->\n" + content)
