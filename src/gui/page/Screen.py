from pathlib import Path
from pygame_easy_gui import Frame, TextLabel, Udim2, Signal
from src.gui.element.TreeContainer import TreeContainer
from src.gui.element.TabBar import TabBar, TAB_HEIGHT
from src.gui.element.FileView import CreateView
from src.gui.Theme import Theme

SIDEBAR_WIDTH = 220


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
        self.SideBar.Size = Udim2(0, SIDEBAR_WIDTH, 1, 0)
        self.AddChild(self.SideBar)

        self.Tabs = TabBar()
        self.Tabs.Position = Udim2(0, SIDEBAR_WIDTH, 0, 0)
        self.Tabs.Size = Udim2(1, -SIDEBAR_WIDTH, 0, TAB_HEIGHT)
        self.AddChild(self.Tabs)

        self.Content = Frame()
        self.Content.Name = "Content"
        self.Content.BackgroundColor3 = Theme.BACKGROUND
        self.Content.Position = Udim2(0, SIDEBAR_WIDTH, 0, TAB_HEIGHT)
        self.Content.Size = Udim2(1, -SIDEBAR_WIDTH, 1, -TAB_HEIGHT)
        self.AddChild(self.Content)

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
        self.Tabs.TabActivated.Connect(self._ShowView)
        self.Tabs.TabClosed.Connect(self._DestroyView)

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
