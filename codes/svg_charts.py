import requests
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ------------------ GLOBAL STYLE ------------------
IVORY = "#F6F4EF"
CHARCOAL = "#2A2529"

COLORS = {
    "blitz": "#5C3A2E",        # Umber
    "rapid": "#3E5F45",       # Moss Green
    "bullet": "#1F2A44",      # Midnight Blue
}

matplotlib.rcParams.update({
    "figure.facecolor": IVORY,
    "axes.facecolor": IVORY,
    "axes.edgecolor": CHARCOAL,
    "axes.labelcolor": CHARCOAL,
    "xtick.color": CHARCOAL,
    "ytick.color": CHARCOAL,
    "text.color": CHARCOAL,
    "font.weight": "bold",
    "font.size": 11,
    "svg.fonttype": "path",
})

# ------------------ CONFIG ------------------
USERNAME = "Atharva-Shimpi"
RULES = "chess"
NGAMES = {
    "blitz": 100,
    "rapid": 60,
    "bullet": 50,
}

ARCHIVES_URL = "https://api.chess.com/pub/player/{user}/games/archives"

# ------------------ DATA FETCH ------------------
def get_archives():
    r = requests.get(ARCHIVES_URL.format(user=USERNAME))
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
