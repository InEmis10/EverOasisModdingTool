import re
from collections import OrderedDict
import pygame
from pygame_easy_gui import ScrollingFrame, Udim2
from src.gui.Theme import Theme

KEYWORDS = {
    "while", "do", "if", "else", "break", "continue", "return", "null", "function", "for", "foreach", "in",
    "typeof", "base", "delete", "try", "catch", "throw", "clone", "yield", "resume", "switch", "case",
    "default", "this", "parent", "class", "extends", "constructor", "instanceof", "vargc", "vargv",
    "true", "false", "local", "static", "enum", "const",
}

TOKEN = re.compile(r'''
    (?P<comment>//.*|/\*.*?(?:\*/|$))
  | (?P<string>"(?:\\.|[^"\\])*"?|'(?:\\.|[^'\\])*'?)
  | (?P<number>\b0[xX][0-9a-fA-F]+\b|\b\d+(?:\.\d+)?\b)
  | (?P<word>[A-Za-z_]\w*)
''', re.VERBOSE)

PADDING = 4
GUTTER_PADDING = 12
CACHE_SIZE = 300


def _WordColor(word: str, line: str, end: int):
    if word in KEYWORDS:
        return Theme.CODE_KEYWORD
    if word.startswith("__") or (word.isupper() and len(word) > 1):
        return Theme.CODE_CONSTANT
    if line[end:end + 1] == "(":
        return Theme.CODE_FUNCTION
    return Theme.CODE_TEXT


def Highlight(line: str) -> list[tuple[int, str, object]]:
    """Découpe une ligne en (colonne, texte, couleur)."""
    parts, pos = [], 0
    for match in TOKEN.finditer(line):
        if match.start() > pos:
            parts.append((pos, line[pos:match.start()], Theme.CODE_TEXT))
        kind, text = match.lastgroup, match.group()
        if kind == "word":
            color = _WordColor(text, line, match.end())
        else:
            color = {"comment": Theme.CODE_COMMENT, "string": Theme.CODE_STRING, "number": Theme.CODE_NUMBER}[kind]
        parts.append((match.start(), text, color))
        pos = match.end()
    if pos < len(line):
        parts.append((pos, line[pos:], Theme.CODE_TEXT))
    return parts


class CodeView(ScrollingFrame):
    """Affichage de code en lecture seule : seules les lignes visibles sont dessinées."""

    def __init__(self):
        super().__init__()
        self.Name = "CodeView"
        self.BackgroundColor3 = Theme.CODE_BACKGROUND
        self.BorderSizePixel = 0
        self.ScrollingDirection = "xy"
        self.ScrollBarThickness = 8
        self.Font = pygame.font.Font(Theme.CODE_FONT, Theme.CODE_TEXT_SIZE)
        self.CharWidth = self.Font.size("M")[0]
        self.LineHeight = self.Font.get_linesize()
        self.ScrollStep = self.LineHeight * 3
        self.Lines: list[str] = []
        self.Message = ""
        self.MessageColor = Theme.CODE_LINE_NUMBER
        self._Cache: OrderedDict[int, pygame.Surface | None] = OrderedDict()
        self.CanvasSize = Udim2(0, 0, 0, 0)

    def SetText(self, text: str):
        self.Lines = text.expandtabs(4).splitlines()
        self.Message = ""
        self._Cache.clear()
        longest = max((len(line) for line in self.Lines), default=0)
        width = self._GutterWidth() + GUTTER_PADDING + longest * self.CharWidth + 40
        self.CanvasSize = Udim2(0, width, 0, len(self.Lines) * self.LineHeight + PADDING * 2)
        self._MarkRenderDirty()

    def SetMessage(self, text: str, color=Theme.CODE_LINE_NUMBER):
        self.Lines = []
        self._Cache.clear()
        self.Message = text
        self.MessageColor = color
        self.CanvasSize = Udim2(0, 0, 0, 0)
        self._MarkRenderDirty()

    def _GutterWidth(self) -> int:
        return len(str(max(1, len(self.Lines)))) * self.CharWidth + GUTTER_PADDING * 2

    def _LineSurface(self, index: int) -> pygame.Surface | None:
        if index in self._Cache:
            self._Cache.move_to_end(index)
            return self._Cache[index]
        line = self.Lines[index]
        surface = None
        if line.strip():
            surface = pygame.Surface((len(line) * self.CharWidth + 1, self.LineHeight), pygame.SRCALPHA)
            for column, text, color in Highlight(line):
                if text.strip():
                    surface.blit(self.Font.render(text, True, tuple(color)), (column * self.CharWidth, 0))
        self._Cache[index] = surface
        if len(self._Cache) > CACHE_SIZE:
            self._Cache.popitem(last=False)
        return surface

    def _Draw(self, Surface: pygame.Surface):
        super()._Draw(Surface)
        Rect = self.GetRect()
        OldClip = Surface.get_clip()
        View = Rect.clip(OldClip)
        if View.width <= 0 or View.height <= 0:
            return

        if self.Message:
            Surface.set_clip(View)
            Text = self.Font.render(self.Message, True, tuple(self.MessageColor))
            Surface.blit(Text, Text.get_rect(center=Rect.center))
            Surface.set_clip(OldClip)
            return

        Scroll = self._GetClampedCanvasPosition()
        Gutter = self._GutterWidth()
        First = max(0, int((Scroll.y - PADDING) // self.LineHeight))
        Last = min(len(self.Lines), First + Rect.height // self.LineHeight + 2)
        Top = Rect.top + PADDING - Scroll.y

        CodeArea = pygame.Rect(Rect.left + Gutter, Rect.top, Rect.width - Gutter, Rect.height).clip(View)
        Surface.set_clip(CodeArea)
        x = Rect.left + Gutter + GUTTER_PADDING - Scroll.x
        for index in range(First, Last):
            line = self._LineSurface(index)
            if line is not None:
                Surface.blit(line, (x, Top + index * self.LineHeight))

        Surface.set_clip(pygame.Rect(Rect.left, Rect.top, Gutter, Rect.height).clip(View))
        Surface.fill(tuple(Theme.CODE_GUTTER), pygame.Rect(Rect.left, Rect.top, Gutter, Rect.height))
        for index in range(First, Last):
            number = self.Font.render(str(index + 1), True, tuple(Theme.CODE_LINE_NUMBER))
            Surface.blit(number, (Rect.left + Gutter - GUTTER_PADDING - number.get_width(), Top + index * self.LineHeight))
        Surface.set_clip(OldClip)
