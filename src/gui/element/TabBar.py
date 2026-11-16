from pathlib import Path
import pygame
from pygame_easy_gui import ScrollingFrame, TextButton, UIListLayout, Udim2, Signal, UserInputService
from src.classe.FileTypes import GetFileType
from src.gui import Icons
from src.gui.Theme import Theme

TAB_HEIGHT = 28
TAB_WIDTH = 170
CLOSE_SIZE = 8


class ClosableTab(TextButton):
    """Bouton d'onglet : icône, texte, croix de fermeture (visible au survol ou si actif)."""

    def __init__(self, text: str, icon: tuple[str, object] | None, closable: bool = True, width: int = TAB_WIDTH):
        super().__init__()
        self.Selected = Signal()
        self.CloseRequested = Signal()
        self.IconInfo = icon
        self.Closable = closable
        self.IsActive = False
        self.Hovered = False

        self.Size = Udim2(0, width, 1, 0)
        self.Text = text
        self.FontName = Theme.TREE_FONT
        self.TextSize = 13
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.AutoButtonColor = False
        self.BorderSizePixel = 0
        self._RefreshStyle()

        self.MouseEnter.Connect(lambda: self._SetHovered(True))
        self.MouseLeave.Connect(lambda: self._SetHovered(False))
        self.MouseMoved.Connect(lambda x, y: self._MarkRenderDirty())
        self.MouseButton1Click.Connect(self._OnClick)

    def SetActive(self, value: bool):
        self.IsActive = value
        self._RefreshStyle()

    def _SetHovered(self, value: bool):
        self.Hovered = value
        self._RefreshStyle()

    def _RefreshStyle(self):
        if self.IsActive:
            self.BackgroundColor3, self.TextColor3 = Theme.BACKGROUND, Theme.TEXT
        elif self.Hovered:
            self.BackgroundColor3, self.TextColor3 = Theme.TREE_HOVER, Theme.TEXT
        else:
            self.BackgroundColor3, self.TextColor3 = Theme.TOPBAR, Theme.TREE_FILE_TEXT

    def _CloseRect(self) -> pygame.Rect:
        Rect = self.GetRect()
        return pygame.Rect(Rect.right - 20, Rect.centery - 8, 16, 16)

    def _OnClick(self):
        if self.Closable and self._CloseRect().collidepoint(UserInputService.GetMouseLocation()):
            self.CloseRequested.Fire()
        else:
            self.Selected.Fire()

    def _GetTextArea(self) -> pygame.Rect:
        Rect = self.GetRect()
        Left = 26 if self.IconInfo else 10
        Right = 24 if self.Closable else 8
        return pygame.Rect(Rect.x + Left, Rect.y, max(0, Rect.width - Left - Right), Rect.height)

    def _Draw(self, Surface):
        super()._Draw(Surface)
        Rect = self.GetRect()
        if self.IsActive:
            pygame.draw.line(Surface, tuple(Theme.HOVER), (Rect.left, Rect.top), (Rect.right - 1, Rect.top), 2)
        pygame.draw.line(Surface, tuple(Theme.BORDER), (Rect.right - 1, Rect.top), (Rect.right - 1, Rect.bottom - 1))
        if self.IconInfo:
            Icons.Draw(Surface, self.IconInfo[0], Rect.left + 13, Rect.centery, self.IconInfo[1])
        if self.Closable and (self.IsActive or self.Hovered):
            Close = self._CloseRect()
            if Close.collidepoint(UserInputService.GetMouseLocation()):
                pygame.draw.rect(Surface, tuple(Theme.MENU), Close, border_radius=3)
            c, h = Close.center, CLOSE_SIZE // 2
            Color = tuple(Theme.TEXT)
            pygame.draw.line(Surface, Color, (c[0] - h, c[1] - h), (c[0] + h - 1, c[1] + h - 1), 2)
            pygame.draw.line(Surface, Color, (c[0] - h, c[1] + h - 1), (c[0] + h - 1, c[1] - h), 2)


class TabBar(ScrollingFrame):
    """Onglets des fichiers ouverts d'un écran."""

    def __init__(self):
        super().__init__()
        self.Name = "TabBar"
        self.TabActivated = Signal()
        self.TabClosed = Signal()
        self.Tabs: dict[Path, ClosableTab] = {}
        self.ActivePath: Path | None = None
        self._Order = 0

        self.BackgroundColor3 = Theme.TOPBAR
        self.BorderSizePixel = 0
        self.ScrollingDirection = "x"
        self.AutomaticCanvasSize = "x"
        self.CanvasSize = Udim2(0, 0, 0, 0)
        self.ScrollBarThickness = 3
        self.AddChild(UIListLayout(FillDirection="horizontal"))

    def Open(self, path: Path):
        tab = self.Tabs.get(path)
        if tab is None:
            category = GetFileType(path).Category
            tab = ClosableTab(path.name, (category.Icon, category.Color))
            self._Order += 1
            tab.LayoutOrder = self._Order
            tab.Selected.Connect(lambda: self.Activate(path))
            tab.CloseRequested.Connect(lambda: self.Close(path))
            self.Tabs[path] = tab
            self.AddChild(tab)
        self.Activate(path)

    def Activate(self, path: Path | None):
        if self.ActivePath in self.Tabs:
            self.Tabs[self.ActivePath].SetActive(False)
        self.ActivePath = path
        if path is not None:
            self.Tabs[path].SetActive(True)
        self.TabActivated.Fire(path)

    def Close(self, path: Path):
        tab = self.Tabs.pop(path, None)
        if tab is None:
            return
        ordered = sorted([*self.Tabs.items(), (path, tab)], key=lambda kv: kv[1].LayoutOrder)
        index = [p for p, _ in ordered].index(path)
        tab.Destroy()
        self.TabClosed.Fire(path)
        if path == self.ActivePath:
            remaining = [p for p, _ in ordered if p != path]
            self.Activate(remaining[min(index, len(remaining) - 1)] if remaining else None)
