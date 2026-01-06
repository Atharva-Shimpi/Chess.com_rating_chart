import requests
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["svg.image_inline"] = False        # Prevents embedded PNGs
matplotlib.rcParams["svg.fonttype"] = "path"           # Converts text --> vector paths (no embedded fonts)

USERNAME = "Atharva-Shimpi"
RULES = "chess"
NGAMES = 100

TIME_CLASSES = {
    "blitz": {"up": "#22c55e", "down": "#ef4444"},
    "rapid": {"up": "#3b82f6", "down": "#ef4444"},
    "bullet": {"up": "#f59e0b", "down": "#ef4444"},
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

def get_archives():
    resp = requests.get(ARCHIVES_URL.format(user=USERNAME))
    if resp.status_code != 200:
        return []
    data = resp.json()
    return data.get("archives", [])[::-1]


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
    plt.savefig(f"rating-{time_class}.svg")
    plt.close()
