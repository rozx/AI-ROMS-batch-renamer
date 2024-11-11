import { writeFile, readFile } from "fs/promises";
import { apiKeyCache, titleCache } from "./cacheUtils";
import { ChatGPTAPI } from "chatgpt";
import type { RomData } from "./types";
import { version } from "./consts";
import md5File from "md5-file";
import { basename, extname } from "path";

export const fetchTitleUsingAI = async (
	apiKey: string | Boolean | null,
	md5: string,
	filePath: string,
	noCache?: boolean
) => {
	if (!apiKey || typeof apiKey === "boolean") {
		// read api key from file
		// check if cache is available
		apiKey = apiKeyCache.getSync("apiKey") ?? null;

		if (!apiKey) {
			try {
				apiKey = await readFile("apiKey.txt", "utf8");
				apiKeyCache.putSync("apiKey", apiKey);
			} catch (error) {
				apiKey = null;
			}
		}

		if (!apiKey) {
			console.log(
				"No API key found in apiKey.txt or cache, skipping AI title fetching."
			);
			return null;
		}
	} else {
		await apiKeyCache.putSync("apiKey", apiKey);
	}

	// get basename and extname
	const extName = extname(filePath);
	const baseName = basename(filePath, extName);

	const chatGPT = new ChatGPTAPI({
		apiKey: apiKey as string,
		completionParams: {
			model: "gpt-4o-mini",
		},
	});

	try {
		// check if cache is available
		const cachedTitle: RomData = titleCache.getSync(md5);

		if (cachedTitle) {
			// check if cached version is the same as the current version
			if (cachedTitle.version !== version || noCache) {
				// if not, clear the cache
				titleCache.deleteSync(md5);
			} else {
				return cachedTitle;
			}
		}

		let res = await chatGPT.sendMessage(
			`
			Please provide game emulation rom information with "${baseName}" as filename ${
				extName ? ` also with "${extName}" as extension name` : ``
			}.`,
			{
				systemMessage:
					"you are ChatGPT, serve to fetch the rom information of the game emulation rom, return the response as [Official Chinese Game Title]|[Official English Game Title]|[Game Platform]|[Game release year]|[Region], without [] or anything extra.",
			}
		);

		let romDataList = res.text.split("|");

		const romData: RomData = {
			chineseTitle: romDataList[0],
			title: romDataList[1],
			platform: romDataList[2],
			year: romDataList[3],
			region: romDataList[4],
			version: version,
		};

		// cache the title
		titleCache.putSync(md5, romData);

		return romData;
	} catch (error: any) {
		console.log(
			`Error happened using chatgpt for file ${baseName}: not applied.`
		);
		console.log(error.message);
		// clear the cached api key
		apiKeyCache.deleteSync("apiKey");
		titleCache.deleteSync(md5);

		return null;
	}
};
