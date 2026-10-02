import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from nhl_score import models
from nhl_score.client import NHLAPIError, NHLClient
from nhl_score.server import make_handler, route

SCORE = {
    "prevDate": "2026-10-07", "currentDate": "2026-10-08", "nextDate": "2026-10-09",
    "games": [
        {
            "id": 2026020001, "gameDate": "2026-10-08", "startTimeUTC": "2026-10-08T23:00:00Z",
            "gameState": "LIVE", "venue": {"default": "Centre Bell"},
            "awayTeam": {"id": 10, "abbrev": "TOR", "name": {"default": "Maple Leafs"}, "score": 1, "sog": 12},
            "homeTeam": {"id": 8, "abbrev": "MTL", "name": {"default": "Canadiens"}, "score": 2, "sog": 15},
            "clock": {"timeRemaining": "07:41", "inIntermission": False},
            "periodDescriptor": {"number": 2, "periodType": "REG"},
            "goals": [{
                "periodDescriptor": {"number": 1}, "timeInPeriod": "04:32", "teamAbbrev": "MTL",
                "name": {"default": "N. Suzuki"}, "goalsToDate": 1, "strength": "pp",
                "assists": [{"name": {"default": "C. Caufield"}, "assistsToDate": 1}],
                "awayScore": 0, "homeScore": 1,
            }],
        },
        {
            "id": 2026020002, "gameState": "FUT", "startTimeUTC": "2026-10-09T02:00:00Z",
            "awayTeam": {"abbrev": "BOS", "name": {"default": "Bruins"}},
            "homeTeam": {"abbrev": "VAN", "name": {"default": "Canucks"}},
        },
    ],
}
STANDINGS = {"standings": [
    {"teamAbbrev": {"default": "TOR"}, "teamName": {"default": "Maple Leafs"}, "points": 2, "gamesPlayed": 2},
    {"teamAbbrev": {"default": "MTL"}, "teamName": {"default": "Canadiens", "fr": "Canadiens de Montréal"},
     "points": 4, "gamesPlayed": 2, "streakCode": "W", "streakCount": 2},
]}
LANDING = {**SCORE["games"][0], "goals": None, "summary": {"scoring": [
    # Gamecenter localizes teamAbbrev, unlike the score feed.
    {"periodDescriptor": {"number": 1},
     "goals": [{**SCORE["games"][0]["goals"][0], "teamAbbrev": {"default": "MTL"}}]},
]}}


def fake_fetch(calls):
    def fetch(url):
        calls.append(url)
        if "/score/" in url:
            return SCORE
        if "/standings/" in url:
            return STANDINGS
        if "/gamecenter/" in url:
            return LANDING
        raise NHLAPIError("boom")
    return fetch


class ModelTests(unittest.TestCase):
    def test_scoreboard(self):
        board = models.scoreboard(SCORE)
        self.assertTrue(board["has_live"])
        live, fut = board["games"]
        self.assertEqual(live["status"], "live")
        self.assertEqual(live["period"], "2e")
        self.assertEqual(live["home"]["score"], 2)
        self.assertEqual(live["goals"][0]["scorer"], "N. Suzuki")
        self.assertEqual(live["goals"][0]["strength"], "PP")
        self.assertEqual(fut["status"], "scheduled")

    def test_team_filter(self):
        board = models.scoreboard(SCORE, "van")
        self.assertEqual([g["id"] for g in board["games"]], [2026020002])
        self.assertFalse(board["has_live"])

    def test_standings_sorted_and_french(self):
        rows = models.standings(STANDINGS)["standings"]
        self.assertEqual(rows[0]["abbrev"], "MTL")
        self.assertEqual(rows[0]["name"], "Canadiens de Montréal")
        self.assertEqual(rows[0]["streak"], "W2")

    def test_game_detail_flattens_goals(self):
        detail = models.game_detail(LANDING)
        self.assertEqual(len(detail["goals"]), 1)
        self.assertEqual(detail["goals"][0]["period"], 1)
        self.assertEqual(detail["goals"][0]["team"], "MTL")

    def test_period_labels(self):
        self.assertEqual(models._period_label({"number": 1, "periodType": "REG"}), "1re")
        self.assertEqual(models._period_label({"number": 4, "periodType": "OT"}), "Prol.")
        self.assertEqual(models._period_label({"number": 5, "periodType": "SO"}), "TB")


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.client = NHLClient(fetch=fake_fetch(self.calls), ttl=60)

    def test_scores_date(self):
        status, body = route(self.client, "/api/scores", {"date": ["2026-10-08"]})
        self.assertEqual(status, 200)
        self.assertTrue(self.calls[-1].endswith("/score/2026-10-08"))

    def test_bad_date(self):
        status, _ = route(self.client, "/api/scores", {"date": ["demain"]})
        self.assertEqual(status, 400)

    def test_team_score(self):
        status, body = route(self.client, "/api/teams/mtl/score", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["game"]["home"]["abbrev"], "MTL")

    def test_game_and_standings(self):
        self.assertEqual(route(self.client, "/api/games/2026020001", {})[0], 200)
        self.assertEqual(route(self.client, "/api/standings", {})[0], 200)

    def test_cache(self):
        route(self.client, "/api/scores", {})
        route(self.client, "/api/scores", {})
        self.assertEqual(len(self.calls), 1)

    def test_upstream_error_and_404(self):
        def broken(url):
            raise NHLAPIError("down")
        self.assertEqual(route(NHLClient(fetch=broken), "/api/scores", {})[0], 502)
        self.assertEqual(route(self.client, "/api/nope", {})[0], 404)


class ServerTests(unittest.TestCase):
    def test_http_roundtrip(self):
        client = NHLClient(fetch=fake_fetch([]))
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(client))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urllib.request.urlopen(f"{base}/api/scores?team=MTL") as r:
                self.assertEqual(len(json.load(r)["games"]), 1)
            with urllib.request.urlopen(f"{base}/") as r:
                self.assertIn(b"Scores NHL", r.read())
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f"{base}/../server.py")
            self.assertEqual(ctx.exception.code, 404)
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
