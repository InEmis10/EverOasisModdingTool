from pygame_easy_gui import Frame, UIListLayout, Udim2, Signal
from src.gui.element.TabBar import ClosableTab
from src.gui.Theme import Theme

BUTTON_WIDTH = 150


class ScreenBar(Frame):
    """Sélecteur d'écrans, dans la barre du haut."""

    def __init__(self):
        super().__init__()
        self.Name = "ScreenBar"
        self.BackgroundTransparency = 1
        self.Selected = Signal()
        self.CloseRequested = Signal()
        self._Buttons = {}
        self.AddChild(UIListLayout(FillDirection="horizontal", HorizontalAlignment="right"))

    def Refresh(self, screens: list, active):
        for button in self._Buttons.values():
            button.Destroy()
        self._Buttons = {}
        for order, screen in enumerate(screens):
            button = ClosableTab(screen.Title, ("folder", Theme.TREE_FOLDER_TEXT), screen.Closable, BUTTON_WIDTH)
            button.LayoutOrder = order
            button.SetActive(screen is active)
            button.Selected.Connect(lambda s=screen: self.Selected.Fire(s))
            button.CloseRequested.Connect(lambda s=screen: self.CloseRequested.Fire(s))
            self._Buttons[screen] = button
            self.AddChild(button)
