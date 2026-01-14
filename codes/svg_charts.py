import matplotlib.pyplot as plt
import numpy as np


# ─────────────────────────────
# FIGURE / LAYOUT CONFIGURATION
# ─────────────────────────────

FIGURE_WIDTH = 12
FIGURE_HEIGHT = 4.8  # Taller, editorial feel

# Margins (0 → 1 in figure coordinates)
MARGIN_LEFT   = 0.08
MARGIN_RIGHT  = 0.08
MARGIN_TOP    = 0.18   # Reserved for header (future phase)
MARGIN_BOTTOM = 0.12   # Slightly reduced


# ─────────────────────────────
# DOT / GRAPH CONFIGURATION
# ─────────────────────────────

DOT_SIZE = 6                   # Scatter dot size (visual)
DOT_STEP = 8                   # Rating step per dot row
DOT_DIAMETER_Y = 8             # Fixed semantic vertical diameter (do NOT derive)

FLOAT_GAP_RATIO = 0.08         # Space below floating base
X_PADDING_GAMES = 0.5          # Space between y-axis and first dot column

MAX_Y_TICKS = 6                # Editorial Y-axis density


# ─────────────────────────────
# CORE CHART FUNCTION
# ─────────────────────────────

def render_rating_chart(
    ratings,
    title,
    color,
    output_path
):
    ratings = np.array(ratings)
    game_count = len(ratings)

    min_rating = ratings.min()
    max_rating = ratings.max()
    rating_range = max_rating - min_rating

    # Floating base (logical)
    float_base = min_rating

    # Visual base of dots (accounts for dot geometry)
    visual_dot_base = float_base - (DOT_DIAMETER_Y / 2)

    # Axis floor (invisible padding below dots)
    axis_floor = visual_dot_base - (rating_range * FLOAT_GAP_RATIO)
    axis_ceiling = max_rating + (rating_range * 0.12)

    # X values (1-indexed games)
    x_vals = np.arange(1, game_count + 1)

    # ──────────────
    # Figure & Axes
    # ──────────────
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    plt.subplots_adjust(
        left=MARGIN_LEFT,
        right=1 - MARGIN_RIGHT,
        top=1 - MARGIN_TOP,
        bottom=MARGIN_BOTTOM
    )

    # ──────────────
    # Plot dots
    # ──────────────
    for i, rating in enumerate(ratings):
        y_vals = np.arange(float_base, rating + DOT_STEP, DOT_STEP)
        ax.scatter(
            np.full_like(y_vals, x_vals[i]),
            y_vals,
            s=DOT_SIZE,
            color=color,
            linewidths=0
        )

    # ──────────────
    # Axes limits
    # ──────────────
    ax.set_xlim(1 - X_PADDING_GAMES, game_count + X_PADDING_GAMES)
    ax.set_ylim(axis_floor, axis_ceiling)

    # ──────────────
    # Y-axis ticks (editorial)
    # ──────────────
    yticks = np.linspace(
        visual_dot_base + DOT_DIAMETER_Y,
        axis_ceiling,
        MAX_Y_TICKS
    )
    ax.set_yticks(yticks)
    ax.set_yticklabels([int(y) for y in yticks])

    # ──────────────
    # Styling
    # ──────────────
    ax.set_title(title, loc="left", fontsize=11, pad=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9)

    ax.set_facecolor("#f7f5ee")
    fig.patch.set_facecolor("white")

    # ──────────────
    # Export
    # ──────────────
    plt.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)
