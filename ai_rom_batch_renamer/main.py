from typing import Optional
import typer
from rich import print as rprint, console
from InquirerPy.resolver import prompt
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
    ] = "",
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
    ] = "",
    trim: Annotated[
        bool,
        typer.Option(
            "--trim",
            "-t",
            help="去除无用的信息 (Trim the filename)",
            is_flag=True,
        ),
    ] = False,
    dry: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="只输出结果，不实际重命名 (Output the result without actually renaming)",
            is_flag=True,
        ),
    ] = False,
    pinyin: Annotated[
        bool,
        typer.Option(
            "--pinyin",
            "-py",
            help="在开头加上拼音首字符来更好的支持查找 (Add pinyin initials at the beginning for better sort support)",
            is_flag=True,
        ),
    ] = False,
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
            is_flag=True,
        ),
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="读取目标目录下的文件夹中的文件 (Read files in the subdirectories of the target directory)",
            is_flag=True,
        ),
    ] = False,
    unzip: Annotated[
        bool,
        typer.Option(
            "--unzip",
            "-u",
            help="解压zip文件(Also unzip the zip files)",
            is_flag=True,
        ),
    ] = False,
    pwd: Annotated[
        str,
        typer.Option(
            "--password",
            "-pwd",
            help="zip文件的密码(Password for the zip files)",
        ),
    ] = "",
    ai: Annotated[
        bool,
        typer.Option(
            "--ai",
            "-ai",
            help="使用AI来重命名文件,默认为 gpt-4.1 (Use AI to rename files, default is gpt-4.1)",
            is_flag=True,
        ),
    ] = False,
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="保存使用的AI模型 (Update the AI model to use)",
        ),
    ] = "",
    apiKey: Annotated[
        str,
        typer.Option(
            "--api-key",
            "-key",
            help="保存AI模型的API密钥 (Update the API key for the AI model)",
        ),
    ] = "",
    endpoint: Annotated[
        str,
        typer.Option(
            "--endpoint",
            "-ep",
            help="保存AI模型的API端点 (Update the API endpoint for the AI model)",
        ),
    ] = "",
    platform: Annotated[
        str,
        typer.Option(
            "--platform",
            "-p",
            help="提供Roms的平台来使AI更好的获取游戏信息,只有ai启用时有用 (Provide the platform of the Roms to help AI get better game information, only useful when AI is enabled)",
        ),
    ] = "",
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

    # Saving options in a dictionary
    options = {
        "dir": dir,
        "files": files,
        "trim": trim,
        "dry": dry,
        "pinyin": pinyin,
        "includes": includes,
        "excludes": excludes,
        "output": output,
        "recursive": recursive,
        "unzip": unzip,
        "pwd": pwd,
        "ai": ai,
        "model": model,
        "apiKey": apiKey,
        "endpoint": endpoint,
        "platform": platform,
    }

    renameModule.rename(options)

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
    ] = "",
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
    ] = "",
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="读取目标目录下的文件夹中的文件 (Read files in the subdirectories of the target directory)",
            is_flag=True,
        ),
    ] = False,
    dryrun: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="只输出结果，不实际重命名 (Output the result without actually renaming)",
            is_flag=True,
        ),
    ] = False,
):
    """
    还原重命名后的文件 (Revert changed file names)
    """

    revertModule.revert(dir, files, recursive, dryrun)
    pass


@app.command("about", no_args_is_help=False)
def about():
    """
    显示程序信息 (Show the program info)
    """

    rprint(
        f"AI-rom-batch-renamer [bold]v{constModule.VERSION}[/bold] by [bold blue]@rozx[/bold blue]"
    )
    pass


if __name__ == "__main__":
    app()
