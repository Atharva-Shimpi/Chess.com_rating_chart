import math
import matplotlib.pyplot as plt
import numpy as np


# =========================
# CONFIGURATION (SAFE TO TUNE)
# =========================
SVG_WIDTH = 1200
SVG_HEIGHT = 260

LEFT_MARGIN = 80
RIGHT_MARGIN = 30
TOP_MARGIN = 28
BOTTOM_MARGIN = 40

FLOAT_GAP_PX = 18        # X-axis → floating base
Y_LABEL_GAP_PX = 14     # Y labels → dot grid
X_LABEL_GAP_PX = 10

DOT_STEP = 8             # rating units per dot row
DOT_RADIUS = 2.1
MAX_Y_TICKS = 6


# =========================
# CORE RENDER FUNCTION
# =========================
def render_dot_chart(
    ratings,
    title,
    color,
    output_path,
):
    n = len(ratings)
    x_vals = np.arange(1, n + 1)

    min_rating = min(ratings)
    max_rating = max(ratings)

    # Dynamic range with breathing room
    padding = (max_rating - min_rating) * 0.08
    y_min = min_rating - padding
    y_max = max_rating + padding
    rating_range = y_max - y_min

    # --- SVG space calculations ---
    chart_width = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    chart_height = SVG_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

    x_axis_y = TOP_MARGIN + chart_height
    float_base_y = x_axis_y - FLOAT_GAP_PX

    # Grid height is limited by highest dot
    grid_height = float_base_y - TOP_MARGIN

    # --- Figure ---
    fig = plt.figure(figsize=(SVG_WIDTH / 100, SVG_HEIGHT / 100), dpi=100)
    ax = plt.gca()
    ax.set_xlim(0, SVG_WIDTH)
    ax.set_ylim(SVG_HEIGHT, 0)
    ax.axis("off")

    # --- Title ---
    ax.text(
        LEFT_MARGIN,
        TOP_MARGIN - 8,
        title.upper(),
        ha="left",
        va="bottom",
        fontsize=10,
        color="#2A2529",
        fontweight="medium",
    )

    # --- X-axis ---
    ax.plot(
        [LEFT_MARGIN, SVG_WIDTH - RIGHT_MARGIN],
        [x_axis_y, x_axis_y],
        color="#8A8A8A",
        linewidth=1,
    )

    # X ticks (6 evenly spaced)
    tick_indices = np.linspace(0, n - 1, 6, dtype=int)
    for idx in tick_indices:
        x = LEFT_MARGIN + (idx / (n - 1)) * chart_width
        ax.text(
            x,
            x_axis_y + X_LABEL_GAP_PX,
            str(idx + 1),
            ha="center",
            va="top",
            fontsize=9,
            color="#2A2529",
        )

    # --- Y-axis labels (OUTSIDE, baseline aligned) ---
    y_ticks = np.linspace(min_rating, max_rating, MAX_Y_TICKS)

    for val in y_ticks:
        y = float_base_y - ((val - y_min) / rating_range) * grid_height
        ax.text(
            LEFT_MARGIN - Y_LABEL_GAP_PX,
            y,
            f"{int(round(val))}",
            ha="right",
            va="baseline",
            fontsize=9,
            color="#2A2529",
        )

    # --- Dot grid ---
    for i, rating in enumerate(ratings):
        x = LEFT_MARGIN + (i / (n - 1)) * chart_width

        dot_levels = int((rating - y_min) // DOT_STEP)
        for level in range(dot_levels + 1):
            dot_y = float_base_y - (level * DOT_STEP / rating_range) * grid_height
            ax.add_patch(
                plt.Circle(
                    (x, dot_y),
                    DOT_RADIUS,
                    color=color,
                    linewidth=0,
                )
            )

    # --- Export ---
    plt.savefig(output_path, format="svg", bbox_inches="tight", pad_inches=0)
    plt.close(fig)


# =========================
# PUBLIC API
# =========================
def generate_chart(ratings, mode):
    COLORS = {
        "blitz": "#4A3F35",   # Umber
        "rapid": "#4E6B4C",   # Moss Green
        "bullet": "#1F2A44",  # Midnight Blue
    }

    title = f"{mode.upper()} · LAST {len(ratings)} GAMES"
    output_path = f"{mode}.svg"

    render_dot_chart(
        ratings=ratings,
        title=title,
        color=COLORS[mode],
        output_path=output_path,
    )
