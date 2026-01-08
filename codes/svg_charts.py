import requests

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

# --- SVG safety ---
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# --- CONFIG ---
USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz":  {"color": "#5A4632"},   # Umber
    "rapid":  {"color": "#4E6B4E"},   # Moss Green
    "bullet": {"color": "#24324A"},   # Midnight Blue
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"


# -------------------------------------------------
# DATA FETCHING
# -------------------------------------------------
def get_archives():
    resp = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if resp.status_code != 200:
        return []
    return resp.json().get("archives", [])[::-1]


def get_ratings(time_class):
    games = []

    for archive in get_archives():
        resp = requests.get(archive)
        if resp.status_code != 200:
            continue

        data = resp.json().get("games", [])

        filtered = [
            g for g in data
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ][::-1]

        games.extend(filtered)

    ratings = []
    for g in games:
        side = (
            "white"
            if g["white"]["username"].lower() == USERNAME.lower()
            else "black"
        )
        ratings.append(g[side]["rating"])

    return ratings[::-1]


# -------------------------------------------------
# DOTTED FLOATING PLOT (PHASE 3)
# -------------------------------------------------
def plot_dotted_fill(ax, ratings, color):
    x_positions = list(range(1, len(ratings) + 1))

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # -------- FLOATING PARAMETERS --------
    FLOAT_RATIO = 0.12        # distance above x-axis
    SOFT_MIN_RATIO = 0.08     # prevents hard minimum cut
    TOP_PADDING_RATIO = 0.18  # headroom above max

    soft_min = min_rating - (rating_range * SOFT_MIN_RATIO)
    float_base = soft_min + (rating_range * FLOAT_RATIO)
    dynamic_max = max_rating + (rating_range * TOP_PADDING_RATIO)

    # Dot density
    dot_step = max(6, int(rating_range / 22))

    # -------- DRAW DOTS --------
    for x, rating in zip(x_positions, ratings):
        y_values = list(
            range(
                int(float_base),
                int(rating),
                dot_step
            )
        )

        ax.scatter(
            [x] * len(y_values),
            y_values,
            s=18,
            color=color,
            alpha=0.95,
            linewidths=0
        )

    # -------- AXES --------
    ax.set_ylim(soft_min, dynamic_max)
    ax.set_xlim(0.5, len(ratings) + 0.5)

    # 6 evenly spaced x-ticks
    step = max(1, len(ratings) // 5)
    xticks = [1 + i * step for i in range(6)]
    xticks[-1] = len(ratings)

    ax.set_xticks(xticks)
    ax.set_xticklabels([str(x) for x in xticks])


# -------------------------------------------------
# RENDER
# -------------------------------------------------
for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class)
    if not ratings:
        continue

    fig, ax = plt.subplots(figsize=(12, 4.6))

    plot_dotted_fill(
        ax=ax,
        ratings=ratings,
        color=cfg["color"]
    )

    # ---- Styling ----
    ax.set_facecolor("#F6F4EC")  # Ivory
    fig.patch.set_facecolor("#F6F4EC")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#8A8A8A")

    ax.tick_params(axis="y", length=0)
    ax.grid(False)

    ax.set_title(
        f"{time_class.upper()} · LAST {len(ratings)} GAMES",
        loc="left",
        fontsize=11,
        pad=10,
        color="#2A2529"
    )

    plt.tight_layout(pad=2)

    plt.savefig(
        f"assets/svg/rating-{time_class}.svg",
        format="svg",
        bbox_inches="tight"
    )

    plt.close()
