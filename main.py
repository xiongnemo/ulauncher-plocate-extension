"""Fast File Finder — Ulauncher extension using plocate.

Search modes:
  f <query>         — spaces become wildcards (glob *word* per token)
  f r <regex>       — raw regex mode
  f p <pathglob>    — path glob mode (e.g. f p *.pdf)
"""
import os
import subprocess
import shutil
import re
from pathlib import Path

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.event import ItemEnterEvent


def _find_plocate():
    return shutil.which("plocate") or shutil.which("locate")


def _run_locate(args: list[str], limit: int) -> list[str]:
    cmd = _find_plocate()
    if not cmd:
        return []
    try:
        result = subprocess.run(
            [cmd, "-i", "-l", str(limit)] + args,
            capture_output=True, text=True, timeout=5,
        )
        return [l for l in result.stdout.splitlines() if l.strip()]
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return []


def search_normal(query: str, limit: int) -> list[str]:
    """Spaces become wildcards: 'da vinci' → '*da*vinci*' (glob pattern)."""
    tokens = query.split()
    if not tokens:
        return []
    # Build glob pattern: each token wrapped in *...*
    pattern = "*" + "*".join(tokens) + "*"
    return _run_locate([pattern], limit)


def search_regex(pattern: str, limit: int) -> list[str]:
    """Raw regex mode."""
    return _run_locate([pattern], limit)


def search_path_glob(pattern: str, limit: int) -> list[str]:
    """Path glob mode: match against full path."""
    return _run_locate(["--glob", pattern], limit)


def format_result(path: str) -> tuple[str, str]:
    """Return (display_name, icon_path)."""
    p = Path(path)
    parent = p.parent.name or "/"
    name = p.name
    display = f"{name}  —  {parent}{os.sep}"
    return display, str(p)


def get_file_icon(path: str) -> str:
    """Return a suitable icon path."""
    ext = Path(path).suffix.lower()
    if Path(path).is_dir():
        return "images/folder.png"
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"):
        return "images/image.png"
    if ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
        return "images/audio.png"
    if ext in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
        return "images/video.png"
    if ext in (".pdf",):
        return "images/pdf.png"
    if ext in (".py", ".js", ".ts", ".rs", ".go", ".c", ".cpp", ".java", ".sh"):
        return "images/code.png"
    return "images/file.png"


class FinderExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryListener())
        self.subscribe(ItemEnterEvent, ItemEnterListener())


class ItemEnterListener(EventListener):
    def on_event(self, event, data):
        path = data
        return RenderResultListAction([
            ExtensionSmallResultItem(
                icon="images/file.png",
                name=f"Copy: {path}",
                on_enter=CopyToClipboardAction(path),
            ),
        ])


class KeywordQueryListener(EventListener):
    def on_event(self, event, extension):
        arg = (event.get_argument() or "").strip()
        limit = int(extension.preferences.get("limit", 10))
        ignore_case = extension.preferences.get("ignore_case", "true") == "true"

        if not arg:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Type to search files...",
                    description="Spaces are wildcards | 'r regex' for regex | 'p *.pdf' for path glob",
                    on_enter=None,
                ),
            ])

        # Parse mode
        if arg.startswith("r ") and len(arg) > 2:
            results = search_regex(arg[2:], limit)
        elif arg.startswith("p ") and len(arg) > 2:
            results = search_path_glob(arg[2:], limit)
        else:
            results = search_normal(arg, limit)

        if not results:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="No results found",
                    description=f'Search: "{arg}"',
                    on_enter=None,
                ),
            ])

        items = []
        for path in results:
            display, _ = format_result(path)
            items.append(ExtensionSmallResultItem(
                icon="images/file.png",
                name=display,
                description=path,
                on_enter=OpenAction(path),
            ))

        return RenderResultListAction(items)


if __name__ == "__main__":
    FinderExtension().run()
