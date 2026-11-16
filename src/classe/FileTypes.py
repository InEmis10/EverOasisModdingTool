"""Types de fichiers d'Ever Oasis : catégorie, couleur et icône de chaque extension.

Source : EverOasisMods/extension.md. Pour ajouter un type : une ligne dans EXTENSIONS (ou NAMES).
"""
from dataclasses import dataclass
from pathlib import Path
from pygame_easy_gui import Color3


@dataclass(frozen=True)
class Category:
    Id: str
    Label: str
    Color: Color3
    Icon: str        # nom de l'icône dessinée par src.gui.Icons


ARCHIVE   = Category("archive",   "Archive",            Color3(230, 170, 70),  "archive")
TEXTURE   = Category("texture",   "Image / texture",    Color3(120, 200, 120), "image")
MODEL     = Category("model",     "Modèle 3D",          Color3(100, 190, 225), "cube")
ANIMATION = Category("animation", "Animation",          Color3(190, 145, 235), "film")
SCRIPT    = Category("script",    "Script",             Color3(230, 210, 100), "code")
CODE      = Category("code",      "Code exécutable",    Color3(235, 110, 100), "chip")
TEXT      = Category("text",      "Texte",              Color3(150, 180, 245), "text")
AUDIO     = Category("audio",     "Son / musique",      Color3(235, 130, 185), "note")
DATA      = Category("data",      "Données de jeu",     Color3(110, 205, 185), "table")
UI        = Category("ui",        "Interface",          Color3(215, 175, 135), "window")
EFFECT    = Category("effect",    "Effet / shader",     Color3(245, 150, 90),  "spark")
META      = Category("meta",      "Métadonnées",        Color3(140, 142, 148), "doc")
OTHER     = Category("other",     "Fichier",            Color3(180, 182, 186), "doc")


@dataclass(frozen=True)
class FileType:
    Category: Category
    Description: str


def _T(category, description):
    return FileType(category, description)


# Extension (sans le point, en minuscules) -> type
EXTENSIONS: dict[str, FileType] = {
    # Archives
    "gar":   _T(ARCHIVE, "Archive Grezzo (regroupe les autres fichiers)"),
    "zar":   _T(ARCHIVE, "Archive Grezzo (ancienne version)"),
    "lzs":   _T(ARCHIVE, "Données compressées LzS"),
    # Textes
    "gmsg":  _T(TEXT, "Textes du jeu pour une langue"),
    "gzf":   _T(TEXT, "Police d'écriture"),
    # Son
    "bcsar": _T(AUDIO, "Archive sonore (effets, instruments)"),
    "bcstm": _T(AUDIO, "Musique en streaming"),
    # Effets / shaders
    "shbin": _T(EFFECT, "Shaders compilés"),
    "ptcl":  _T(EFFECT, "Effets de particules"),
    # Données de jeu
    "acb":   _T(DATA, "Configuration (paramètres à clés)"),
    "bdb":   _T(DATA, "Base de données"),
    "vlb":   _T(DATA, "Disposition d'une carte"),
    "rteb":  _T(DATA, "Routes des PNJ et objets mobiles"),
    "cidb":  _T(DATA, "Collisions"),
    "btb":   _T(DATA, "Arbre de comportement de l'IA"),
    "colb":  _T(DATA, "Palettes du ciel et des nuages"),
    # Scripts
    "gsb":   _T(SCRIPT, "Script compilé (Squirrel)"),
    "nut":   _T(SCRIPT, "Script Squirrel décompilé"),
    "gsa":   _T(SCRIPT, "Script en assembleur éditable"),
    # Graphismes
    "cmb":   _T(MODEL, "Modèle 3D (maillages, matériaux, squelette)"),
    "cmtb":  _T(MODEL, "Table de matériaux"),
    "ctxb":  _T(TEXTURE, "Texture"),
    "cstb":  _T(TEXTURE, "Vignettes et modèles précalculés"),
    # Animations
    "csab":  _T(ANIMATION, "Animation de squelette"),
    "cmab":  _T(ANIMATION, "Animation de matériau"),
    "ccb":   _T(ANIMATION, "Animation de caméra"),
    "tlab":  _T(ANIMATION, "Timeline d'animation"),
    "icab":  _T(ANIMATION, "Animation d'interface"),
    # Interface
    "ibb":   _T(UI, "Mise en page d'un écran d'interface"),
    "itpb":  _T(UI, "Changement d'image dans l'interface"),
    "amb":   _T(UI, "Masque de forme"),
    # Divers
    "json":  _T(META, "JSON"),
}

# Nom exact du fichier -> type (prioritaire sur l'extension)
NAMES: dict[str, FileType] = {
    "code.bin":        _T(CODE, "Code exécutable du jeu (moteur)"),
    "exh.bin":         _T(CODE, "Exheader (infos d'exécution)"),
    "ncchheader.bin":  _T(META, "En-tête NCCH"),
    "icon.icn":        _T(TEXTURE, "Icône et titre du menu 3DS"),
    "banner.bnr":      _T(TEXTURE, "Bannière animée du menu 3DS"),
    "_manifest.json":  _T(META, "Manifeste de l'archive extraite"),
    "_gar_header.bin": _T(META, "En-tête de l'archive extraite"),
    "workspace.json":  _T(META, "Configuration de la workspace"),
    "mod.json":        _T(META, "Description du mod"),
}

UNKNOWN = FileType(OTHER, "Fichier")


def GetFileType(path: Path | str) -> FileType:
    name = Path(path).name.lower()
    found = NAMES.get(name)
    if found is not None:
        return found
    _, dot, ext = name.rpartition(".")
    return EXTENSIONS.get(ext, UNKNOWN) if dot else UNKNOWN
