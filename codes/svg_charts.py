import requests
import matplotlib.pyplot as plt

USERNAME = "Atharva-Shimpi"
RULES = "chess"
NGAMES = 100

TIME_CLASSES = {
    "blitz": "#E74C3C",
    "rapid": "#3498DB",
    "bullet": "#2ECC71",
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

def get_archives():
    return requests.get(ARCHIVES_URL.format(user=USERNAME)).json()["archives"][::-1]

def get_ratings(time_class):
    games = []
    for archive in get_archives():
        data = requests.get(archive).json()["games"]
        filtered = [
            g for g in data
            if g["time_class"] == time_class and g["rules"] == RULES
        ][::-1]
        games.extend(filtered)
        if len(games) >= NGAMES:
            break

    ratings = []
    for g in games[:NGAMES]:
        side = "white" if g["white"]["username"].lower() == USERNAME.lower() else "black"
        ratings.append(g[side]["rating"])
    return ratings

for time_class, color in TIME_CLASSES.items():
    ratings = get_ratings(time_class)
    if not ratings:
        continue

    plt.figure(figsize=(10, 4))
    plt.plot(ratings, color=color, linewidth=2)
    plt.title(f"{time_class.capitalize()} Rating ({NGAMES} games)")
    plt.xlabel("Games")
    plt.ylabel("Rating")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"rating-{time_class}.svg")
    plt.close()
