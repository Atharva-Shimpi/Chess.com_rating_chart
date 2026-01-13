def plot_dotted_fill(ax, ratings, color):
    x_positions = list(range(len(ratings)))

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # -------- DESIGN CONTROLS --------
    FLOAT_GAP_RATIO = 0.20
    TOP_PADDING_RATIO = 0.15

    LEFT_GRAPH_PADDING = 2
    RIGHT_GRAPH_PADDING = 1

    dot_step = max(6, int(rating_range / 22))

    # -------- FLOATING BASE --------
    float_base = min_rating
    visual_dot_base = float_base - (dot_step / 2)

    axis_floor = visual_dot_base - rating_range * FLOAT_GAP_RATIO
    axis_ceiling = max_rating + rating_range * TOP_PADDING_RATIO

    # -------- DRAW DOTS --------
    for x, rating in zip(x_positions, ratings):
        y_values = list(range(
            int(visual_dot_base),
            rating + dot_step,
            dot_step
        ))
        ax.scatter(
            [x] * len(y_values),
            y_values,
            s=18,
            color=color,
            alpha=0.95,
            linewidths=0
        )

    # -------- LIMITS --------
    ax.set_ylim(axis_floor, axis_ceiling)
    ax.set_xlim(-LEFT_GRAPH_PADDING, len(ratings) + RIGHT_GRAPH_PADDING)

    # -------- Y TICKS (CORRECTLY ALIGNED) --------
    yticks = np.linspace(float_base, axis_ceiling, 6)
    yticks = [int(round(y)) for y in yticks]
    ax.set_yticks(yticks)
