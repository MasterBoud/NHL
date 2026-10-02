# Annonce des Bruins à l'arrivée à la maison

Quand vous arrivez chez vous, un haut-parleur de la maison (ex. Google Nest Hub)
dit à voix haute si les Bruins jouent aujourd'hui, et le score si le match est
commencé ou terminé.

Exemples de messages :

- « Les Bruins jouent aujourd'hui à 19 h 30 : Boston Bruins contre Winnipeg Jets. »
- « Les Bruins jouent en ce moment. Boston Bruins 2, Winnipeg Jets 1. Période 2, il reste 07:41. »
- « Le match des Bruins est terminé. Score final : Boston Bruins 4, Winnipeg Jets 3. »
- « Les Bruins ne jouent pas aujourd'hui. Prochain match le 4 octobre à 19 h 30. »

## Ce qu'il faut

- Home Assistant avec l'intégration **NHL API** (HACS → chercher « NHL »).
- L'application **Home Assistant** sur le téléphone, connectée et avec la
  localisation autorisée « tout le temps » (c'est elle qui détecte l'arrivée).
- **Home Assistant Cloud** (`tts.home_assistant_cloud`) pour la voix, et un
  haut-parleur compatible (Google Cast, Sonos…).

## Installation

1. **Le capteur des Bruins.** Avec NHL API v1.2 ou plus récent : *Paramètres →
   Appareils et services → Ajouter une intégration → NHL API*, équipe **BOS**.
   Le capteur (ex. `sensor.nhl_bos`) est trouvé automatiquement.
   Avec une version plus ancienne, dans `configuration.yaml` :

   ```yaml
   sensor:
     - platform: nhl_api
       team_abbrev: bos
       name: Bruins
   ```

   Redémarrez Home Assistant. Vérifiez dans *Outils de développement → États*
   que `sensor.bruins` existe.

2. **Trouver vos deux noms à adapter.**
   - Votre personne : *Paramètres → Personnes* ; l'identifiant ressemble à
     `person.carl`.
   - Votre haut-parleur : *Outils de développement → États*, tapez
     `media_player.` ; prenez celui de l'appareil lui-même (Google Cast),
     par exemple `media_player.hubcuisine`, pas sa copie Music Assistant.

3. **L'automatisation.** Copiez le contenu de
   [`bruins_arrivee_maison.yaml`](bruins_arrivee_maison.yaml) à la fin de
   `automations.yaml`, remplacez les deux lignes marquées `A ADAPTER`, puis
   *Outils de développement → YAML → Recharger les automatisations*.

## Tester sans sortir de chez soi

*Paramètres → Automatisations* → « Bruins - annonce à l'arrivée à la maison »
→ menu ⋮ → **Exécuter**. Le haut-parleur doit parler.

## Vidéo YouTube les soirs de match

Si les Bruins jouent aujourd'hui, l'écran (ex. Google Nest Hub) lance une vidéo
YouTube 15 secondes après l'annonce. Dans le fichier, remplacez
`ID_VIDEO_YOUTUBE` par l'identifiant de la vidéo : pour
`https://www.youtube.com/watch?v=AbC123xyz`, c'est `AbC123xyz` (pour un lien
`https://youtu.be/AbC123xyz`, c'est aussi ce qui suit le dernier `/`).

## Musique Spotify à chaque arrivée

Après l'annonce (et après la vidéo les soirs de match, une fois celle-ci
terminée), une playlist Spotify démarre sur le même appareil via **Music
Assistant**, qui doit avoir Spotify comme fournisseur de musique (compte
Premium). Dans le fichier, mettez l'appareil tel que Music Assistant le voit
(ex. `media_player.hubcuisine_2`) et l'identifiant de la playlist : pour
`https://open.spotify.com/playlist/AbC123?si=...`, c'est `AbC123`.

## Bon à savoir

- **Changer de voix :** dans le fichier, remplacez `SylvieNeural` par
  `AntoineNeural`, `JeanNeural` ou `ThierryNeural` (voix québécoises).
- **Aussi sur le téléphone :** enlevez les `#` du bloc commenté à la fin du
  fichier et mettez le nom de votre téléphone (`notify.mobile_app_...`). Ce
  message passe par le flux « alarme » d'Android, audible même en silencieux.
- Autre équipe : changez l'équipe de l'intégration NHL API et le mot « Bruins »
  dans les messages.
