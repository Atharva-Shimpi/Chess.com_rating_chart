import requests

import os
os.makedirs("assets/svg", exist_ok=True)

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

matplotlib.rcParams["svg.image_inline"] = False        # Prevents embedded PNGs
matplotlib.rcParams["svg.fonttype"] = "path"           # Converts text --> vector paths (no embedded fonts)

HEADERS = {
    "User-Agent": "ChessRatingRefresh/1.0 atharvashimpi2005@gmail.com"
}

USERNAME = "Wawa_wuwa"        # Your Username here...
RULES = "chess"
NGAMES = 100                  # No. of recent games you want to display...

TIME_CLASSES = {
    "blitz": {"up": "#22c55e", "down": "#ef4444"},
    "rapid": {"up": "#3b82f6", "down": "#ef4444"},
    "bullet": {"up": "#f59e0b", "down": "#ef4444"},
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

def get_archives():
    resp = requests.get(
        ARCHIVES_URL.format(user=USERNAME),
        headers=HEADERS
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("archives", [])[::-1]


def get_ratings(time_class):
    games = []

    for archive in get_archives():
        resp = requests.get(archive, headers=HEADERS)
        if resp.status_code != 200:
            continue

        data = resp.json().get("games", [])

        filtered = [
            g for g in data
            if g.get("time_class") == time_class and g.get("rules") == RULES
        ][::-1]

        games.extend(filtered)

        if len(games) >= NGAMES:
            break

    ratings = []
    for g in games[:NGAMES]:
        side = (
            "white"
            if g["white"]["username"].lower() == USERNAME.lower()
            else "black"
        )
        ratings.append(g[side]["rating"])

    return ratings


def plot_colored_segments(data, up_color, down_color):
    for i in range(1, len(data)):
        color = up_color if data[i] >= data[i - 1] else down_color
        plt.plot(
            [i - 1, i],
            [data[i - 1], data[i]],
            color=color,
            linewidth=2
        )


for time_class, colors in TIME_CLASSES.items():
    ratings = get_ratings(time_class)
    if not ratings:
        plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No data available",
                 ha="center", va="center", fontsize=14)
        plt.axis("off")
        plt.savefig(f"assets/svg/rating-{time_class}.svg", format="svg")
        plt.close()
        continue


    plt.figure(figsize=(10, 4))
    plot_colored_segments(
        ratings,
        up_color=colors["up"],
        down_color=colors["down"]
    )


    plt.title(f"{time_class.capitalize()} Rating ({NGAMES} games)")
    plt.xlabel("Games")
    plt.ylabel("Rating")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        f"assets/svg/rating-{time_class}.svg",
        format="svg",
        bbox_inches="tight"
    )
    plt.close()
