"""Thin client for the public NHL web API (api-web.nhle.com) with a TTL cache."""

import json
import threading
import time
import urllib.error
import urllib.request

BASE_URL = "https://api-web.nhle.com/v1"
USER_AGENT = "nhl-score-app/0.1"


class NHLAPIError(Exception):
    """Raised when the upstream NHL API cannot be reached or returns bad data."""


def http_get_json(url, timeout=10):
    """Fetch a URL and decode its JSON body."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        raise NHLAPIError(f"GET {url} failed: {err}") from err


class NHLClient:
    """Fetch NHL endpoints, caching each path for `ttl` seconds.

    The NHL refreshes its feeds roughly every 15 seconds, so a short cache
    keeps many browser clients from multiplying upstream requests.
    """

    def __init__(self, fetch=http_get_json, ttl=15, base_url=BASE_URL):
        self._fetch = fetch
        self._ttl = ttl
        self._base_url = base_url
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, path):
        now = time.monotonic()
        with self._lock:
            hit = self._cache.get(path)
            if hit and now - hit[0] < self._ttl:
                return hit[1]
        data = self._fetch(f"{self._base_url}/{path}")
        with self._lock:
            self._cache[path] = (now, data)
        return data

    def scores(self, date=None):
        return self.get(f"score/{date or 'now'}")

    def standings(self, date=None):
        return self.get(f"standings/{date or 'now'}")

    def game(self, game_id):
        return self.get(f"gamecenter/{int(game_id)}/landing")
