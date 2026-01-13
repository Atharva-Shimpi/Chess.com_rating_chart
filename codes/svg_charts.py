import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# =========================
# USER CONFIG
# =========================
USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz":  {"games": 100, "color": "#5B4636"},  # Umber
    "rapid":  {"games": 66,  "color": "#4F6B4F"},  # Moss Green
    "bullet": {"games": 53,  "color": "#2E3A4F"},  # Midnight Blue
}

# =========================
# DESIGN CONSTANTS (EDIT SAFELY)
# =========================
DOT_SIZE = 8                  # scatter size (visual only)
DOT_STEP = 8                  # vertical spacing between dot rows (rating units)
DOT_DIAMETER_Y = 8            # ❗ hard-coded semantic dot height (rating units)

FLOAT_GAP_RATIO = 0.10        # how much empty space below dots
TOP_PADDING_RATIO = 0.12      # headroom above highest dot

Y_TICKS_COUNT = 6
X_TICKS_COUNT = 6

BG_COLOR = "#F7F4EE"          # Ivory
TEXT_COLOR = "#2A2529"        # Charcoal

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
        data = requests.get(archive).json().get("games", [])

        filtered = [
            g for g in data
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ][::-1]

        games.extend(filtered)
        if len(games) >= ngames:
            break

    ratings = []
    for g in games[:ngames]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings


# =========================
# PLOTTING
# =========================
def plot_dotted_chart(ratings, title, color, ngames):
    ratings = ratings[:ngames]
    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # -------------------------
    # FLOATING BASE LOGIC
    # -------------------------
    float_base = min_rating                      # mathematical first dot center
    visual_dot_base = float_base - DOT_DIAMETER_Y / 2

    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    # -------------------------
    # BUILD DOTS
    # -------------------------
    xs, ys = [], []
    for i, r in enumerate(ratings, start=1):
        for y in range(int(float_base), int(r) + DOT_STEP, DOT_STEP):
            xs.append(i)
            ys.append(y)

    # -------------------------
    # FIGURE
    # -------------------------
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    ax.scatter(xs, ys, s=DOT_SIZE, color=color, linewidths=0)

    # -------------------------
    # AXIS LIMITS
    # -------------------------
    ax.set_xlim(0, ngames + 1)
    ax.set_ylim(axis_floor, axis_ceiling)

    # -------------------------
    # X TICKS
    # -------------------------
    ax.set_xticks(np.linspace(1, ngames, X_TICKS_COUNT).astype(int))
    ax.tick_params(axis="x", colors=TEXT_COLOR, labelsize=8)

    # -------------------------
    # Y TICKS (CRITICAL FIX)
    # -------------------------
    yticks = np.linspace(
        visual_dot_base + DOT_DIAMETER_Y,  # ✅ one dot ABOVE dot base
        axis_ceiling,
        Y_TICKS_COUNT
    )
    ax.set_yticks(yticks.astype(int))
    ax.tick_params(axis="y", colors=TEXT_COLOR, labelsize=8, length=0)

    # -------------------------
    # CLEAN LOOK
    # -------------------------
    ax.grid(False)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color("#9A9A9A")
    ax.spines["bottom"].set_linewidth(1)

    # -------------------------
    # TITLE
    # -------------------------
    ax.text(
        0.01, 0.96,
        title.upper(),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=TEXT_COLOR
    )

    plt.tight_layout()
    plt.savefig(f"rating-{title.split()[0].lower()}.svg")
    plt.close()


# =========================
# RUN
# =========================
for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class, cfg["games"])
    if ratings:
        plot_dotted_chart(
            ratings,
            f"{time_class} · last {cfg['games']} games",
            cfg["color"],
            cfg["games"]
        )


# axis_floor        → invisible padding below everything
# visual_dot_base   → where dots visually touch
# float_base        → first dot row center
# first_y_tick      → one dot diameter ABOVE visual_dot_base
