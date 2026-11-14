# thc/cli.py

"""Lecture de la ligne de commande de THC.

Usage (options de lancement Steam) :
    uv run run.py [options] -- %command%

Tout ce qui suit le premier « -- » est la commande du jeu ; avant le « -- », les
options de THC. Ce module ne fait que lire la ligne de commande : l'enchaînement
des étapes est dans run.py.
"""

import argparse
from pathlib import Path


def split_command(argv: list[str]) -> tuple[list[str], list[str]]:
    """Sépare les options de THC de la commande du jeu, au premier « -- »."""
    if "--" not in argv:
        return argv, []
    index = argv.index("--")
    return argv[:index], argv[index + 1 :]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        usage="run.py [options] -- <commande du jeu>",
        description="Tag Host Chain : synchronise la save d'un jeu coop entre amis "
        "autour du lancement du jeu.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="chemin du fichier de config (défaut : config/thc.toml)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="affiche aussi les messages de détail sur la console",
    )
    return parser


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    """Lit la ligne de commande. Renvoie (options de THC, commande du jeu)."""
    options, command = split_command(argv)
    return build_parser().parse_args(options), command