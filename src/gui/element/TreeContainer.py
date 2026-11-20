import math
import os
from pathlib import Path
from pygame_easy_gui import ScrollingFrame, Signal, Udim2, Vector2
from src.gui.element.FolderElement import FolderElement, UNLOAD_THRESHOLD
from src.gui.element.FileElement import FileElement
from src.gui.element.TreeItems import TreeItem, ROW_HEIGHT

BOTTOM_MARGIN = 4
SEARCH_LIMIT = 2000   # nombre max de résultats affichés (le compte total reste exact)


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
        self.SearchExited = Signal()      # () Reveal a quitté la recherche : le champ de recherche doit se vider
        self.ScrollingDirection = "y"
        self.ScrollStep = ROW_HEIGHT * 3
        self.ScrollBarThickness = 6
        self.CanvasSize = Udim2(0, 0, 0, 0)
        self._ViewHeight = -1

        # Recherche : Rows affiche alors les résultats, l'arbre normal est mis de côté dans _TreeRows
        self.Query = ""
        self.ResultCount = 0
        self._TreeRows: list | None = None
        self._TreeScroll = Vector2(0, 0)
        self._Index: list[tuple[str, str, str, bool]] | None = None   # (nom, chemin relatif) en minuscules, chemin relatif, dossier ?

    @property
    def Searching(self) -> bool:
        return self._TreeRows is not None

    # Projet
    def SetRoot(self, path) -> FolderElement:
        self.Root = FolderElement(path)
        self.Rows = [self.Root]
        self.Selected = None
        self.Query = ""
        self._TreeRows = None
        self._Index = None
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
        self._Index = None   # le disque a changé : l'index de recherche sera reconstruit
        if self.Searching:   # Toggle travaille sur l'arbre : on le remet en place le temps du rechargement
            query = self.Query
            self.SetFilter("")
            self.Reload(path)
            self.SetFilter(query)
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

    # Recherche
    def _BuildIndex(self):
        """Liste tous les fichiers et dossiers sous la racine (~0,1 s pour 50 000 entrées)"""
        root = str(self.Root.Path)
        prefix = len(root) + 1
        entries, stack = [], [root]
        while stack:
            try:
                it = os.scandir(stack.pop())
            except OSError:
                continue
            with it:
                for e in it:
                    try:
                        is_dir = e.is_dir(follow_symlinks=False)
                    except OSError:
                        is_dir = False
                    rel = e.path[prefix:]
                    entries.append((e.name.lower(), rel.lower(), rel, is_dir))
                    if is_dir:
                        stack.append(e.path)
        entries.sort(key=lambda entry: entry[1])
        self._Index = entries

    def SetFilter(self, query: str):
        """Affiche les fichiers et dossiers dont le nom contient chaque mot de query ("" = retour à l'arbre).
        Un mot contenant "/" est cherché dans le chemin relatif (ex : "database.gar_x/ bdb")."""
        if self.Root is None:
            return
        self.Query = query = query.strip()
        if not query:
            if self.Searching:
                self.Rows = self._TreeRows
                self._TreeRows = None
                self._OnRowsChanged()
                self.CanvasPosition = self._TreeScroll
            self.ResultCount = 0
            return
        if not self.Searching:
            self._TreeRows = self.Rows
            self._TreeScroll = self.CanvasPosition   # Vector2 immuable : pas besoin de copie
        if self._Index is None:
            self._BuildIndex()

        lowered = query.lower()
        terms = lowered.split()
        name_terms = [t for t in terms if "/" not in t]
        path_terms = [t for t in terms if "/" in t]
        matches = [entry for entry in self._Index
                   if all(t in entry[0] for t in name_terms) and all(t in entry[1] for t in path_terms)]
        # le nom exact d'abord, puis les noms qui commencent par la recherche, puis le reste (ordre du chemin)
        first = name_terms[0] if name_terms else ""
        matches.sort(key=lambda entry: (entry[0] != lowered, not entry[0].startswith(first)))

        self.ResultCount = len(matches)
        root = self.Root.Path
        rows = []
        for _, _, rel, is_dir in matches[:SEARCH_LIMIT]:
            node = (FolderElement if is_dir else FileElement)(root / rel, 0, self.Root)
            node.Name = rel   # chemin relatif affiché : on voit d'où vient le fichier
            rows.append(node)
        self.Rows = rows
        self._OnRowsChanged()
        self.CanvasPosition = Vector2(0, 0)

    def Reveal(self, path: Path):
        """Quitte la recherche, ouvre les dossiers jusqu'à path, le sélectionne et défile jusqu'à lui"""
        if self.Root is None or not path.is_relative_to(self.Root.Path):
            return
        if self.Searching:
            self.SetFilter("")
            self.SearchExited.Fire()
        node = self.Root
        if not node.Open:
            self.Toggle(node)
        for part in path.relative_to(self.Root.Path).parts:
            child = next((c for c in node.GetChildren() if c.Name == part), None)
            if child is None:
                break
            node = child
            if node.IsDir and not node.Open:
                self.Toggle(node)
        self.Select(node)
        index = self.Rows.index(node)
        self.CanvasPosition = Vector2(0, max(0, index * ROW_HEIGHT - self.GetAbsSize().y // 3))

    def _OnRowClicked(self, row: TreeItem):
        node = row.Node
        if node is None:
            return
        if self.Searching and node.IsDir:   # dans les résultats, un dossier s'ouvre dans l'arbre
            self.Reveal(node.Path)
            self.NodeActivated.Fire(self.Selected)
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
