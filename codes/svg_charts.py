import requests
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# ---------------- CONFIG ----------------

USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz": {"games": 100, "color": "#5a4a42"},   # Umber
    "rapid": {"games": 66,  "color": "#4f6b4f"},   # Moss Green
    "bullet": {"games": 53, "color": "#2f3b52"},   # Midnight Blue
}

BACKGROUND = "#f7f5ee"   # Ivory
TEXT_COLOR = "#2A2529"   # Charcoal

# Layout tuning (easy knobs)
FLOAT_PADDING_RATIO = 0.08      # space below dots
TOP_PADDING_RATIO   = 0.10      # headroom above dots
Y_LABEL_OFFSET_RATIO = 0.04     # keeps labels visually above dot base
LEFT_GRAPH_PADDING = 0.6        # x-space before first column of dots

MAX_Y_TICKS = 6

matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# ---------------- DATA ----------------

def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if r.status_code != 200:
        return []
    return r.json().get("archives", [])[::-1]

def get_ratings(time_class, n_games):
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
        if len(games) >= n_games:
            break

    ratings = []
    for g in games[:n_games]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings

# ---------------- PLOTTING ----------------

def plot_dotted_columns(ax, ratings, color):
    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    float_padding = rating_range * FLOAT_PADDING_RATIO
    top_padding   = rating_range * TOP_PADDING_RATIO

    float_base = min_rating - float_padding
    ceiling    = max_rating + top_padding

    dot_step = max(6, int(rating_range / 22))

    # draw dots
    for x, r in enumerate(ratings):
        y_vals = np.arange(float_base, r + 0.01, dot_step)
        ax.scatter(
            [x + LEFT_GRAPH_PADDING] * len(y_vals),
            y_vals,
            s=10,
            color=color,
            linewidths=0
        )

    # axis limits
    ax.set_xlim(LEFT_GRAPH_PADDING - 0.4, len(ratings) + LEFT_GRAPH_PADDING)
    ax.set_ylim(float_base, ceiling)

    # ---------- Y AXIS (editorial separation) ----------
    # Labels live ABOVE dot base — not on it
    y_label_start = float_base + rating_range * Y_LABEL_OFFSET_RATIO
    y_ticks = np.linspace(y_label_start, ceiling, MAX_Y_TICKS)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{int(t)}" for t in y_ticks], color=TEXT_COLOR)

    # ---------- X AXIS ----------
    x_ticks = np.linspace(LEFT_GRAPH_PADDING, len(ratings), 6)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([str(int(t - LEFT_GRAPH_PADDING)) for t in x_ticks], color=TEXT_COLOR)

    # ---------- CLEANUP ----------
    ax.grid(False)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color("#999999")
    ax.spines["bottom"].set_linewidth(1)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=TEXT_COLOR)

# ---------------- MAIN ----------------

for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class, cfg["games"])
    if not ratings:
        continue

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    plot_dotted_columns(ax, ratings, cfg["color"])

    ax.set_title(
        f"{time_class.upper()} · LAST {len(ratings)} GAMES",
        loc="left",
        fontsize=11,
        color=TEXT_COLOR,
        pad=12
    )

    plt.tight_layout()
    plt.savefig(f"rating-{time_class}.svg")
    plt.close()
