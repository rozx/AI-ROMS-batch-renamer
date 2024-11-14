import os
import modules.utils as utilsModule
from rich import print as rprint, console
from rich.progress import track


# Rename files


def rename(dir: str, files: str, trim: bool):

    fileList: list[str] = []

    # first adds all files into the list

    if files:
        fileList.append(files)

    # then check if the directory is provided, if it is, add all files in the directory to the list
    if dir:
        fileList.extend(os.listdir(dir))

    # filter out unwanted files
    for file in fileList:
        if utilsModule.isSystemOrHiddenFile(file):
            fileList.remove(file)

    # for each file in the list, processing the file
    for value in track(range(len(fileList)), description="Renaming files..."):

        # full path of the file
        file = fileList[value]

        # directory of the file
        dir = os.path.dirname(file)

        # file name, base name and extension name
        fileName, baseName, extName = (
            os.path.basename(file),
            os.path.splitext(file)[0],
            os.path.splitext(file)[1],
        )

        rprint(f"Renaming {baseName} {extName}")

        pass

    pass
