from openai import OpenAI
import json
import time
from ai_rom_batch_renamer.modules import cache as cacheModule

from ai_rom_batch_renamer.classes.AIConfig import AIConfig
from ai_rom_batch_renamer.classes.RomFile import RomFile
from rich import print as rprint, console


class AIQueryError(Exception):
    pass


def _cache_key(romFile: RomFile, platform: str) -> str:
    # Use filename + platform for caching AI metadata; avoids heavy file hashing
    return f"{platform.lower()}::{romFile.originalFilename}"


def _chat_completion_content(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict],
    temperature: float = 1,
    stream: bool = True,
    progress_prefix: str | None = None,
    max_retries: int = 2,
    retry_backoff_seconds: float = 1.0,
) -> str | None:
    """Fetch chat completion content, optionally via streaming.

    When streaming, prints a lightweight progress indicator (dots) while
    accumulating the full content to return.
    """

    def _request_with_retry(use_stream: bool):
        attempts = max(0, max_retries) + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=use_stream,
                )
            except Exception as e:
                last_error = e
                if attempt >= attempts - 1:
                    raise
                sleep_seconds = retry_backoff_seconds * (2**attempt)
                rprint(
                    f"[yellow]AI 请求重试 (Retry) {attempt + 1}/{max_retries}，"
                    f"等待 {sleep_seconds:.1f}s：{e}[/yellow]"
                )
                time.sleep(sleep_seconds)
        if last_error:
            raise last_error

    if stream:
        # Minimal progress indicator without leaking content
        if progress_prefix:
            rprint(f"[cyan]{progress_prefix}[/cyan] [dim](streaming)[/dim]")
        content = ""
        dot_count = 0
        try:
            resp = _request_with_retry(True)
            for event in resp:  # type: ignore[assignment]
                try:
                    delta = event.choices[0].delta.content or ""
                except Exception:
                    delta = ""
                if delta:
                    content += delta
                    dot_count += len(delta)
                    if dot_count >= 48:
                        print(".", end="", flush=True)
                        dot_count = 0
        finally:
            if dot_count > 0:
                print(".", end="", flush=True)
            print("")
        return content
    else:
        try:
            response = _request_with_retry(False)
        except Exception as e:
            rprint(f"[red]Error during AI processing: {e}[/red]")
            return None
        return response.choices[0].message.content if response.choices else None


def _extract_json_object(text: str) -> str | None:
    """Extract the first top-level JSON object substring from text."""
    in_string = False
    escape = False
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return text[start : i + 1]
    return None


def _parse_json_object(content: str) -> dict | None:
    if not content:
        return None
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    obj = _extract_json_object(content)
    if obj:
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    if "```" in content:
        try:
            inner = content.split("```", 2)[1]
            maybe = _extract_json_object(inner) or inner
            parsed = json.loads(maybe)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return None


def _extract_json_array(text: str) -> str | None:
    """Extract the first top-level JSON array substring from text.

    Handles extra prose/code fences by scanning for balanced square brackets
    while ignoring brackets inside quoted strings.
    """
    in_string = False
    escape = False
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == '[':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == ']':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return text[start : i + 1]
    return None


def _parse_batch_content(content: str) -> list[dict]:
    # 1) Direct JSON parse
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    # 2) Try extracting an array substring
    arr = _extract_json_array(content)
    if arr:
        try:
            parsed = json.loads(arr)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    # 3) Code fence extraction
    if "```" in content:
        try:
            inner = content.split("```", 2)[1]
            maybe = _extract_json_array(inner) or inner
            parsed = json.loads(maybe)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    # 4) Pipe-delimited fallback (line based) - only englishTitle|chineseTitle
    out: list[dict] = []
    for line in content.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            out.append(
                {
                    "index": len(out),
                    "englishTitle": parts[0],
                    "chineseTitle": parts[1],
                }
            )
    return out


def _parse_single_pipe_content(content: str) -> dict | None:
    if not content:
        return None

    line = content.strip()
    if "\n" in line:
        line = line.splitlines()[0].strip()

    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 2:
        return None

    return {
        "englishTitle": parts[0],
        "chineseTitle": parts[1],
    }


def _parse_single_content(content: str) -> dict | None:
    """Parse single-item AI content. Prefer JSON object, fallback to pipe format."""
    parsed = _parse_json_object(content)
    if isinstance(parsed, dict):
        return {
            "englishTitle": str(parsed.get("englishTitle", "")).strip(),
            "chineseTitle": str(parsed.get("chineseTitle", "")).strip(),
        }
    return _parse_single_pipe_content(content)


def aiScraper(config: AIConfig, romFile: RomFile, platform: str = "unknown", useCache: bool = True):

    # rprint(
    #     f"[blue]Using AI to scrape information for ROM file: {romFile.originalFilename}[/blue]"
    # )
    # rprint(f"[blue]Platform: {platform}[/blue]")
    # rprint(f"[blue]Model: {config.model}[/blue]")
    # rprint(f"[blue]API Key: {config.apiKey}[/blue]")
    # rprint(f"[blue]Endpoint: {config.endpoint}[/blue]")
    
    # cacheModule.romInfoCache is a Cache instance
    cache = cacheModule.romInfoCache
    
    key = _cache_key(romFile, platform)
    rprint(
        f"[cyan]AI 正在查询 (Querying)[/cyan] [white]{romFile.originalFilename}[/white] "
        f"[cyan]平台 (Platform): {platform}[/cyan]"
    )
    if useCache:
        cachedResult = cache.get(key)
        if cachedResult is not None:
            rprint(f"[green]AI 缓存命中 (Cache hit):[/green] {romFile.originalFilename}")
            return cachedResult

    client = OpenAI(
        api_key=config.apiKey,
        base_url=config.endpoint,
    )

    # Implement the AI renaming logic here

    try:
        content = _chat_completion_content(
            client,
            model=config.model,
            messages=[
                {
                    "role": "system",
                    "content": "You will help to identify emulator ROM file names. Return ONLY one JSON object with fields: englishTitle, chineseTitle. Use empty string when unknown. Do not return any other information.",
                },
                {
                    "role": "user",
                    "content": f"Here is a ROM file name: {romFile.originalFilename}. The game platform might be on: {platform} platform. Return the English title and Chinese title of this game.",
                },
            ],
            temperature=0.1,
            stream=True,
            progress_prefix=f"AI 正在流式返回 (Streaming) {romFile.originalFilename}",
        )
    except Exception as e:
        raise AIQueryError(str(e)) from e

    if content is not None:
        ai_result = _parse_single_content(content)
        if ai_result is None:
            rprint(
                f"[yellow]AI 返回格式无法解析 (Unparseable response), filename: {romFile.originalFilename}[/yellow]"
            )
            return None

        if useCache and ai_result["chineseTitle"] and ai_result["englishTitle"]:
            cache.add(key, ai_result, timeout=-1)
        rprint(f"[green]AI 返回结果 (Received):[/green] {romFile.originalFilename}")
        rprint(
            f"  标题 (CN/EN): {ai_result['chineseTitle']} / {ai_result['englishTitle']}"
        )
        return ai_result

    rprint("[red]No content returned from AI response.[/red]")
    pass


def aiScraperBatch(
    config: AIConfig,
    romFiles: list[RomFile],
    platform: str = "unknown",
    useCache: bool = True,
    batch_size: int = 10,
):
    """Batch AI enrichment for multiple ROM filenames.

    Returns a dict mapping originalFilename -> result dict.
    Caches by filename+platform key to avoid re-querying.
    """

    cache = cacheModule.romInfoCache
    results: dict[str, dict] = {}
    to_query: list[RomFile] = []
    cache_hits = 0

    # First, satisfy from cache
    for rf in romFiles:
        key = _cache_key(rf, platform)
        if useCache:
            cached = cache.get(key)
            if cached is not None:
                results[rf.originalFilename] = cached
                cache_hits += 1
                continue
        to_query.append(rf)

    rprint(
        f"[cyan]AI 准备处理 (Enrichment requested):[/cyan] [white]{len(romFiles)}[/white] 文件 (files) "
        f"[cyan]平台 (Platform): {platform}, 批量 (Batch size): {batch_size}[/cyan]"
    )
    if cache_hits:
        rprint(f"[green]AI 缓存命中 (Cache hits):[/green] {cache_hits}")

    if not to_query:
        rprint("[green]AI 全部来自缓存 (All results served from cache).[/green]")
        return results

    client = OpenAI(api_key=config.apiKey, base_url=config.endpoint)

    # Chunk queries to keep context reasonable
    total_batches = (len(to_query) + max(1, batch_size) - 1) // max(1, batch_size)
    for batch_idx, start in enumerate(range(0, len(to_query), max(1, batch_size))):
        chunk = to_query[start : start + max(1, batch_size)]
        rprint(
            f"[cyan]AI 批次 (Batch) {batch_idx + 1}/{total_batches}:[/cyan] 正在查询 (Querying) {len(chunk)} 文件 (files)..."
        )
        # Build a compact prompt expecting strict JSON
        listing = [
            {"index": i, "filename": rf.originalFilename}
            for i, rf in enumerate(chunk)
        ]
        system = (
            "You identify emulator ROM file names. Return ONLY a JSON array."
            " Each array element MUST correspond to the input items IN THE SAME ORDER."
            " For every input item include these fields exactly: index, filename, englishTitle, chineseTitle."
            " Rules: Do not skip items. Do not reorder. 'index' must match the provided index."
            " If chineseTitle clearly indicates a specific game, do NOT substitute a different game title."
            " Prefer leaving englishTitle empty over guessing if uncertain."
            " If data unknown, use an empty string (""). No markdown, no explanations, no trailing text."
        )
        user = {
            "task": "enrich",
            "platformHint": platform,
            "items": listing,
        }
        try:
            content = _chat_completion_content(
                client,
                model=config.model,
                messages=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(user, ensure_ascii=False),
                    },
                ],
                temperature=0.1,
                stream=True,
                progress_prefix=f"AI 批次流式返回 (Batch streaming) {batch_idx + 1}/{total_batches}",
            )
        except Exception as e:
            raise AIQueryError(str(e)) from e
        if content is None:
            rprint("[red]AI 错误 (Error): 批次返回为空 (None). 将跳过该批次。[/red]")
            continue
        if not content:
            rprint("[red]AI 错误 (Error): 批次返回空字符串。将跳过该批次。[/red]")
            continue

        parsed = _parse_batch_content(content)
        if not parsed:
            rprint(
                f"[yellow]AI 解析警告 (Parse warning): 批次 {batch_idx + 1} 内容未识别为结构化结果，长度 {len(content)}。[/yellow]"
            )

        # Map back to files for this batch with robust validation
        mapped = 0
        mismatches = 0
        for item in parsed:
            try:
                idx = int(item.get("index"))
            except Exception:
                continue
            if idx < 0 or idx >= len(chunk):
                continue
            rf = chunk[idx]
            # If filename returned and doesn't match expected, log mismatch and attempt to realign by filename search
            returned_filename = str(item.get("filename", "")).strip()
            if returned_filename and returned_filename != rf.originalFilename:
                # Try to locate the correct RomFile by filename inside chunk
                alt = next((c for c in chunk if c.originalFilename == returned_filename), None)
                if alt is not None:
                    rf = alt
                mismatches += 1
            ai_result = {
                "englishTitle": str(item.get("englishTitle", "")).strip(),
                "chineseTitle": str(item.get("chineseTitle", "")).strip(),
            }
            results[rf.originalFilename] = ai_result
            if useCache and ai_result["chineseTitle"] and ai_result["englishTitle"]:
                cache.add(_cache_key(rf, platform), ai_result, timeout=-1)
            mapped += 1
        if mismatches:
            rprint(f"[yellow]AI 警告 (Warning): 文件名不匹配次数 (filename mismatches): {mismatches}[/yellow]")

        # If nothing could be mapped, retry once with a stricter minimal prompt
        if mapped == 0 and parsed:
            # We had syntactic items but none mapped (likely index mismatch). Retry once.
            rprint("[yellow]AI 重试 (Retry): 解析后无映射，使用简化提示重试该批次。[/yellow]")
            simple_system = (
                "Return ONLY JSON array, same order, fields: index, filename, englishTitle, chineseTitle."
            )
            simple_user = {
                "items": listing,
                "platformHint": platform,
            }
            try:
                content_retry = _chat_completion_content(
                    client,
                    model=config.model,
                    messages=[
                        {"role": "system", "content": simple_system},
                        {"role": "user", "content": json.dumps(simple_user, ensure_ascii=False)},
                    ],
                    temperature=0.1,
                    stream=True,
                    progress_prefix=f"AI 批次重试流式返回 (Batch retry streaming) {batch_idx + 1}/{total_batches}",
                )
            except Exception as e:
                raise AIQueryError(str(e)) from e
            if content_retry:
                try:
                    parsed_retry = json.loads(content_retry)
                except Exception:
                    parsed_retry = []
                for item in parsed_retry:
                    try:
                        idx = int(item.get("index"))
                    except Exception:
                        continue
                    if idx < 0 or idx >= len(chunk):
                        continue
                    rf = chunk[idx]
                    returned_filename = str(item.get("filename", "")).strip()
                    if returned_filename and returned_filename != rf.originalFilename:
                        alt = next((c for c in chunk if c.originalFilename == returned_filename), None)
                        if alt is not None:
                            rf = alt
                    ai_result = {
                        "englishTitle": str(item.get("englishTitle", "")).strip(),
                        "chineseTitle": str(item.get("chineseTitle", "")).strip(),
                    }
                    results[rf.originalFilename] = ai_result
                    if useCache and ai_result["chineseTitle"] and ai_result["englishTitle"]:
                        cache.add(_cache_key(rf, platform), ai_result, timeout=-1)
                    mapped += 1

        if mapped < len(chunk):
            rprint(
                f"[yellow]AI 提示 (Notice): 映射条目少于输入 (mapped < input): {mapped}/{len(chunk)}。部分文件未被匹配。[/yellow]"
            )
        rprint(
            f"[green]AI 批次完成 (Batch complete) {batch_idx + 1}/{total_batches}:[/green] 匹配 (Mapped) {mapped}/{len(chunk)}"
        )
        # Print items where info appears missing or partial (one title missing)
        missing_or_partial: list[tuple[str, dict, str]] = []
        for item in parsed:
            try:
                idx = int(item.get("index"))
            except Exception:
                continue
            if idx < 0 or idx >= len(chunk):
                continue
            cn = str(item.get('chineseTitle','')).strip()
            en = str(item.get('englishTitle','')).strip()
            if not cn and not en:
                rf = chunk[idx]
                missing_or_partial.append((rf.originalFilename, item, "both"))
            elif not cn or not en:
                rf = chunk[idx]
                which = 'chinese' if not cn else 'english'
                missing_or_partial.append((rf.originalFilename, item, which))
        # Detect completely unmapped files in this chunk
        mapped_names = {name for name in results if name in [c.originalFilename for c in chunk]}
        for rf in chunk:
            if rf.originalFilename not in mapped_names:
                missing_or_partial.append((rf.originalFilename, {}, "unmapped"))
        if missing_or_partial:
            rprint(f"[yellow]AI 提示 (Notice): 以下文件存在缺失或未匹配信息 (missing/partial/unmapped): {len(missing_or_partial)}[/yellow]")
            for filename, item, kind in missing_or_partial:
                if kind == 'unmapped':
                    rprint(f"  [white]{filename}[/white]\n    未匹配 (Unmapped in batch response)")
                    continue
                rprint(
                    f"  [white]{filename}[/white]\n"
                    f"    缺失类型 (Missing type): {kind} 标题 (CN/EN): {item.get('chineseTitle','')} / {item.get('englishTitle','')}"
                )

        # Post-batch targeted retries only when englishTitle is missing
        refinement_targets: list[RomFile] = []
        required_fields = ["englishTitle", "chineseTitle"]
        for rf in chunk:
            data = results.get(rf.originalFilename)
            if not data:
                continue
            if not str(data.get("englishTitle", "")).strip():
                refinement_targets.append(rf)
        if refinement_targets:
            rprint(f"[cyan]AI 细化重试 (Refinement retry): 仅针对英文标题缺失的文件 {len(refinement_targets)}[/cyan]")
            for rf in refinement_targets:
                existing = results[rf.originalFilename]
                missing_list = ["englishTitle"]
                present_summary = {f: existing.get(f, '') for f in required_fields if f not in missing_list and existing.get(f)}
                user_msg = (
                    "Filename: " + rf.originalFilename + "; Platform hint: " + platform +
                    ". Provide missing fields only if you are certain."
                    " Return ONLY one JSON object with fields: englishTitle, chineseTitle."
                    " Missing fields: " + ",".join(missing_list) + ". Present fields (keep identical): " + json.dumps(present_summary, ensure_ascii=False)
                )
                try:
                    single = _chat_completion_content(
                        client,
                        model=config.model,
                        messages=[
                            {"role": "system", "content": "Return ONLY one JSON object with fields: englishTitle, chineseTitle. Use empty string if unknown. Do NOT alter existing non-empty values."},
                            {"role": "user", "content": user_msg},
                        ],
                        temperature=0.1,
                        stream=True,
                        progress_prefix=f"AI 字段补全重试 (Field fill retry) {rf.originalFilename}",
                    )
                except Exception as e:
                    raise AIQueryError(str(e)) from e
                if single:
                    single_data = _parse_json_object(single)
                    if single_data:
                        update_fields = ["englishTitle", "chineseTitle"]
                        for field in update_fields:
                            if field in missing_list:
                                value = str(single_data.get(field, "")).strip()
                                if value:
                                    results[rf.originalFilename][field] = value
                        # If after fill both titles present, store to cache
                        filled = results[rf.originalFilename]
                        if useCache and filled.get("chineseTitle") and filled.get("englishTitle"):
                            cache.add(_cache_key(rf, platform), filled, timeout=-1)
                        rprint(f"[green]AI 字段补全完成 (Fields filled): {rf.originalFilename} 缺失 -> {missing_list}" )

    rprint(
        f"[green]AI 处理完成 (Enrichment complete).[/green] 查询 (Queried) {len(to_query)}, 缓存命中 (Cache hits) {cache_hits}, 总计 (Total) {len(romFiles)}"
    )
    return results
