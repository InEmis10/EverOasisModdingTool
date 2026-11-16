##TODO : Avoir le code editor qui est une class qui est display on clique d'une fichier
##TODO : Avoir le tree workspace qui affiche les fichier definit le type de fichier et est lod on clique sur une view qui differe en fonction du type
##TODO : Basic window event handling
import pygame_easy_gui as peg
from src.gui.page.MainPage import MainPage
from src import Event

class Workspace:
    DEFAULT_TITLE = "Ever Oasis Mods Maker"
    def __init__(self):
        self.App = peg.Application(Title=Workspace.DEFAULT_TITLE)
        self.Projects = []
        self.Path = None
        self.currentPath = None

        ##Gui handler
        self.MainPage = MainPage()
        self.App.Gui.Add(self.MainPage)

        ##EVENT
        Event.OpenProject.Connect(self.OnProjectOpened)

    ##TODO : RELOAD PROJECT TREE, CLOSE ALL TAB OPENED
    def OnProjectOpened(self, path):
        self.Path = path

    def run(self):
        self.App.run()
        if self.Path is None:
            self.SetTitle("Workspace")

    def SetTitle(self, title):
        self.App.setTitle(title)
