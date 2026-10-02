# API et app Scores NHL

Petite API JSON + application web pour suivre les scores NHL en direct, sans
dépendance externe (Python 3.9+ standard seulement). Les données proviennent de
l'API publique de la NHL (`api-web.nhle.com`), mises en cache 15 s.

## Lancer

Sous Windows : double-cliquer sur `lancer.bat`. Le navigateur s'ouvre tout
seul ; fermer la fenêtre noire arrête l'app.

Autrement :

```bash
cd app
python3 -m nhl_score --port 8000        # options : --host 0.0.0.0 --ttl 15
```

Ouvrir <http://127.0.0.1:8000> : scores du jour, navigation par date, filtre
par équipe (ex. `MTL`, mémorisé), détail des buts au clic, classement de la
ligue. La page se rafraîchit toutes les 15 s quand un match est en direct.

## API

| Route | Description |
|-------|-------------|
| `GET /api/health` | État du serveur |
| `GET /api/scores?date=YYYY-MM-DD&team=MTL` | Matchs du jour (ou de la date), filtrables par équipe |
| `GET /api/teams/MTL/score?date=YYYY-MM-DD` | Match d'une équipe (`game` est `null` si aucun) |
| `GET /api/games/<id>` | Détail d'un match avec les buts et les aides |
| `GET /api/standings?date=YYYY-MM-DD` | Classement de la ligue, trié par points |

Champ `status` d'un match : `scheduled`, `pregame`, `live` ou `final`
(le `state` brut de la NHL est aussi fourni). Erreurs : `400` date invalide,
`404` route inconnue, `502` API NHL injoignable.

Exemple :

```bash
curl 'http://127.0.0.1:8000/api/teams/MTL/score'
```

## Tests

```bash
cd app
python3 -m unittest discover -s tests -t .
```
