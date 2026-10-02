"""Normalize raw NHL API payloads into compact, stable JSON for the app."""

LIVE_STATES = {"LIVE", "CRIT"}
FINAL_STATES = {"OFF", "FINAL", "OVER"}


def _text(value):
    """NHL names are localized dicts like {"default": "Canadiens", "fr": ...}."""
    if isinstance(value, dict):
        return value.get("fr") or value.get("default")
    return value


def status_of(state):
    if state in LIVE_STATES:
        return "live"
    if state in FINAL_STATES:
        return "final"
    if state == "PRE":
        return "pregame"
    return "scheduled"


def _team(raw):
    raw = raw or {}
    return {
        "id": raw.get("id"),
        "abbrev": raw.get("abbrev"),
        "name": _text(raw.get("name")) or _text(raw.get("commonName")),
        "logo": raw.get("logo"),
        "score": raw.get("score"),
        "sog": raw.get("sog"),
    }


def _period_label(descriptor):
    if not descriptor:
        return None
    period_type = descriptor.get("periodType")
    number = descriptor.get("number")
    if period_type == "SO":
        return "TB"
    if period_type == "OT":
        return "Prol." if not number or number <= 4 else f"{number - 3}e prol."
    return f"{number}e" if number and number > 1 else "1re"


def _goal(raw):
    return {
        "period": (raw.get("periodDescriptor") or {}).get("number", raw.get("period")),
        "time": raw.get("timeInPeriod"),
        "team": raw.get("teamAbbrev"),
        "scorer": _text(raw.get("name")),
        "scorer_total": raw.get("goalsToDate"),
        "strength": (raw.get("strength") or "ev").upper(),
        "assists": [
            {"name": _text(a.get("name")), "total": a.get("assistsToDate")}
            for a in raw.get("assists") or []
        ],
        "away_score": raw.get("awayScore"),
        "home_score": raw.get("homeScore"),
    }


def game(raw):
    state = raw.get("gameState")
    clock = raw.get("clock") or {}
    descriptor = raw.get("periodDescriptor")
    return {
        "id": raw.get("id"),
        "date": raw.get("gameDate"),
        "start_time_utc": raw.get("startTimeUTC"),
        "state": state,
        "status": status_of(state),
        "venue": _text(raw.get("venue")),
        "away": _team(raw.get("awayTeam")),
        "home": _team(raw.get("homeTeam")),
        "period": _period_label(descriptor),
        "period_type": (descriptor or {}).get("periodType"),
        "clock": clock.get("timeRemaining"),
        "intermission": bool(clock.get("inIntermission")),
        "goals": [_goal(g) for g in raw.get("goals") or []],
    }


def scoreboard(raw, team=None):
    games = [game(g) for g in raw.get("games") or []]
    if team:
        team = team.upper()
        games = [g for g in games if team in (g["away"]["abbrev"], g["home"]["abbrev"])]
    return {
        "date": raw.get("currentDate"),
        "prev_date": raw.get("prevDate"),
        "next_date": raw.get("nextDate"),
        "has_live": any(g["status"] == "live" for g in games),
        "games": games,
    }


def standings(raw):
    rows = []
    for r in raw.get("standings") or []:
        rows.append({
            "abbrev": _text(r.get("teamAbbrev")),
            "name": _text(r.get("teamName")),
            "logo": r.get("teamLogo"),
            "conference": r.get("conferenceName"),
            "division": r.get("divisionName"),
            "games_played": r.get("gamesPlayed"),
            "wins": r.get("wins"),
            "losses": r.get("losses"),
            "ot_losses": r.get("otLosses"),
            "points": r.get("points"),
            "goal_diff": r.get("goalDifferential"),
            "streak": f"{r.get('streakCode') or ''}{r.get('streakCount') or ''}" or None,
        })
    rows.sort(key=lambda r: (-(r["points"] or 0), r["games_played"] or 0))
    return {"standings": rows}


def game_detail(raw):
    """Gamecenter landing nests goals under summary.scoring[].goals."""
    goals = []
    for period in (raw.get("summary") or {}).get("scoring") or []:
        for g in period.get("goals") or []:
            goals.append({**g, "periodDescriptor": period.get("periodDescriptor")})
    return game({**raw, "goals": goals})
