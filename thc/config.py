# thc/config.py

"""Chargement de la config du joueur (config/thc.toml).

Lit le fichier TOML, vérifie chaque champ et renvoie un objet Config prêt à
l'emploi. Toute erreur (fichier absent, champ manquant, mauvais type, chemin
relatif...) lève ConfigError avec un message écrit pour le joueur.

Les erreurs de config sont des exceptions (ConfigError) que cli.py affiche et
écrit dans les logs.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from thc.constants import SUPPORTED_BACKENDS
from thc.profiles import UnknownGameError, get_profile

_TYPE_NAMES = {str: "du texte", int: "un nombre entier", dict: "une section"}


class ConfigError(Exception):
    """Config absente ou invalide. Le message s'adresse au joueur."""


@dataclass(frozen=True)
class StorageConfig:
    backend: str


@dataclass(frozen=True)
class Config:
    player: str
    game: str
    save_dir: Path
    slot: int
    storage: StorageConfig


def default_config_path() -> Path:
    """config/thc.toml à la racine du repo, indépendamment du dossier courant."""
    return Path(__file__).resolve().parent.parent / "config" / "thc.toml"


def load_config(path: Path | None = None) -> Config:
    """Lit et valide la config. `path` sert aux tests ou à une option --config."""
    path = path or default_config_path()
    data = _read_toml(path)
    try:
        return _build_config(data)
    except ConfigError as err:
        raise ConfigError(f"Config invalide ({path}) : {err}") from None


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except FileNotFoundError:
        example = path.with_name("thc.example.toml")
        raise ConfigError(
            f"Fichier de config introuvable : {path}\n"
            f"Copie {example} en {path.name} puis adapte-le (au minimum save_dir)."
        ) from None
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"Fichier de config illisible ({path}) : {err}") from None


def _build_config(data: dict[str, Any]) -> Config:
    player = _get(data, "player", str).strip()
    if not player:
        raise ConfigError("« player » ne peut pas être vide")

    game = _get(data, "game", str)
    slot = _get(data, "slot", int)
    try:
        profile = get_profile(game)
        profile.file_patterns(slot)  # on ne garde pas le résultat : c'est juste la validation du slot
    except (UnknownGameError, ValueError) as err:
        raise ConfigError(str(err)) from None

    save_dir = _get_path(data, "save_dir")
    if not save_dir.is_dir():
        raise ConfigError(
            f"le dossier « save_dir » n'existe pas : {save_dir}\n"
            "Vérifie le chemin dans ta config."
        )

    storage_table = _get(data, "storage", dict)
    backend = _get(storage_table, "backend", str, section="storage")
    if backend not in SUPPORTED_BACKENDS:
        raise ConfigError(
            f"« storage.backend » vaut {backend!r} ; valeurs gérées : "
            f"{', '.join(SUPPORTED_BACKENDS)}"
        )
    return Config(
        player=player,
        game=game,
        save_dir=save_dir,
        slot=slot,
        storage=StorageConfig(backend=backend),
    )


def _label(section: str, key: str) -> str:
    return f"{section}.{key}" if section else key


def _get(table: dict[str, Any], key: str, expected: type, *, section: str = "") -> Any:
    """Lit `key` dans `table` (obligatoire) et vérifie son type."""
    label = _label(section, key)
    if key not in table:
        raise ConfigError(f"champ « {label} » manquant")
    value = table[key]
    # bool est un sous-type de int en Python : on refuse `slot = true`
    wrong_type = not isinstance(value, expected) or (expected is int and isinstance(value, bool))
    if wrong_type:
        raise ConfigError(f"« {label} » doit être {_TYPE_NAMES[expected]} (reçu : {value!r})")
    return value


def _to_absolute_path(raw: str, label: str) -> Path:
    path = Path(raw).expanduser()  # développe ~ en dossier utilisateur
    if not path.is_absolute():
        raise ConfigError(f"« {label} » doit être un chemin absolu (reçu : {raw!r})")
    return path


def _get_path(table: dict[str, Any], key: str) -> Path:
    return _to_absolute_path(_get(table, key, str), key)