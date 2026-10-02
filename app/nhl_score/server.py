"""HTTP server exposing the NHL score JSON API and the static web app.

Routes:
    GET /api/health
    GET /api/scores[?date=YYYY-MM-DD][&team=MTL]
    GET /api/teams/<ABBREV>/score[?date=YYYY-MM-DD]
    GET /api/games/<id>
    GET /api/standings[?date=YYYY-MM-DD]
    GET /            -> web app
"""

import argparse
import json
import mimetypes
import re
from datetime import date as date_cls
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, models
from .client import NHLAPIError, NHLClient

STATIC_DIR = Path(__file__).parent / "static"
TEAM_RE = re.compile(r"^/api/teams/([A-Za-z]{3})/score$")
GAME_RE = re.compile(r"^/api/games/(\d+)$")


class BadRequest(Exception):
    pass


def _date_param(query):
    value = query.get("date", [None])[0]
    if value in (None, "", "now"):
        return None
    try:
        return date_cls.fromisoformat(value).isoformat()
    except ValueError as err:
        raise BadRequest("date must be YYYY-MM-DD") from err


def route(client, path, query):
    """Resolve an API path to (status, payload). Kept pure for testing."""
    try:
        if path == "/api/health":
            return 200, {"status": "ok", "version": __version__}
        if path == "/api/scores":
            team = query.get("team", [None])[0]
            return 200, models.scoreboard(client.scores(_date_param(query)), team)
        match = TEAM_RE.match(path)
        if match:
            board = models.scoreboard(client.scores(_date_param(query)), match.group(1))
            return 200, {**board, "game": board["games"][0] if board["games"] else None}
        match = GAME_RE.match(path)
        if match:
            return 200, models.game_detail(client.game(match.group(1)))
        if path == "/api/standings":
            return 200, models.standings(client.standings(_date_param(query)))
    except BadRequest as err:
        return 400, {"error": str(err)}
    except NHLAPIError as err:
        return 502, {"error": "NHL API unavailable", "detail": str(err)}
    return 404, {"error": "not found"}


def make_handler(client):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"nhl-score/{__version__}"

        def do_GET(self):
            url = urlparse(self.path)
            if url.path.startswith("/api/"):
                status, payload = route(client, url.path, parse_qs(url.query))
                self._send(status, json.dumps(payload).encode(), "application/json")
            else:
                self._static(url.path)

        def _static(self, path):
            name = "index.html" if path in ("", "/") else path.lstrip("/")
            file = (STATIC_DIR / name).resolve()
            if STATIC_DIR.resolve() not in file.parents or not file.is_file():
                self._send(404, b"not found", "text/plain")
                return
            ctype = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            self._send(200, file.read_bytes(), ctype)

        def _send(self, status, body, ctype):
            self.send_response(status)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="NHL score API and web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--ttl", type=int, default=15, help="upstream cache seconds")
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(NHLClient(ttl=args.ttl)))
    print(f"NHL Score running on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
