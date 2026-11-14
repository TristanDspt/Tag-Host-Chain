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
| Synchro | Pull au lancement, push à la fermeture, **seulement si les fichiers ont changé** |
| Portée | Moteur indépendant du jeu, un *profil* par jeu, Enshrouded en premier |
| Steam Cloud | Désactivé chez les trois (2026-11-14) : un seul écrivain sur les fichiers, THC. Procédure dans le README |

## Jalons du MVP

*MVP = la plus petite version qui fait déjà le travail : pull, lancement, attente, push,
lock simple et backups, pour Enshrouded seulement.*

- [ ] **J0 – Squelette** : structure du repo, config TOML par joueur, profil de jeu
  (Enshrouded : motifs `<hex>*`, chemin de save), logs
- [ ] **J1 – Stockage** : interface commune (lire, écrire, lister, supprimer, créer si
  absent) et backend dossier local
- [ ] **J2 – Moteur de sync** : collecte des fichiers du monde, pull avec backup local
  avant d'écraser, push seulement si modifié, rotation des backups
- [ ] **J3 – Wrapper complet** : lancement via `%command%`, attente de la fin du jeu,
  attente de la stabilité des fichiers, push. Testé avec un faux jeu, puis Enshrouded
- [ ] **J4 – Lock** : prise, battement régulier, libération, détection d'un lock mort avec
  question « forcer ? », commande `unlock`
- [ ] **J5 – Backend R2** : même interface avec boto3, lock atomique
- [ ] **J6 – Mise en service** : config de chaque joueur, procédure d'installation,
  **test sous Linux/Proton**

## Déjà fait

- [x] Test de plomberie Windows : Steam transmet `-- <chemin du jeu>`, le wrapper attend
  la fin du jeu (227 s mesurées), uv installe boto3 dans un environnement isolé

## Backlog

- Profils d'autres jeux
- Push en cours de session (limiter la perte si l'hôte plante)
- Notifications (Discord ?) quand un joueur prend ou libère le lock
- Commande `restore` pour revenir à une version précédente
- Interface minimale (tkinter ?) pour le non-technique

## Questions ouvertes

- **Chemin de save** : Steam Cloud est désactivé (voir décisions), la save est donc attendue
  dans `Saved Games\Enshrouded`. À confirmer sur la machine de chaque joueur après la
  bascule, avec une vraie save (J3).
- **Linux/Proton** : forme exacte de `%command%` (chemins Proton), nom du processus,
  chemin de la save dans le prefix. À tester chez le frère sous Linux.
- **R2** : inscription (carte bancaire demandée ?), droits minimaux des clés d'accès.
- **Durée avant lock considéré mort** (valeur par défaut à choisir).