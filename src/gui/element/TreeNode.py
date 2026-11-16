from pathlib import Path
from pygame_easy_gui import Color3


class TreeNode:
    """Une entrée de l'arbre (dossier ou fichier) : simple donnée, aucun widget.

    L'affichage est fait par TreeContainer, qui ne crée des widgets (TreeItem) que pour les lignes visibles.
    __slots__ : pas de __dict__ par nœud, ~10x plus léger qu'un widget.
    """
    __slots__ = ("Path", "Name", "Depth", "Parent")
    IsDir = False

    def __init__(self, path: Path, depth: int, parent: "TreeNode | None" = None):
        self.Path = path
        self.Name = path.name or str(path)
        self.Depth = depth
        self.Parent = parent

    def GetTextColor(self) -> Color3:
        raise NotImplementedError

    def GetIcon(self) -> tuple[str, Color3] | None:
        """(nom de l'icône de src.gui.Icons, couleur), ou None : rien à gauche du nom"""
        return None

    def __repr__(self):
        return f"{type(self).__name__}({self.Path})"
