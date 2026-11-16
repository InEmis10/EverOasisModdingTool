"""Outils d'extraction d'Ever Oasis (scripts de ~/EverOasisProject/tool) vers le dossier modified/ de la workspace.

Workspace (créée par tool/workspace.sh) :
    workspace/
    ├── workspace.json   marqueur
    ├── base/            jeu d'origine extrait (exefs/, romfs/, extracted/)
    └── modified/        <- sortie des extractions, même arborescence que base/

Pour ajouter un outil : un ExtractTool dans TOOLS.
"""
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pygame_easy_gui import TimeService

WORKSPACE_MARKER = "workspace.json"
OUTPUT_DIR = "modified"

# Dossiers où chercher les scripts (extract, decompile, asm.py), dans l'ordre.
# Variable d'environnement EVEROASIS_TOOLS : prioritaire.
TOOL_DIR_CANDIDATES = [
    "{workspace}/../tool",
    "{workspace}/../EverOasisMods/binary",
    "~/EverOasisProject/tool",
    "~/EverOasisProject/EverOasisMods/binary",
]


class ToolError(Exception):
    pass


# Workspace
def FindWorkspace(path: Path) -> Path | None:
    """Dossier contenant workspace.json, en remontant depuis path"""
    for folder in [path, *path.parents]:
        if (folder / WORKSPACE_MARKER).is_file():
            return folder
    return None


def RelativeInWorkspace(path: Path, workspace: Path) -> Path:
    """Chemin à reproduire dans modified/ : relatif à base/ si le fichier vient du jeu d'origine"""
    base = workspace / "base"
    if path.is_relative_to(base):
        return path.relative_to(base)
    return path.relative_to(workspace)


def FindToolDir(workspace: Path) -> Path:
    candidates = []
    if os.environ.get("EVEROASIS_TOOLS"):
        candidates.append(os.environ["EVEROASIS_TOOLS"])
    candidates += [c.format(workspace=workspace) for c in TOOL_DIR_CANDIDATES]
    for c in candidates:
        folder = Path(c).expanduser().resolve()
        if (folder / "extract").is_file():
            return folder
    raise ToolError("outils introuvables (extract, decompile…) : définis EVEROASIS_TOOLS=chemin/vers/tool")


# Outils
@dataclass(frozen=True)
class ExtractTool:
    Name: str                                        # affiché dans le menu
    Description: str
    Extensions: tuple[str, ...]                      # extensions acceptées ("*" = toutes)
    Output: Callable[[Path], Path]                   # chemin dans modified/ -> sortie produite
    Command: Callable[[Path, Path, Path], list] | None = None   # (outils, source, sortie) -> commande ; None = copie

    def Accepts(self, path: Path) -> bool:
        return "*" in self.Extensions or path.suffix.lower().lstrip(".") in self.Extensions


TOOLS: list[ExtractTool] = [
    ExtractTool(
        "Ouvrir l'archive", "extract : fichiers de l'archive dans <nom>_x/",
        ("gar", "zar", "lzs"),
        Output=lambda rel: rel.with_name(rel.name + "_x"),
        # extract écrit <dossier -o>/<nom>_x/
        Command=lambda tools, src, out: [sys.executable, str(tools / "extract"), "extract", str(src), "-o", str(out.parent)],
    ),
    ExtractTool(
        "Décompiler en Squirrel (.nut)", "decompile : code lisible et modifiable",
        ("gsb",),
        Output=lambda rel: rel.with_suffix(".nut"),
        Command=lambda tools, src, out: [sys.executable, str(tools / "decompile"), str(src), "-o", str(out)],
    ),
    ExtractTool(
        "Désassembler (.gsa)", "asm.py dump : bytecode éditable, recompilable à l'identique",
        ("gsb",),
        Output=lambda rel: rel.with_suffix(".gsa"),
        Command=lambda tools, src, out: [sys.executable, str(tools / "asm.py"), "dump", str(src), "-o", str(out)],
    ),
    ExtractTool(
        "Copier tel quel", "copie le fichier d'origine pour le modifier",
        ("*",),
        Output=lambda rel: rel,
    ),
]


def GetTools(path: Path) -> list[ExtractTool]:
    return [t for t in TOOLS if t.Accepts(path)]


# Exécution
@dataclass
class ToolResult:
    Success: bool
    Message: str
    Output: Path | None = None


def RunTool(tool: ExtractTool, source: Path, on_done: Callable[[ToolResult], None]) -> None:
    """Lance l'outil sans bloquer l'interface ; on_done(ToolResult) est appelé à la fin.
    Ne remplace jamais une sortie existante (elle peut contenir des modifications)."""
    try:
        workspace = FindWorkspace(source.parent)
        if workspace is None:
            raise ToolError(f"{source.name} n'est pas dans une workspace (pas de {WORKSPACE_MARKER})")
        out = workspace / OUTPUT_DIR / tool.Output(RelativeInWorkspace(source, workspace))
        if out.exists():
            raise ToolError(f"existe déjà : {out.relative_to(workspace)}")
        out.parent.mkdir(parents=True, exist_ok=True)

        if tool.Command is None:
            shutil.copy2(source, out)
            on_done(ToolResult(True, f"copié vers {out.relative_to(workspace)}", out))
            return

        proc = subprocess.Popen(tool.Command(FindToolDir(workspace), source, out),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except (ToolError, OSError, ValueError) as e:
        on_done(ToolResult(False, str(e)))
        return

    def Check():
        if proc.poll() is None:
            return
        timer.Cancel()
        log = proc.stdout.read().strip()
        proc.stdout.close()
        errors = [line for line in log.splitlines() if "ERREUR" in line or "Error" in line]
        if proc.returncode == 0 and out.exists() and not errors:
            on_done(ToolResult(True, f"{tool.Name} → {out.relative_to(workspace)}", out))
        else:
            detail = (errors or log.splitlines() or [f"code {proc.returncode}"])[-1]
            on_done(ToolResult(False, f"{tool.Name} a échoué : {detail}", out if out.exists() else None))

    timer = TimeService.Every(0.1, Check)
