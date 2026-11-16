from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from pygame_easy_gui import (Frame, TextButton, TextLabel, UIListLayout, UIPadding, UICorner, Udim, Udim2,
                             Signal, UserInputService, UserInputType)
from src.classe.FileTypes import GetFileType
from src.gui import Icons
from src.gui.Theme import Theme

WIDTH = 270
ITEM_HEIGHT = 36
HEADER_HEIGHT = 40
PADDING = 4


@dataclass(frozen=True)
class MenuItem:
    Label: str
    Description: str
    Callback: Callable[[], None]


class _Header(TextLabel):
    def __init__(self, path: Path):
        super().__init__()
        if path.is_dir():
            self.IconName, self.IconColor, subtitle = "folder", Theme.TREE_FOLDER_TEXT, "Dossier"
        else:
            file_type = GetFileType(path)
            category = file_type.Category
            self.IconName, self.IconColor = category.Icon, category.Color
            subtitle = f"{category.Label} · {file_type.Description}"

        self.Size = Udim2(1, 0, 0, HEADER_HEIGHT)
        self.BackgroundTransparency = 1
        self.FontName = Theme.TREE_FONT
        self.TextSize = 13
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.TextColor3 = Theme.TEXT
        self.Text = path.name
        self.AddChild(UIPadding(PaddingLeft=Udim(0, 26), PaddingRight=Udim(0, 6), PaddingBottom=Udim(0, 14)))

        sub = _SmallLabel(subtitle, self.IconColor)
        sub.Position = Udim2(0, 0, 1, 0)
        self.AddChild(sub)

    def _Draw(self, Surface):
        super()._Draw(Surface)
        Rect = self.GetRect()
        Icons.Draw(Surface, self.IconName, Rect.left + 12, Rect.top + 13, self.IconColor)


class _SmallLabel(TextLabel):
    def __init__(self, text: str, color):
        super().__init__()
        self.Size = Udim2(1, 0, 0, 14)
        self.BackgroundTransparency = 1
        self.FontName = Theme.TREE_FONT
        self.TextSize = 11
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.TextColor3 = color
        self.Text = text


class ContextMenu(Frame):
    """Menu flottant ouvert au clic droit sur un fichier ou un dossier. Se ferme au clic en dehors."""

    def __init__(self, path: Path, items: list[MenuItem], screen_pos):
        super().__init__()
        self.Name = "ContextMenu"
        self.Closed = Signal()
        self.ZIndex = 100
        self.BackgroundColor3 = Theme.MENU
        self.BorderColor3 = Theme.BORDER
        self.BorderSizePixel = 1
        self.AddChild(UICorner(CornerRadius=Udim(0, 4)))
        self.AddChild(UIListLayout(FillDirection="vertical"))
        self.AddChild(UIPadding(PaddingLeft=Udim(0, PADDING), PaddingRight=Udim(0, PADDING),
                                PaddingTop=Udim(0, PADDING), PaddingBottom=Udim(0, PADDING)))

        header = _Header(path)
        header.LayoutOrder = 0
        self.AddChild(header)
        for order, item in enumerate(items, start=1):
            self.AddChild(self._MakeButton(item, order))

        self.Size = Udim2(0, WIDTH, 0, HEADER_HEIGHT + len(items) * ITEM_HEIGHT + PADDING * 2)
        self.Position = Udim2(0, int(screen_pos[0]), 0, int(screen_pos[1]))
        self._InputConn = UserInputService.InputBegan.Connect(self._OnInput)

    def _MakeButton(self, item: MenuItem, order: int) -> TextButton:
        btn = TextButton()
        btn.LayoutOrder = order
        btn.Size = Udim2(1, 0, 0, ITEM_HEIGHT)
        btn.BackgroundColor3 = Theme.MENU
        btn.AutoButtonColor = False
        btn.FontName = Theme.TREE_FONT
        btn.TextSize = 13
        btn.TextXAlignment = "left"
        btn.TextYAlignment = "top"
        btn.TextColor3 = Theme.TEXT
        btn.TextTruncate = "atend"
        btn.Text = item.Label
        btn.AddChild(UIPadding(PaddingLeft=Udim(0, 8), PaddingTop=Udim(0, 3)))
        btn.AddChild(UICorner(CornerRadius=Udim(0, 3)))

        desc = _SmallLabel(item.Description, Theme.TREE_ARROW)
        desc.Position = Udim2(0, 0, 0, 17)
        btn.AddChild(desc)

        btn.MouseEnter.Connect(lambda: setattr(btn, "BackgroundColor3", Theme.HOVER))
        btn.MouseLeave.Connect(lambda: setattr(btn, "BackgroundColor3", Theme.MENU))
        btn.MouseButton1Click.Connect(lambda: self._Choose(item))
        return btn

    def ClampToScreen(self, screen_size):
        Size = self.GetAbsSize()
        x = min(self.Position.X.Offset, int(screen_size[0] - Size.x - 2))
        y = min(self.Position.Y.Offset, int(screen_size[1] - Size.y - 2))
        self.Position = Udim2(0, max(0, x), 0, max(0, y))

    def _Choose(self, item: MenuItem):
        self.Close()
        item.Callback()

    def _OnInput(self, Input, _GameProcessed):
        if Input.UserInputType in (UserInputType.MouseButton1, UserInputType.MouseButton2) \
                and not self.GetRect().collidepoint(Input.Position):
            self.Close()

    def Close(self):
        if self._Destroyed:
            return
        self._InputConn.Disconnect()
        self.Closed.Fire()
        self.Destroy()
