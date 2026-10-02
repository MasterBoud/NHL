# Annonce des Bruins à l'arrivée à la maison

Quand vous arrivez chez vous, votre téléphone Android dit à voix haute si les
Bruins jouent aujourd'hui, et le score si le match est commencé ou terminé.

Exemples de messages :

- « Les Bruins jouent aujourd'hui à 19 h 30 : Boston Bruins contre Winnipeg Jets. »
- « Les Bruins jouent en ce moment. Boston Bruins 2, Winnipeg Jets 1. Période 2, il reste 07:41. »
- « Le match des Bruins est terminé. Score final : Boston Bruins 4, Winnipeg Jets 3. »
- « Les Bruins ne jouent pas aujourd'hui. Prochain match le 4 octobre à 19 h 30. »

## Ce qu'il faut

- Home Assistant avec l'intégration **NHL API** (HACS → chercher « NHL »).
- L'application **Home Assistant** sur le téléphone Android, connectée et avec
  la localisation autorisée « tout le temps » (c'est elle qui détecte l'arrivée).

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
   - Votre téléphone : *Outils de développement → Actions*, tapez
     `notify.mobile_app` ; prenez celui de votre téléphone, par exemple
     `notify.mobile_app_galaxy_s24`.

3. **L'automatisation.** Copiez le contenu de
   [`bruins_arrivee_maison.yaml`](bruins_arrivee_maison.yaml) à la fin de
   `automations.yaml`, remplacez les deux lignes marquées `A ADAPTER`, puis
   *Outils de développement → YAML → Recharger les automatisations*.

## Tester sans sortir de chez soi

*Paramètres → Automatisations* → « Bruins - annonce à l'arrivée à la maison »
→ menu ⋮ → **Exécuter**. Le téléphone doit parler.

## Bon à savoir

- Le message utilise le flux « alarme » d'Android : il est audible même si le
  téléphone est en mode silencieux. Pour l'éviter, remplacez `alarm_stream`
  par `music_stream`.
- La voix est celle du moteur de synthèse vocale du téléphone ; s'il parle
  avec un accent anglais, choisissez le français dans *Paramètres Android →
  Synthèse vocale*.
- Autre équipe : changez `team_abbrev` (voir [teams.md](../teams.md)), le nom
  du capteur et le mot « Bruins » dans les messages.
