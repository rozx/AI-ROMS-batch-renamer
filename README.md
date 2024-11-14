# Rom-batch-renamer

A command line tool for batch renaming ROM files using AI.

一个使用AI来批量重命名ROM文件的命令行工具。

[![HitCount](https://hits.dwyl.com/rozx/rozx/AI-ROMS-batch-renamer.svg?style=flat-square)](http://hits.dwyl.com/rozx/rozx/AI-ROMS-batch-renamer)  [![Github All Releases](https://img.shields.io/github/downloads/rozx/AI-ROMS-batch-renamer/total.svg)]()  [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/rozx/AI-ROMS-batch-renamer/issues)

## Downloads


[点击这里下载 | Click here to download](https://github.com/rozx/AI-ROMS-batch-renamer/releases/latest)



## Examples

- 黄金太阳 - 失落的时代\[Mobile&Elffinal](简)(UE)(128Mb).zip -> H 黄金太阳 - 失落的时代 (Golden Sun: The Lost Age) (2002) - 简.gba
- 哈利波特 - 阿兹卡班的逃犯\[施珂昱](简)(JP)(128Mb).zip -> H 哈利波特 - 阿兹卡班的逃犯 (Harry Potter and the Prisoner of Azkaban) (2004) - 简.gba
- 指环王－王者归来(0.4b小字体)\[Advance-004](简)(JP)(136Mb).zip -> Z 指环王－王者归来 (The Lord of the Rings: The Return of the King) (2003) - 简.gba
- 王国之心 - 记忆之链\[天使汉化组](简)(JP)(256Mb).zip -> W 王国之心 - 记忆之链 (Kingdom Hearts- Chain of Memories) (2004) - 简.gba

## Usage

```
Options:
  -V, --version           output the version number
  -h, --help              display help for command

Commands:
  rename [options] [dir]  批量重命文件夹中的文件为拼音首字母+原文件名 (Batch rename files to pinyin initials)
  revert [options] <dir>  还原文件名 (Revert file names)
  help [command]          display help for command
```

## Rename

```
Usage: renamer rename [options] [dir]

批量重命文件夹中的文件为拼音首字母+原文件名 (Batch rename files to pinyin initials)

Arguments:
    dir                      文件夹路径 (Directory path)

Options:
  -d, --dry-run                       仅显示重命名后的文件名，不实际重命名 (Display the renamed file names without actually renaming them)
  -n, --name-only                     仅显示重命名后的文件名，不输出其他信息 (Display the renamed file names only, without other information)
  -r, --recursive                     递归重命名文件夹中的所有文件 (Recursively rename all files in the directory)
  -t, --trim                          去除文件名中的空格与括号中的信息 (Remove spaces and content in brackets in file names)
  -f, --force                         强制重命名文件，即使文件名已经被命名过了 (Force rename files even if the file name already being renamed)
  -fl, --files <files...>             只重命名文件，不重命名文件夹,以空格分隔 (Only rename files, not folders, separated by spaces)
  -e, --excludes <extension name...>  排除特定的文件后缀名，以空格分隔 (Filer out certain files by extensions, separated by spaces)
  -i, --includes <extension name...>  只重命名特定的文件后缀名，以空格分隔 (Only rename certain files by extensions, separated by spaces)
  -ai, --ai [chatgpt token]           以 gpt-4o-mini 获取rom的英文名称，方便获取封面资源，[如果没有提供apiKey的话会默认读取本地目录下的apiKey.txt] (Using gpt-4o-mini to fetch rom's English name,
                                      will read from 'apiKey.txt' if not provided)
  -m, --no-cache                      强制不使用已有的ai重命名信息缓存，强制获取新的信息, 必须与 -ai 命令一起使用。(Manually invalidate the cache and force to fetch the latest information from
                                      AI, must be used with the -ai command)
  -p, --prettify                      使用AI获取的游戏名称取代原有的文件名，必须与 -ai 命令一起使用。 (Use the game title fetched by AI to replace the original file name, must be used
                                      with the -ai command)
  -py, --pinyin                       在文件名前加上拼音首字母来更好的支持排序，也支持英文和字母 (Adds pinyin initials at the beginning of file name for better sorting, also supports
                                      English and numbers)
  -h, --help                          display help for command
```

### Example

`renamer rename -t -py -ai -p D:/Downloads/`

铁臂阿童木-阿童木之心的秘密\[v1.0]\[心灵的冬天](简)(66Mb).zip -> /Users/rozx/Downloads/TestDir/T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy -  The Video Game) (2004) - 简.zip

## Revert

```
Usage: renamer revert [options] <dir>

还原文件名 (Revert file names)

Arguments:
    dir              文件夹路径 (Directory path)

Options:
    -d, --dry-run    仅显示还原后的文件名，不实际还原 (Display the reverted file names without actually reverting them)
    -r, --recursive  递归还原文件夹中的所有文件 (Recursively revert all files in the directory)
    -h, --help       display help for command
```

### Example

`renamer revert -t D:/Downloads/`

T 铁臂阿童木 - 阿童木之心的秘密 (Astro Boy -  The Video Game) (2004) - 简.gba -> 铁臂阿童木-阿童木之心的秘密\[v1.0]\[心灵的冬天](简)(66Mb).gba

## Roadmap

- AI rom title fetch with in-memory cache. (Done in v1.5.0) ✅
- Store original filename for the revert action. (Done in v1.6.0) ✅
- Support different AI model and 3rd party api.
- Prettify rom name using AI. (Done in v1.6.0) ✅
