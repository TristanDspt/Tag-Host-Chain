# Architecture (estimée)

> Version de cadrage. Elle bougera pendant J0 à J3, c'est normal.

## Principe

Un **wrapper** lancé par Steam qui entoure le jeu :

```
Steam ──► uv run thc.py -- %command%
                │
                ├─ 1. prendre le lock
                ├─ 2. pull (backup local avant d'écraser)
                ├─ 3. lancer le jeu et attendre sa fin      (+ battement du lock en tâche de fond)
                ├─ 4. attendre que les fichiers soient stables
                ├─ 5. push si modifié
                └─ 6. libérer le lock
```

Les invités n'utilisent pas le wrapper pour rejoindre : seul l'hôte de la session passe par
THC. C'est le lock qui désigne l'hôte.

## Arborescence prévue

```
Tag-Host-Chain/
├── thc.py                  # point d'entrée mince (uv run thc.py -- %command%)
├── requirements.txt
├── README.md  ROADMAP.md  ARCHITECTURE.md  CLAUDE_CONTEXT.md
├── thc/
│   ├── cli.py              # sous-commandes : run (défaut), status, unlock, restore
│   ├── config.py           # lecture de la config joueur (TOML)
│   ├── profiles.py         # profils de jeu (chemin de save, motifs de fichiers)
│   ├── runner.py           # lancement du jeu, attente, stabilité des fichiers
│   ├── sync.py             # collecte, manifeste, pull, push
│   ├── lock.py             # prise, battement, libération, détection de lock mort
│   ├── backup.py           # backups locaux et rotation
│   ├── log.py              # journal dans un fichier à côté du script
│   └── storage/
│       ├── base.py         # interface Storage
│       ├── local.py        # backend dossier local (dev et tests)
│       └── r2.py           # backend Cloudflare R2 (boto3)
├── config/
│   ├── thc.example.toml    # modèle de config (la vraie config n'est PAS dans git)
│   └── games/
│       └── enshrouded.toml # profil de jeu
├── tests/
│   └── fake_game.py        # faux jeu : modifie des fichiers de save factices puis se termine
└── tools/
    └── test_launch.py      # test de plomberie Steam + uv
```

## Modules

| Module | Responsabilité |
|---|---|
| `cli` | Lit la ligne de commande, choisit l'action, retire le `--` en tête |
| `config` | Charge la config du joueur ; chemins absolus, jamais relatifs au dossier courant |
| `profiles` | Décrit un jeu : dossier de save par OS, motifs de fichiers à synchroniser |
| `runner` | Lance la commande du jeu, attend sa fin, puis la stabilité des fichiers de save |
| `sync` | Construit la liste des fichiers du monde et un manifeste (hash, auteur, date) ; pull et push |
| `lock` | Crée le lock si absent, le met à jour régulièrement, le libère, juge s'il est mort |
| `backup` | Copie locale avant écrasement, garde les N dernières versions |
| `storage` | Interface unique : lire, écrire, lister, supprimer, **créer si absent** |

## Organisation du stockage

```
<bucket>/
└── worlds/<world_id>/
    ├── lock.json            # propriétaire, date de prise, dernier battement
    ├── manifest.json        # version courante : auteur, date, hash de chaque fichier
    ├── current/<fichiers>   # dernière version poussée
    └── history/<horodatage>/<fichiers>   # N versions précédentes
```

## Lock

États : **libre**, **tenu** (battement récent), **périmé** (battement trop ancien).

- Prise : écriture de `lock.json` avec « crée seulement s'il n'existe pas » (atomique sur R2).
- Battement : mise à jour de la date toutes les ~60 s tant que le jeu tourne.
- Périmé : le joueur suivant est prévenu (« lock de X depuis N min, forcer ? »). Forcer ne
  supprime aucune donnée ; la dernière version poussée reste la référence.
- Retour de l'hôte planté : son wrapper voit qu'un autre a repris le lock et **refuse de
  pousser** sans confirmation.
- `thc unlock` : libération manuelle.

## Synchro : règles

- Pull au lancement, backup local avant d'écraser.
- Push à la fermeture seulement si l'ensemble des fichiers du monde a changé
  (comparaison de hash avec le manifeste tiré au lancement).
- Avant le push : attendre que la date de modification des fichiers soit stable
  (même idée que Hearth : ~4 s sans changement, 60 s maximum).
- Le jeu qui plante n'empêche pas le push : le wrapper survit au jeu.
- Le wrapper qui meurt (coupure, kill) laisse un lock périmé, géré ci-dessus.

## Config joueur (TOML, hors git)

| Champ | Rôle |
|---|---|
| `player` | Nom du joueur |
| `game` | Profil à utiliser (`enshrouded`) |
| `save_dir` | Dossier de save sur cette machine (Windows ou Proton) |
| `world_id` | Identifiant du monde, par exemple le hex du slot Enshrouded |
| `storage.backend` | `local` ou `r2` |
| `storage.*` | Dossier local, ou endpoint, bucket, clés R2 |
| `backups.keep` | Nombre de versions gardées |
| `lock.stale_after_min` | Délai avant de considérer le lock mort |

## Profil Enshrouded (connu grâce au code de Hearth)

Pour un slot d'ID hex `H` : `H`, `H-1` à `H-9`, `H_info`, `H_info-1`…, `H-index`,
`H_info-index`. Il faut **tous** les copier (les fichiers `-index` pointent vers la
version numérotée à charger). Ne pas toucher au fichier des personnages, propre à chaque
joueur. Motif retenu : `<hex>*` dans le dossier de save.

## Risques et inconnues

- Interaction avec **Steam Cloud** (ordre pull / synchro Steam, chemin de save).
- Forme de `%command%` sous **Proton**, nom du processus, chemin de la save.
- Fuite de clés R2 : la config réelle et les logs sont dans `.gitignore`, jamais commités.
- Deux joueurs en solo en même temps : couvert par le lock (le second est refusé).
- Dépendance à uv et à Internet au premier lancement.