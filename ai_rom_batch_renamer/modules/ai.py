from openai import OpenAI
from ai_rom_batch_renamer.modules import cache as cacheModule

from ai_rom_batch_renamer.classes import AIConfig, RomFile
from rich import print as rprint, console


def aiScraper(config: AIConfig, romFile: RomFile, useCache: bool = True, platform: str = "unknown"):

    # rprint(
    #     f"[blue]Using AI to scrape information for ROM file: {romFile.originalFilename}[/blue]"
    # )
    # rprint(f"[blue]Platform: {platform}[/blue]")
    # rprint(f"[blue]Model: {config.model}[/blue]")
    # rprint(f"[blue]API Key: {config.apiKey}[/blue]")
    # rprint(f"[blue]Endpoint: {config.endpoint}[/blue]")
    
    cache = cacheModule.romInfoCache()
    
    if useCache:
        cachedResult = cache.get(romFile.md5)
        if cachedResult is not None:
            rprint(f"[green]Found cached result for {romFile.originalFilename}[/green]")
            return cachedResult

    client = OpenAI(
        api_key=config.apiKey,
        base_url=config.endpoint,
    )

    # Implement the AI renaming logic here

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {
                    "role": "system",
                    "content": "You will help to scrape emulator ROM file information from internet sources. Return the result in the format of [English title]|[Chinese title]|[region]|[platform]|[release year]|[publisher]|[developer]. Do not return any other information.",
                },
                {
                    "role": "user",
                    "content": f"Here is a ROM file name: {romFile.originalFilename}. The game platform might be on: {platform} platform.",
                },
            ],
            temperature=1.0,
            stream=False,  # Set to True if you want streaming responses
        )
    except Exception as e:
        rprint(f"[red]Error during AI processing: {e}[/red]")
        return

    if response.choices:
        # rprint(response.choices[0].message.content)

        # Process the AI response here
        content = response.choices[0].message.content
        if content is not None:
            split_content = content.split("|")
            
            ai_result = {
                "englishTitle": split_content[0].strip(),
                "chineseTitle": split_content[1].strip(),
                "region": split_content[2].strip(),
                "platform": split_content[3].strip(),
                "releaseYear": split_content[4].strip(),
                "publisher": split_content[5].strip(),
                "developer": split_content[6].strip(),
            }

            cache.add(romFile.md5, ai_result, timeout=-1)
            return ai_result

        else:
            rprint("[red]No content returned from AI response.[/red]")
    pass
