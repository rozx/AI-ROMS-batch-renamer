# Rom-batch-renamer

A command line tool for batch renaming ROM files.

一个批量重命名ROM文件的命令行工具. (Batch rename Rom files)

## Usage


### Example

- 黄金太阳 - 失落的时代\[Mobile&Elffinal](简)(UE)(128Mb).zip -> H 黄金太阳 - 失落的时代 (Golden Sun: The Lost Age) (2002) - 简.gba
- 哈利波特 - 阿兹卡班的逃犯\[施珂昱](简)(JP)(128Mb).zip -> H 哈利波特 - 阿兹卡班的逃犯 (Harry Potter and the Prisoner of Azkaban) (2004) - 简.gba
- 指环王－王者归来(0.4b小字体)\[Advance-004](简)(JP)(136Mb).zip -> Z 指环王－王者归来 (The Lord of the Rings: The Return of the King) (2003) - 简.gba
- 王国之心 - 记忆之链\[天使汉化组](简)(JP)(256Mb).zip -> W 王国之心 - 记忆之链 (Kingdom Hearts- Chain of Memories) (2004) - 简.gba

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
Usage: pinyin-batch-renamer rename [options] [dir]

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
  -u, --unzip                         解压并重命名zip文件 (Unzip and rename zip files)
  -ai, --ai [chatgpt token]           以gpt-4o-mini获取rom的英文名称，方便获取封面资源，[如果没有提供apiKey的话会默认读取本地目录下的apiKey.txt] (Using gpt-4o-mini to fetch rom's English name, will read from 'apiKey.txt' if not provided)
  -h, --help                          display help for command
```

### Example
`pinyin-batch-renamer rename -t D:/Downloads/`

冰河世纪 (繁) (新特奇).zip -> B 冰河世纪 - 繁.zip

## Revert

```
Usage: pinyin-batch-renamer revert [options] <dir>

还原文件名 (Revert file names)

Arguments:
    dir              文件夹路径 (Directory path)

Options:
    -d, --dry-run    仅显示还原后的文件名，不实际还原 (Display the reverted file names without actually reverting them)
    -r, --recursive  递归还原文件夹中的所有文件 (Recursively revert all files in the directory)
    -h, --help       display help for command
```

### Example
`pinyin-batch-renamer revert -t D:/Downloads/`

B 冰河世纪.zip -> 冰河世纪.zip

## Roadmap

- AI rom title fetch with in-memory cache.
