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
- 🔤 **Pinyin Support**: Add pinyin initials for better sorting and searching  
  **拼音支持**: 添加拼音首字母以便更好地排序和搜索
- 📁 **Batch Processing**: Process multiple files and directories at once  
  **批量处理**: 一次性处理多个文件和目录
- 🔄 **Revert Capability**: Easily restore original filenames  
  **还原功能**: 轻松恢复原始文件名
- 🗜️ **ZIP Support**: Extract and rename files from ZIP archives  
  **ZIP支持**: 从ZIP压缩包中提取并重命名文件
- 🎯 **File Filtering**: Include or exclude specific file types  
  **文件过滤**: 包含或排除特定文件类型
- 🌐 **Platform-Aware**: Optimize renaming based on gaming platform  
  **平台感知**: 基于游戏平台优化重命名

## 📖 Examples | 示例

### Before → After | 重命名前后对比

| Original | Renamed |
|----------|---------|
| `黄金太阳 - 失落的时代[Mobile&Elffinal](简)(UE)(128Mb).zip` | `H 黄金太阳 - 失落的时代 (Golden Sun: The Lost Age) (2002)[简].gba` |
| `哈利波特 - 阿兹卡班的逃犯[施珂昱](简)(JP)(128Mb).zip` | `H 哈利波特 - 阿兹卡班的逃犯 (Harry Potter and the Prisoner of Azkaban) (2004)[简].gba` |
| `指环王－王者归来(0.4b小字体)[Advance-004](简)(JP)(136Mb).zip` | `Z 指环王－王者归来 (The Lord of the Rings: The Return of the King) (2003) [简].gba` |
| `王国之心 - 记忆之链[天使汉化组](简)(JP)(256Mb).zip` | `W 王国之心 - 记忆之链 (Kingdom Hearts- Chain of Memories) (2004)[简].gba` |

## 🚀 Usage | 使用方法

```bash
renamer [command] [options]
```

### 📋 Global Options | 全局选项

```

Commands:
  rename [options]  批量重命文件夹中的文件为拼音首字母+原文件名 (Batch rename files to pinyin initials)
  revert [options]  还原文件名 (Revert file names)
  about             显示关于信息 (Show about information)
```

## 📝 Rename Command | 重命名命令

### Syntax | 语法
```bash
renamer rename [options]
```

### 🛠️ Options | 选项参数

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--directory` | `-dir` | TEXT | 要重命名的文件夹路径 (Directory path to rename files in) |
| `--files` | `-files` | TEXT | 要重命名的文件 (Specific files to rename) |
| `--trim` | `-t` | FLAG | 去除无用的信息 (Trim unnecessary information from filename) |
| `--dry-run` | `-d` | FLAG | 只输出结果，不实际重命名 (Preview results without actual renaming) |
| `--pinyin` | `-py` | FLAG | 在开头加上拼音首字符 (Add pinyin initials for better sorting) |
| `--includes` | `-i` | TEXT | 只处理特定的文件类型 e.g: gba (Process only specific file types) |
| `--excludes` | `-e` | TEXT | 不处理特定的文件类型 e.g: zip (Exclude specific file types) |
| `--output` | `-o` | FLAG | 只输出重命名后的文件名 (Output only renamed filenames) |
| `--recursive` | `-r` | FLAG | 读取子目录中的文件 (Process files in subdirectories) |
| `--unzip` | `-u` | FLAG | 解压ZIP文件 (Extract ZIP files) |
| `--password` | `-pwd` | TEXT | ZIP文件密码 (Password for ZIP files) |
| `--ai` | `-ai` | FLAG | 使用AI重命名 (Use AI for intelligent renaming) |
| `--model` | `-m` | TEXT | AI模型设置 (AI model configuration) |
| `--api-key` | `-key` | TEXT | AI模型API密钥 (API key for AI model) |
| `--endpoint` | `-ep` | TEXT | AI模型API端点 (API endpoint for AI model) |
| `--platform` | `-p` | TEXT | ROM平台信息 (Platform info for better AI recognition) |

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

# Rename files in subdirectories with AI
# 使用AI重命名子目录中的文件
renamer rename -r -ai --directory "~/ROMs/" -t -m "gpt-3.5-turbo" -key "your_api_key" -p "GBＡ"
```

### 📤 Sample Output | 输出示例
```
铁臂阿童木-阿童木之心的秘密[v1.0][心灵的冬天](简)(66Mb).zip 
→ T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy - The Video Game) (2004) - 简.zip
```

## ↩️ Revert Command | 还原命令

### Syntax | 语法
```bash
renamer revert [options]
```

### 🛠️ Options | 选项参数

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--directory` | `-dir` | TEXT | 要还原文件名的文件夹路径 (Directory path to revert files in) |
| `--files` | `-files` | TEXT | 要还原的特定文件 (Specific files to revert) |
| `--recursive` | `-r` | FLAG | 处理子目录 (Process subdirectories) |
| `--dry-run` | `-d` | FLAG | 预览还原结果 (Preview revert results) |

### 💡 Example Usage | 使用示例

```bash
# Revert all files in directory
# 还原目录中的所有文件
renamer revert "D:/Downloads/"

# Dry run revert
# 预览还原结果（不实际执行）
renamer revert -d "~/ROMs/"
```

### 📤 Sample Output | 输出示例
```
T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy -  The Video Game) (2004) - 简.gba 
→ 铁臂阿童木-阿童木之心的秘密[v1.0][心灵的冬天](简)(66Mb).gba
```

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
- [ ] 🔄 **Local cache** - Improve performance and reduce API calls
  **本地缓存** - 提高性能并减少API调用
- [ ] 🔄 **GUI Support** - Add GUI support for easier use.
  **图形界面支持** - 增加图形界面。

## 📝 License | 许可证

This project is open source and available under the [MIT License](LICENSE).

该项目为开源项目，遵循 [MIT 许可证](LICENSE)。

## 🤝 Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

欢迎贡献！请随时提交 Pull Request 或创建 Issue。

---

**Made with ❤️ for retro gaming enthusiasts**

**为复古游戏爱好者用心制作 ❤️**
