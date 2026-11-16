import os
from pathlib import Path
from pygame_easy_gui import Color3
from src.gui.Theme import Theme
from src.classe.FileTypes import ARCHIVE
from src.gui.element.TreeNode import TreeNode
from src.gui.element.FileElement import FileElement

# Au-delà de ce nombre d'enfants, fermer le dossier oublie ses enfants (relus à la prochaine ouverture)
UNLOAD_THRESHOLD = 2000


class FolderConfig:
    _Rules: dict[str, Color3] = {
        ".git": Color3(100, 200, 0),
    }

    @classmethod
    def AddSpecialFolder(cls, name, color=Color3(0, 0, 0)):
        cls._Rules[name] = color

    @classmethod
    def FindFolderRule(cls, name: str, default: Color3 = Theme.TREE_FOLDER_TEXT) -> Color3:
        return cls._Rules.get(name, default)


class FolderElement(TreeNode):
    """Un dossier de l'arbre (donnée seulement, affiché par TreeContainer).
    Ses enfants ne sont lus sur le disque qu'à la première ouverture."""
    __slots__ = ("Open", "Children")
    IsDir = True

    def __init__(self, path, depth: int = 0, parent: "FolderElement | None" = None):
        super().__init__(Path(path).expanduser().resolve() if parent is None else Path(path), depth, parent)
        self.Open = False
        self.Children: list[TreeNode] | None = None

    def GetTextColor(self):
        Rule = FolderConfig.FindFolderRule(self.Name, None)
        if Rule is not None:
            return Rule
        if self.Name.endswith("_x"):          # archive déjà ouverte par extract (ex: Area_central.gar_x)
            return ARCHIVE.Color
        return Theme.TREE_FOLDER_TEXT

    def GetChildren(self) -> list[TreeNode]:
        if self.Children is None:
            self.Children = self._ReadChildren()
        return self.Children

    def _ReadChildren(self) -> list[TreeNode]:
        try:
            # scandir récupère le type de chaque entrée en lisant le dossier : pas de stat() par fichier
            with os.scandir(self.Path) as it:
                entries = sorted(it, key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError:
            return []
        depth = self.Depth + 1
        return [
            (FolderElement if e.is_dir() else FileElement)(Path(e.path), depth, self)
            for e in entries
        ]

    def IterVisibleDescendants(self):
        """Descendants affichés quand ce dossier est ouvert, dans l'ordre de l'arbre"""
        for child in self.GetChildren():
            yield child
            if child.IsDir and child.Open:
                yield from child.IterVisibleDescendants()

    def Unload(self):
        """Oublie les enfants (libère la mémoire) : ils seront relus à la prochaine ouverture"""
        self.Children = None
        self.Open = False
