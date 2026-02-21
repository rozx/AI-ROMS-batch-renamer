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
from ai_rom_batch_renamer.modules import cn_lookup as cnLookupModule
from ai_rom_batch_renamer.classes.RomFile import RomFile as RomFile
from ai_rom_batch_renamer.classes.AIConfig import AIConfig as AIConfig

# Rename files


def rename(options: dict) -> int:

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
    tavilyApiKey: str = options.get("tavilyApiKey", "")
    platform: str = options.get("platform", "unknown")
    ai_batch_size: int = options.get("ai_batch_size", 10)
    ai_no_cache: bool = options.get("ai_no_cache", False)
    force: bool = options.get("force", False)
    cn_lookup: bool = options.get("cn_lookup", False)

    # Resolve short aliases (e.g. "gb" -> "Nintendo - Game Boy")
    platform = utilsModule.sanitizePlatform(platform)

    # Validate cn_lookup requires platform
    if cn_lookup and (not platform or platform.lower() == "unknown"):
        rprint(
            "[red bold]使用 --cn-lookup 时必须提供 --platform。 "
            "(--platform is required when using --cn-lookup)[/red bold]"
        )
        return 2

    # initialize the file list

    fileList: list[str] = []

    # first adds all files into the list

    if files:
        fileList.extend(utilsModule.parseFilesInput(files))

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
        return 2

    # load AI config

    aiConfig = AIConfig()
    aiConfig.load()

    # if AI config is provided, update the config
    if apiKey:
        aiConfig.apiKey = apiKey
        rprint(f"[green]API key 更新成功。 AI API key is set[/green]")
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
    if tavilyApiKey:
        aiConfig.tavilyApiKey = tavilyApiKey
        rprint("[green]Tavily API key 更新成功。 Tavily API key is set[/green]")

    # update the AI config
    if apiKey or endpoint or model or tavilyApiKey:
        rprint("[green]AI配置已更新。 AI config updated successfully[/green]")
        aiConfig.save()

    if ai:
        if not aiConfig.apiKey:
            rprint(
                "[red bold]无法使用AI功能。APIKey为空。 AI API key is not set. Please set the AI API key in the config file. [/red bold]"
            )
            return 2

    # Prepare RomFile objects first (needed for batching)
    romFiles: list[RomFile] = [RomFile(path) for path in fileList]

    # Pre-process: apply trim before any lookup so that lookup uses cleaned names.
    # This ensures tags like "[简]" and prefixes like "C " are stripped before
    # CN/AI lookup, avoiding key mismatches caused by CJK chars inside brackets.
    if trim:
        for rf in romFiles:
            trimFileName(rf)

    # Step 1: Local CN alias lookup (CSV + name_alias JSON)
    cn_results: dict[str, dict] = {}
    if cn_lookup:
        cn_results = cnLookupModule.lookupBatch(romFiles, platform)

    # Step 2: Build CSV candidate hints for AI context.
    # - When cn_lookup + ai: only query AI for files not fully covered by CSV.
    # - When ai only (with platform): still fetch candidates as AI context hints.
    csv_candidates: dict[str, list[str]] = {}
    ai_results: dict[str, dict] = {}
    if ai:
        # Determine which files still need AI (csv result missing or incomplete)
        if cn_lookup:
            ai_needed = [
                rf
                for rf in romFiles
                if rf.originalFilename not in cn_results
                or not cn_results[rf.originalFilename].get("englishTitle")
            ]
        else:
            ai_needed = romFiles

        # Collect CSV candidates to pass as AI context hints (when platform is known)
        if platform and platform.lower() != "unknown":
            for rf in ai_needed:
                candidates = cnLookupModule.get_candidates(
                    rf.originalFilename, platform
                )
                if candidates:
                    csv_candidates[rf.originalFilename] = candidates
            if csv_candidates:
                rprint(
                    f"[cyan]CSV 候选提示 (Candidate hints for AI):[/cyan] "
                    f"为 {len(csv_candidates)} 个文件提供候选 (files with hints)"
                )

        if ai_needed:
            ai_results = aiScraperModule.aiScraperBatch(
                aiConfig,
                ai_needed,
                platform=platform,
                useCache=(not ai_no_cache),
                batch_size=ai_batch_size,
                csv_candidates=csv_candidates if csv_candidates else None,
            )

    # Merge results: CSV takes priority; AI fills gaps
    merged_results: dict[str, dict] = {**cn_results}
    for filename, ai_data in ai_results.items():
        if filename not in merged_results:
            merged_results[filename] = ai_data
        else:
            # Fill missing fields from AI
            existing = merged_results[filename]
            if not existing.get("englishTitle") and ai_data.get("englishTitle"):
                existing["englishTitle"] = ai_data["englishTitle"]
            if not existing.get("chineseTitle") and ai_data.get("chineseTitle"):
                existing["chineseTitle"] = ai_data["chineseTitle"]

    # renamed files list
    renamedFiles: list[str] = []

    # for each file in the list, processing the file
    for value in track(
        range(len(romFiles)), description="正在重命名文件... (Renaming files...)"
    ):

        romFile = romFiles[value]

        # Match hack naming conventions.
        # Check originalFilename FIRST so that [Hack]/(Hack) tags stripped by
        # --trim are still detected.  Fall back to the current baseName.
        hackMatch = regex.search(
            regexModule.hackMatchRegex, romFile.originalFilename, flags=regex.IGNORECASE
        ) or regex.search(
            regexModule.hackMatchRegex, romFile.baseName, flags=regex.IGNORECASE
        )  # type: ignore

        # Step 1: Apply enrichment first (cn_lookup / AI results).
        # Track the Chinese title so it can be reused for pinyin initial and
        # region inference below.
        cn_title_from_lookup: str | None = None
        if romFile.originalFilename in merged_results:
            result = merged_results[romFile.originalFilename]
            cn = (result.get("chineseTitle") or "").strip()
            en = (result.get("englishTitle") or "").strip()
            cn_title_from_lookup = cn or None

            # Use English title as primary, Chinese title as secondary
            new_base = None
            if cn and en:
                # EN + CN
                new_base = f"{en} ({cn})"
            elif cn:
                # CN only
                new_base = f"{romFile.baseName}"
            elif en:
                # EN only
                new_base = en

            if new_base:
                romFile.updateFileName(f"{new_base}{romFile.extName}")

        # Step 2: Detect region.
        # Check originalFilename FIRST so that tags like "[简]" removed by --trim
        # are still visible.  Fall back to the current (enriched) baseName, and
        # finally infer "简" from the presence of a Chinese title from lookup.
        chineseMatch = regex.search(
            regexModule.chineseMatchRegex, romFile.originalFilename
        ) or regex.search(regexModule.chineseMatchRegex, romFile.baseName)
        regionMatch = regex.search(
            regexModule.regionMatchRegex, romFile.originalFilename
        ) or regex.search(regexModule.regionMatchRegex, romFile.baseName)

        if chineseMatch:
            region = "简"
        elif regionMatch:
            region = utilsModule.getRegion(regionMatch.group(0))
        elif cn_title_from_lookup:
            # A Chinese title from cn_lookup/AI implies simplified-Chinese content.
            region = "简"
        else:
            region = "Unknown"

        # Step 3: Add pinyin initials AFTER enrichment.
        # Pass the Chinese title so the initial is derived from its first character
        # (e.g. 超级机器人大战 → "C") rather than the English portion of the name.
        if pinyin:
            addsPinyinInitials(romFile, cn_title=cn_title_from_lookup)

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
        result = renameFiles(pendingRenameFiles, romFile, dry, renamedFiles, None)

        # add the file to the renamed files tracking
        renamedFiles.extend(result)

        # ----------- prompt the result -------------
        if output:
            print(romFile.fileName)
        else:
            rprint(
                f"[bold]Renamed重命名{' preview 预览' if dry else ''}({value + 1}/{len(fileList)}):[/bold] [blue1 underline]{romFile.path}[/blue1 underline] -> [green3]{result}[/green3]",
            )

        pass

    return 0


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


def addsPinyinInitials(romFile: RomFile, cn_title: str | None = None) -> None:

    # get the base name and extension name
    baseName, extName = romFile.baseName, romFile.extName

    # Prefer the Chinese title as the source for the pinyin initial so that
    # e.g. "超级机器人大战" yields "C" rather than the English title "S(uper)".
    source = cn_title.strip() if cn_title else baseName

    # get the pinyin initials
    pinyinInitials = pinyin.get_initial(source)[0].upper()

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
    base_name = regex.sub(rf"[^ {allowed}]", "", base_name)

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
