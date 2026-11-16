import math
from pygame_easy_gui import ScrollingFrame, Signal, Udim2, Vector2
from src.gui.element.FolderElement import FolderElement, UNLOAD_THRESHOLD
from src.gui.element.TreeItems import TreeItem, ROW_HEIGHT

BOTTOM_MARGIN = 4


class TreeContainer(ScrollingFrame):
    """Arbre de fichiers virtualisé.

    - Rows : liste plate des nœuds visibles (TreeNode), dans l'ordre d'affichage. Simples données.
    - _Pool : juste assez de TreeItem (widgets) pour remplir la hauteur visible.
      La ligne d'index i est affichée par _Pool[i % len(_Pool)] : en défilant d'une ligne,
      un seul widget change de contenu.
    Le coût ne dépend donc pas du nombre de fichiers, seulement de la hauteur de la SideBar.
    """

    def __init__(self):
        self._Pool: list[TreeItem] = []   # avant super().__init__ : le setter de CanvasPosition l'utilise
        self.Rows: list = []
        super().__init__()
        self.Root: FolderElement | None = None
        self.Selected = None              # nœud sélectionné
        self.NodeActivated = Signal()     # (TreeNode) clic gauche sur une ligne (ex: ouvrir un fichier)
        self.NodeContextMenu = Signal()   # (TreeNode) clic droit sur une ligne (menu contextuel)
        self.ScrollingDirection = "y"
        self.ScrollStep = ROW_HEIGHT * 3
        self.ScrollBarThickness = 6
        self.CanvasSize = Udim2(0, 0, 0, 0)
        self._ViewHeight = -1

    # Projet
    def SetRoot(self, path) -> FolderElement:
        self.Root = FolderElement(path)
        self.Rows = [self.Root]
        self.Selected = None
        self.CanvasPosition = Vector2(0, 0)
        self.Toggle(self.Root)   # projet ouvert d'emblée
        return self.Root

    def Clear(self):
        self.Root = None
        self.Rows = []
        self.Selected = None
        self._OnRowsChanged()

    # Ouverture / fermeture
    def Toggle(self, node: FolderElement):
        Index = self.Rows.index(node)
        if node.Open:
            End = Index + 1
            while End < len(self.Rows) and self.Rows[End].Depth > node.Depth:
                End += 1
            del self.Rows[Index + 1:End]
            node.Open = False
            if node.Children is not None and len(node.Children) > UNLOAD_THRESHOLD:
                node.Unload()
        else:
            node.Open = True
            self.Rows[Index + 1:Index + 1] = node.IterVisibleDescendants()
        self._OnRowsChanged()

    def Reload(self, path):
        """Relit sur le disque le dossier chargé le plus profond qui contient path
        (ex: après une extraction, pour faire apparaître le nouveau fichier)"""
        node = self.Root
        if node is None or not path.is_relative_to(node.Path):
            return
        for part in path.relative_to(node.Path).parts:
            if node.Children is None:
                break
            child = next((c for c in node.Children if c.IsDir and c.Name == part), None)
            if child is None:
                break
            node = child
        if node.Children is None:
            return   # jamais ouvert : sera lu à la première ouverture
        WasOpen = node.Open
        if WasOpen:
            self.Toggle(node)
        node.Unload()
        if WasOpen:
            self.Toggle(node)

    def _OnRowClicked(self, row: TreeItem):
        node = row.Node
        if node is None:
            return
        self.Select(node)
        if node.IsDir:
            self.Toggle(node)
        self.NodeActivated.Fire(node)

    def _OnRowRightClicked(self, row: TreeItem):
        if row.Node is None:
            return
        self.Select(row.Node)
        self.NodeContextMenu.Fire(row.Node)

    def Select(self, node):
        self.Selected = node
        for row in self._Pool:
            row.RefreshBackground()

    # Virtualisation
    def _OnRowsChanged(self):
        """La liste des lignes a changé (ouverture, fermeture…) : tout est réaffecté"""
        self.CanvasSize = Udim2(0, 0, 0, len(self.Rows) * ROW_HEIGHT + BOTTOM_MARGIN)
        for row in self._Pool:
            row.Index = -1
        self._RefreshRows()

    def _EnsurePool(self):
        Height = self.GetAbsSize().y
        if Height == self._ViewHeight:
            return
        self._ViewHeight = Height
        Needed = max(1, math.ceil(Height / ROW_HEIGHT) + 1)
        if Needed == len(self._Pool):
            return
        # Le modulo change avec la taille du pool : toutes les lignes sont réaffectées
        while len(self._Pool) < Needed:
            row = TreeItem(self)
            row.Visible = False
            self.AddChild(row)
            self._Pool.append(row)
        while len(self._Pool) > Needed:
            self._Pool.pop().Destroy()
        for row in self._Pool:
            row.Index = -1

    def _RefreshRows(self):
        if not self._Pool and self._ViewHeight < 0:
            self._EnsurePool()
        Count = len(self._Pool)
        if Count == 0:
            return
        First = int(self._GetClampedCanvasPosition().y // ROW_HEIGHT)
        for Index in range(First, First + Count):
            row = self._Pool[Index % Count]
            if Index < len(self.Rows):
                if row.Index != Index:
                    row.Bind(self.Rows[Index], Index)
            elif row.Index != -1 or row.Visible:
                row.Unbind()

    @ScrollingFrame.CanvasPosition.setter
    def CanvasPosition(self, Value):
        ScrollingFrame.CanvasPosition.fset(self, Value)
        if self._Pool:
            self._RefreshRows()

    def _Update(self, Dt: float):
        # La hauteur visible peut changer (fenêtre redimensionnée) : adapte le nombre de lignes
        if self.GetAbsSize().y != self._ViewHeight:
            self._EnsurePool()
            self._RefreshRows()
