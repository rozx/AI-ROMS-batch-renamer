import os
import regex
import pinyin

from rich import print as rprint, console
from rich.progress import track


import modules.utils as utilsModule
import modules.regex as regexModule

# Rename files


def rename(
    dir: str,
    files: str,
    trim: bool,
    dry: bool,
    pinyin: bool,
    includes: list[str],
    excludes: list[str],
):

    fileList: list[str] = []

    # first adds all files into the list

    if files:
        fileList.append(files)

    # then check if the directory is provided, if it is, add all files in the directory to the list
    if dir:
        for file in os.listdir(dir):
            fileList.append(os.path.join(os.path.abspath(dir), file))

    # check if the file list is empty
    if not fileList:
        rprint(
            f"[red bold]重命名的文件为空 (No files found in the directory or the file does not exist.)[/red bold]"
        )
        return

    # filter out unwanted files
    for file in fileList.copy():

        baseName, extName = getBasenameAndExtensions(file)

        # exclude files with specific extensions
        if excludes:
            if extName in excludes:
                fileList.remove(file)
                continue

        # include files with specific extensions
        if includes:
            if extName not in includes:
                fileList.remove(file)
                continue

        if not os.path.isfile(file):
            fileList.remove(file)
            continue

        if not os.path.exists(file):
            rprint(
                f"[red bold]Skipping file {baseName} due to it does not exist.[/red bold]"
            )
            fileList.remove(file)
            continue

        if utilsModule.isSystemOrHiddenFile(baseName):
            fileList.remove(file)
            continue

    # for each file in the list, processing the file
    for value in track(range(len(fileList)), description="Renaming files..."):

        # full path of the file
        file = fileList[value]

        # directory of the file
        dir = os.path.dirname(file)

        # file name, base name and extension name
        fileName = os.path.basename(file)
        baseName, extName = getBasenameAndExtensions(fileName)

        # Match hack naming conventions
        hackMatch = regex.search(regexModule.hackMatchRegex, baseName, regex.IGNORECASE)

        # Match region naming conventions
        chineseMatch = regex.search(regexModule.chineseMatchRegex, baseName)
        regionMatch = regex.search(regexModule.regionMatchRegex, baseName)

        if chineseMatch:
            region = "简"
        elif regionMatch:
            region = utilsModule.getRegion(regionMatch.group(0))
        else:
            region = "Unknown"

        # trim the filename
        if trim:
            fileName = trimFileName(fileName)

        # update the basename
        baseName = getBasenameAndExtensions(fileName)[0]

        # add pinyin initials
        if pinyin:
            fileName = addsPinyinInitials(fileName)

            # update the basename
            baseName = getBasenameAndExtensions(fileName)[0]

        # adds hack to the filename
        if hackMatch:
            fileName = f"{baseName} (Hack){extName}"

            # update the basename
            baseName = getBasenameAndExtensions(fileName)[0]

        # adds region to the filename
        fileName = f"{baseName} - {region}{extName}"
        # update the basename
        baseName = getBasenameAndExtensions(fileName)[0]

        rprint(
            f"[bold]Renamed{' preview' if dry else ''}[/bold] [blue1 underline]{file}[/blue1 underline] -> [green3]{fileName}[/green3]",
        )

        pass

    pass


def trimFileName(fileName: str) -> str:

    baseName, extName = getBasenameAndExtensions(fileName)

    # Remove the title initials
    baseName = regex.sub(
        regexModule.titleInitialMatchRegEx, "", baseName, ignore_unused=True
    )

    # Remove index from filename
    baseName = regex.sub(regexModule.indexMatchRegex, "", baseName, ignore_unused=True)

    # Remove brackets and contents
    baseName = regex.sub(
        regexModule.bracketsAndContentMatchRegEx, "", baseName, ignore_unused=True
    )

    # remove file name after _, excluding the extension
    baseName = regex.sub(
        regexModule.contentAfterUnderscoreMatchRegEx, "", baseName, ignore_unused=True
    )

    # Remove extra spaces
    baseName = regex.sub(
        regexModule.extraSpaceMatchRegEx, " ", baseName, ignore_unused=True
    )

    fileName = f"{baseName.strip()}{extName}"

    return fileName


def getBasenameAndExtensions(fileName: str) -> tuple[str, str]:

    baseName = os.path.basename(fileName)

    return (
        os.path.splitext(baseName)[0],
        os.path.splitext(baseName)[1],
    )
    pass


def addsPinyinInitials(fileName: str) -> str:

    # get the base name and extension name
    baseName, extName = getBasenameAndExtensions(fileName)

    # get the pinyin initials
    pinyinInitials = pinyin.get_initial(baseName)[0].upper()

    # add the pinyin initials to the base name
    fileName = f"{pinyinInitials} {baseName}{extName}"

    return fileName
