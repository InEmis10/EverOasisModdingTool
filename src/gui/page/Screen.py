from pathlib import Path
import pygame
from pygame_easy_gui import Frame, TextLabel, Udim2, Signal
from pygame_easy_gui import UserInputService, UserInputType, KeyCode
from src.gui.element.TreeContainer import TreeContainer, SEARCH_LIMIT
from src.gui.element.SearchBar import SearchBar, SEARCH_HEIGHT
from src.gui.element.TabBar import TabBar, TAB_HEIGHT
from src.gui.element.FileView import CreateView
from src.gui.element.Splitter import Splitter, HANDLE_WIDTH
from src.gui.Theme import Theme

SIDEBAR_WIDTH = 220
SIDEBAR_MIN_WIDTH = 120
CONTENT_MIN_WIDTH = 200   # place minimale laissée aux onglets / à la vue

_LastSideBarWidth = SIDEBAR_WIDTH   # les nouveaux écrans reprennent la dernière largeur choisie


class Screen(Frame):
    """Un écran (comme un bureau Windows) : arbre de fichiers depuis Root, onglets et vue des fichiers ouverts."""

    def __init__(self, root: Path, title: str, closable: bool):
        super().__init__()
        self.Name = f"Screen:{title}"
        self.Title = title
        self.Closable = closable
        self.Size = Udim2(1, 0, 1, 0)
        self.BackgroundColor3 = Theme.BACKGROUND
        self.ContextMenuRequested = Signal()
        self.Views: dict[Path, Frame] = {}

        self.SideBar = TreeContainer()
        self.SideBar.Name = "SideBar"
        self.SideBar.BackgroundColor3 = Theme.SIDEBAR
        self.SideBar.BorderColor3 = Theme.BORDER
        self.SideBar.BorderSizePixel = 1
        self.AddChild(self.SideBar)

        self.Search = SearchBar()
        self.Search.QueryChanged.Connect(self._OnQueryChanged)
        self.Search.Submitted.Connect(self._OpenFirstResult)
        self.AddChild(self.Search)

        self.Tabs = TabBar()
        self.AddChild(self.Tabs)

        self.Content = Frame()
        self.Content.Name = "Content"
        self.Content.BackgroundColor3 = Theme.BACKGROUND
        self.AddChild(self.Content)

        # ajoutée en dernier : au-dessus de la bordure de l'arbre et des onglets
        self.Resizer = Splitter()
        self.Resizer.Moved.Connect(lambda x: self.SetSideBarWidth(x - self.GetRect().left))
        self.AddChild(self.Resizer)

        self.SideBarWidth = 0
        self.SetSideBarWidth(_LastSideBarWidth)

        self.Empty = TextLabel()
        self.Empty.Size = Udim2(1, 0, 1, 0)
        self.Empty.BackgroundTransparency = 1
        self.Empty.FontName = Theme.TREE_FONT
        self.Empty.TextSize = 14
        self.Empty.TextColor3 = Theme.TREE_ARROW
        self.Empty.Text = "Aucun fichier ouvert : clic gauche sur un fichier pour l'ouvrir"
        self.Content.AddChild(self.Empty)

        self.SideBar.SetRoot(root)
        self.SideBar.NodeActivated.Connect(self._OnNodeActivated)
        self.SideBar.NodeContextMenu.Connect(self.ContextMenuRequested.Fire)
        self.SideBar.SearchExited.Connect(self.Search.Clear)
        self.Tabs.TabActivated.Connect(self._ShowView)
        self.Tabs.TabClosed.Connect(self._DestroyView)
        self._KeyConnection = UserInputService.InputBegan.Connect(self._OnInputBegan)

    def Destroy(self):
        self._KeyConnection.Disconnect()   # signal global : sinon l'écran fermé réagirait encore à Ctrl+F
        super().Destroy()

    # Recherche
    def _OnInputBegan(self, Input, _GameProcessed):
        """Ctrl+F : focus sur la recherche si la souris est sur la side bar (ou si on y est déjà)"""
        if (Input.UserInputType != UserInputType.Keyboard or Input.KeyCode != KeyCode.F
                or not Input.IsModifierDown(pygame.KMOD_CTRL) or not self.Visible):
            return
        side = self.Search.GetRect().union(self.SideBar.GetRect())
        if side.collidepoint(UserInputService.GetMouseLocation()) or self.Search.IsFocused():
            self.Search.Focus()

    def _OnQueryChanged(self, query: str):
        self.SideBar.SetFilter(query)
        self.Search.SetCount(self.SideBar.ResultCount if self.SideBar.Searching else None, SEARCH_LIMIT)

    def _OpenFirstResult(self):
        """Entrée dans la recherche : ouvre le premier résultat (fichier) ou le montre dans l'arbre (dossier)"""
        if not self.SideBar.Searching or not self.SideBar.Rows:
            return
        node = self.SideBar.Rows[0]
        if node.IsDir:
            self.SideBar.Reveal(node.Path)
        else:
            self.SideBar.Select(node)
            self.OpenFile(node.Path)

    def SetSideBarWidth(self, width: int):
        """Largeur de l'arbre de fichiers : les onglets et la vue prennent le reste."""
        global _LastSideBarWidth
        screen_width = self.GetRect().width
        maximum = screen_width - CONTENT_MIN_WIDTH if screen_width > 0 else width
        width = int(max(SIDEBAR_MIN_WIDTH, min(width, maximum)))
        if width == self.SideBarWidth:
            return
        self.SideBarWidth = width
        _LastSideBarWidth = width
        self.Search.Size = Udim2(0, width, 0, SEARCH_HEIGHT)
        self.SideBar.Position = Udim2(0, 0, 0, SEARCH_HEIGHT)
        self.SideBar.Size = Udim2(0, width, 1, -SEARCH_HEIGHT)
        self.Tabs.Position = Udim2(0, width, 0, 0)
        self.Tabs.Size = Udim2(1, -width, 0, TAB_HEIGHT)
        self.Content.Position = Udim2(0, width, 0, TAB_HEIGHT)
        self.Content.Size = Udim2(1, -width, 1, -TAB_HEIGHT)
        self.Resizer.Position = Udim2(0, width - HANDLE_WIDTH // 2, 0, 0)

    @property
    def Root(self) -> Path:
        return self.SideBar.Root.Path

    def OpenFile(self, path: Path):
        self.Tabs.Open(path)

    def _OnNodeActivated(self, node):
        if not node.IsDir:
            self.OpenFile(node.Path)

    def _ShowView(self, path: Path | None):
        if path is not None and path not in self.Views:
            view = CreateView(path)
            self.Views[path] = view
            self.Content.AddChild(view)
        for view_path, view in self.Views.items():
            view.Visible = view_path == path
        self.Empty.Visible = path is None

    def _DestroyView(self, path: Path):
        view = self.Views.pop(path, None)
        if view is not None:
            view.Destroy()
