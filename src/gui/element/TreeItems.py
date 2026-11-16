import pygame
from pygame_easy_gui import TextButton, Udim2
from src.gui.Theme import Theme
from src.gui import Icons

ROW_HEIGHT = 22
INDENT = 14         # décalage par niveau de profondeur
LEFT_MARGIN = 6     # marge à gauche de la racine
ARROW_SPACE = 20    # colonne réservée à la flèche des dossiers (vide pour les fichiers : les noms restent alignés)
RIGHT_MARGIN = 4


class TreeItem(TextButton):
    """Une ligne de l'arbre. Réutilisée : TreeContainer lui fait afficher le nœud (TreeNode) visible à sa position."""

    def __init__(self, View):
        super().__init__()
        self.View = View
        self.Node = None
        self.Index = -1          # index de la ligne dans View.Rows (-1 = libre)

        # Propriétés publiques : les modifier redessine la ligne automatiquement
        self.Indent = 0          # x (relatif à la ligne) de la colonne de la flèche
        self.IsDir = False
        self.IsOpen = False
        self.Icon = None         # (nom, couleur) dessiné à la place de la flèche pour les fichiers

        self.Size = Udim2(1, 0, 0, ROW_HEIGHT)
        self.FontName = Theme.TREE_FONT
        self.TextSize = Theme.TREE_TEXT_SIZE
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.BackgroundColor3 = Theme.TREE_HOVER
        self.BackgroundTransparency = 1
        self.BorderSizePixel = 0
        self.AutoButtonColor = False

        self._Hovered = False
        self.MouseEnter.Connect(lambda: self._SetHovered(True))
        self.MouseLeave.Connect(lambda: self._SetHovered(False))
        self.MouseButton1Click.Connect(lambda: self.View._OnRowClicked(self))
        self.MouseButton2Click.Connect(lambda: self.View._OnRowRightClicked(self))

    def Bind(self, Node, Index : int):
        """Affiche Node à la ligne Index"""
        self.Node = Node
        self.Index = Index
        self.Position = Udim2(0, 0, 0, Index * ROW_HEIGHT)
        self.Text = Node.Name
        self.TextColor3 = Node.GetTextColor()
        self.Indent = LEFT_MARGIN + Node.Depth * INDENT
        self.IsDir = Node.IsDir
        self.IsOpen = Node.IsDir and Node.Open
        self.Icon = Node.GetIcon()
        self.Visible = True
        self.RefreshBackground()

    def Unbind(self):
        self.Node = None
        self.Index = -1
        self.Visible = False

    # Texte décalé de l'indentation + colonne de la flèche (remplace un UIPadding par ligne)
    def _GetTextArea(self) -> pygame.Rect:
        Rect = self.GetRect()
        Left = self.Indent + ARROW_SPACE
        return pygame.Rect(Rect.x + Left, Rect.y, max(0, Rect.width - Left - RIGHT_MARGIN), Rect.height)

    def _Draw(self, Surface):
        super()._Draw(Surface)
        Rect = self.GetRect()
        cx = Rect.left + self.Indent + ARROW_SPACE // 2 - 1
        cy = Rect.centery
        if not self.IsDir:
            if self.Icon is not None:
                Icons.Draw(Surface, self.Icon[0], cx, cy, self.Icon[1])
            return
        if self.IsOpen:   # ▾
            Points = [(cx - 4, cy - 2), (cx + 4, cy - 2), (cx, cy + 3)]
        else:             # ▸
            Points = [(cx - 2, cy - 4), (cx - 2, cy + 4), (cx + 3, cy)]
        pygame.draw.polygon(Surface, tuple(Theme.TREE_ARROW), Points)

    # Survol / sélection
    def _SetHovered(self, Value : bool):
        self._Hovered = Value
        self.RefreshBackground()

    def RefreshBackground(self):
        if self.Node is not None and self.Node is self.View.Selected:
            self.BackgroundColor3 = Theme.TREE_SELECTED
            self.BackgroundTransparency = 0
        elif self._Hovered:
            self.BackgroundColor3 = Theme.TREE_HOVER
            self.BackgroundTransparency = 0
        else:
            self.BackgroundTransparency = 1
