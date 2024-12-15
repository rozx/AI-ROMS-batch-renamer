import os
import regex
import pinyin

from rich import print as rprint, console
from rich.progress import track


import modules.utils as utilsModule
import modules.regex as regexModule
import modules.const as constModule
import modules.cache as cacheModule

from classes.RomFile import RomFile

# Rename files

def rename(
    dir: str,
    files: str,
    trim: bool,
    dry: bool,
    pinyin: bool,
    includes: list[str],
    excludes: list[str],
    output: bool,
    recursive: bool,
):

    fileList: list[str] = []

    # first adds all files into the list

    if files:
        fileList.append(files)

    # then check if the directory is provided, if it is, add all files in the directory to the list
    if dir:
        for file in os.listdir(dir):
            fileList.append(os.path.join(os.path.abspath(dir), file))

    # traverse the sub-directories
    for file in fileList.copy():
        # check if the file is a directory
        if os.path.isdir(file):
            if recursive:
                fileList.extend(utilsModule.traversalDirectory(file))
                fileList.remove(file)
            else:
                fileList.remove(file)

    # filter out unwanted files
    for file in fileList.copy():
        baseName, extName = utilsModule.getBasenameAndExtensions(file)

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

        if not os.path.exists(file):
            rprint(
                f"[red bold]Skipping file {baseName} due to it does not exist.[/red bold]"
            )
            fileList.remove(file)
            continue

        if utilsModule.isSystemOrHiddenFile(baseName):
            fileList.remove(file)
            continue

    # check if the file list is empty
    if not fileList:
        rprint(
            f"[red bold]重命名的文件为空 (No files found in the directory or the file does not exist.)[/red bold]"
        )
        return

    # renamed files list
    renamedFiles = []

    # for each file in the list, processing the file
    for value in track(range(len(fileList)), description="Renaming files..."):


        # full path of the file
        file = fileList[value]

        # create new RomFile object
        romFile =  RomFile(file)

        # Match hack naming conventions
        hackMatch = regex.search(regexModule.hackMatchRegex, romFile.baseName, regex.IGNORECASE)

        # Match region naming conventions
        chineseMatch = regex.search(regexModule.chineseMatchRegex, romFile.baseName)
        regionMatch = regex.search(regexModule.regionMatchRegex, romFile.baseName)

        if chineseMatch:
            region = "简"
        elif regionMatch:
            region = utilsModule.getRegion(regionMatch.group(0))
        else:
            region = "Unknown"

        # trim the filename
        if trim:
            trimFileName(romFile)

        # add pinyin initials
        if pinyin:
           addsPinyinInitials(romFile)

        # adds hack to the filename
        if hackMatch:
            romFile.updateFileName(f"{romFile.baseName} (Hack){romFile.extName}")

        # adds region to the filename
        romFile.updateFileName(f"{romFile.baseName} [{region}]{romFile.extName}")


        # ----------- Rename the file -------------


        # adds current file to the pending name files renamed files
        pendingRenameFiles = [romFile.path]

        # rename the file
        result = renameFiles(pendingRenameFiles, romFile, dry, renamedFiles)

        # add the file to the pending rename files
        renamedFiles.extend(result)

        # ----------- prompt the result -------------
        if output:
            print(romFile.fileName)
            continue
        else:
            rprint(
                f"[bold]Renamed{' preview' if dry else ''}({value}/{len(fileList)-1}):[/bold] [blue1 underline]{romFile.path}[/blue1 underline] -> [green3]{result}[/green3]", 
            )

        
        
        pass

    pass


def trimFileName(romFile: RomFile):

    baseName, extName = romFile.baseName, romFile.extName

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

    # Remove copy from filename
    baseName = regex.sub(regexModule.copyMatchRegEx, "", baseName, ignore_unused=True)

    romFile.updateFileName(f"{baseName.strip()}{extName}")

    return


def addsPinyinInitials(romFile: RomFile) -> None:

    # get the base name and extension name
    baseName, extName = romFile.baseName, romFile.extName

    # get the pinyin initials
    pinyinInitials = pinyin.get_initial(baseName)[0].upper()

    # add the pinyin initials to the base name
    romFile.updateFileName(f"{pinyinInitials} {baseName}{extName}")

    return


def getNextAvailableName(fileName: str, dir: str, renamedFiles: list[str]) -> str:

    baseName, extName = utilsModule.getBasenameAndExtensions(fileName)

    fileNameIndex = 0
    while fileName in renamedFiles or os.path.exists(os.path.join(dir, fileName)):

        fileNameIndex += 1
        fileName = f"{baseName}({fileNameIndex}){extName}"

    return fileName


def renameFiles(
    pendingRenameFiles: list[str],
    romFile: RomFile,
    dryrun: bool,
    renamedFiles: list[str],
) -> list[str]:

    _renamedFiles = renamedFiles.copy()
    proceedFiles = []

    for file in pendingRenameFiles:

        # get the next available name
        fileName = getNextAvailableName(romFile.fileName, romFile.dir, _renamedFiles)
        targetRenamePath = os.path.join(romFile.dir, fileName)

        # rename file if not in dry run mode
        if not dryrun:
            os.rename(file, targetRenamePath)

            # add rename history to cache history
            cacheModule.renameHistoryCache.add(
                targetRenamePath,
                {
                    "md5": romFile.md5,
                    "original": file,
                    "new": targetRenamePath,
                    "version": constModule.VERSION,
                    "timestamp": utilsModule.getTimeStamp(),
                },
                timeout=-1,
            )

            # rprint(
            #     f"Renaming [blue]{file}[/blue] to [yellow]{os.path.join(dir, fileName)}[/yellow]"
            # )
        # else:
        #     rprint(
        #         f"Renaming [blue]{file}[/blue] to [yellow]{os.path.join(dir, fileName)}[/yellow] in dry run mode"
        #     )

        # add the file to the renamed files
        _renamedFiles.append(fileName)
        proceedFiles.append(fileName)

    return proceedFiles
