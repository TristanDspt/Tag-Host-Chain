# thc/constants.py

"""Réglages du développeur.

Les valeurs qu'on peut vouloir changer en tant que dev, regroupées ici. Ce ne sont
pas des réglages de joueur (ceux-là sont dans config/thc.toml).

Les autres modules les importent, souvent comme valeurs par défaut de leurs
paramètres ; les tests passent des valeurs courtes en paramètre.

Ici seulement ce qu'on peut vouloir ajuster. Les détails internes (nom du logger,
messages d'erreur...) restent dans le fichier qui s'en sert.
"""

from pathlib import Path

# Logs (thc/log.py)
LOG_MAX_BYTES = 1_000_000  # taille max d'un fichier de log avant rotation (~1 Mo)
LOG_BACKUP_COUNT = 5  # anciens fichiers gardés : thc.log.1 ... thc.log.5

# Config (thc/config.py)
SUPPORTED_BACKENDS = ("local",)  # "r2" arrivera au jalon J5

# Stockage (backend « local », thc/storage/local.py)
# Dossier qui joue le rôle de « bucket » pendant le développement : à la racine du
# repo, et dans le .gitignore. Les tests passent leur propre dossier en paramètre.
LOCAL_STORAGE_DIR = Path(__file__).resolve().parent.parent / "dev-storage"