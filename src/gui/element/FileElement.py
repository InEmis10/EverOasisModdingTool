from src.classe.FileTypes import GetFileType
from src.gui.element.TreeNode import TreeNode


class FileElement(TreeNode):
    """Un fichier de l'arbre (donnée seulement, affiché par TreeContainer).
    Couleur et icône selon son type (src/classe/FileTypes.py)."""
    __slots__ = ()

    @property
    def FileType(self):
        return GetFileType(self.Name)

    def GetTextColor(self):
        return self.FileType.Category.Color

    def GetIcon(self):
        """(nom de l'icône, couleur) dessinée à gauche du nom"""
        Category = self.FileType.Category
        return Category.Icon, Category.Color
