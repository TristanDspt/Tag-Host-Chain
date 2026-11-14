# Architecture (estimée)

> Version de cadrage. Elle bougera pendant J0 à J3, c'est normal.

## Principe

Un **wrapper** lancé par Steam qui entoure le jeu :

```
Steam ──► uv run run.py -- %command%
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
├── run.py                  # point d'entrée : main() enchaîne les étapes (uv run run.py -- %command%)
├── requirements.txt
├── README.md  ROADMAP.md  ARCHITECTURE.md  CLAUDE_CONTEXT.md
├── thc/
│   ├── cli.py              # lecture de la ligne de commande (sous-commandes unlock, restore... plus tard)
│   ├── config.py           # lecture de la config joueur (TOML)
│   ├── constants.py        # réglages du développeur (constantes)
│   ├── profiles.py         # profils de jeu (fichiers de la save), en Python
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
│   └── thc.example.toml    # modèle de config (la vraie config thc.toml n'est PAS dans git)
├── dev-storage/            # « bucket » local de développement (hors git)
├── logs/                   # journal de THC (hors git, créé au premier lancement)
├── tests/
│   └── fake_game.py        # faux jeu : modifie un faux world0.ksd puis se termine
└── tools/
    └── test_launch.py      # test de plomberie Steam + uv
```

## Modules

| Module | Responsabilité |
|---|---|
| `run.py` | Point d'entrée : démarre les logs, charge la config, enchaîne les étapes (lock, pull, jeu, push, unlock). Si une étape échoue, le jeu n'est pas lancé |
| `cli` | Lit la ligne de commande : options de THC avant le premier `--`, commande du jeu après |
| `constants` | Réglages du développeur : rotation des logs, backends gérés, dossier de stockage local ; plus tard nombre de versions gardées et délai de lock périmé |
| `log` | Journal `logs/thc.log` avec rotation, plus écho sur la console. Les modules font `logging.getLogger(__name__)` (`run.py` : `"thc.run"`, car son `__name__` vaut `__main__`) |
| `config` | Charge la config du joueur ; chemins absolus, jamais relatifs au dossier courant |
| `profiles` | Décrit un jeu : motifs des fichiers à synchroniser. Ne connaît pas le dossier de save (il vient de la config) |
| `runner` | Lance la commande du jeu, attend sa fin, puis la stabilité des fichiers de save |
| `sync` | Construit la liste des fichiers du monde et un manifeste (hash, auteur, date) ; pull et push |
| `lock` | Crée le lock si absent, le met à jour régulièrement, le libère, juge s'il est mort |
| `backup` | Copie locale avant écrasement, garde les N dernières versions |
| `storage` | Interface unique : lire, écrire, lister, supprimer, **créer si absent** |

## Organisation du stockage

La clé du monde est dérivée de la config : jeu + slot (par exemple `enshrouded-slot0`).

```
<bucket>/
└── worlds/<clé du monde>/
    ├── lock.json            # propriétaire, date de prise, dernier battement
    ├── manifest.json        # version courante : auteur, date, hash de chaque fichier
    ├── current/<fichiers>   # dernière version poussée (Enshrouded : world0.ksd)
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

## Démarrage et erreurs

1. Lecture de la ligne de commande (`cli`) : options de THC avant le premier `--`, commande du
   jeu après.
2. Démarrage des logs, **avant** la config : une config cassée est aussi dans le fichier.
3. Chargement et validation de la config (`ConfigError` avec un message pour le joueur).
4. (J3) Garde-fou : si la variable d'environnement `SteamAppId` existe et ne correspond pas au
   `steam_app_id` du profil, arrêt avant tout pull ou push.
5. Étapes de synchro et lancement du jeu (jalons suivants).

Toute erreur de THC (prévue ou non) est écrite dans les logs et donne le code de sortie 1 ; le
jeu n'est **pas** lancé, pour ne pas jouer sur une save périmée.

## Synchro : règles

- Pull au lancement, backup local avant d'écraser.
- Push à la fermeture seulement si le **contenu** des fichiers du monde a changé
  (comparaison de hash avec le manifeste tiré au lancement). Jamais la date de modification :
  le jeu réécrit ses fichiers à chaque fermeture, même sans changement réel.
- Avant le push : attendre que la date de modification des fichiers soit stable
  (même idée que Hearth : ~4 s sans changement, 60 s maximum). Ici la date sert à détecter
  que le jeu a fini d'écrire, pas à décider s'il faut pousser.
- Le jeu qui plante n'empêche pas le push : le wrapper survit au jeu.
- Le wrapper qui meurt (coupure, kill) laisse un lock périmé, géré ci-dessus.

## Config joueur (TOML, hors git)

| Champ | Rôle |
|---|---|
| `player` | Nom du joueur |
| `game` | Profil à utiliser (`enshrouded`) |
| `save_dir` | Dossier de save sur cette machine (Windows ou Proton). Chemin absolu (`~` accepté), dossier existant. **Obligatoire**, aucun défaut |
| `slot` | Numéro du slot de monde (entier, `0` pour `world0.ksd`) ; la clé de stockage en est dérivée |
| `storage.backend` | `local` (développement : dossier `dev-storage/`) ou `r2` |
| `storage.r2.*` | (jalon J5) endpoint, bucket, clés d'accès du joueur : secrets, jamais dans git |

**Règle** : les réglages du **joueur** sont dans `config/thc.toml` (hors git) ; les réglages du
**développeur** sont des constantes dans `thc/constants.py` (rotation des logs, backends gérés,
dossier de stockage local `dev-storage/` ; à venir : nombre de versions gardées = 5, délai avant
lock périmé = 10 min, provisoire). Les autres modules les prennent comme valeurs par défaut de
leurs paramètres ; les tests passent des valeurs courtes en paramètre. Pas de réglage de backups,
de lock ni de dossier de logs dans la config du joueur : les logs vont toujours dans `logs/` à
côté de `run.py`.

## Profil Enshrouded (format 1.0, vérifié sur la machine de référence)

- Un monde = un seul fichier `world<N>.ksd` (N = numéro de slot, `0` à `9` d'après les guides
  d'hébergeurs). Les trois joueurs utilisent `world0`. Motif : `world{slot}.ksd`.
- **Seul ce fichier est synchronisé.** Restent locaux : `character<N>.ksd` (personnages),
  `global.ksd` (contenu inconnu, à examiner au J3), `user_settings.json` (réglages) et le
  dossier `backup/` du jeu (dix copies tournantes `*.backup-0` à `-9`). THC a ses propres
  backups.
- Emplacement sur la machine de référence : `<disque>:\Steam\userdata\<ID>\1203620\remote`, avec Steam Cloud
  coupé. Pas de dossier `Saved Games`. Le chemin change d'une machine à l'autre : d'où
  `save_dir` obligatoire.
- L'ancien format (Early Access : fichiers `<hex>`, `<hex>-1`…, `-index`, décrit par le code de
  Hearth) n'est plus d'actualité.

## Risques et inconnues

- Interaction avec **Steam Cloud** : il doit rester coupé chez les trois, sinon deux écrivains
  sur le même dossier. À vérifier chez les frères.
- **Format de save** : changé avec la 1.0 (octobre 2026), il peut changer encore. Revérifier
  le profil après les grosses mises à jour du jeu.
- Forme de `%command%` sous **Proton**, nom du processus, chemin de la save sous Linux
  (hypothèse : `userdata` dans l'installation Steam native, à vérifier).
- Fuite de clés R2 : la config réelle et les logs sont dans `.gitignore`, jamais commités.
- Deux joueurs en solo en même temps : couvert par le lock (le second est refusé).
- Dépendance à uv et à Internet au premier lancement.