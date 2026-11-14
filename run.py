# run.py

"""Point d'entrée de THC : uv run run.py [options] -- %command%

main() enchaîne les étapes. Pour l'instant (jalon J0), THC démarre les logs,
charge la config et note ce qu'il ferait : il ne lance rien et ne synchronise rien.

Si THC échoue (config cassée, plus tard lock pris par un autre...), le jeu n'est
PAS lancé : jouer sans avoir récupéré la dernière save risquerait d'écraser le
monde partagé au prochain push.
"""

import logging
import sys

from thc.cli import parse_args
from thc.config import ConfigError, load_config
from thc.log import setup_logging

EXIT_OK = 0
EXIT_ERROR = 1

# Nom écrit en dur : ici __name__ vaudrait "__main__", hors de la famille « thc »
# configurée par setup_logging(), et les messages ne finiraient pas dans le fichier.
log = logging.getLogger("thc.run")


def main(argv: list[str] | None = None) -> int:
    """Enchaîne les étapes. Renvoie le code de sortie du programme."""
    argv = sys.argv[1:] if argv is None else argv
    args, command = parse_args(argv)

    setup_logging(verbose=args.verbose)

    try:
        if not command:
            log.error("Aucune commande de jeu. Usage : run.py [options] -- <commande du jeu>")
            return EXIT_ERROR

        config = load_config(args.config)
        log.info(
            "Config chargée : joueur=%s, jeu=%s, slot=%d, stockage=%s",
            config.player,
            config.game,
            config.slot,
            config.storage.backend,
        )
        log.debug("save_dir=%s", config.save_dir)
        log.info("Commande du jeu : %s", command)
        log.info("Squelette J0 : rien n'est lancé ni synchronisé pour l'instant.")
        return EXIT_OK
    except ConfigError as err:
        log.error("%s", err)
    except Exception:  # dernier filet : une erreur imprévue doit finir dans les logs
        log.exception("Erreur inattendue")
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())