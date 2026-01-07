# codes/svg_charts.py
# Drop-in replacement for your existing svg_charts.py
# - Adds User-Agent header for Chess.com API requests
# - Ensures assets/svg directory exists
# - Prints debug info to workflow logs
# - Writes a "No data available" placeholder svg when no data found

import os
import requests
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Make matplotlib create vector text (no embedded fonts) and avoid inline PNGs
matplotlib.rcParams["svg.image_inline"] = False
matplotlib.rcParams["svg.fonttype"] = "path"

# --- CONFIG ---
USERNAME = "Wawa_wuwa"   # <--- use this username now (you asked)
RULES = "chess"
NGAMES = 100

# Monotone colors (you provided final color mapping earlier).
# Keep these here to use per time-class
TIME_CLASSES = {
    "blitz": {"color": "#6B4F3E"},   # Umber (example)
    "rapid": {"color": "#4A6B47"},   # Moss Green (example)
    "bullet": {"color": "#1F3140"},  # Midnight Blue (example)
}

# Chess.com API URL template
ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# IMPORTANT: polite User-Agent required by chess.com API
HEADERS = {
    "User-Agent": "ChessRatingRefresh/1.0 (+https://github.com/Atharva-Shimpi/Chess.com_rating_chart)"
}

# Output dir used by README markdown
OUT_DIR = "assets/svg"

# Create output directory if missing
os.makedirs(OUT_DIR, exist_ok=True)


def get_archives():
    """Return list of archive URLs (oldest -> newest)."""
    url = ARCHIVES_URL.format(user=USERNAME)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"[ERROR] get_archives request failed: {e}")
        return []
    if resp.status_code != 200:
        print(f"[WARN] get_archives: status_code={resp.status_code} for {url}")
        return []
    data = resp.json()
    archives = data.get("archives", [])
    # reverse so oldest first (we append and then take newest NGAMES)
    return archives[::-1]


def get_ratings(time_class):
    """Fetch recent games and extract rating (for the player) for the given time_class.
       Returns a list in chronological order (oldest -> newest)."""
    games = []
    archives = get_archives()
    if not archives:
        print("[INFO] No archives returned by API.")
        return []

    for archive_url in archives:
        try:
            resp = requests.get(archive_url, headers=HEADERS, timeout=10)
        except Exception as e:
            print(f"[WARN] Failed to fetch archive {archive_url}: {e}")
            continue
        if resp.status_code != 200:
            print(f"[WARN] archive {archive_url} returned {resp.status_code}")
            continue

        month_games = resp.json().get("games", [])
        # filter for time_class and rules, and reverse to chronological (oldest->newest)
        filtered = [
            g for g in month_games
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ][::-1]

        if filtered:
            games.extend(filtered)

        if len(games) >= NGAMES:
            break

    # trim to NGAMES (most recent NGAMES). After we appended chronologically, the tail is newest.
    selected = games[:NGAMES]

    ratings = []
    for g in selected:
        # determine which side is the user (white or black)
        try:
            if g["white"]["username"].lower() == USERNAME.lower():
                ratings.append(g["white"]["rating"])
            else:
                ratings.append(g["black"]["rating"])
        except Exception as e:
            # malformed game object? skip
            print(f"[WARN] skipping a malformed game entry: {e}")
            continue

    # ratings is oldest -> newest (chronological order from left to right)
    return ratings


def draw_placeholder_svg(path, title_text="No data", w=1000, h=320, bg="#F7F6F0"):
    """Create a minimal SVG that says 'No data available' so GitHub won't render blank/invalid images."""
    # A very small custom SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="{bg}" rx="6" />
  <text x="50%" y="50%" font-family="Arial,Helvetica,sans-serif" font-size="18" fill="#6B6B6B" text-anchor="middle" dy=".3em">No data available</text>
  <text x="8" y="{h-10}" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="#9A9A9A">{title_text}</text>
</svg>'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[INFO] wrote placeholder SVG: {path}")


def plot_dotted_area(ratings, dot_color="#333333", title="", out_path=None, bg="#F7F6F0"):
    """
    Draw a dotted 'area' chart (stacked dots from y=0 up to rating for each x).
    ratings: list of ints (oldest -> newest)
    out_path: destination svg path
    """
    if out_path is None:
        raise ValueError("out_path required")

    if not ratings:
        draw_placeholder_svg(out_path, title_text=title)
        return

    # Chart size and margins
    fig_w, fig_h = 10, 3.6  # inches
    dpi = 100
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_axes([0.06, 0.12, 0.92, 0.78])  # left,bottom,width,height (so we have padding)

    # Background color (ivory-like)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    n = len(ratings)
    xs = list(range(n))

    # compute y range
    min_y = 0  # we want dots from zero up to rating
    max_rating = max(ratings)
    # give a small top margin
    y_margin = max(1, int(max_rating * 0.08))
    max_y = max_rating + y_margin

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(min_y - 1, max_y)

    # Draw dotted columns: for each x, place dots at integer y levels from 0..rating with a spacing
    # To control dot size and spacing, decide on vertical dot step (pixel-based).
    # We'll compute target number of vertical steps (about 15-22 dots tall for typical rating range)
    target_dot_rows = 18
    # determine dot step in rating units
    if max_rating <= 0:
        step = 1
    else:
        step = max(1, math.ceil(max_rating / target_dot_rows))

    # dot style
    dot_size = 18  # scatter s param (area)
    dot_edgewidth = 0
    dot_alpha = 1.0

    # For performance, build lists and scatter once
    all_x = []
    all_y = []
    for xi, r in enumerate(ratings):
        # generate y levels stepping by 'step', but keep last dot close to rating:
        # e.g., y = 0, step, 2*step ... up to r
        top = int(r)
        ys = list(range(0, top + 1, step))
        # ensure top is included (if not a multiple)
        if ys and ys[-1] != top:
            ys.append(top)
        elif not ys:
            ys = [0]
        # add these to arrays
        all_x.extend([xi] * len(ys))
        all_y.extend(ys)

    # plot the dots
    ax.scatter(all_x, all_y, s=dot_size, c=dot_color, edgecolors=None, linewidths=dot_edgewidth, alpha=dot_alpha)

    # Axes styling (Type B inspiration)
    # - keep x-axis line visible (thin)
    # - y-axis borderless, only ticks and tick labels (max 6 ticks)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#A0A0A0")
    ax.spines["bottom"].set_linewidth(1.0)

    # Y ticks: maximum of 6 ticks
    max_yticks = 6
    # compute nice tick interval
    approx_interval = max(1, math.ceil((max_y - min_y) / max_yticks))
    # snap interval to a round number (10, 50, 100 scale)
    # simple rounding: round to nearest power-of-ten multiple
    def nice_round(n):
        # round n to 1,2,5 multiples of power of 10
        p = 10 ** (len(str(int(n))) - 1)
        for factor in (1, 2, 5, 10):
            cand = factor * p
            if cand >= n:
                return cand
        return n

    interval = nice_round(approx_interval)
    # build ticks
    yticks = list(range(0, max_y + interval, interval))
    # cap at 6 if too many
    if len(yticks) > max_yticks:
        # recompute with bigger interval
        interval = interval * math.ceil(len(yticks) / max_yticks)
        yticks = list(range(0, max_y + interval, interval))
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(t) for t in yticks], fontfamily="sans-serif", fontsize=10, color="#2A2529")
    ax.yaxis.set_ticks_position('left')
    ax.yaxis.set_tick_params(length=0)  # remove tick lines

    # X ticks: show a small number of ticks (0..n). We'll put 5 ticks including first and last
    xtick_count = min(6, n)
    if xtick_count <= 1:
        xticks = [0]
    else:
        step_x = max(1, int(round((n - 1) / (xtick_count - 1))))
        xticks = list(range(0, n, step_x))
        if xticks[-1] != n - 1:
            xticks.append(n - 1)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(x) for x in xticks], fontfamily="sans-serif", fontsize=10, color="#2A2529")
    ax.xaxis.set_tick_params(length=6, color="#A0A0A0")

    # Title / header area like Type A: we draw a small text block at top-left and compact meta at top-right
    # We'll place the header inside the figure using text()
    header_fontsize = 12
    meta_fontsize = 11
    # left header
    ax.text(0, max_y - (y_margin * 0.3), title, fontsize=header_fontsize, fontweight="normal",
            verticalalignment='top', horizontalalignment='left', color="#2A2529")
    # right meta placeholder (we keep it empty here; README will show other text)
    # draw a subtle separator line under the header area (spans horizontally)
    ax.hlines(y=max_y - (y_margin * 0.6), xmin=-0.5, xmax=n - 0.5, colors="#E0DED6", linewidth=1.0, alpha=0.6)

    # Remove grid lines (or keep very subtle)
    ax.grid(False)

    # Tight layout and save
    # Ensure the figure background color is used in svg
    plt.savefig(out_path, format="svg", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[INFO] wrote chart SVG: {out_path} (n={n}, max_rating={max_rating}, step={step})")


def main():
    for time_class, cfg in TIME_CLASSES.items():
        print(f"[INFO] Generating chart for time_class={time_class}")
        ratings = get_ratings(time_class)
        print(f"[INFO] -> ratings count = {len(ratings)}")
        out_file = os.path.join(OUT_DIR, f"rating-{time_class}.svg")
        title = f"{time_class.capitalize()} · Last {len(ratings) if ratings else 0} games"
        # pick color
        color = cfg.get("color", "#333333")
        if not ratings:
            # create placeholder with title so README won't break
            draw_placeholder_svg(out_file, title_text=title)
            continue
        plot_dotted_area(ratings, dot_color=color, title=title, out_path=out_file)
    print("[DONE] All charts attempted.")


if __name__ == "__main__":
    main()
