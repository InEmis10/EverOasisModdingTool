"""Package racine de Ever Oasis Mods Maker.

Imports conseillés (depuis n'importe quel fichier du projet) :
    from src.classe import Workspace
    from src.gui.page import MainPage
    from src.gui.element import FileElement, FolderElement
    from src import Event

Ce fichier reste volontairement léger : importer ici Workspace / MainPage
créerait des imports circulaires (MainPage importe src.Event).
"""
