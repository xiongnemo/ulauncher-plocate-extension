# ulauncher-finder

Fast file search extension for [Ulauncher](https://ulauncher.io) using [plocate](https://plocate.sesse.net/).

## Features

- **Spaces are wildcards** — `da vinci` matches `da_vinci.jpg`, `Da Vinci Code.pdf`, etc.
- **Three search modes:**
  - `f <query>` — fuzzy glob search (default)
  - `f r <regex>` — raw regex mode
  - `f p <pathglob>` — path glob mode (e.g., `f p *.pdf`)
- **Fast** — powered by plocate's indexed database
- **Configurable** — result limit, case sensitivity, keyword

## Requirements

- [plocate](https://plocate.sesse.net/) (`sudo apt install plocate`)
- Updated index: `sudo updatedb`

## Installation

### Via Ulauncher Extensions

Search for "Fast File Finder" in Ulauncher's extension manager.

### Manual

```bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/xiongnemo/ulauncher-plocate-extension.git nemo.ulauncher-finder
```

Then restart Ulauncher.

## Usage

| Input | Mode | Example |
|-------|------|---------|
| `f da vinci` | Glob | Matches files containing both "da" and "vinci" |
| `f r \.pdf$` | Regex | Matches files ending in .pdf |
| `f p *.pdf` | Path glob | Matches .pdf files in the path |

- **Enter** → Open file with default app
- **Alt+Enter** → Copy path to clipboard

## Configuration

In Ulauncher Preferences → Extensions → Fast File Finder:

- **Keyword** — trigger keyword (default: `f`)
- **Max results** — number of results to show (default: `10`)
- **Case insensitive** — ignore case when searching (default: on)

## License

MIT
