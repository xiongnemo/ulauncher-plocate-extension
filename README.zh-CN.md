# Fast File Finder（plocate）— Ulauncher 扩展

[English README](README.md)

基于 `plocate`（或 `locate`）索引库的“秒级”文件路径搜索扩展。

## 特性

- 多关键词 AND 搜索（任意顺序）
- 支持引号短语：`"..."`
- 支持过滤/模式：`ext:` / `path:` / `regex:`
- 结果展示：`name - full path`（目录名自动追加 `/`）
- 图标：尽量使用系统主题图标（GNOME/KDE 等），失败则回退到 `images/icon.png`

> 这是“路径搜索”，不是“内容搜索”。

## 依赖

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

## 安装

### 方式 A：Ulauncher 官方 Extensions（推荐）

打开下面页面并按提示安装：

https://ext.ulauncher.io/-/github-xiongnemo-ulauncher-plocate-extension

### 方式 B：手动安装（git clone）

```bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/xiongnemo/ulauncher-plocate-extension.git nemo.ulauncher-finder
```

然后重启 Ulauncher。

## 配置

Ulauncher Preferences → Extensions → Fast File Finder：

- **Keyword**（默认 `f`）
- **Max results**（默认 `10`）
- **Case sensitivity**

说明：

- Case sensitivity 影响 `plocate` 的基础搜索（普通关键词/regex）。
- `ext:` / `path:` 过滤本身始终不区分大小写。

## 使用

触发：`f <query>`（或你配置的 keyword）。

### 查询语法

- `f da vinci`
  - AND 搜索：路径里同时包含两个 token
- `f "da vinci"`
  - 把带空格的短语当作一个整体 token
- `f report ext:pdf`
  - 扩展名过滤
- `f cat ext:jpg;png`
  - 多扩展名过滤：用 `;` 或 `,` 分隔
- `f invoice path:Downloads`
  - 路径子串过滤（可重复写多个 `path:`；需要全部命中）
- `f regex:da.*vinci`
  - 正则模式（实际走 `plocate --regex`；以 `man plocate` 为准）

### 快捷键

- **Enter**：打开文件/目录
- **Alt+Enter**：复制完整路径

## 排错

### 为什么新建/移动的文件搜不到？

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
- 安装上面“可选依赖”里的 GTK/Gio Python 绑定

## 备注

- 只搜索“路径”，不搜索文件内容。
- 结果来自索引库：已删除/移动的旧路径可能会短暂存在，直到下次 `updatedb`。
