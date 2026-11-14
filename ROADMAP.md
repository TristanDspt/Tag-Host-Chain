# Roadmap

Dernière mise à jour : 2026-11-14

## Décisions prises

| Sujet | Décision |
|---|---|
| Lancement | Options de lancement Steam : `uv run <script> -- %command%` (testé OK sous Windows) |
| Langage | Python uniquement, lancé par uv |
| Stockage | Cloudflare R2 via boto3 (lock atomique par « crée si absent ») |
| Développement | Backend dossier local d'abord, R2 ensuite |
| Lock périmé | Détecter (battement régulier), demander « forcer ? », ne jamais effacer de données |
| Synchro | Pull au lancement, push à la fermeture, **seulement si le contenu a changé** (comparaison de hash, jamais de la date de modification : le jeu réécrit ses fichiers à chaque fermeture) |
| Portée | Moteur indépendant du jeu, un *profil* par jeu, Enshrouded en premier |
| Jeu de la config | `game` reste dans `thc.toml` (une ligne explicite, nécessaire aussi hors Steam : `status`, tests). **Garde-fou au démarrage du wrapper** : si la variable d'environnement `SteamAppId` (fournie par Steam) existe et ne correspond pas au `steam_app_id` du profil, THC s'arrête avec un message clair, avant tout pull ou push (évite de synchroniser le monde en lançant un autre jeu). Config multi-jeux : reportée à l'arrivée d'un 2e profil |
| Steam Cloud | Désactivé chez les trois joueurs (2026-11-14) : un seul écrivain sur les fichiers, THC. Procédure dans le README. Sur la machine de référence (coupé depuis ~2-3 jours), la save reste dans `Steam\userdata\<ID>\1203620\remote` |
| Fichiers synchronisés | **Uniquement le fichier du monde** `world<N>.ksd`. Personnages, `global.ksd`, réglages et dossier `backup/` du jeu restent locaux (les trois joueurs ne s'échangent déjà que le monde) |
| Slot | `world0` chez les trois : un seul champ `slot` en config, la clé de stockage en est dérivée. Pas de nom de monde partagé pour l'instant |
| Dossier de save | `save_dir` **obligatoire** dans la config de chaque joueur, aucun défaut (le chemin dépend du disque, de l'ID Steam et de l'OS) |
| Config : peu de réglages | Chemins absolus obligatoires, `~` accepté. Pas de réglage de backups ni de lock dans la config : ce sont des constantes du développeur dans `thc/constants.py` (rotation des logs, backends gérés, dossier de stockage local `dev-storage/` ; à venir : `BACKUPS_KEEP` = 10 au J2, `LOCK_STALE_AFTER_MIN` = 10 provisoire au J4), utilisées comme valeurs par défaut des paramètres ; les tests passent des valeurs courtes en paramètre. Réglages du joueur dans `thc.toml`, réglages du développeur dans `constants.py` : moins de choix pour le joueur, moins de code |
| Point d'entrée | `run.py`, avec `main()` dedans (pas `thc.py` : un fichier du même nom que le package `thc/` empêche d'importer `main` depuis les tests). `thc/cli.py` ne fait que lire la ligne de commande. Option de lancement Steam : `uv run run.py -- %command%`. Si THC échoue (config, plus tard lock), le jeu n'est **pas** lancé |
| Logs | Démarrés avant la config, donc les erreurs de config sont aussi dans le fichier. Toujours dans `logs/` à côté de `run.py` (pas de réglage joueur) |

## Jalons du MVP

*MVP = la plus petite version qui fait déjà le travail : pull, lancement, attente, push,
lock simple et backups, pour Enshrouded seulement.*

- [x] **J0 – Squelette** : structure du repo, config TOML par joueur, profil de jeu
  (Enshrouded : fichier `world<N>.ksd`), logs.
  *Fait (2026-11-14) : `log.py`, `profiles.py`, `constants.py`, `config.py`, `cli.py`,
  `run.py`, `thc.example.toml`. Testé sur la machine de référence : config chargée, commande
  du jeu notée, rien n'est lancé.*
- [ ] **J1 – Stockage** : interface commune (lire, écrire, lister, supprimer, créer si
  absent) et backend dossier local
- [ ] **J2 – Moteur de sync** : collecte du fichier du monde, pull avec backup local
  avant d'écraser, push seulement si le contenu a changé (hash), rotation des backups
- [ ] **J3 – Wrapper complet** : garde-fou `SteamAppId` au démarrage (le profil reçoit alors
  un champ `steam_app_id`, `1203620` pour Enshrouded), lancement via `%command%`, attente de
  la fin du jeu, attente de la stabilité des fichiers, push. Testé avec un faux jeu, puis
  Enshrouded (dont : le monde seul suffit-il à jouer chez un autre joueur, sans `global.ksd`
  ni personnage ?)
- [ ] **J4 – Lock** : prise, battement régulier, libération, détection d'un lock mort avec
  question « forcer ? », commande `unlock`
- [ ] **J5 – Backend R2** : même interface avec boto3, lock atomique
- [ ] **J6 – Mise en service** : config de chaque joueur, procédure d'installation,
  **test sous Linux/Proton**

## Déjà fait

- [x] Test de plomberie Windows : Steam transmet `-- <chemin du jeu>`, le wrapper attend
  la fin du jeu (227 s mesurées), uv installe boto3 dans un environnement isolé
- [x] Test du kill (2026-11-14) : jeu tué depuis le gestionnaire des tâches, le wrapper survit,
  note la fin (code de sortie 1) et reprend la main. Conséquence : le **code de sortie du jeu
  n'influence pas le push** (seul compte : les fichiers ont-ils changé ?)
- [x] Format de save identifié (2026-11-14) : Enshrouded 1.0 = un fichier `world<N>.ksd` par
  monde. L'ancien format `<hex>*` avec fichiers `-index` (décrit par Hearth) n'est plus
  d'actualité. Vérifié sur le dossier : `world0.ksd` réécrit à la fin du test
  (19:09), et les fichiers sont réécrits à chaque fermeture, même après 50 s de jeu
  (d'où la comparaison par hash)

## Backlog

- Documenter le stockage dans le README (section Cloudflare R2 ou autre) **une fois la décision
  prise à J5** (version retirée le 2026-11-14 : stockage pas encore tranché)
- Profils d'autres jeux (et config multi-jeux : une section par jeu)
- Push en cours de session (limiter la perte si l'hôte plante)
- Notifications (Discord ?) quand un joueur prend ou libère le lock
- Commande `restore` pour revenir à une version précédente
- Interface minimale (tkinter ?) pour le non-technique

## Questions ouvertes

- **Chemin de save** : c'est le chemin standard de Steam par defaut,
  `<dossier Steam>\userdata\<ID>\1203620\remote` (pas de dossier `Saved Games`, Steam Cloud
  coupé). Seuls le disque et l'ID changent, d'où le `save_dir` obligatoire. Reste à vérifier
  l'emplacement exact du dossier Steam sous Linux (hypothèse : installation Steam native et
  non prefix Proton) et que Steam Cloud est bien coupé chez chacun.
- **Format de save** : il a changé avec la 1.0 (octobre 2026) ; une mise à jour du jeu peut
  le changer encore. Revérifier le profil après chaque grosse mise à jour.
- **Linux/Proton** : forme exacte de `%command%` (chemins Proton), nom du processus.
  À tester sur une machine Linux.
- **R2** : compte Cloudflare créé (connexion via GitHub, 2026-11-14). R2 demande un moyen de
  paiement à l'activation (carte ou PayPal), rien n'est facturé dans l'offre gratuite.
  **Décision reportée à J5.** Un seul compte et un seul bucket ; chaque
  utilisateur reçoit son propre token API (Object Read & Write limité au bucket), sans compte
  Cloudflare.
- **Durée avant lock considéré mort** : 10 min, constante `LOCK_STALE_AFTER_MIN` de `constants.py`, provisoire (battement
  toutes les ~60 s). À rediscuter au J4.
- **Fichiers corrompus après un kill** : un jeu tué en pleine écriture peut laisser une save
  incohérente. Le push ne doit jamais écraser `history/` ; à évaluer au J2 / J3 (validation
  minimale avant push ?).