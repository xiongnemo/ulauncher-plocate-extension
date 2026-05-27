# Fast File Finder (plocate) — Ulauncher Extension

[中文说明](README.zh-CN.md)

Instant file-path search for Ulauncher powered by `plocate` (or `locate`).

## Features

- AND search with multiple tokens (any order)
- Quoted phrases: `"..."`
- Filters / modes: `ext:` / `path:` / `regex:`
- Result text: `name - full path` (directories end with `/`)
- Icons: uses your current desktop icon theme when possible; falls back to `images/icon.png`

> This extension searches file paths only (not file contents).

## Requirements

- Ulauncher 5.x (API v2)
- `plocate` (recommended) or `locate`
- `updatedb` (to build/update the index database)

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install plocate
sudo updatedb
```

Optional (for themed system icons; often already present with Ulauncher installs):

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

## Installation

### Option A: Ulauncher Extensions (recommended)

Open and install from the official catalog:

https://ext.ulauncher.io/-/github-xiongnemo-ulauncher-plocate-extension

### Option B: Manual (git clone)

```bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/xiongnemo/ulauncher-plocate-extension.git nemo.ulauncher-finder
```

Then restart Ulauncher.

## Configuration

Ulauncher Preferences → Extensions → Fast File Finder:

- **Keyword** (default: `f`)
- **Max results** (default: `10`)
- **Case sensitivity**

Notes:

- Case sensitivity affects the base `plocate` query (normal tokens / regex).
- `ext:` and `path:` filtering is always case-insensitive.

## Usage

Trigger: `f <query>` (or your configured keyword).

### Query syntax

- `f da vinci`
  - AND search: matches paths containing both tokens
- `f "da vinci"`
  - treat the phrase as a single token
- `f report ext:pdf`
  - extension filter
- `f cat ext:jpg;png`
  - multiple extensions separated by `;` or `,`
- `f invoice path:Downloads`
  - path substring filter (can be repeated; all parts must match)
- `f regex:da.*vinci`
  - regex mode (delegates to `plocate --regex`; see `man plocate`)

### Actions

- **Enter**: open file/folder
- **Alt+Enter**: copy full path

## Troubleshooting

### New files are not found

`plocate` searches an index database. New/renamed/moved files appear only after an update:

```bash
sudo updatedb
```

To enable periodic updates (systemd):

```bash
sudo systemctl enable --now plocate-updatedb.timer
```

Also check `/etc/updatedb.conf` (`PRUNEPATHS` / `PRUNEFS`) if some locations are excluded.

### Missing themed icons

- The extension falls back to `images/icon.png`
- Install the optional GTK/Gio Python bindings listed above

## Notes

- Path search only; no content search.
- Results come from the index database; deleted paths may linger until the next `updatedb`.
