from pathlib import Path
import pygame
from pygame_easy_gui import Frame, TextLabel, UIListLayout, UIPadding, Udim, Udim2
from src.classe.FileTypes import GetFileType
from src.classe.ModTools import FindWorkspace, GetTools, DecompileToText
from src.gui.element.CodeView import CodeView
from src.gui import Icons
from src.gui.Theme import Theme


def _FormatSize(size: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if size < 1024 or unit == "Go":
            return f"{size:.0f} {unit}" if unit == "o" else f"{size:.1f} {unit}"
        size /= 1024


class _Line(TextLabel):
    def __init__(self, text: str, size: int, color, height: int, order: int):
        super().__init__()
        self.LayoutOrder = order
        self.Size = Udim2(1, 0, 0, height)
        self.BackgroundTransparency = 1
        self.FontName = Theme.TREE_FONT
        self.TextSize = size
        self.TextColor3 = color
        self.TextXAlignment = "left"
        self.TextTruncate = "atend"
        self.Text = text


class FileView(Frame):
    """Contenu d'un onglet. En attendant un éditeur par type : fiche du fichier."""

    def __init__(self, path: Path):
        super().__init__()
        self.Path = path
        self.Name = f"FileView:{path.name}"
        self.Size = Udim2(1, 0, 1, 0)
        self.BackgroundTransparency = 1
        self.FileType = GetFileType(path)
        self.AddChild(UIListLayout(FillDirection="vertical", Padding=Udim(0, 4)))
        self.AddChild(UIPadding(PaddingLeft=Udim(0, 24), PaddingTop=Udim(0, 20), PaddingRight=Udim(0, 24)))

        category = self.FileType.Category
        try:
            size = _FormatSize(path.stat().st_size)
        except OSError:
            size = "?"
        workspace = FindWorkspace(path.parent)
        location = str(path.relative_to(workspace)) if workspace else str(path)
        tools = ", ".join(t.Name for t in GetTools(path))

        lines = [
            (path.name, 20, Theme.TEXT, 30),
            (f"{category.Label} · {self.FileType.Description}", 14, category.Color, 22),
            (f"{size}  ·  {location}", 13, Theme.TREE_FILE_TEXT, 20),
            ("", 13, Theme.TEXT, 10),
            ("Pas encore d'éditeur pour ce type de fichier.", 13, Theme.TREE_ARROW, 20),
            (f"Clic droit dans l'arbre : {tools}", 13, Theme.TREE_ARROW, 20),
        ]
        for order, (text, text_size, color, height) in enumerate(lines):
            label = _Line(text, text_size, color, height, order)
            if order == 0:
                label.AddChild(UIPadding(PaddingLeft=Udim(0, 22)))
            self.AddChild(label)
        self._Title = self.GetChildren()[0]

    def _Draw(self, Surface):
        super()._Draw(Surface)
        Rect = self._Title.GetRect()
        Icons.Draw(Surface, self.FileType.Category.Icon, Rect.left + 7, Rect.centery, self.FileType.Category.Color)


TEXT_EXTENSIONS = {"nut", "gsa", "json", "txt", "md", "xml", "csv"}
MAX_TEXT_SIZE = 8 * 1024 * 1024
HEADER_HEIGHT = 26


class CodeFileView(Frame):
    """Onglet d'un script .gsb (décompilé à l'ouverture) ou d'un fichier texte, en lecture seule."""

    def __init__(self, path: Path):
        super().__init__()
        self.Path = path
        self.Name = f"CodeFileView:{path.name}"
        self.Size = Udim2(1, 0, 1, 0)
        self.BackgroundTransparency = 1
        self.IsScript = path.suffix.lower() == ".gsb"

        self.Header = TextLabel()
        self.Header.Size = Udim2(1, 0, 0, HEADER_HEIGHT)
        self.Header.BackgroundColor3 = Theme.CODE_GUTTER
        self.Header.BorderColor3 = Theme.BORDER
        self.Header.BorderSizePixel = 1
        self.Header.FontName = Theme.TREE_FONT
        self.Header.TextSize = 12
        self.Header.TextColor3 = Theme.TREE_ARROW
        self.Header.TextXAlignment = "left"
        self.Header.TextTruncate = "atend"
        self.Header.AddChild(UIPadding(PaddingLeft=Udim(0, 10)))
        self.AddChild(self.Header)

        self.Code = CodeView()
        self.Code.Position = Udim2(0, 0, 0, HEADER_HEIGHT)
        self.Code.Size = Udim2(1, 0, 1, -HEADER_HEIGHT)
        self.AddChild(self.Code)

        if self.IsScript:
            self.Header.Text = "Squirrel décompilé · lecture seule"
            self.Code.SetMessage("Décompilation…")
            DecompileToText(path, self._OnDecompiled)
        else:
            self._LoadText()

    def _OnDecompiled(self, text: str | None, error: str):
        if self._Destroyed:
            return
        if text is None:
            self.Header.Text = "Échec de la décompilation"
            self.Code.SetMessage(error, Theme.STATUS_ERROR)
            return
        self.Code.SetText(text)
        self.Header.Text = (f"Squirrel décompilé · lecture seule · {len(self.Code.Lines)} lignes"
                            f" · clic droit dans l'arbre > Décompiler pour obtenir un .nut modifiable")

    def _LoadText(self):
        try:
            if self.Path.stat().st_size > MAX_TEXT_SIZE:
                raise OSError("fichier trop gros pour l'aperçu")
            text = self.Path.read_text("utf-8", errors="replace")
        except OSError as e:
            self.Header.Text = "Lecture impossible"
            self.Code.SetMessage(str(e), Theme.STATUS_ERROR)
            return
        self.Code.SetText(text)
        self.Header.Text = f"{GetFileType(self.Path).Description} · lecture seule · {len(self.Code.Lines)} lignes"


def CreateView(path: Path) -> Frame:
    """Vue adaptée au type du fichier ouvert dans un onglet."""
    extension = path.suffix.lower().lstrip(".")
    if extension == "gsb" or extension in TEXT_EXTENSIONS:
        return CodeFileView(path)
    return FileView(path)
