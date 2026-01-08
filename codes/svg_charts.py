def plot_dotted_fill(ax, ratings, color):
    x_positions = list(range(1, len(ratings) + 1))

    min_rating = min(ratings)
    max_rating = max(ratings)
    rating_range = max_rating - min_rating

    # ---------------- FLOATING PARAMETERS ----------------
    FLOAT_RATIO = 0.12        # controls distance from x-axis
    SOFT_MIN_RATIO = 0.08     # prevents hard minimum cut
    TOP_PADDING_RATIO = 0.18  # headroom above max

    soft_min = min_rating - (rating_range * SOFT_MIN_RATIO)
    float_base = soft_min + (rating_range * FLOAT_RATIO)
    dynamic_max = max_rating + (rating_range * TOP_PADDING_RATIO)

    # Dot density
    dot_step = max(6, int(rating_range / 22))

    # ---------------- DOTTED FILL ----------------
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

    # ---------------- AXES ----------------
    ax.set_ylim(soft_min, dynamic_max)
    ax.set_xlim(0.5, len(ratings) + 0.5)

    # 6 evenly spaced x-ticks
    step = max(1, len(ratings) // 5)
    xticks = [1 + i * step for i in range(6)]
    xticks[-1] = len(ratings)

    ax.set_xticks(xticks)
    ax.set_xticklabels([str(x) for x in xticks])
