# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3"]
# ///
"""Test minimal : uv + dépendances + options de lancement Steam.

Options de lancement Steam (chemin complet de uv conseillé) :
    C:\\chemin\\uv.exe run C:\\chemin\\test_launch.py -- %command%
    (tester aussi sans le "--")

Le script écrit tout dans test_launch.log (à côté du script), lance la
commande du jeu reçue en arguments, attend sa fin et note la durée.
"""
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).with_name("test_launch.log")


def log(msg: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def main() -> int:
    log("=" * 60)
    log(f"python {sys.version.split()[0]} | {platform.platform()}")
    log(f"cwd = {os.getcwd()}")
    log(f"SteamAppId = {os.environ.get('SteamAppId')}")
    log(f"argv brut = {sys.argv[1:]!r}")

    # Teste que uv a bien installé la dépendance
    try:
        import boto3

        log(f"boto3 OK ({boto3.__version__})")
    except Exception as e:  # noqa: BLE001
        log(f"boto3 KO : {e!r}")

    # Retire un éventuel "--" en tête (selon comment uv/Steam le passent)
    cmd = sys.argv[1:]
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    log(f"commande jeu = {cmd!r}")

    if not cmd:
        log("aucune commande reçue -> rien à lancer")
        return 1

    t0 = time.time()
    try:
        proc = subprocess.Popen(cmd)
    except Exception as e:  # noqa: BLE001
        log(f"échec du lancement : {e!r}")
        return 1
    log(f"jeu lancé, pid={proc.pid}")

    code = proc.wait()
    log(f"jeu terminé, code={code}, durée={time.time() - t0:.0f}s")
    return code


if __name__ == "__main__":
    sys.exit(main())