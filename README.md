# 🎮 ROM AI 批量重命名工具

**[📥 下载最新版本](https://github.com/rozx/AI-ROMS-batch-renamer/releases/latest)**

[![GitHub Release](https://img.shields.io/github/v/release/rozx/AI-ROMS-batch-renamer)](https://github.com/rozx/AI-ROMS-batch-renamer/releases)
[![Github All Releases](https://img.shields.io/github/downloads/rozx/AI-ROMS-batch-renamer/total.svg)](https://github.com/rozx/AI-ROMS-batch-renamer/releases)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/rozx/AI-ROMS-batch-renamer/issues)

支持终端与图形界面，结合本地别名数据库与 AI 进行 ROM 批量重命名。

## 🆕 v3.0.0 新功能亮点

> **v3.0.0** 在原有 AI 工作流基础上新增三大核心功能：

### 🖥️ 全新图形界面

基于 **PySide6** 的桌面 GUI 正式上线，无需使用终端。重命名、还原、缓存管理等所有操作均可在界面中完成，与 CLI 行为完全一致，所有设置会话间自动保存。

![GUI Screenshot](screenshots/gui3.0.png)

### 📖 本地英/中文标题查找

`--cn-lookup` 可从内置平台 CSV 数据库**离线**解析英文与中文标题，无需 API 密钥。采用多步模糊匹配（精确 → 模糊 → 别名），优先返回 USA / World 区版本，输出格式与 AI 模块完全兼容，可无缝混用。

### 🔍 Tavily 远程 MCP 联网搜索

通过 `--tavily-api-key` 接入 `mcp.tavily.com`，为 AI 重命名增加实时网络搜索支持，无需安装 Node.js，对冷门或命名混乱的 ROM 特别有效。

---

## ✨ 功能特性

| 功能 | 说明 |
| ---- | ---- |
| 🖥️ 图形界面 | 完整的 PySide6 桌面 GUI，与所有 CLI 选项保持同步 |
| 📖 本地查找 (`--cn-lookup`) | 从内置 CSV 数据库离线解析英文与中文标题，无需 API 密钥 |
| 🤖 AI 补全 (`--ai`) | 通过任意 OpenAI 兼容 API 批量查询标题 |
| 🔍 Tavily 联网搜索 (`--tavily-api-key`) | 通过 `mcp.tavily.com` 进行实时网络搜索，无需 Node.js |
| 🔤 拼音首字母 (`--pinyin`) | 在文件名前添加拼音首字母，优化排序 |
| 🧩 平台别名归一化 (`--platform`) | 自动将常见平台别名转换为标准名称 |
| 🔄 还原功能 | 从历史缓存中恢复原始文件名 |
| 🗜️ ZIP 支持 (`--unzip`) | 解压 ZIP 压缩包并重命名内容 |
| 💾 智能缓存 | 自动跳过重复 AI 请求，可用 `--ai-no-cache` 禁用 |
| 🛡️ 安全默认 | 自动跳过已重命名文件，除非使用 `--force` |

## 📖 重命名示例

| 原始文件名 | 重命名后 |
| ---------- | -------- |
| `黄金太阳 - 失落的时代[Mobile&Elffinal](简)(UE)(128Mb).zip` | `H Golden Sun - The Lost Age (黄金太阳 - 失落的时代) [简].gba` |
| `哈利波特 - 阿兹卡班的逃犯[施珂昱](简)(JP)(128Mb).zip` | `H Harry Potter and the Prisoner of Azkaban (哈利波特 - 阿兹卡班的逃犯) [简].gba` |
| `指环王－王者归来(0.4b小字体)[Advance-004](简)(JP)(136Mb).zip` | `Z The Lord of the Rings - The Return of the King (指环王 - 王者归来) [简].gba` |

## ⚡ 快速开始

```bash
git clone https://github.com/rozx/AI-ROMS-batch-renamer.git
cd AI-ROMS-batch-renamer
poetry install
```

**图形界面（新手推荐）**

```bash
poetry run gui
```

将 ROM 目录拖入输入框，选择平台，勾选所需选项，点击 **🚀 开始重命名** 即可。

**命令行 — 建议先模拟运行预览**

```bash
# 模拟运行，不修改文件
poetry run main rename -d -r --cn-lookup -p GBA -t -py -dir "~/ROMs/GBA"

# 实际执行
poetry run main rename    -r --cn-lookup -p GBA -t -py -dir "~/ROMs/GBA"

# 加 AI 补全
poetry run main rename    -r --cn-lookup --ai -p GBA --ai-batch-size 15 -t -py -dir "~/ROMs/GBA"
```

**还原文件名**

```bash
poetry run main revert -d -dir "~/ROMs/GBA"   # 预览还原
poetry run main revert    -dir "~/ROMs/GBA"   # 执行还原
```

## 🖥️ 图形界面说明

![GUI Screenshot](screenshots/gui_start.png)

窗口分为左右两栏：**设置面板**（左）和**实时日志**（右）。

| 界面字段 | 对应 CLI 参数 | 说明 |
| -------- | ------------- | ---- |
| 平台 | `--platform` | 支持别名自动补全，如输入 `gb` → `Game Boy` |
| 裁剪多余字符 | `--trim` | 处理前去除文件名中的噪声标签 |
| 拼音转换 | `--pinyin` | 添加拼音首字母 |
| 中文别名查找 | `--cn-lookup` | 离线查找，需要指定平台 |
| 递归子目录 | `--recursive` | 处理子目录中的文件 |
| 模拟运行 | `--dry-run` | 仅预览，不修改文件 |
| 强制重命名 | `--force` | 重新处理已重命名的文件 |
| 自动解压 | `--unzip` | 解压 ZIP 压缩包 |
| 启用 AI 重命名 | `--ai` | 展开 AI 配置区域 |
| 模型 / API Key / Endpoint | `--model / --api-key / --endpoint` | OpenAI 兼容设置 |
| Tavily API Key | `--tavily-api-key` | 启用实时联网搜索 |
| 批量大小 | `--ai-batch-size` | 每次 AI 请求的文件数量（默认 10） |

## 📝 命令行参考

### `rename`

```bash
renamer rename [选项]
```

| 参数 | 简写 | 类型 | 说明 |
| ---- | ---- | ---- | ---- |
| `--directory` | `-dir` | TEXT | 要重命名的目录路径 |
| `--files` | `-files` | TEXT | 要重命名的文件（分号分隔多个） |
| `--platform` | `-p` | TEXT | 平台提示（GBA、NDS、PSX 等） |
| `--trim` | `-t` | FLAG | 去除文件名中的噪声标签 |
| `--dry-run` | `-d` | FLAG | 仅预览，不修改文件 |
| `--pinyin` | `-py` | FLAG | 添加拼音首字母 |
| `--recursive` | `-r` | FLAG | 递归处理子目录 |
| `--force` | `-f` | FLAG | 强制重新处理已重命名文件 |
| `--unzip` | `-u` | FLAG | 解压 ZIP 后再重命名 |
| `--password` | `-pwd` | TEXT | 加密 ZIP 的解压密码 |
| `--includes` | `-i` | TEXT | 仅处理指定扩展名（可重复） |
| `--excludes` | `-e` | TEXT | 跳过指定扩展名（可重复） |
| `--output` | `-o` | FLAG | 仅输出新文件名（静默模式） |
| `--cn-lookup` | `--cn` | FLAG | 从内置 CSV 离线查找标题（需要 `--platform`） |
| `--ai` | `-ai` | FLAG | 启用 AI 补全 |
| `--model` | `-model` | TEXT | AI 模型（如 `deepseek-chat`、`gpt-4o-mini`） |
| `--api-key` | `-key` | TEXT | 覆盖 API 密钥 |
| `--endpoint` | `-ep` | TEXT | 自定义 OpenAI 兼容接口地址 |
| `--ai-batch-size` | | INT | 每次 AI 请求的文件数量（默认 10） |
| `--ai-no-cache` | `-nc` | FLAG | 跳过 AI 缓存，强制重新请求 |
| `--tavily-api-key` | `-tav` | TEXT | Tavily API Key，用于联网搜索增强 |

**常用示例：**

```bash
# 仅使用本地查找（无需 API 密钥）
renamer rename --cn-lookup -p GBA -t -py -dir "~/ROMs/GBA"

# 本地查找 + AI 补全（中文 ROM 合集推荐）
renamer rename --cn-lookup --ai -p GBA -t -py --ai-batch-size 15 -dir "~/ROMs/GBA"

# 自定义 AI 端点（如 DeepSeek）
renamer rename --ai -p GBA -model "deepseek-chat" -ep "https://api.deepseek.com" -key "sk-..." -dir "~/ROMs/GBA"

# 终极组合：本地库 + AI + 联网搜索
renamer rename --cn-lookup --ai --tavily-api-key "tvly-xxxx" -p GBA -t -py -dir "~/ROMs/GBA"

# 处理单个文件
renamer rename --cn-lookup --ai -p GBA -files "~/ROMs/GBA/黄金太阳.zip"

# 递归处理所有子目录
renamer rename -r --cn-lookup --ai -p NDS -t -py -dir "~/ROMs/"

# 强制重新处理已重命名文件
renamer rename -r --cn-lookup --ai -f -p GBA -dir "~/ROMs/GBA"
```

### `revert`

```bash
renamer revert [选项]
```

| 参数 | 简写 | 类型 | 说明 |
| ---- | ---- | ---- | ---- |
| `--directory` | `-dir` | TEXT | 要还原的目录路径 |
| `--files` | `-files` | TEXT | 要还原的文件（分号分隔多个） |
| `--recursive` | `-r` | FLAG | 递归处理子目录 |
| `--dry-run` | `-d` | FLAG | 仅预览，不修改文件 |

### `clear-cache`

```bash
renamer clear-cache [-d] [-y]
```

| 参数 | 说明 |
| ---- | ---- |
| `--delete-files / -d` | 删除缓存目录及缓存文件 |
| `--yes / -y` | 跳过确认提示 |

### 退出码

| 代码 | 含义 |
| ---- | ---- |
| `0` | 成功 |
| `1` | I/O 或权限错误 |
| `2` | 参数无效或缺少必要输入 |
| `3` | AI API 错误 |
| `4` | ZIP 解压失败 |

## ⚙️ 配置与缓存路径

| 路径 | 用途 |
| ---- | ---- |
| `%APPDATA%/ai-rom-batch-renamer/config.json`（Windows） | AI 配置文件 |
| `$XDG_CONFIG_HOME/ai-rom-batch-renamer/config.json`（Linux/macOS） | AI 配置文件 |
| `<temp>/ai-rom-batch-renamer/renamerRomInfoCache.cache` | AI 结果缓存 |
| `<temp>/ai-rom-batch-renamer/renamerHistory.cache` | 重命名历史（还原功能依赖此文件） |

## 🛠️ 从源码构建

```bash
poetry run build --verbose                    # 构建 CLI 版本
poetry run build --target gui --verbose       # 构建 GUI 版本
poetry run build --target both --verbose      # 同时构建两者
```

## 📝 许可证

[MIT License](LICENSE) — 欢迎通过 Pull Request 或 Issue 参与贡献。

## 🙏 致谢

[rom-name-cn](https://github.com/yingw/rom-name-cn) — ROM 中英文名称数据库

---

为复古游戏爱好者用心制作 ❤️


