from typing import Optional
import typer
from rich import print as rprint, console
from InquirerPy.resolver import prompt
from typing_extensions import Annotated

# Use absolute package imports so it works for both package entry and compiled onefile
from ai_rom_batch_renamer.modules import rename as renameModule
from ai_rom_batch_renamer.modules import const as constModule
from ai_rom_batch_renamer.modules import revert as revertModule
from ai_rom_batch_renamer.modules import cache as cacheModule
from ai_rom_batch_renamer.modules.ai import AIQueryError


app = typer.Typer(
    name="renamer",
    help="一个支持终端/GUI的 ROM 批量重命名工具，支持本地别名查找与 AI 增强。(A terminal/GUI ROM batch renamer with local alias lookup and AI enrichment.)",
    no_args_is_help=True,
)


def _raise_exit(code: int) -> None:
    raise typer.Exit(code=code)


@app.command("rename", no_args_is_help=False)
def rename(
    directory: Annotated[
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
            help="要重命名的文件（支持分号/换行分隔多个文件） (The files to rename; supports multiple files separated by semicolon or newline)",
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
            help="使用AI来重命名文件,默认为 deepseek-chat (Use AI to rename files, default is deepseek-chat)",
            is_flag=True,
        ),
    ] = False,
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-model",
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
    tavilyApiKey: Annotated[
        str,
        typer.Option(
            "--tavily-api-key",
            "-tav",
            help="Tavily 远程 MCP Key，连接 mcp.tavily.com 进行联网搜索增强（无需 Node.js）(Tavily API key; connects to the remote MCP server at mcp.tavily.com — no Node.js required)",
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
    ai_batch_size: Annotated[
        int,
        typer.Option(
            "--ai-batch-size",
            help="批量AI查询的大小 (Batch size for AI lookups; query multiple filenames per request)",
        ),
    ] = 10,
    ai_no_cache: Annotated[
        bool,
        typer.Option(
            "--ai-no-cache",
            "-nc",
            help="禁用AI缓存 (Do not use AI cache; always query the API)",
            is_flag=True,
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="强制重命名文件 (Force rename files)",
            is_flag=True,
        ),
    ] = False,
    cn_lookup: Annotated[
        bool,
        typer.Option(
            "--cn-lookup",
            "--cn",
            help="使用本地中文别名数据库查找游戏名称，需要提供 --platform (Use local Chinese alias database to look up game titles, requires --platform)",
            is_flag=True,
        ),
    ] = False,
):
    """
    批量重命名Roms文件 (Batch rename files by providing a directory or files)
    """

    # check if both directory and files are provided, if not, prompt the user to provide them
    if not directory and not files:
        rprint(
            "[red bold]请提供要重命名的文件夹路径或文件 (Please provide the directory path or files to rename)[/red bold]"
        )
        _raise_exit(2)

    # Saving options in a dictionary
    options = {
        "dir": directory,
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
        "tavilyApiKey": tavilyApiKey,
        "platform": platform,
        "ai_batch_size": ai_batch_size,
        "ai_no_cache": ai_no_cache,
        "force": force,
        "cn_lookup": cn_lookup,
    }

    try:
        code = renameModule.rename(options)
    except AIQueryError as e:
        rprint(f"[red bold]AI请求失败 (AI API error): {e}[/red bold]")
        _raise_exit(3)
    except ValueError as e:
        rprint(f"[red bold]{e}[/red bold]")
        _raise_exit(2)
    except PermissionError as e:
        rprint(f"[red bold]文件权限错误 (Permission denied): {e}[/red bold]")
        _raise_exit(1)
    except OSError as e:
        rprint(f"[red bold]文件系统错误 (File system error): {e}[/red bold]")
        _raise_exit(1)
    except Exception as e:
        rprint(f"[red bold]未知错误 (Unexpected error): {e}[/red bold]")
        _raise_exit(1)

    if code != 0:
        _raise_exit(code)


@app.command("revert", no_args_is_help=False)
def revert(
    directory: Annotated[
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
            help="要还原文件名的文件（支持分号/换行分隔多个文件） (The files to revert; supports multiple files separated by semicolon or newline)",
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

    if not directory and not files:
        rprint(
            "[red bold]请提供要还原的文件夹路径或文件 (Please provide the directory path or files to revert)[/red bold]"
        )
        _raise_exit(2)

    try:
        code = revertModule.revert(directory, files, recursive, dryrun)
    except PermissionError as e:
        rprint(f"[red bold]文件权限错误 (Permission denied): {e}[/red bold]")
        _raise_exit(1)
    except OSError as e:
        rprint(f"[red bold]文件系统错误 (File system error): {e}[/red bold]")
        _raise_exit(1)
    except Exception as e:
        rprint(f"[red bold]未知错误 (Unexpected error): {e}[/red bold]")
        _raise_exit(1)

    if code != 0:
        _raise_exit(code)


@app.command("about", no_args_is_help=False)
def about():
    """
    显示程序信息 (Show the program info)
    """

    rprint(
        f"AI ROM Batch Renamer [bold]v{constModule.VERSION}[/bold] by [bold blue]@rozx[/bold blue]"
    )
    rprint(
        "Terminal + GUI | Local alias lookup + AI enrichment | Revert + Cache management"
    )
    pass


@app.command("gui", no_args_is_help=False)
def gui():
    """
    启动图形界面 (Launch GUI)
    """

    # When running as a compiled standalone binary, Qt platform plugins are not
    # bundled with the CLI build — direct the user to the GUI binary instead.
    _is_compiled = False
    try:
        _is_compiled = bool(__compiled__)  # type: ignore[name-defined]  # noqa: F821
    except NameError:
        pass

    if _is_compiled:
        rprint(
            "[yellow]此命令在独立构建的 CLI 版本中不可用。请使用 GUI 版本启动图形界面。"
            " (The gui command is not available in the standalone CLI build. Use the GUI binary instead.)[/yellow]"
        )
        _raise_exit(1)

    try:
        from ai_rom_batch_renamer.gui import launch_gui
    except Exception as e:
        rprint(
            f"[red bold]无法启动GUI，请确认已安装 PySide6。 (Failed to launch GUI, ensure PySide6 is installed): {e}[/red bold]"
        )
        _raise_exit(1)

    try:
        code = launch_gui()
    except Exception as e:
        rprint(f"[red bold]GUI运行失败 (GUI runtime error): {e}[/red bold]")
        _raise_exit(1)

    if code != 0:
        _raise_exit(code)


@app.command("clear-cache", no_args_is_help=True)
def clear_cache(
    delete_files: Annotated[
        bool,
        typer.Option(
            "--delete-files",
            "-d",
            help="Delete cache directory and files completely (删除缓存目录和文件)",
            is_flag=True,
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt (跳过确认提示)",
            is_flag=True,
        ),
    ] = False,
):
    """
    清除所有缓存数据 (Clear all cache data)
    """
    if delete_files:
        # Delete the entire cache directory - require confirmation
        if not yes:
            result = prompt(
                [
                    {
                        "type": "confirm",
                        "message": f"删除缓存目录及所有文件？(Delete cache directory and all files?)\n  路径 (Path): {cacheModule.CACHE_DIR}",
                        "default": False,
                    }
                ]
            )
            if not result:
                rprint("[yellow]操作已取消 (Operation cancelled.)[/yellow]")
                return

        if cacheModule.delete_cache_files():
            rprint(
                f"[green]✓[/green] 缓存目录已删除 (Cache directory deleted): [dim]{cacheModule.CACHE_DIR}[/dim]"
            )
        else:
            rprint(
                f"[yellow]缓存目录不存在 (Cache directory does not exist): [dim]{cacheModule.CACHE_DIR}[/dim]"
            )
    else:
        # Clear cache data only - show info and ask for confirmation
        rom_info_count = len(cacheModule.romInfoCache.get_all_keys())
        rename_history_count = len(cacheModule.renameHistoryCache.get_all_keys())

        if rom_info_count == 0 and rename_history_count == 0:
            rprint("[yellow]缓存已为空 (Cache is already empty.)[/yellow]")
            return

        rprint(
            f"缓存内容 (Cache contents):\n"
            f"  - ROM 信息缓存 (ROM info cache): [bold]{rom_info_count}[/bold] 条 (items)\n"
            f"  - 重命名历史缓存 (Rename history cache): [bold]{rename_history_count}[/bold] 条 (items)\n"
            f"  - 缓存目录 (Cache directory): [dim]{cacheModule.CACHE_DIR}[/dim]"
        )

        if not yes:
            result = prompt(
                [
                    {
                        "type": "confirm",
                        "message": "清除所有缓存数据？(Clear all cache data?)",
                        "default": False,
                    }
                ]
            )
            if not result:
                rprint("[yellow]操作已取消 (Operation cancelled.)[/yellow]")
                return

        # Clear cache data
        cacheModule.clear_all_cache()
        rprint("[green]✓[/green] 缓存已清除 (Cache cleared successfully).")


if __name__ == "__main__":
    app()
