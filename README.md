# Tag Host Chain (THC)

> **Statut : en cours de conception (WIP).** Rien n'est encore utilisable, voir [ROADMAP.md](ROADMAP.md).

Faire tourner l'hôte d'un jeu coop entre amis **sans serveur dédié** : le monde est
récupéré au lancement du jeu et renvoyé à la fermeture, avec un verrou pour qu'un seul
joueur héberge à la fois.

Né d'un problème concret : trois frères qui jouent à Enshrouded (hébergement P2P par
le client d'un joueur) et qui se passaient la sauvegarde à la main.

*THC* = **T**ristan, **H**enri, **C**harles, ou *Tag Host Chain*, selon l'humeur.

## Comment ça marche (cible)

1. Le jeu est lancé depuis Steam avec une option de lancement qui passe par THC.
2. THC prend le **verrou**, télécharge la dernière sauvegarde du monde et lance le jeu.
3. Quand le jeu se ferme, THC attend que les fichiers soient stables, envoie la nouvelle
   version dans le stockage et libère le verrou.
4. Si un hôte plante et laisse un verrou périmé, le joueur suivant est prévenu et peut
   le forcer. Les versions précédentes sont conservées.

## Principes

- **Python seulement**, lancé avec [uv](https://docs.astral.sh/uv/) : même commande sous
  Windows et Linux, aucun venv à créer pour jouer.
- **Stockage** : Cloudflare R2 (compatible S3, via `boto3`) et un backend dossier local
  pour développer et tester.
- **Indépendant du jeu** : chaque jeu est un *profil* (chemin de save, motifs de fichiers).
  Enshrouded est le premier.

## Prérequis

**Désactiver Steam Cloud pour le jeu, sur chaque machine.** Sinon Steam et THC écrivent
sur les mêmes fichiers et peuvent s'écraser mutuellement.

1. **Sauvegarde d'abord** ton dossier de save actuel (Enshrouded avec Steam Cloud :
   `Steam\userdata\<ton id>\1203620\remote`).
2. Steam → clic droit sur le jeu → Propriétés → Général → décocher
   « Conserver les sauvegardes dans le Steam Cloud ».
3. Si Steam demande quoi faire des fichiers, garder les **fichiers locaux**.
4. Lancer le jeu, charger le monde, quitter : les fichiers sont maintenant écrits en local
   (Enshrouded : `Saved Games\Enshrouded`, à confirmer sur ta machine).

Attention : sans Steam Cloud, le fichier des personnages n'est plus sauvegardé par Steam.
THC ne le synchronise pas (il est propre à chaque joueur), pense à en garder une copie.

## Essayer l'option de lancement (test de plomberie)

Un script de test (`tools/test_launch.py`) vérifie que Steam transmet bien la commande du
jeu et que le wrapper attend sa fin. Option de lancement Steam :

```
C:\chemin\vers\uv.exe run C:\chemin\vers\tools\test_launch.py -- %command%
```

## Documentation

- [ROADMAP.md](ROADMAP.md) : jalons et décisions
- [ARCHITECTURE.md](ARCHITECTURE.md) : architecture estimée

## Licence

[MIT](LICENSE)