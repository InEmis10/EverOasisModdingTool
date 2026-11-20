import pygame
from pygame_easy_gui import Frame, TextBox, TextLabel, Signal, Udim2, UIPadding, Udim
from src.gui.Theme import Theme

SEARCH_HEIGHT = 30
COUNT_WIDTH = 64


class _SearchBox(TextBox):
    def _OnKeyDown(self, Event: pygame.event.Event):
        if Event.key == pygame.K_ESCAPE and self.Text:   # Échap : vide la recherche (puis relâche le focus)
            self.Text = ""
            self.CursorPosition = 0
            self.SelectionStart = -1
        super()._OnKeyDown(Event)


class SearchBar(Frame):
    """Champ de recherche du workspace, en haut de la side bar.

    QueryChanged(texte) à chaque frappe · Submitted() sur Entrée.
    """

    def __init__(self):
        super().__init__()
        self.Name = "SearchBar"
        self.BackgroundColor3 = Theme.SIDEBAR
        self.BorderColor3 = Theme.BORDER
        self.BorderSizePixel = 1
        self.QueryChanged = Signal()
        self.Submitted = Signal()

        self.Box = _SearchBox()
        self.Box.Name = "SearchBox"
        self.Box.Position = Udim2(0, 6, 0, 4)
        self.Box.Size = Udim2(1, -12 - COUNT_WIDTH, 1, -8)
        self.Box.BackgroundColor3 = Theme.BACKGROUND
        self.Box.BorderColor3 = Theme.BORDER
        self.Box.BorderSizePixel = 1
        self.Box.FontName = Theme.TREE_FONT
        self.Box.TextSize = 13
        self.Box.TextColor3 = Theme.TEXT
        self.Box.PlaceholderText = "Rechercher (Ctrl+F)"
        self.Box.PlaceholderColor3 = tuple(Theme.CODE_LINE_NUMBER)
        self.Box.TextTruncate = "atend"
        self.Box.AddChild(UIPadding(PaddingLeft=Udim(0, 6), PaddingRight=Udim(0, 6)))
        self.Box.GetPropertyChangedSignal("Text").Connect(lambda: self.QueryChanged.Fire(self.Box.Text))
        self.Box.FocusLost.Connect(lambda enter: self.Submitted.Fire() if enter else None)
        self.AddChild(self.Box)

        self.Count = TextLabel()
        self.Count.Name = "SearchCount"
        self.Count.Position = Udim2(1, -COUNT_WIDTH - 4, 0, 0)
        self.Count.Size = Udim2(0, COUNT_WIDTH, 1, 0)
        self.Count.BackgroundTransparency = 1
        self.Count.FontName = Theme.TREE_FONT
        self.Count.TextSize = 12
        self.Count.TextColor3 = Theme.TREE_ARROW
        self.Count.TextXAlignment = "right"
        self.Count.Text = ""
        self.AddChild(self.Count)

    @property
    def Query(self) -> str:
        return self.Box.Text

    def Focus(self):
        """Donne le focus au champ et sélectionne son texte (taper remplace la recherche précédente)"""
        self.Box.CaptureFocus()
        self.Box.SelectionStart = 0
        self.Box.CursorPosition = len(self.Box.Text)

    def IsFocused(self) -> bool:
        return self.Box.IsFocused()

    def Clear(self):
        self.Box.Text = ""
        self.Box.CursorPosition = 0
        self.Box.SelectionStart = -1

    def SetCount(self, count: int | None, limit: int):
        if count is None:
            self.Count.Text = ""
        elif count == 0:
            self.Count.Text = "aucun"
            self.Count.TextColor3 = Theme.STATUS_ERROR
        else:
            self.Count.Text = f"{limit}+" if count > limit else str(count)
            self.Count.TextColor3 = Theme.TREE_ARROW
