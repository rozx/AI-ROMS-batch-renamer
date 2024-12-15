import typer
from rich import print as rprint, console
from InquirerPy import prompt
from typing_extensions import Annotated

import modules.rename as renameModule
import modules.const as constModule
import modules.revert as revertModule


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
    ] = None,
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
    dry: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="只输出结果，不实际重命名 (Output the result without actually renaming)",
        ),
    ] = None,
    pinyin: Annotated[
        bool,
        typer.Option(
            "--pinyin",
            "-py",
            help="在开头加上拼音首字符来更好的支持查找 (Add pinyin initials at the beginning for better sort support)",
        ),
    ] = None,
    includes: Annotated[
        list[str],
        typer.Option(
            "--includes",
            "-i",
            help="只处理特定的文件类型 (Only process specific file types)",
        ),
    ] = [],
    excludes: Annotated[
        list[str],
        typer.Option(
            "--excludes",
            "-e",
            help="不处理特定的文件类型 (Do not process specific file types)",
        ),
    ] = [],
    output: Annotated[
        bool,
        typer.Option(
            "--output",
            "-o",
            help="只输出重命名后的文件名，不附加其他信息 (Only output the renamed file names without additional prompts)",
        ),
    ] = None,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="读取目标目录下的文件夹中的文件 (Read files in the subdirectories of the target directory)",
        ),
    ] = None,
):
    """
    批量重命名Roms文件 (Batch rename files by providing a directory or files)
    """

    # check if both dir and files are provided, if not, prompt the user to provide them
    if not dir and not files:
        rprint(
            "[red bold]请提供要重命名的文件夹路径或文件 (Please provide the directory path or files to rename)[/red bold]"
        )
        return

    renameModule.rename(
        dir, files, trim, dry, pinyin, includes, excludes, output, recursive
    )

    pass


@app.command("revert", no_args_is_help=True)
def revert(
    dir: Annotated[
        str,
        typer.Option(
            "--directory",
            "-dir",
            help="要还原文件名的文件夹路径 (The directory path to rename files in)",
            resolve_path=True,
            dir_okay=True,
            file_okay=False,
        ),
    ] = None,
    files: Annotated[
        str,
        typer.Option(
            "--files",
            "-files",
            help="要还原文件名的文件 (The files to rename)",
            resolve_path=True,
            dir_okay=False,
            file_okay=True,
        ),
    ] = None,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="读取目标目录下的文件夹中的文件 (Read files in the subdirectories of the target directory)",
        ),
    ] = None,
    dryrun: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="只输出结果，不实际重命名 (Output the result without actually renaming)",
        ),
    ] = None,
):
    """
    还原重命名后的文件 (Revert changed file names)
    """

    revertModule.revert(dir, files, recursive, dryrun)
    pass


@app.command("version", no_args_is_help=False)
def version():
    """
    显示程序版本 (Show the program version)
    """

    rprint(f"[bold]v{constModule.VERSION}[/bold]")
    pass


if __name__ == "__main__":
    app()
