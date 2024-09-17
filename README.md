# Rom-batch-renamer

A command line tool for batch renaming ROM files.
一个批量重命名ROM文件的命令行工具. (Batch rename Rom files)

## Usage


### Example

- 冰河世纪 (繁) (新特奇).zip -> B 冰河世纪 - 繁.zip
- Colin McRae - DiRT 2 (USA) (PSP) (PSN).iso -> C Colin McRae - DiRT 2 - US.iso
- 1941 - GT赛车 [繁] [官方中文版] [SONY].iso -> G GT赛车 - 繁.iso

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
    -d, --dry-run            仅显示重命名后的文件名，不实际重命名 (Display the renamed file names without actually renaming them)
    -n, --name-only          仅显示重命名后的文件名，不输出其他信息 (Display the renamed file names only, without other information)
    -r, --recursive          递归重命名文件夹中的所有文件 (Recursively rename all files in the directory)
    -t, --trim               去除编号、文件名中的空格与括号中的信息，但保留Rom版本信息 (Removes index, spaces and content in brackets, but keeps the region information)
    -f, --force              强制重命名文件，即使文件名已经被命名过了 (Force rename files even if the file name already being renamed)
    -fl, --files <files...>  只重命名文件，不重命名文件夹,以空格分隔 (Only rename files, not folders, separated by spaces)
    -h, --help               display help for command
```

### Example
`pinyin-batch-renamer rename -t D:/Downloads/`

冰河世纪 (繁) (新特奇).zip -> B 冰河世纪.zip

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
