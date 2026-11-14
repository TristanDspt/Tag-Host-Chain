# thc/log.py

"""Journal de THC.

Écrit dans un fichier avec rotation (logs/thc.log) et recopie l'essentiel sur la
console. Règle d'or : on ne logge jamais de secret (clés R2, etc.).

Les autres modules n'ont rien à importer d'ici : ils font simplement
    log = logging.getLogger(__name__)
et leurs messages (« thc.config », « thc.sync »...) atterrissent ici, parce que
setup_logging() configure le logger parent « thc ».
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from thc.constants import LOG_BACKUP_COUNT, LOG_MAX_BYTES

ROOT_LOGGER_NAME = "thc"
LOG_FILE_NAME = "thc.log"

FILE_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
CONSOLE_FORMAT = "[THC] %(levelname)-7s %(message)s"


def default_log_dir() -> Path:
    """Dossier logs/ à la racine du repo, à côté de run.py.

    Calculé depuis l'emplacement de CE fichier, pas depuis le dossier courant :
    Steam lance le wrapper avec le dossier du jeu comme dossier courant.
    """
    return Path(__file__).resolve().parent.parent / "logs"


def setup_logging(log_dir: Path | None = None, verbose: bool = False) -> logging.Logger:
    """Configure le logger « thc » : un fichier tournant + la console.

    Le fichier garde tout (DEBUG). La console n'affiche que INFO et plus,
    sauf si verbose=True.
    """
    log_dir = log_dir or default_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # ne pas remonter au logger racine de Python
    logger.handlers.clear()  # si on est appelé deux fois, pas de messages en double

    file_handler = RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    logger.addHandler(console_handler)

    return logger