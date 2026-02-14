# 🎮 ROM AI Batch Renamer | ROM AI批量重命名工具

A powerful command-line tool for batch renaming ROM files using AI technology.

一个使用AI技术批量重命名ROM文件的强大命令行工具。

[![GitHub Release](https://img.shields.io/github/v/release/rozx/AI-ROMS-batch-renamer)](https://github.com/rozx/AI-ROMS-batch-renamer/releases)
[![Github All Releases](https://img.shields.io/github/downloads/rozx/AI-ROMS-batch-renamer/total.svg)](https://github.com/rozx/AI-ROMS-batch-renamer/releases)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/rozx/AI-ROMS-batch-renamer/issues)

## 📥 Downloads | 下载

**[🔗 Click here to download | 点击这里下载](https://github.com/rozx/AI-ROMS-batch-renamer/releases/latest)**

## ✨ Features | 功能特性

- 🤖 **AI-Powered Renaming**: Intelligent file renaming using advanced AI models  
  **AI智能重命名**: 使用先进AI模型进行智能文件重命名
- 🧠 **Batch AI Enrichment**: Query multiple filenames in one request (`--ai-batch-size`) to reduce latency & cost  
  **批量AI增强**: 使用批量查询降低延迟与成本
- 🔤 **Pinyin Support**: Add pinyin initials for better sorting and searching  
  **拼音支持**: 添加拼音首字母以便更好地排序和搜索
- 📁 **Batch Processing**: Process multiple files and directories (with recursion)  
  **批量处理**: 支持递归处理多个文件与目录
- 🔄 **Revert Capability**: Easily restore original filenames  
  **还原功能**: 轻松恢复原始文件名
- 🗜️ **ZIP Support**: Extract and rename files from ZIP archives (with optional password)  
  **ZIP支持**: 支持解压（含密码）并重命名压缩包内容
- 🎯 **File Filtering**: Include or exclude specific file types  
  **文件过滤**: 包含或排除特定文件类型
- 🌐 **Platform-Aware**: Optimize AI enrichment via platform hints (`--platform`)  
  **平台感知**: 通过平台提示优化 AI 结果
- 💾 **Smart Caching**: Avoid duplicate AI calls (disable with `--ai-no-cache`)  
  **智能缓存**: 避免重复 AI 请求（可用 `--ai-no-cache` 禁用）
- 🛡️ **Safe Idempotent Runs**: Skip already-renamed files unless forced (`--force`)  
  **安全幂等**: 自动跳过已处理文件，除非使用 `--force`
- 🧹 **Filename Trimming**: Remove noisy segments before enrichment (`--trim`)  
  **文件名清理**: 清理噪声后再进行处理
- 🧼 **Cache Management**: Clear cache data or delete cache files (`clear-cache`)  
  **缓存管理**: 支持清空缓存数据或删除缓存文件（`clear-cache`）

## 📖 Examples | 示例

### Before → After | 重命名前后对比

| Original                                                       | Renamed                                                                                 |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `黄金太阳 - 失落的时代[Mobile&Elffinal](简)(UE)(128Mb).zip`    | `H 黄金太阳 - 失落的时代 (Golden Sun: The Lost Age) (2002)[简].gba`                     |
| `哈利波特 - 阿兹卡班的逃犯[施珂昱](简)(JP)(128Mb).zip`         | `H 哈利波特 - 阿兹卡班的逃犯 (Harry Potter and the Prisoner of Azkaban) (2004)[简].gba` |
| `指环王－王者归来(0.4b小字体)[Advance-004](简)(JP)(136Mb).zip` | `Z 指环王－王者归来 (The Lord of the Rings: The Return of the King) (2003) [简].gba`    |
| `王国之心 - 记忆之链[天使汉化组](简)(JP)(256Mb).zip`           | `W 王国之心 - 记忆之链 (Kingdom Hearts- Chain of Memories) (2004)[简].gba`              |

## 🚀 Usage | 使用方法

```bash
renamer [command] [options]
```

### 📋 Global Options | 全局选项

```text

Commands:
  rename [options]       批量重命名文件 (Batch rename files)
  revert [options]  还原文件名 (Revert file names)
  gui                   启动图形界面 (Launch GUI)
  clear-cache [options] 清除缓存数据 (Clear cache data)
  about                 显示关于信息 (Show about information)
```

## 🖥️ GUI Mode | 图形界面模式

```bash
# via CLI app command
poetry run main gui

# via dedicated script entry
poetry run gui
```

- Requires `PySide6` dependency.
  **需要安装 `PySide6` 依赖。**
- GUI internally calls CLI commands, so behavior/exit codes stay consistent.
  **GUI 内部复用 CLI 命令，行为与退出码保持一致。**

## 📝 Rename Command | 重命名命令

### Syntax | 语法

```bash
renamer rename [options]
```

### 🛠️ Options | 选项参数

| Option            | Short    | Type | Description                                                    |
| ----------------- | -------- | ---- | -------------------------------------------------------------- |
| `--directory`     | `-dir`   | TEXT | 要重命名的文件夹路径 (Directory path to rename files in)       |
| `--files`         | `-files` | TEXT | 要重命名的文件 (Specific file to rename; single path)          |
| `--trim`          | `-t`     | FLAG | 去除无用的信息 (Trim noisy segments from filename)             |
| `--dry-run`       | `-d`     | FLAG | 只输出结果，不实际重命名 (Preview only; no changes)            |
| `--pinyin`        | `-py`    | FLAG | 在开头加上拼音首字符 (Add pinyin initial for sorting)          |
| `--includes`      | `-i`     | TEXT | 只处理特定扩展 (Only process these extensions; repeatable)     |
| `--excludes`      | `-e`     | TEXT | 排除特定扩展 (Skip these extensions; repeatable)               |
| `--output`        | `-o`     | FLAG | 只输出新文件名 (Print new names only; quiet mode)              |
| `--recursive`     | `-r`     | FLAG | 递归处理子目录 (Process subdirectories)                        |
| `--unzip`         | `-u`     | FLAG | 解压 zip 再处理 (Unzip archives then rename contents)          |
| `--password`      | `-pwd`   | TEXT | zip 文件密码 (Password for encrypted ZIP)                      |
| `--ai`            | `-ai`    | FLAG | 使用 AI 获取游戏信息 (Enable AI enrichment)                    |
| `--model`         | `-model` | TEXT | AI 模型 (Model identifier)                                     |
| `--api-key`       | `-key`   | TEXT | AI API 密钥 (Override API key)                                 |
| `--endpoint`      | `-ep`    | TEXT | AI API 端点 (Custom base URL)                                  |
| `--platform`      | `-p`     | TEXT | 平台提示 (Platform hint: GBA, NDS, PSX...)                     |
| `--ai-batch-size` |          | INT  | AI 批量查询大小 (Batch size for multi-file AI requests)        |
| `--ai-no-cache`   | `-nc`    | FLAG | 禁用 AI 缓存 (Disable caching; force fresh calls)              |
| `--force`         | `-f`     | FLAG | 强制重命名已处理文件 (Force rename even if previously renamed) |

### 💡 Example Usage | 使用示例

```bash
# Basic rename with AI and pinyin support
# 基础重命名，使用AI和拼音支持
renamer rename -t -py -dir "D:/Downloads/"

# Dry run to preview changes
# 预览更改（不实际执行）
renamer rename -d -t -py -ai --directory "~/ROMs/"

# Process specific file types only
# 仅处理特定文件类型
renamer rename -i "gba" -i "zip" -dir "~/Games/" -t

# Rename files in subdirectories with AI (batched calls)
# 使用AI重命名子目录中的文件（批量调用）
renamer rename -r -ai --directory "~/ROMs/" -t -model "deepseek-chat" -ep "https://api.deepseek.com" -key "your_api_key" -p "GBA" --ai-batch-size 20

# Force fresh AI results (no cache)
# 强制不使用缓存，始终从AI获取
renamer rename -r -ai --directory "~/ROMs/" -t -p "GBA" --ai-no-cache

```

### 🔧 Additional Examples | 更多示例

```bash

# 1. Dry run first, then execute (推荐先预览)
renamer rename -d -r -ai -dir "~/ROMs/GBA" -p GBA --ai-batch-size 15
renamer rename -r -ai -dir "~/ROMs/GBA" -p GBA --ai-batch-size 15

# 2. Force reprocess already renamed files (强制重新处理已重命名文件)
renamer rename -r -ai -f -dir "~/ROMs/GBA" -p GBA

# 3. Unzip with password then rename (带密码解压后重命名)
renamer rename -r -u -pwd "mypassword" -dir "~/Incoming/Archives" -i zip -ai -p NDS

# 4. Includes + Excludes combo (组合过滤)
renamer rename -dir "~/MixedRoms" -i gba -i zip -e txt -t

# 5. Quiet output (只输出新文件名)
renamer rename -dir "~/ROMs/GBA" -o -ai -p GBA

# 6. Disable cache for troubleshooting (禁用缓存以排查)
renamer rename -dir "~/ROMs/GBA" -ai -p GBA --ai-no-cache

# 7. Minimal AI single file (单文件 AI 处理)
renamer rename -files "~/ROMs/GBA/黄金太阳.zip" -ai -p GBA

# 8. Large batch size tuning (大批量调优)
renamer rename -r -ai -dir "~/ROMs/GBA" --ai-batch-size 25 -p GBA

# 9. Pinyin only normalization (仅拼音首字母规范化)
renamer rename -dir "~/ChineseRoms" -py -t
```

### ⚡ Quickstart | 快速开始

1. Install dependencies | 安装依赖

```bash
git clone https://github.com/rozx/AI-ROMS-batch-renamer.git
cd AI-ROMS-batch-renamer
poetry install
```


2. Run a dry preview | 运行预览

```bash
poetry run main rename -d -r -ai -dir "~/ROMs/GBA" -p GBA --ai-batch-size 15 -t -py
```

3. Execute for real | 真正执行

```bash
poetry run main rename -r -ai -dir "~/ROMs/GBA" -p GBA --ai-batch-size 15 -t -py
```

4. Revert if needed | 如需还原

```bash
poetry run main revert -d -dir "~/ROMs/GBA"
poetry run main revert -dir "~/ROMs/GBA"
```

5. Build onefile binary | 构建单文件可执行

```bash
poetry run build --verbose
```

#### ✅ Recommended Workflow | 推荐工作流

| Step | Action                          | Rationale            |
| ---- | ------------------------------- | -------------------- |
| 1    | Dry run (`-d`)                  | 确认重命名结果安全   |
| 2    | Enable trim & pinyin            | 清理噪声并优化排序   |
| 3    | Add platform hint               | 更精确的 AI 标题匹配 |
| 4    | Increase batch size (10–25)     | 减少 API 调用次数    |
| 5    | Inspect cache file              | 复用结果，节约配额   |
| 6    | Use `--force` only if necessary | 避免无意义重复处理   |

#### 🔍 Tips | 小贴士

- Prefer starting with smaller batches to validate AI results.
  **建议先从较小批次开始验证 AI 结果，确保重命名逻辑正确。**
- Use `--output` for scripting pipelines (e.g., feeding names to another tool).
  **使用 `--output` 便于脚本管道处理（例如传递结果给其他工具）。**
- Avoid `--ai-no-cache` for large runs unless debugging freshness.
  **大量处理时避免使用 `--ai-no-cache`，除非需要调试最新结果。**
- Refinement retry is triggered only when `englishTitle` is missing; other missing fields are not retried automatically.
  **细化重试仅在 `englishTitle` 缺失时触发；其他字段缺失不会自动重试。**
- Revert stores original path keyed by new filename; keep `renamerHistory.cache` safe.
  **还原功能依赖 `renamerHistory.cache`，请妥善保存避免误删。**

#### 🛡️ Safety | 安全

- Always keep backups of curated ROM sets.
  **务必保留 ROM 集合的备份，以防意外修改。**
- Run on a copy first if unsure.
  **不确定时先在副本目录执行，确认结果后再处理正式目录。**
- Encrypted ZIPs are handled only if password provided; errors will skip gracefully.
  **加密 ZIP 需提供密码才能处理，失败会被跳过而不中断整体流程。**

### 📤 Sample Output | 输出示例

```text
铁臂阿童木-阿童木之心的秘密[v1.0][心灵的冬天](简)(66Mb).zip 
→ T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy - The Video Game) (2004) - 简.zip
```

## ↩️ Revert Command | 还原命令

### Syntax (Revert) | 语法（还原）

```bash
renamer revert [options]
```

### 🛠️ Options (Revert) | 选项参数（还原）

| Option        | Short    | Type | Description                                                  |
| ------------- | -------- | ---- | ------------------------------------------------------------ |
| `--directory` | `-dir`   | TEXT | 要还原文件名的文件夹路径 (Directory path to revert files in) |
| `--files`     | `-files` | TEXT | 要还原的特定文件 (Specific file to revert; single path)      |
| `--recursive` | `-r`     | FLAG | 处理子目录 (Process subdirectories)                          |
| `--dry-run`   | `-d`     | FLAG | 预览还原结果 (Preview revert results)                        |

### 💡 Example Usage (Revert) | 使用示例（还原）

```bash
# Revert all files in directory
# 还原目录中的所有文件
renamer revert --directory "D:/Downloads/"

# Dry run revert
# 预览还原结果（不实际执行）
renamer revert --dry-run --directory "~/ROMs/"
```

### 📤 Sample Output (Revert) | 输出示例（还原）

```text
T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy -  The Video Game) (2004) - 简.gba 
→ 铁臂阿童木-阿童木之心的秘密[v1.0][心灵的冬天](简)(66Mb).gba
```

## 🧼 Clear Cache Command | 缓存清理命令

### Syntax (Clear Cache) | 语法（清理缓存）

```bash
renamer clear-cache [options]
```

### 🛠️ Options (Clear Cache) | 选项参数（清理缓存）

| Option             | Short | Type | Description                                                          |
| ------------------ | ----- | ---- | -------------------------------------------------------------------- |
| `--delete-files`   | `-d`  | FLAG | 删除整个缓存目录与缓存文件 (Delete cache directory and cache files)  |
| `--yes`            | `-y`  | FLAG | 跳过确认提示 (Skip confirmation prompt)                             |

### 💡 Example Usage (Clear Cache) | 使用示例（清理缓存）

```bash
# Clear cache data only (keep files)
# 仅清空缓存数据（保留缓存目录）
renamer clear-cache

# Delete cache directory without prompt
# 删除缓存目录且不提示确认
renamer clear-cache -d -y
```

## ⚙️ Config & Cache Paths | 配置与缓存路径

- AI 配置文件默认保存在用户配置目录：
  - Windows: `%APPDATA%/ai-rom-batch-renamer/config.json`
  - Linux/macOS: `$XDG_CONFIG_HOME/ai-rom-batch-renamer/config.json`（未设置时回退到 `~/.config/...`）
- 兼容旧版：若工作目录存在 `config.json`，会自动迁移到新目录。
- 缓存目录使用系统临时目录：`<temp>/ai-rom-batch-renamer`
  - `renamerRomInfoCache.cache`：AI 元数据缓存
  - `renamerHistory.cache`：重命名历史（revert 依赖）

## 🛠️ Build from Source | 从源码构建

```bash
# 1) Install dependencies
poetry install

# 2) Build cross-platform onefile binary (dynamic spec)
poetry run build --verbose

# 3) Build GUI only
poetry run build --target gui --verbose

# 4) Build both terminal + GUI in one command
poetry run build --target both --verbose

# Options:
#   --target cli|gui|both   构建终端版 / GUI版 / 同时构建（默认 cli）
#   --outdir ./dist         指定输出目录
#   --name my-binary        自定义输出文件名
#   --icon ./assets/icos/icon.ico    Windows 图标
#   --icon ./assets/icos/icon.icns   MacOS 图标
#   --no-windows-disable-console      GUI 版在 Windows 保留控制台窗口
#   --extra ...             追加原生 Nuitka 参数
#   --dry-run               仅打印命令，不实际构建
```

版本来源优先级：环境变量 APP_VERSION > pyproject.toml 中的 version。

## 🔁 Versioning & Releases | 版本与发布

- CI 使用 Release Drafter 计算版本标签（例如 `v2.1.0`）。
- 构建任务下载标签并设置 `APP_VERSION`，然后执行 `APP_VERSION="$APP_VERSION" poetry run bump` 以同步版本文件。
- 构建调用 `poetry run build --verbose`，并在每个平台生成两类产物：Terminal（`main.py`）与 GUI（`gui.py`）。
- 产物以版本号命名并上传至同一个草稿发布（每个平台各 2 份压缩包）。

如果你更偏向以本地 `pyproject.toml` 为真源（Option A），也可以直接基于其版本创建发布并跳过标签到版本的转换。

## 🔧 Version bump (local) | 本地版本号更新

本仓库使用 bump2version 同步版本至多个文件（`pyproject.toml` 与 `ai_rom_batch_renamer/modules/const.py`）。

配置文件：`.bumpversion.cfg`

```bash
# 交互式选择 patch/minor/major
poetry run bump

# 直接按位更新
poetry run bump-patch
poetry run bump-minor
poetry run bump-major
```

在 CI 的 Option B 模式下（Release Drafter 生成 tag），构建任务会设置 `APP_VERSION` 环境变量并运行统一脚本：

```bash
# 同步 pyproject.toml 与 ai_rom_batch_renamer/modules/const.py
APP_VERSION="$APP_VERSION" poetry run bump
```

如果提供了 `APP_VERSION`，该脚本会直接写入对应版本；否则会回退为 patch 自动递增。这样应用的 About/版本输出将与发布标签一致。

## 🗺️ Roadmap | 开发路线图

- [x] ✅ **AI ROM Title Fetch** - *(v2.0.0)*  
  **AI ROM标题获取** *(v2.0.0)*
- [x] ✅ **Original Filename Storage** - For revert functionality *(v2.0.0)*  
  **原始文件名存储** - 用于还原功能 *(v2.0.0)*
- [x] ✅ **AI-Powered Prettification** - Enhanced naming with AI *(v2.0.0)*  
  **AI智能美化** - 使用AI增强命名 *(v2.0.0)*
- [x] 🔄 **Multiple AI Model Support** - Support for different AI providers  
  **多AI模型支持** - 支持不同的AI提供商
- [x] 🔄 **Third-party OpenAI API Integration** - Extended API compatibility
  **第三方OpenAI API集成** - 扩展API兼容性
- [x] 🔄 **Local cache** - Improve performance and reduce API calls
  **本地缓存** - 提高性能并减少API调用
- [x] ✅ **GUI Support** - GUI is now available and integrated with CLI behavior.
  **图形界面支持** - 已上线并与 CLI 行为保持一致。

## 📝 License | 许可证

This project is open source and available under the [MIT License](LICENSE).

该项目为开源项目，遵循 [MIT 许可证](LICENSE)。

## 🤝 Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

欢迎贡献！请随时提交 Pull Request 或创建 Issue。

---

Made with ❤️ for retro gaming enthusiasts

为复古游戏爱好者用心制作 ❤️
