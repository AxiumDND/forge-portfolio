"""Fetch the CNN Fear & Greed Index."""

import requests


_CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"

_CNN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://edition.cnn.com/markets/fear-and-greed",
    "Origin": "https://edition.cnn.com",
}


def fetch_fear_greed() -> dict:
    """Fetch the current Fear & Greed Index from CNN.

    Returns:
        dict with keys: score (float 0-100), rating (str).
        On failure returns score=None, rating="Unavailable".
    """
    try:
        resp = requests.get(_CNN_URL, headers=_CNN_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        fg = data.get("fear_and_greed", {})
        score = fg.get("score")
        rating = fg.get("rating", "Unknown")

        if score is not None:
            return {"score": round(float(score), 1), "rating": rating}
    except Exception:
        pass

    return {"score": None, "rating": "Unavailable"}
