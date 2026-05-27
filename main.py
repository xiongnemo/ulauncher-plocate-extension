"""Fast File Finder — Ulauncher extension using plocate.

Syntax:
    f da vinci              AND search: contains both da and vinci, any order
    f "da vinci"            exact phrase
    f da vinci ext:pdf      extension filter
    f ext:jpg;png cat       multiple extension filters
    f da vinci path:Music   path substring filter
    f regex:da.*vinci       regex mode
"""
import shlex
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

try:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gio, Gtk
except Exception:
    Gio = None
    Gtk = None

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


def find_plocate():
    return shutil.which("plocate") or shutil.which("locate")


_SYSTEM_ICON_LOOKUP_SIZE = 64
_ICON_THEME = Gtk.IconTheme.get_default() if Gtk else None


@lru_cache(maxsize=512)
def _lookup_themed_icon_file(icon_name: str, size: int):
    if not _ICON_THEME or not Gtk or not icon_name:
        return None

    # Prefer non-SVG icons since GdkPixbuf SVG support is loader-dependent.
    for flags in (
        Gtk.IconLookupFlags.FORCE_SIZE | Gtk.IconLookupFlags.NO_SVG,
        Gtk.IconLookupFlags.FORCE_SIZE,
    ):
        info = _ICON_THEME.lookup_icon(icon_name, size, flags)
        if not info:
            continue
        filename = info.get_filename()
        if filename:
            return filename

    return None


def _gicon_to_icon_path(icon, size: int):
    if not Gio or not icon:
        return None

    # Unwrap emblems.
    if isinstance(icon, Gio.EmblemedIcon):
        return _gicon_to_icon_path(icon.get_icon(), size)

    if isinstance(icon, Gio.FileIcon):
        file = icon.get_file()
        return file.get_path() if file else None

    if isinstance(icon, Gio.ThemedIcon):
        names = list(icon.get_names() or [])
        preferred = [n for n in names if not n.endswith("-symbolic")]
        fallback = [n for n in names if n.endswith("-symbolic")]
        for name in preferred + fallback:
            filename = _lookup_themed_icon_file(name, size)
            if filename:
                return filename

    return None


@lru_cache(maxsize=4096)
def get_system_icon_path(path: str, size: int = _SYSTEM_ICON_LOOKUP_SIZE):
    """Resolve a filesystem path to an icon file from the current GTK icon theme.

    Returns an absolute icon file path (PNG/SVG), or None on failure.
    """
    if not (Gio and Gtk and _ICON_THEME):
        return None

    try:
        info = Gio.File.new_for_path(path).query_info(
            "standard::icon",
            Gio.FileQueryInfoFlags.NONE,
            None,
        )
        icon = info.get_icon() if info else None
        return _gicon_to_icon_path(icon, size)
    except Exception:
        return None


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


def parse_limit(value, default=10):
    try:
        value = int(value)
        return value if value > 0 else default
    except Exception:
        return default


def parse_query(query):
    """Parse a small Everything-like query language.

    Returns:
        patterns: normal plocate AND patterns
        ext_filters: set of suffixes like {'.pdf'}
        path_filters: list of lowercase path substrings
        regex_pattern: optional regex string
    """
    try:
        tokens = shlex.split(query)
    except ValueError:
        # Unclosed quote: fall back to simple splitting instead of erroring.
        tokens = query.split()

    patterns = []
    ext_filters = set()
    path_filters = []
    regex_parts = []

    for token in tokens:
        lower = token.lower()

        if lower.startswith("ext:"):
            raw = token[4:]
            for ext in raw.replace(",", ";").split(";"):
                ext = ext.strip().lower().lstrip(".")
                if ext:
                    ext_filters.add("." + ext)
            continue

        if lower.startswith("path:"):
            path = token[5:].strip()
            if path:
                path_filters.append(path.lower())
            continue

        if lower.startswith("regex:"):
            regex = token[6:].strip()
            if regex:
                regex_parts.append(regex)
            continue

        patterns.append(token)

    regex_pattern = " ".join(regex_parts).strip() if regex_parts else None
    return patterns, ext_filters, path_filters, regex_pattern


def run_plocate(patterns, limit, case_sensitive=False, regex=False):
    cmd = find_plocate()
    if not cmd:
        return []

    # Fetch more than we display because ext:/path: post-filters may discard rows.
    search_limit = max(limit * 10, 50)

    args = [cmd, "-l", str(search_limit)]
    if not case_sensitive:
        args.append("-i")
    if regex:
        args.append("--regex")

    args.extend(patterns)

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode not in (0, 1):
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def post_filter(paths, ext_filters=None, path_filters=None, limit=10):
    ext_filters = ext_filters or set()
    path_filters = path_filters or []

    out = []
    seen = set()

    for path in paths:
        if path in seen:
            continue
        seen.add(path)

        p = Path(path)
        lower_path = path.lower()

        if ext_filters and p.suffix.lower() not in ext_filters:
            continue

        if path_filters and not all(part in lower_path for part in path_filters):
            continue

        out.append(path)
        if len(out) >= limit:
            break

    return out


def score_path(path, patterns):
    """Simple ranking: basename matches and shorter paths first."""
    p = Path(path)
    basename = p.name.lower()
    lower_path = path.lower()

    score = 0
    for pat in patterns:
        low = pat.lower()
        if low in basename:
            score -= 20
        elif low in lower_path:
            score -= 5

    score += len(path) / 1000
    return score


def search(query, limit=10, case_sensitive=False):
    patterns, ext_filters, path_filters, regex_pattern = parse_query(query)

    if regex_pattern:
        raw = run_plocate([regex_pattern], limit, case_sensitive=case_sensitive, regex=True)
        return post_filter(raw, ext_filters, path_filters, limit)

    if not patterns and not ext_filters and not path_filters:
        return []

    # Use plocate to prefilter ext:/path: queries instead of searching "*" first.
    base_patterns = list(patterns)
    if not case_sensitive:
        base_patterns.extend(path_filters)

    def _run(pats):
        return run_plocate(pats or ["*"], limit, case_sensitive=case_sensitive, regex=False)

    if ext_filters:
        raw = []
        for ext in sorted(ext_filters):
            raw.extend(_run(base_patterns + [ext]))
    else:
        raw = _run(base_patterns)

    filtered = post_filter(raw, ext_filters, path_filters, max(limit * 3, limit))
    filtered.sort(key=lambda p: score_path(p, patterns))
    return filtered[:limit]


def format_result(path):
    p = Path(path)
    name = p.name or path
    try:
        is_dir = p.is_dir()
    except OSError:
        is_dir = False

    if is_dir and name not in ("/",) and not name.endswith("/"):
        name = name + "/"

    return f"{name} - {path}", ""


class FinderExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryListener())
        self.subscribe(ItemEnterEvent, ItemEnterListener())


class ItemEnterListener(EventListener):
    def on_event(self, event, extension):
        path = event.get_data()
        return RenderResultListAction([
            ExtensionSmallResultItem(
                icon="images/icon.png",
                name="Copy path",
                description=path,
                on_enter=CopyToClipboardAction(path),
            )
        ])


class KeywordQueryListener(EventListener):
    def on_event(self, event, extension):
        arg = (event.get_argument() or "").strip()
        limit = parse_limit(extension.preferences.get("limit"), 10)
        case_sensitive = parse_bool(extension.preferences.get("case_sensitive"), False)

        if not arg:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Type to search files...",
                    description='Examples: da vinci | "da vinci" | ext:pdf | path:Music | regex:da.*vinci',
                    on_enter=None,
                )
            ])

        results = search(arg, limit=limit, case_sensitive=case_sensitive)

        if not results:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="No results found",
                    description=f"Search: {arg}",
                    on_enter=None,
                )
            ])

        items = []
        for path in results:
            name, parent = format_result(path)
            icon = get_system_icon_path(path) or "images/icon.png"
            items.append(ExtensionSmallResultItem(
                icon=icon,
                name=name,
                description=parent,
                on_enter=OpenAction(path),
                on_alt_enter=CopyToClipboardAction(path),
            ))

        return RenderResultListAction(items)


if __name__ == "__main__":
    FinderExtension().run()
