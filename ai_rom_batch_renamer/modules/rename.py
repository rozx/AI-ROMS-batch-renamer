import os
import regex
import pinyin


from rich import print as rprint, console
from rich.progress import track


from ai_rom_batch_renamer.modules import utils as utilsModule
from ai_rom_batch_renamer.modules import regex as regexModule
from ai_rom_batch_renamer.modules import const as constModule
from ai_rom_batch_renamer.modules import cache as cacheModule
from ai_rom_batch_renamer.modules import ai as aiScraperModule
from ai_rom_batch_renamer.classes.RomFile import RomFile as RomFile
from ai_rom_batch_renamer.classes.AIConfig import AIConfig as AIConfig

# Rename files


def rename(options: dict):

    # get options

    dir = options.get("dir", "")
    files = options.get("files", "")
    trim = options.get("trim", False)
    dry = options.get("dry", False)
    pinyin = options.get("pinyin", False)
    includes = options.get("includes", [])
    excludes = options.get("excludes", [])
    output = options.get("output", False)
    recursive = options.get("recursive", False)
    unzip = options.get("unzip", False)
    pwd = options.get("pwd", "")
    ai: bool = options.get("ai", False)
    model: str = options.get("model", "")
    apiKey: str = options.get("apiKey", "")
    endpoint: str = options.get("endpoint", "")
    platform: str = options.get("platform", "unknown")
    ai_batch_size: int = options.get("ai_batch_size", 10)
    ai_no_cache: bool = options.get("ai_no_cache", False)
    force: bool = options.get("force", False)

    # initialize the file list

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
                f"[red bold]跳过文件 {baseName} 因为文件不存在。Skipping file due to it does not exist.[/red bold]"
            )
            fileList.remove(file)
            continue

        if utilsModule.isSystemOrHiddenFile(file):
            fileList.remove(file)
            continue
        
        if utilsModule.isFileRenamed(file) and not force:
            rprint(
                f"[yellow]跳过文件 {baseName} 因为已经被重命名过了。Skipping file as it appears to be already renamed.[/yellow]"
            )
            fileList.remove(file)
            continue

    # check if the file list is empty
    if not fileList:
        rprint(
            f"[red bold]重命名的文件为空 (No files found in the directory or the file does not exist.)[/red bold]"
        )
        return

    # load AI config

    aiConfig = AIConfig()
    aiConfig.load()

    # if AI config is provided, update the config
    if apiKey:
        aiConfig.apiKey = apiKey
        rprint(
            f"[green]API key 更新成功。 AI API key is set to {aiConfig.apiKey}[/green]"
        )
    if endpoint:
        aiConfig.endpoint = endpoint
        rprint(
            f"[green]API endpoint 更新成功。 AI API endpoint is set to {aiConfig.endpoint}[/green]"
        )
    if model:
        aiConfig.model = model
        rprint(
            f"[green]API model 更新成功。 AI model is set to {aiConfig.model}[/green]"
        )

    # update the AI config
    if apiKey or endpoint or model:
        rprint("[green]AI配置已更新。 AI config updated successfully[/green]")
        aiConfig.save()

    if ai:
        if not aiConfig.apiKey:
            rprint(
                "[red bold]无法使用AI功能。APIKey为空。 AI API key is not set. Please set the AI API key in the config file. [/red bold]"
            )
            return

    # Prepare RomFile objects first (needed for batching)
    romFiles: list[RomFile] = [RomFile(path) for path in fileList]

    # Batch AI enrichment to reduce per-file calls
    ai_results: dict[str, dict] = {}
    if ai:
        ai_results = aiScraperModule.aiScraperBatch(
            aiConfig,
            romFiles,
            platform=platform,
            useCache=(not ai_no_cache),
            batch_size=ai_batch_size,
        )

    # renamed files list
    renamedFiles: list[str] = []

    # for each file in the list, processing the file
    for value in track(range(len(romFiles)), description="Renaming files..."):

        romFile = romFiles[value]

        # Match hack naming conventions
        hackMatch = regex.search(
            regexModule.hackMatchRegex, romFile.baseName, flags=regex.IGNORECASE
        )  # type: ignore

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

        # apply AI enrichment if present (supports partial info)
        if ai and romFile.originalFilename in ai_results:
            result = ai_results[romFile.originalFilename]
            cn = (result.get('chineseTitle') or '').strip()
            en = (result.get('englishTitle') or '').strip()
            year = (result.get('releaseYear') or '').strip()

            
            # Use original base name as source of truth
            new_base = None
            if cn and en:
                # CN + EN
                new_base = f"{romFile.baseName} ({en})"
            elif cn:
                # CN only
                new_base = f"{romFile.baseName}"
            elif en:
                # EN only
                new_base = en

            if new_base:
                if year and year.isdigit() and len(year) == 4:
                    new_base = f"{new_base}({year})"
                romFile.updateFileName(f"{new_base}{romFile.extName}")

        # adds region to the filename
        if region != "Unknown":
            romFile.updateFileName(f"{romFile.baseName}[{region}]{romFile.extName}")

        # adds hack to the filename
        if hackMatch:
            romFile.updateFileName(f"{romFile.baseName}[Hack]{romFile.extName}")

        # if the file is a zip file, unzip the file
        if unzip and romFile.extName == ".zip":
            pendingRenameFiles = utilsModule.unzipFiles(romFile.path, dry, pwd)
        else:
            # adds current file to the pending name files renamed files
            pendingRenameFiles = [romFile.path]

        # ----------- Rename the file -------------
        # Pass None to allow autodetect of current OS; if needed, a future CLI flag
        # could override this behaviour for cross-platform normalization.
        result = renameFiles(
            pendingRenameFiles, romFile, dry, renamedFiles, None
        )

        # add the file to the renamed files tracking
        renamedFiles.extend(result)

        # ----------- prompt the result -------------
        if output:
            print(romFile.fileName)
        else:
            rprint(
                f"[bold]Renamed{' preview' if dry else ''}({value + 1}/{len(fileList)}):[/bold] [blue1 underline]{romFile.path}[/blue1 underline] -> [green3]{result}[/green3]",
            )

        pass

    pass


def trimFileName(romFile: RomFile):

    baseName, extName = romFile.baseName, romFile.extName

    # Remove index from filename
    baseName = regex.sub(regexModule.indexMatchRegex, "", baseName, ignore_unused=True)

    # Remove the title initials
    baseName = regex.sub(
        regexModule.titleInitialMatchRegEx, "", baseName, ignore_unused=True
    )

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


def sanitize_for_os(base_name: str, os_platform: str | None = None) -> str:
    """
    Sanitize a ROM base filename based on OS-specific filesystem constraints.

    - Windows: remove <>:"/\|?* and control chars; trim trailing dots/spaces
    - macOS: remove '/' and control chars
    - Linux: remove '/' and control chars
    We keep Unicode letters/numbers to preserve CJK.
    """

    # Detect OS platform if not provided
    try:
        import platform as _platform
        detected = _platform.system().lower()
    except Exception:
        detected = "unknown"

    os_norm = (os_platform or detected or "unknown").lower()
    if os_norm.startswith("win"):
        os_norm = "windows"
    elif os_norm in {"darwin", "mac", "macos", "osx"}:
        os_norm = "mac"
    elif os_norm.startswith("linux"):
        os_norm = "linux"

    # 1) Remove control characters (including NUL if any)
    base_name = regex.sub(r"[\x00\r\n\t\f\v]", " ", base_name)

    # 1.5) Replace colon with a space (safer cross-platform; ':' is invalid on Windows and
    # sometimes leads to confusion when moving archives between OSes). Doing this before
    # other reserved character stripping keeps intentional separation while later space
    # collapsing will normalize multiples.
    base_name = base_name.replace(":", " ")

    # 1.6) Replace path separators with spaces to avoid word concatenation when removed.
    # They are illegal in filenames and later collapsing will normalize multiple spaces.
    base_name = base_name.replace("/", " ")

    # 2) Remove reserved chars per OS
    if os_norm == "windows":
        # Windows forbids: <>:"/\|?*
        # (Colon already converted to space above.)
        base_name = regex.sub(r"[<>\"/\\\|\?\*]+", "", base_name)
        # Also trim trailing dots/spaces
        base_name = base_name.strip().rstrip(". ")
    else:
        # macOS/Linux forbid only '/'
        # Slash already converted to space above; any remaining (unlikely) remove.
        base_name = regex.sub(r"/", " ", base_name)
        base_name = base_name.strip()

    # Keep unicode letters/numbers, spaces and common safe separators
    allowed = r"\p{L}\p{N} _\-\[\]\(\)&',\.+\+"
    base_name = regex.sub(fr"[^ {allowed}]", "", base_name)

    # Collapse spaces
    base_name = regex.sub(r"\s{2,}", " ", base_name).strip()

    if not base_name:
        base_name = "file"

    return base_name


def getNextAvailableName(
    fileName: str, dir: str, renamedFiles: list[str], os_platform: str | None = None
) -> str:

    baseName, extName = utilsModule.getBasenameAndExtensions(fileName)
    # Sanitize base name with OS filesystem rules before uniqueness resolution
    baseName = sanitize_for_os(baseName, os_platform)
    fileName = f"{baseName}{extName}"

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
    os_platform: str | None = None,
) -> list[str]:

    _renamedFiles = renamedFiles.copy()
    proceedFiles = []

    for file in pendingRenameFiles:

        extName = utilsModule.getBasenameAndExtensions(file)[1].lower()

        targetBaseName = f"{romFile.baseName}{extName}"
        
        # check if target filename is same as current filename, if so, skip renaming
        if os.path.basename(file) == targetBaseName:
            _renamedFiles.append(os.path.basename(file))
            proceedFiles.append(os.path.basename(file))
            continue

        # get the next available name
        fileName = getNextAvailableName(
            targetBaseName, romFile.dir, _renamedFiles, os_platform
        )

        targetRenamePath = os.path.join(romFile.dir, fileName)

        # rename file if not in dry run mode
        if not dryrun:
            os.rename(file, targetRenamePath)

            # add rename history to cache history (md5 optional; avoid heavy I/O on large files)
            history = {
                "original": romFile.path,
                "new": targetRenamePath,
                "version": constModule.VERSION,
                "timestamp": utilsModule.getTimeStamp(),
            }
            try:
                # Compute MD5 only for small files to avoid saturating I/O on SD cards
                size = os.path.getsize(targetRenamePath)
                # 64 MiB threshold
                if size <= 64 * 1024 * 1024:
                    history["md5"] = utilsModule.getMD5HashFromFile(targetRenamePath)
                else:
                    history["md5"] = ""
            except Exception:
                history["md5"] = ""

            cacheModule.renameHistoryCache.add(
                targetRenamePath,
                history,
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
