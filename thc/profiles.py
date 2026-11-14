# thc/profiles.py

"""Profils de jeu.

Un profil décrit ce qui est vrai pour tous les joueurs d'un jeu : quels fichiers
composent une save. Le reste de THC (sync, lock...) ne connaît aucun jeu : il
demande au profil.

Un profil ne dit PAS où se trouve la save : ça dépend de la machine (disque,
ID Steam, Windows ou Proton). C'est le `save_dir` de la config de chaque joueur.

Pour ajouter un jeu : créer un GameProfile et l'ajouter à PROFILES.
"""

from dataclasses import dataclass


class UnknownGameError(ValueError):
    """Le nom de jeu demandé n'a pas de profil."""


@dataclass(frozen=True)
class GameProfile:
    name: str
    # Motifs de fichiers (style glob) ; {slot} est remplacé par le numéro du slot de monde.
    pattern_templates: tuple[str, ...]

    def file_patterns(self, slot: int) -> list[str]:
        """Motifs des fichiers du monde au slot `slot`, à chercher dans le dossier de save."""
        if not isinstance(slot, int) or slot < 0:
            raise ValueError(
                f"slot invalide : {slot!r} (attendu : un entier >= 0, par exemple 0 "
                "pour world0.ksd)"
            )
        return [template.format(slot=slot) for template in self.pattern_templates]


# Enshrouded 1.0 : un monde = un seul fichier world<N>.ksd (N = numéro de slot).
# Jamais synchronisés : character<N>.ksd (personnages, propres à chaque joueur),
# user_settings.json (réglages) et le dossier backup/ du jeu (THC a ses propres
# backups). global.ksd : contenu inconnu, pas synchronisé pour l'instant (à examiner au J3).
ENSHROUDED = GameProfile(
    name="enshrouded",
    pattern_templates=("world{slot}.ksd",),
)

PROFILES: dict[str, GameProfile] = {profile.name: profile for profile in (ENSHROUDED,)}


def get_profile(name: str) -> GameProfile:
    """Renvoie le profil du jeu `name`, ou lève UnknownGameError avec la liste des jeux gérés."""
    try:
        return PROFILES[name.strip().lower()]
    except KeyError:
        known = ", ".join(sorted(PROFILES))
        raise UnknownGameError(f"Jeu inconnu : {name!r}. Jeux gérés : {known}.") from None