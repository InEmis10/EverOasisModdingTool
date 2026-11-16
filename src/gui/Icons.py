"""Petites icônes vectorielles (12 x 12 px) dessinées avec pygame.draw : aucune police ni image nécessaire.

Draw(Surface, "archive", cx, cy, Color) dessine l'icône centrée sur (cx, cy).
Pour ajouter une icône : une fonction _Nom(S, x, y, c) où (x, y) est le coin haut-gauche du carré 12 x 12.
"""
import pygame

SIZE = 12


def _Archive(S, x, y, c):          # boîte avec couvercle
    pygame.draw.rect(S, c, (x, y + 1, 12, 3))
    pygame.draw.rect(S, c, (x + 1, y + 4, 10, 7), 1)
    pygame.draw.line(S, c, (x + 4, y + 6), (x + 7, y + 6))


def _Image(S, x, y, c):            # cadre avec montagne et soleil
    pygame.draw.rect(S, c, (x, y + 1, 12, 10), 1)
    pygame.draw.polygon(S, c, [(x + 2, y + 9), (x + 5, y + 5), (x + 7, y + 7), (x + 8, y + 6), (x + 10, y + 9)])
    pygame.draw.rect(S, c, (x + 8, y + 3, 2, 2))


def _Cube(S, x, y, c):             # cube en perspective
    top = [(x + 6, y), (x + 11, y + 3), (x + 6, y + 6), (x + 1, y + 3)]
    pygame.draw.polygon(S, c, top, 1)
    pygame.draw.lines(S, c, False, [(x + 1, y + 3), (x + 1, y + 9), (x + 6, y + 12), (x + 11, y + 9), (x + 11, y + 3)])
    pygame.draw.line(S, c, (x + 6, y + 6), (x + 6, y + 11))


def _Film(S, x, y, c):             # pellicule
    pygame.draw.rect(S, c, (x + 1, y, 10, 12), 1)
    for dy in (2, 5, 8):
        pygame.draw.rect(S, c, (x + 2, y + dy, 1, 2))
        pygame.draw.rect(S, c, (x + 9, y + dy, 1, 2))
    pygame.draw.rect(S, c, (x + 4, y + 3, 4, 6))


def _Code(S, x, y, c):             # </>
    pygame.draw.lines(S, c, False, [(x + 3, y + 3), (x, y + 6), (x + 3, y + 9)], 2)
    pygame.draw.lines(S, c, False, [(x + 9, y + 3), (x + 12, y + 6), (x + 9, y + 9)], 2)
    pygame.draw.line(S, c, (x + 7, y + 2), (x + 5, y + 10), 2)


def _Chip(S, x, y, c):             # puce électronique
    pygame.draw.rect(S, c, (x + 2, y + 2, 8, 8), 1)
    pygame.draw.rect(S, c, (x + 4, y + 4, 4, 4))
    for d in (3, 6, 8):
        pygame.draw.line(S, c, (x + d, y), (x + d, y + 1))
        pygame.draw.line(S, c, (x + d, y + 11), (x + d, y + 10))
        pygame.draw.line(S, c, (x, y + d), (x + 1, y + d))
        pygame.draw.line(S, c, (x + 11, y + d), (x + 10, y + d))


def _Text(S, x, y, c):             # lignes de texte
    pygame.draw.rect(S, c, (x, y + 1, 12, 2))
    pygame.draw.line(S, c, (x, y + 5), (x + 11, y + 5))
    pygame.draw.line(S, c, (x, y + 8), (x + 11, y + 8))
    pygame.draw.line(S, c, (x, y + 11), (x + 7, y + 11))


def _Note(S, x, y, c):             # note de musique
    pygame.draw.circle(S, c, (x + 3, y + 9), 3)
    pygame.draw.circle(S, c, (x + 9, y + 8), 3)
    pygame.draw.line(S, c, (x + 5, y + 9), (x + 5, y + 1), 2)
    pygame.draw.line(S, c, (x + 11, y + 8), (x + 11, y), 2)
    pygame.draw.line(S, c, (x + 5, y + 1), (x + 11, y), 2)


def _Table(S, x, y, c):            # tableau
    pygame.draw.rect(S, c, (x, y + 1, 12, 10), 1)
    pygame.draw.rect(S, c, (x, y + 1, 12, 3))
    pygame.draw.line(S, c, (x, y + 7), (x + 11, y + 7))
    pygame.draw.line(S, c, (x + 5, y + 4), (x + 5, y + 10))


def _Window(S, x, y, c):           # fenêtre d'interface
    pygame.draw.rect(S, c, (x, y + 1, 12, 10), 1)
    pygame.draw.rect(S, c, (x, y + 1, 12, 3))
    pygame.draw.rect(S, c, (x + 2, y + 6, 4, 3))
    pygame.draw.line(S, c, (x + 7, y + 6), (x + 9, y + 6))
    pygame.draw.line(S, c, (x + 7, y + 8), (x + 9, y + 8))


def _Spark(S, x, y, c):            # étincelle (effets)
    pygame.draw.polygon(S, c, [(x + 6, y), (x + 7, y + 5), (x + 12, y + 6), (x + 7, y + 7),
                               (x + 6, y + 12), (x + 5, y + 7), (x, y + 6), (x + 5, y + 5)])


def _Doc(S, x, y, c):              # page avec coin plié
    pygame.draw.lines(S, c, True, [(x + 2, y), (x + 7, y), (x + 10, y + 3), (x + 10, y + 11), (x + 2, y + 11)])
    pygame.draw.lines(S, c, False, [(x + 7, y), (x + 7, y + 3), (x + 10, y + 3)])


_ICONS = {
    "archive": _Archive, "image": _Image, "cube": _Cube, "film": _Film, "code": _Code,
    "chip": _Chip, "text": _Text, "note": _Note, "table": _Table, "window": _Window,
    "spark": _Spark, "doc": _Doc,
}


def Draw(Surface: pygame.Surface, Name: str, cx: int, cy: int, Color) -> None:
    _ICONS.get(Name, _Doc)(Surface, cx - SIZE // 2, cy - SIZE // 2, tuple(Color))
