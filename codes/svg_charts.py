import requests
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------
# SVG safety
# ---------------------------
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# ---------------------------
# USER CONFIG
# ---------------------------
USERNAME = "Wawa_wuwa"
RULES = "chess"

TIME_CLASSES = {
    "blitz":  {"games": 100, "color": "#5A4A42"},  # Umber
    "rapid":  {"games": 66,  "color": "#556B4E"},  # Moss Green
    "bullet": {"games": 53,  "color": "#2F3E55"},  # Midnight Blue
}

# ---------------------------
# VISUAL CONSTANTS (DESIGN TUNING)
# ---------------------------
DOT_STEP = 6                 # vertical spacing between dot rows (rating units)
DOT_SIZE = 12                # scatter size (visual only)
DOT_DIAMETER_Y = DOT_STEP    # semantic diameter in *rating units* (DO NOT tie to DOT_SIZE)

FLOAT_GAP_RATIO = 0.12       # space between x-axis and dot base
TOP_PADDING_RATIO = 0.10     # breathing room at top

X_PADDING_RATIO = 0.04       # distance between y-axis and first dot column
X_RIGHT_PADDING_RATIO = 0.02

Y_TICKS_COUNT = 6
X_TICKS_COUNT = 6

FIGSIZE = (10, 4)
BG_COLOR = "#F7F4EC"         # Ivory
TEXT_COLOR = "#2A2529"       # Charcoal
AXIS_COLOR = "#8A8A8A"

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"


# ---------------------------
# DATA FETCHING
# ---------------------------
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
        ][::-1]

        games.extend(filtered)
        if len(games) >= limit:
            break

    ratings = []
    for g in games[:limit]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])

    return ratings


# ---------------------------
# DOT COLUMN DRAWING
# ---------------------------
def draw_dot_columns(ax, ratings, color, float_base):
    xs, ys = [], []

    for i, rating in enumerate(ratings, start=1):
        for y in range(int(float_base), int(rating) + 1, DOT_STEP):
            xs.append(i)
            ys.append(y)

    ax.scatter(xs, ys, s=DOT_SIZE, color=color, linewidths=0)


# ---------------------------
# MAIN RENDER LOOP
# ---------------------------
for time_class, cfg in TIME_CLASSES.items():
    ratings = get_ratings(time_class, cfg["games"])
    if not ratings:
        continue

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # ---------------------------
    # FLOATING BASE (CANONICAL)
    # ---------------------------
    float_base = min_rating

    # visual dot base (what the eye sees)
    visual_dot_base = float_base - (DOT_DIAMETER_Y / 2)

    # axis floor (x-axis location)
    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO

    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    # ---------------------------
    # FIGURE
    # ---------------------------
    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    draw_dot_columns(ax, ratings, cfg["color"], float_base)

    # ---------------------------
    # LIMITS
    # ---------------------------
    x_min = 1 - cfg["games"] * X_PADDING_RATIO
    x_max = cfg["games"] + cfg["games"] * X_RIGHT_PADDING_RATIO

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(axis_floor, axis_ceiling)

    # ---------------------------
    # Y TICKS (≤ 6, BOTTOM ALIGNED CORRECTLY)
    # ---------------------------
    yticks = np.linspace(float_base, axis_ceiling, Y_TICKS_COUNT)

    # 🔒 CRITICAL FIX:
    # First Y-tick sits exactly ONE DOT DIAMETER ABOVE VISUAL DOT BASE
    yticks[0] = visual_dot_base + DOT_DIAMETER_Y

    ax.set_yticks(yticks)
    ax.set_yticklabels([str(int(y)) for y in yticks], color=TEXT_COLOR)

    # ---------------------------
    # X TICKS (6 EVEN)
    # ---------------------------
    xticks = np.linspace(1, cfg["games"], X_TICKS_COUNT)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(int(x)) for x in xticks], color=TEXT_COLOR)

    # ---------------------------
    # AXIS STYLING
    # ---------------------------
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color(AXIS_COLOR)
    ax.tick_params(axis="both", length=3, colors=TEXT_COLOR)

    ax.grid(False)

    # ---------------------------
    # TITLE
    # ---------------------------
    ax.text(
        0.01, 0.98,
        f"{time_class.upper()} · LAST {cfg['games']} GAMES",
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=TEXT_COLOR,
        fontsize=10,
        weight="medium"
    )

    plt.tight_layout()
    plt.savefig(f"rating-{time_class}.svg", format="svg", dpi=300)
    plt.close()
