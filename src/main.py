import typer
from rich import print as rprint, console
from InquirerPy import prompt
from typing_extensions import Annotated

import modules.rename as renameModule

app = typer.Typer(
    name="renamer",
    help="一个使用AI来批量重命名ROM文件的命令行工具。(A command line tool for batch renaming ROM files using AI.)",
    no_args_is_help=True,
)


@app.command("rename", no_args_is_help=True)
def rename(
    dir: Annotated[
        str,
        typer.Option(
            "--directory",
            "-dir",
            help="要重命名的文件夹路径 (The directory path to rename files in)",
            resolve_path=True,
            dir_okay=True,
            file_okay=False,
        ),
    ] = ".",
    files: Annotated[
        str,
        typer.Option(
            "--files",
            "-files",
            help="要重命名的文件 (The files to rename)",
            resolve_path=True,
            dir_okay=False,
            file_okay=True,
        ),
    ] = None,
    trim: Annotated[
        bool,
        typer.Option(
            "--trim",
            "-t",
            help="去除无用的信息 (Trim the filename)",
        ),
    ] = None,
):
    """
    批量重命名Roms文件 (Batch rename files by providing a directory or files)
    """

    # check if both dir and files are provided, if not, prompt the user to provide them
    if not dir and not files:
        rprint(
            "请提供要重命名的文件夹路径或文件 (Please provide the directory path or files to rename)"
        )
        return

    renameModule.rename(dir, files, trim)

    pass


@app.command("revert", no_args_is_help=True)
def revert():
    """
    还原重命名后的文件 (Revert changed file names)
    """
    pass


if __name__ == "__main__":
    app()
