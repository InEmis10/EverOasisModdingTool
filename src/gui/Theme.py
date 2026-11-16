import pygame
from pygame_easy_gui import Color3


def _FindFont(*names):
    """Première police système trouvée parmi names (None = police par défaut de pygame)"""
    for name in names:
        path = pygame.font.match_font(name)
        if path:
            return path
    return None


class Theme:
    BACKGROUND = Color3(30, 31, 34)
    TOPBAR = Color3(43, 45, 48)
    SIDEBAR = Color3(37, 38, 41)
    MENU = Color3(50, 52, 56)
    HOVER = Color3(65, 105, 170)
    BORDER = Color3(70, 73, 78)
    TEXT = Color3(220, 220, 220)

    # Arbre de fichiers
    TREE_HOVER = Color3(50, 52, 56)
    TREE_SELECTED = Color3(46, 67, 110)
    TREE_FOLDER_TEXT = Color3(220, 220, 220)
    TREE_FILE_TEXT = Color3(180, 182, 186)
    TREE_ARROW = Color3(150, 152, 158)
    TREE_FONT = _FindFont("liberationsans", "dejavusans", "cantarell")  # NotoSans variable colle le point après "r"
    TREE_TEXT_SIZE = 14

    STATUS_OK = Color3(120, 200, 120)
    STATUS_ERROR = Color3(235, 110, 100)

    CODE_FONT = _FindFont("adwaitamono", "liberationmono", "monospace")
    CODE_TEXT_SIZE = 13
    CODE_BACKGROUND = Color3(30, 31, 34)
    CODE_GUTTER = Color3(37, 38, 41)
    CODE_LINE_NUMBER = Color3(100, 102, 108)
    CODE_TEXT = Color3(212, 212, 212)
    CODE_KEYWORD = Color3(204, 120, 50)
    CODE_STRING = Color3(106, 171, 115)
    CODE_NUMBER = Color3(104, 151, 187)
    CODE_COMMENT = Color3(128, 128, 128)
    CODE_FUNCTION = Color3(255, 198, 109)
    CODE_CONSTANT = Color3(152, 118, 170)
