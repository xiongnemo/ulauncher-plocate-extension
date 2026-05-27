# Fast File Finder (plocate) — Ulauncher Extension

使用 `plocate`（或 `locate`）的索引库实现“秒级”的文件路径搜索。

亮点：

- 多关键词 AND 搜索（任意顺序）
- 支持引号短语：`"..."`
- 支持过滤/模式：`ext:` / `path:` / `regex:`
- 结果展示：`name - full path`，目录名自动追加 `/`
- 结果图标：优先使用系统主题图标（GNOME/KDE 等），失败则回退到插件内置图标

> 注意：这是“路径搜索”，不是“内容搜索”。

## Requirements

- Ulauncher 5.x（API v2）
- `plocate`（推荐）或 `locate`
- `updatedb`（用于生成/更新索引库）

Debian/Ubuntu：

```bash
sudo apt update
sudo apt install plocate
sudo updatedb
```

可选（用于系统主题图标；通常装了 Ulauncher 就已经满足）：

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

## Installation

```bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/xiongnemo/ulauncher-plocate-extension.git nemo.ulauncher-finder
```

然后重启 Ulauncher。

## Configuration

在 Ulauncher Preferences → Extensions → Fast File Finder 中可配置：

- **Keyword**：默认 `f`
- **Max results**：默认 `10`
- **Case sensitivity**：默认 Ignore case

说明：

- Case sensitivity 影响 `plocate` 的基础搜索（普通关键词/regex）。
- `ext:` / `path:` 过滤本身始终不区分大小写。

## Usage

触发：`f <query>`（或你配置的 keyword）。

### Query Syntax

- `f da vinci`
	- AND 搜索：路径里同时包含 `da` 和 `vinci`（任意顺序）
- `f "da vinci"`
	- 把带空格的短语当作一个整体 token
- `f report ext:pdf`
	- 按扩展名过滤（例如 `.pdf`）
- `f cat ext:jpg;png`
	- 多扩展名：用 `;` 或 `,` 分隔
- `f invoice path:Downloads`
	- 路径子串过滤（匹配完整路径字符串）
	- 支持多个 `path:`：例如 `path:Downloads path:2026`，需要全部命中
- `f regex:da.*vinci`
	- 正则模式（等价于 `plocate --regex` 的行为；语法以 `man plocate` 为准）

组合示例：

- `f budget ext:xlsx path:Work`

### Actions

- **Enter**：打开文件/目录
- **Alt+Enter**：复制完整路径

## Troubleshooting

### 为什么新建的文件搜不到？

`plocate` 只查询索引库，不会实时扫描磁盘。新文件/移动/重命名后，需要更新 DB 才能搜到：

```bash
sudo updatedb
```

如果你希望自动更新（systemd）：

```bash
sudo systemctl enable --now plocate-updatedb.timer
```

另外，`/etc/updatedb.conf` 里的 `PRUNEPATHS` / `PRUNEFS` 可能会排除某些目录或文件系统，导致“永远搜不到”。

### 没有系统图标 / 图标都一样

- 插件会自动回退到 `images/icon.png`
- 确认安装了 GTK/Gio 的 Python 绑定（见 Requirements 的可选项）
- 一些极简环境没有完整的 icon theme，也可能导致主题图标查找失败

### 搜索很慢或直接没结果

- 插件调用 `plocate` 有 5 秒超时；复杂正则可能导致超时
- 建议先在终端复现：`plocate -l 20 <pattern>` 或 `plocate --regex <regex>`，确认 `plocate` 本身是否耗时

## Notes

- 只搜索“路径”，不搜索文件内容。
- 结果来自索引库：已删除/移动的旧路径可能会短暂存在，直到下次 `updatedb`。
