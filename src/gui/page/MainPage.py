import pygame_easy_gui
from pygame_easy_gui import Frame, UIListLayout, UIPadding, Udim, TextButton, ScrollingFrame
from pygame_easy_gui import Color3
from pygame_easy_gui import Udim2
from pygame_easy_gui import ScreenGui
from pygame_easy_gui import Signal
from pygame_easy_gui import TimeService
from pathlib import Path
import subprocess
from src import Event
from src.gui.Theme import Theme
from pygame_easy_gui import UserInputService, InputObject, UserInputState, UserInputType
from pygame_easy_gui import TextLabel
from src.gui.element.ContextMenu import ContextMenu, MenuItem
from src.gui.element.ScreenBar import ScreenBar
from src.gui.page.Screen import Screen
from src.classe.ModTools import GetTools, RunTool, ToolResult

def AskDirectory(callback, title, start):
    try:
        proc = subprocess.Popen(
            ["zenity", "--file-selection", "--directory",
             f"--title={title}", f"--filename={start}/"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("zenity n'est pas installé")
    def check():
        if proc.poll() is None:
            return
        timer.Cancel()
        out = proc.stdout.read().strip()
        proc.stdout.close()
        callback(Path(out) if proc.returncode == 0 and out else None)

    timer = TimeService.Every(0.1, check)

def OnDirectoryChosen(path):
    if path is not None:
        Event.OpenProject.Fire(path)

def OnOpenClicked():
    AskDirectory(OnDirectoryChosen, "Ouvrir un projet Ever Oasis", Path("~").expanduser())


TOPBAR_HEIGHT = 30
STATUS_HEIGHT = 22
SCREENBAR_LEFT = 220


def StylePanel(frame: Frame, color: Color3, name: str):
    frame.Name = name
    frame.BackgroundColor3 = color
    frame.BackgroundTransparency = 0
    frame.BorderColor3 = Theme.BORDER
    frame.BorderSizePixel = 1


##CLASS

class CategorieData:
    def __init__(self):
        self.Content = {}

    @staticmethod
    def _NewEntry(trigger, sub):
        return {"trigger": trigger, "sub": sub if sub is not None else {}}

    def AddBase(self, name: str, trigger=None, sub=None):
        if name in self.Content:
            return
        self.Content[name] = self._NewEntry(trigger, sub)

    def _findFirstSub(self, sub: dict, name: str):
        for key, value in sub.items():
            if key == name:
                return value
            if value["sub"]:
                result = self._findFirstSub(value["sub"], name)
                if result is not None:
                    return result
        return None

    def AddSub(self, baseName, subName, trigger=None, sub=None):
        parent = self._findFirstSub(self.Content, baseName)
        if parent is None:
            raise KeyError(f"Catégorie '{baseName}' introuvable")
        parent["sub"][subName] = self._NewEntry(trigger, sub)

    def __repr__(self):
        def Read(sub, callstate: int = 0):
            tabulation = "\t" * callstate
            string = ""
            for index, (key, value) in enumerate(sub.items(), start=1):
                string += f"{tabulation}{index}-{key} : trigger={value['trigger']}\n"
                if value["sub"]:
                    string += Read(value["sub"], callstate + 1)
            return string
        return Read(self.Content)



class MainPageTopBar(Frame):
    ITEM_HEIGHT = 25
    MENU_WIDTH = 150
    TOP_ITEM_WIDTH = 70
    BG_COLOR = Theme.TOPBAR
    MENU_COLOR = Theme.MENU
    HOVER_COLOR = Theme.HOVER

    def __init__(self):
        super().__init__()

        self.OnClick = Signal()
        self.OnClick.Connect(self.OnClickEvent)

        StylePanel(self, Theme.TOPBAR, "TopBar")
        self.Position = Udim2(0, 0, 0, 0)
        self.Size = Udim2(1, 0, 0, TOPBAR_HEIGHT)

        layout = UIListLayout()
        layout.FillDirection = "horizontal"
        layout.VerticalAlignment = "center"
        layout.HorizontalAlignment = "left"
        self.AddChild(layout)

        self._OpenMenus: list[tuple[TextButton, Frame]] = []
        self._BuildMenu(self.Categories.Content, self, 0)

        UserInputService.InputBegan.Connect(self.OnMouseClick)

    def OnMouseClick(self, Input: InputObject, _GameProcessed):
        if Input.UserInputType != UserInputType.MouseButton1 or not self._OpenMenus:
            return
        for btn, frame in self._OpenMenus:
            if frame.GetRect().collidepoint(Input.Position) or btn.GetRect().collidepoint(Input.Position):
                return
        self.CloseMenus()


    def _CreateButton(self, name: str, depth: int) -> TextButton:
        btn = TextButton()
        btn.Text = name
        btn.Name = name
        btn.TextColor3 = Theme.TEXT
        btn.TextSize = 16
        btn.AutoButtonColor = False
        if depth == 0:
            btn.Size = Udim2(0, MainPageTopBar.TOP_ITEM_WIDTH, 1, 0)
            btn.BackgroundColor3 = MainPageTopBar.BG_COLOR
        else:
            btn.Size = Udim2(1, 0, 0, MainPageTopBar.ITEM_HEIGHT)
            btn.BackgroundColor3 = MainPageTopBar.MENU_COLOR

        baseColor = btn.BackgroundColor3
        btn.MouseEnter.Connect(lambda b=btn: setattr(b, "BackgroundColor3", MainPageTopBar.HOVER_COLOR))
        btn.MouseLeave.Connect(lambda b=btn, c=baseColor: setattr(b, "BackgroundColor3", c))
        return btn

    def _BuildMenu(self, sub: dict, parent, depth: int):
        for name, value in sub.items():
            btn = self._CreateButton(name, depth)
            btn.MouseButton1Click.Connect(lambda b=btn, v=value, d=depth: self._OnItemClick(b, v, d))
            parent.AddChild(btn)

    def _OnItemClick(self, btn: TextButton, value: dict, depth: int):
        if not value["sub"]:
            self.CloseMenus()
            if value["trigger"] is not None:
                value["trigger"]()
            return
        wasOpen = depth < len(self._OpenMenus) and self._OpenMenus[depth][0] is btn
        self.CloseMenus(depth)
        if wasOpen:
            return
        frame = Frame()
        StylePanel(frame, Theme.MENU, f"{btn.Name}Menu")
        frame.Size = Udim2(0, MainPageTopBar.MENU_WIDTH, 0, len(value["sub"]) * MainPageTopBar.ITEM_HEIGHT + 2)
        frame.Position = Udim2(0, 0, 1, 0) if depth == 0 else Udim2(1, 0, 0, 0)
        frame.ZIndex = 10
        frame.AddChild(UIListLayout(FillDirection="vertical"))
        frame.AddChild(UIPadding(PaddingLeft=Udim(0, 1), PaddingRight=Udim(0, 1),
                                 PaddingTop=Udim(0, 1), PaddingBottom=Udim(0, 1)))

        btn.AddChild(frame)
        self._OpenMenus.append((btn, frame))
        self._BuildMenu(value["sub"], frame, depth + 1)

    def CloseMenus(self, depth: int = 0):
        while len(self._OpenMenus) > depth:
            _, frame = self._OpenMenus.pop()
            frame.Destroy()

    @property
    def Categories(self):
        data = CategorieData()

        ##main categories
        data.AddBase("File")
        data.AddBase("Tools")
        data.AddBase("Run")

        ##sub
        data.AddSub("File", "Open", OnOpenClicked)
        data.AddSub("File", "New project", lambda: print("New project"))

        return data

    def OnClickEvent(self):
        pass


class MainPage(ScreenGui):
    def __init__(self):
        super().__init__()
        self.Size = Udim2(1, 0, 1, 0)
        self.Position = Udim2(0, 0, 0, 0)
        self.Name = "MainPage"
        self.Screens: list[Screen] = []
        self.ActiveScreen: Screen | None = None
        self.ContextMenu: ContextMenu | None = None

        self.ScreenArea = Frame()
        self.ScreenArea.Name = "ScreenArea"
        self.ScreenArea.BackgroundColor3 = Theme.BACKGROUND
        self.ScreenArea.Position = Udim2(0, 0, 0, TOPBAR_HEIGHT)
        self.ScreenArea.Size = Udim2(1, 0, 1, -TOPBAR_HEIGHT - STATUS_HEIGHT)
        self.AddChild(self.ScreenArea)

        self.StatusBar = TextLabel()
        StylePanel(self.StatusBar, Theme.TOPBAR, "StatusBar")
        self.StatusBar.Position = Udim2(0, 0, 1, -STATUS_HEIGHT)
        self.StatusBar.Size = Udim2(1, 0, 0, STATUS_HEIGHT)
        self.StatusBar.FontName = Theme.TREE_FONT
        self.StatusBar.TextSize = 13
        self.StatusBar.TextXAlignment = "left"
        self.StatusBar.TextTruncate = "atend"
        self.StatusBar.AddChild(UIPadding(PaddingLeft=Udim(0, 8), PaddingRight=Udim(0, 8)))
        self.SetStatus("File > Open pour ouvrir un projet")
        self.AddChild(self.StatusBar)

        self.OnPathRefresh = Signal()
        self.OnPathRefresh.Connect(self.OnPathRefreshEvent)

        self.TopBar = MainPageTopBar()
        self.AddChild(self.TopBar)

        self.ScreenBar = ScreenBar()
        self.ScreenBar.Position = Udim2(0, SCREENBAR_LEFT, 0, 0)
        self.ScreenBar.Size = Udim2(1, -SCREENBAR_LEFT, 0, TOPBAR_HEIGHT)
        self.ScreenBar.ZIndex = 5
        self.ScreenBar.Selected.Connect(self.SwitchScreen)
        self.ScreenBar.CloseRequested.Connect(self.CloseScreen)
        self.AddChild(self.ScreenBar)

        Event.OpenProject.Connect(self.LoadSideBarProjectFile)

    @property
    def ProjectTree(self):
        return self.Screens[0].SideBar.Root if self.Screens else None

    def LoadSideBarProjectFile(self, path: Path):
        if path is None or not path.is_dir():
            return
        for screen in self.Screens:
            screen.Destroy()
        self.Screens = []
        self.ActiveScreen = None
        self.AddScreen(path, path.name, closable=False)
        self.SetStatus("Clic gauche : ouvrir un fichier · clic droit : outils / nouvel écran depuis un dossier")

    def OnPathRefreshEvent(self):
        pass

    def AddScreen(self, root: Path, title: str, closable: bool = True) -> Screen:
        """Crée un écran dont l'arbre démarre à root (ou affiche celui qui existe déjà)."""
        for screen in self.Screens:
            if screen.Root == root:
                self.SwitchScreen(screen)
                return screen
        screen = Screen(root, title, closable)
        screen.ContextMenuRequested.Connect(lambda node, s=screen: self.OnNodeContextMenu(s, node))
        self.Screens.append(screen)
        self.ScreenArea.AddChild(screen)
        self.SwitchScreen(screen)
        return screen

    def SwitchScreen(self, screen: Screen):
        self.ActiveScreen = screen
        for other in self.Screens:
            other.Visible = other is screen
        self.ScreenBar.Refresh(self.Screens, screen)

    def CloseScreen(self, screen: Screen):
        if not screen.Closable or screen not in self.Screens:
            return
        index = self.Screens.index(screen)
        self.Screens.remove(screen)
        screen.Destroy()
        if self.ActiveScreen is screen:
            self.SwitchScreen(self.Screens[max(0, index - 1)])
        else:
            self.ScreenBar.Refresh(self.Screens, self.ActiveScreen)

    def SetStatus(self, text: str, color=Theme.TREE_ARROW):
        self.StatusBar.Text = text
        self.StatusBar.TextColor3 = color

    def OnNodeContextMenu(self, screen: Screen, node):
        if node.IsDir:
            items = [MenuItem("Nouvel écran depuis ce dossier", "édite ce dossier à part, sans le reste du projet",
                              lambda: self.AddScreen(node.Path, node.Name))]
        else:
            items = [MenuItem("Ouvrir dans un onglet", "affiche le fichier dans cet écran",
                              lambda: screen.OpenFile(node.Path))]
            items += [MenuItem(tool.Name, tool.Description, lambda tool=tool: self.RunTool(tool, node.Path))
                      for tool in GetTools(node.Path)]
        self.ShowContextMenu(node.Path, items)

    def ShowContextMenu(self, path: Path, items: list[MenuItem]):
        if self.ContextMenu is not None:
            self.ContextMenu.Close()
        menu = ContextMenu(path, items, UserInputService.GetMouseLocation() + (8, 4))
        menu.Closed.Connect(lambda: setattr(self, "ContextMenu", None) if self.ContextMenu is menu else None)
        self.AddChild(menu)
        menu.ClampToScreen(self.GetAbsSize())
        self.ContextMenu = menu

    def RunTool(self, tool, path: Path):
        self.SetStatus(f"{tool.Name} : {path.name}…", Theme.TEXT)

        def Done(result: ToolResult):
            self.SetStatus(result.Message, Theme.STATUS_OK if result.Success else Theme.STATUS_ERROR)
            if result.Output is not None:
                for screen in self.Screens:
                    screen.SideBar.Reload(result.Output)

        RunTool(tool, path, Done)
