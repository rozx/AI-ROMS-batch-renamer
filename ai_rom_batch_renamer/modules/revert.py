import os

import modules.cache as cacheModule
import modules.utils as utilsModule

from rich import print as rprint, console
from rich.progress import track


def revert(dir: str, files: str, recursive: bool, dry: bool):
    """
    还原重命名后的文件 (Revert changed file names)
    """

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
            f"[red bold]要还原的文件列表为空 (No files found in the directory or the file does not exist.)[/red bold]"
        )
        return

    for value in track(range(len(fileList)), description="Reverting files..."):

        # full path of the file
        file = fileList[value]

        # check for cache
        renameHistory: dict = cacheModule.renameHistoryCache.get(file)

        if not renameHistory:

            rprint(
                f"Skipping [yellow underline]{file}[/yellow underline]: [red bold]No renaming history found.[/red bold]"
            )

            continue

        baseName, extName = utilsModule.getBasenameAndExtensions(
            renameHistory["original"]
        )

        currentBaseName, currentExtName = utilsModule.getBasenameAndExtensions(file)

        # Revert the file name to the original name using the current extension name
        targetFileName = os.path.join(
            os.path.dirname(file), f"{baseName}{currentExtName}"
        )

        if not dry:
            # rename the file
            os.rename(file, targetFileName)

        rprint(
            f"[bold]Reverted{' preview' if dry else ''}({value + 1}/{len(fileList)}):[/bold] [blue1 underline]{file}[/blue1 underline] -> [yellow]{baseName}{extName}[/yellow]",
        )

        # delete rename history
        cacheModule.renameHistoryCache.delete(file)

    pass
