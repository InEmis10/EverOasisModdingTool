from pathlib import Path
from pygame_easy_gui import (Frame, TextButton, TextLabel, UIListLayout, UIPadding, UICorner, Udim, Udim2,
                             Signal, UserInputService, UserInputType)
from src.classe.FileTypes import GetFileType
from src.classe.ModTools import ExtractTool
from src.gui import Icons
from src.gui.Theme import Theme

WIDTH = 270
ITEM_HEIGHT = 36
HEADER_HEIGHT = 40
PADDING = 4


class _ToolHeader(TextLabel):
    """En-tête : icône du type + nom du fichier + catégorie"""
    def __init__(self, path: Path):
        super().__init__()
        self.FileType = GetFileType(path)
        self.Size = Udim2(1, 0, 0, HEADER_HEIGHT)
        self.BackgroundTransparency = 1
        self.FontName = Theme.TREE_FONT
        self.TextSize = 13
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.TextColor3 = Theme.TEXT
        self.Text = path.name
        self.AddChild(UIPadding(PaddingLeft=Udim(0, 26), PaddingRight=Udim(0, 6), PaddingBottom=Udim(0, 14)))

        Category = self.FileType.Category
        sub = TextLabel()
        sub.Size = Udim2(1, 0, 0, 14)
        sub.Position = Udim2(0, 0, 1, 0)
        sub.BackgroundTransparency = 1
        sub.FontName = Theme.TREE_FONT
        sub.TextSize = 11
        sub.TextXAlignment = "left"
        sub.TextTruncate = "atend"
        sub.TextColor3 = Category.Color
        sub.Text = f"{Category.Label} · {self.FileType.Description}"
        self.AddChild(sub)

    def _Draw(self, Surface):
        super()._Draw(Surface)
        Rect = self.GetRect()
        Icons.Draw(Surface, self.FileType.Category.Icon, Rect.left + 12, Rect.top + 13, self.FileType.Category.Color)


class ToolMenu(Frame):
    """Menu flottant : choisit l'outil à appliquer à un fichier. Se ferme au clic en dehors."""

    def __init__(self, path: Path, tools: list[ExtractTool], screen_pos):
        super().__init__()
        self.Name = "ToolMenu"
        self.Chosen = Signal()          # (ExtractTool)
        self.Closed = Signal()
        self.ZIndex = 100
        self.BackgroundColor3 = Theme.MENU
        self.BorderColor3 = Theme.BORDER
        self.BorderSizePixel = 1
        self.AddChild(UICorner(CornerRadius=Udim(0, 4)))
        self.AddChild(UIListLayout(FillDirection="vertical"))
        self.AddChild(UIPadding(PaddingLeft=Udim(0, PADDING), PaddingRight=Udim(0, PADDING),
                                PaddingTop=Udim(0, PADDING), PaddingBottom=Udim(0, PADDING)))

        header = _ToolHeader(path)
        header.LayoutOrder = 0
        self.AddChild(header)
        for i, tool in enumerate(tools, start=1):
            self.AddChild(self._MakeButton(tool, i))

        Height = HEADER_HEIGHT + len(tools) * ITEM_HEIGHT + PADDING * 2
        self.Size = Udim2(0, WIDTH, 0, Height)
        self.Position = Udim2(0, int(screen_pos[0]), 0, int(screen_pos[1]))

        self._InputConn = UserInputService.InputBegan.Connect(self._OnInput)

    def _MakeButton(self, tool: ExtractTool, order: int) -> TextButton:
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
        btn.Text = tool.Name
        btn.AddChild(UIPadding(PaddingLeft=Udim(0, 8), PaddingTop=Udim(0, 3)))
        btn.AddChild(UICorner(CornerRadius=Udim(0, 3)))

        desc = TextLabel()
        desc.Size = Udim2(1, 0, 0, 14)
        desc.Position = Udim2(0, 0, 0, 17)
        desc.BackgroundTransparency = 1
        desc.FontName = Theme.TREE_FONT
        desc.TextSize = 11
        desc.TextXAlignment = "left"
        desc.TextTruncate = "atend"
        desc.TextColor3 = Theme.TREE_ARROW
        desc.Text = tool.Description
        btn.AddChild(desc)

        btn.MouseEnter.Connect(lambda: setattr(btn, "BackgroundColor3", Theme.HOVER))
        btn.MouseLeave.Connect(lambda: setattr(btn, "BackgroundColor3", Theme.MENU))
        btn.MouseButton1Click.Connect(lambda: self._Choose(tool))
        return btn

    def ClampToScreen(self, screen_size):
        """Garde le menu entier à l'écran (ouvert près du bord droit ou bas)"""
        Size = self.GetAbsSize()
        x = min(self.Position.X.Offset, int(screen_size[0] - Size.x - 2))
        y = min(self.Position.Y.Offset, int(screen_size[1] - Size.y - 2))
        self.Position = Udim2(0, max(0, x), 0, max(0, y))

    def _Choose(self, tool: ExtractTool):
        self.Chosen.Fire(tool)   # avant Close : Destroy déconnecte tous les signaux du menu
        self.Close()

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
