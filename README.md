ulauncher-plocate-extension

Fast file search extension for Ulauncher using plocate.

Features

- f da vinci — contains both da and vinci, any order
- f "da vinci" — exact phrase
- f da vinci ext:pdf — extension filter
- f ext:jpg;png cat — multiple extension filters
- f da vinci path:Music — path substring filter
- f regex:da.*vinci — regex mode

Requirements

bash
sudo apt install plocate
sudo updatedb


Installation

bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/xiongnemo/ulauncher-plocate-extension.git nemo.ulauncher-finder


Restart Ulauncher.

Usage

Default keyword: f

- Enter: open file
- Alt+Enter: copy path

Notes

This plugin searches file paths only. It does not search file contents.
