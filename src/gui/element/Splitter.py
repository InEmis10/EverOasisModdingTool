import pygame
from pygame_easy_gui import Frame, Signal, Udim2
from src.gui.Theme import Theme

HANDLE_WIDTH = 6


class Splitter(Frame):
    """Poignée verticale invisible à glisser pour redimensionner un panneau.

    Moved est émis avec la position X absolue de la souris pendant le glissement.
    """

    def __init__(self):
        super().__init__()
        self.Name = "Splitter"
        self.Size = Udim2(0, HANDLE_WIDTH, 1, 0)
        self.BackgroundColor3 = Theme.HOVER
        self.BackgroundTransparency = 1
        self.BorderSizePixel = 0
        self.ZIndex = 4
        self.Moved = Signal()
        self.Dragging = False
        self._Hovered = False
        self.MouseEnter.Connect(lambda: self._SetHovered(True))
        self.MouseLeave.Connect(lambda: self._SetHovered(False))

    def _SetHovered(self, hovered: bool):
        self._Hovered = hovered
        self._Refresh()

    def _Refresh(self):
        highlighted = self._Hovered or self.Dragging
        self.BackgroundTransparency = 0.4 if highlighted else 1
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE if highlighted else pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass  # curseur système indisponible (pilote vidéo sans curseurs) : la poignée reste utilisable

    def _OnMouseDown(self, Button: int, Pos: pygame.Vector2):
        if Button == 1:
            self.Dragging = True
            self._Refresh()

    def _OnMouseDrag(self, Pos: pygame.Vector2):
        if self.Dragging:
            self.Moved.Fire(int(Pos.x))

    def _OnMouseUp(self, Button: int, Pos: pygame.Vector2, IsOver: bool):
        if Button == 1:
            self.Dragging = False
            self._Hovered = IsOver
            self._Refresh()
