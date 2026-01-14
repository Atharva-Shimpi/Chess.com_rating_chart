import matplotlib.pyplot as plt
import numpy as np


# =========================
# GLOBAL STYLE
# =========================
plt.rcParams.update({
    "figure.facecolor": "#0f1115",
    "axes.facecolor": "#f6f4ec",
    "font.family": "DejaVu Sans",
})


# =========================
# DOT CONFIGURATION
# =========================
DOT_SIZE = 6
DOT_STEP = 6
DOT_DIAMETER_Y = 6  # semantic unit, NOT radius-based


# =========================
# FLOATING GRAPH CONFIG
# =========================
FLOAT_GAP_RATIO = 0.10   # invisible space below dots
X_AXIS_GAP_RATIO = 0.08 # distance between x-axis and dot base


# =========================
# AXIS / TICKS
# =========================
Y_TICKS_COUNT = 6
X_TICKS_COUNT = 6


# =========================
# LAYOUT / MARGINS (PHASE 5)
# =========================
LEFT_MARGIN   = 0.08
RIGHT_MARGIN  = 0.08
TOP_MARGIN    = 0.16   # intentionally larger (future header)
BOTTOM_MARGIN = 0.10   # reduced slightly


# =========================
# CHART RENDER FUNCTION
# =========================
def render_chart(ax, ratings, title, color):
    games = np.arange(len(ratings))
    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # Floating base (logical)
    float_base = min_rating

    # Visual base (what eye sees)
    visual_dot_base = float_base - DOT_DIAMETER_Y

    # Axis limits
    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * 0.12

    ax.set_ylim(axis_floor, axis_ceiling)
    ax.set_xlim(-1, len(ratings))

    # Draw dots
    for x, rating in zip(games, ratings):
        y_values = np.arange(float_base, rating + DOT_STEP, DOT_STEP)
        ax.scatter(
            np.full_like(y_values, x),
            y_values,
            s=DOT_SIZE,
            color=color,
            linewidths=0
        )

    # Y ticks (bottom aligned correctly)
    yticks = np.linspace(float_base, axis_ceiling, Y_TICKS_COUNT)
    yticks[0] = visual_dot_base + DOT_DIAMETER_Y
    ax.set_yticks(yticks.astype(int))
    ax.tick_params(axis="y", length=0, labelsize=9)

    # X ticks
    xticks = np.linspace(0, len(ratings), X_TICKS_COUNT).astype(int)
    ax.set_xticks(xticks)
    ax.tick_params(axis="x", labelsize=9)

    # Remove spines
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color("#9a9a9a")

    # Title
    ax.text(
        0.01, 0.95,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color="#222"
    )


# =========================
# SVG EXPORT WRAPPER
# =========================
def generate_svg(ratings, title, color, filename):
    fig, ax = plt.subplots(figsize=(10, 3.2))

    plt.subplots_adjust(
        left=LEFT_MARGIN,
        right=1 - RIGHT_MARGIN,
        top=1 - TOP_MARGIN,
        bottom=BOTTOM_MARGIN
    )

    render_chart(ax, ratings, title, color)
    plt.savefig(filename, format="svg")
    plt.close(fig)
