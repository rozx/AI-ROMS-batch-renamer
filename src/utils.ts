import { file } from "bun";
import { ChatGPTAPI } from "chatgpt";
import { createWriteStream, WriteStream } from "fs";
import { writeFile, readFile } from "fs/promises";
import { rename } from "fs/promises";
import { basename, extname, dirname, resolve } from "path";
import { pipeline } from "stream/promises";
import * as yauzl from "yauzl-promise";
import type { RomData } from "./types";
import persistentCache from "persistent-cache";

// Reg Ex

export const fileNameDuplicateRegEx = /-\s*\(\d\)(|.\w{1,})$/g;

export const indexMatchRegEx = /^\d+\s?-\s?/g;

export const chineseMatchRegEx = /(汉化|润色)/g;

export const regionMatchRegEx =
	/((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|简&繁|简繁|繁简|(SC&TC|sc&tc)|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww)|(UE|ue))(?=[\)\]]))/g;

export const hackMatchRegEx = /((\(|\[)([Hh]ack|H)(\)|\]))|(盗版|非官方)/g;

export const invalidFileNameMatchRegEx = /[\*\?\"\<\>\|\:|：|？]/g;

export const ignoredUnzipExt = [".txt"];

// Cache
const apiKeyCache = persistentCache({
	name: "apiKey",
	base: "./.romRenamerCache",
});

const titleCache = persistentCache({
	name: "title",
	base: "./.romRenamerCache",
});

// Methods

export const isFileIsBeingRenamed = (fileName: string) => {
	const pinyinInitialsRegex = /^[A-Z0-9]{1}\s.+/g;
	if (pinyinInitialsRegex.test(fileName)) {
		return true;
	}
	return false;
};

export const regionMatch = (_key: string) => {
	const items = [
		{
			item: "US",
			keys: ["USA", "US", "us", "usa"],
		},
		{
			item: "JP",
			keys: ["Japan", "JP", "jp"],
		},
		{
			item: "EU",
			keys: ["Europe", "EU", "eu"],
		},
		{
			item: "繁",
			keys: ["繁", "繁体", "繁體", "繁中", "TC", "tc"],
		},
		{
			item: "简",
			keys: ["简", "简体", "简體", "简中", "中文", "SC", "sc"],
		},
		{
			item: "简&繁",
			keys: ["简&繁", "简繁", "繁简", "SC&TC", "sc&tc"],
		},
		{
			item: "WW",
			keys: ["World", "WW", "ww"],
		},
		{
			item: "UE",
			keys: ["UE", "ue"],
		},
	];

	const _filtered = items
		.filter(function (item) {
			return item.keys.indexOf(_key) != -1;
		})
		.map(function (item) {
			return item.item;
		});
	return !!_filtered.length ? _filtered[0] : _key;
};

export const getRegionInfo = (fileName: string) => {
	// check if rom is chinese
	const _chineseMatch = fileName.match(chineseMatchRegEx);

	if (_chineseMatch) {
		return "简";
	}
	// else return region info
	const _regionMatch = fileName.match(regionMatchRegEx);
	if (_regionMatch) {
		return regionMatch(_regionMatch[0]);
	}
	return null;
};

export const trimFileName = (fileName: string) => {
	// removes index from the file name
	fileName = fileName.replaceAll(indexMatchRegEx, "");

	// check if rom is hacked version
	const hackMatch = fileName.match(hackMatchRegEx);

	// remove all brackets and their contents
	fileName = fileName.replaceAll(/(\(.+\)|\[.+\]|\{.+\})/g, "");

	// remove extra spaces
	fileName = fileName.replaceAll(/\s{2,}/g, " ");

	// remove file name after _, excluding the extension
	fileName = fileName.replace(/_.+?(?=\.\w{1,})/g, "");

	const extName = extname(fileName);

	// remove leading and trailing spaces
	const baseName = fileName.substring(0, fileName.indexOf(extName)).trim();

	// adds hack to the file name
	if (hackMatch) {
		fileName = `${baseName} (Hack)`;
	} else {
		fileName = baseName;
	}

	fileName = fileName + extName;

	return fileName;
};

export const isSystemOrHiddenFile = (fileName: string) => {
	if (
		fileName.startsWith(".") ||
		fileName.endsWith(".") ||
		fileName.startsWith("~")
	) {
		return true;
	}
	return false;
};

export const unzipAndRenameFile = async (
	filePath: string,
	targetFilename: string,
	password?: string,
	preview?: boolean,
	nameOnly?: boolean
) => {
	// check if the file is a zip file
	const extName = extname(filePath);
	const unzippedFiles: string[] = [];

	if (extName !== ".zip") {
		return;
	}

	const zip = await yauzl.open(filePath);
	let readStream: any;
	let writeStream: WriteStream;

	try {
		for await (const entry of zip) {
			// skip if the entry is a directory
			if (entry.filename.endsWith("/")) continue;

			// skip if the file should be ignored
			if (ignoredUnzipExt.includes(extname(entry.filename))) continue;

			const targetUnzipFilename = `${basename(
				targetFilename,
				extName
			)}${extname(entry.filename)}`;

			unzippedFiles.push(targetUnzipFilename);

			if (nameOnly) {
				console.log(targetUnzipFilename);
			} else {
				console.log(
					`Unzip and rename${
						preview ? " preview" : ""
					}: ${filePath} -> ${targetUnzipFilename}`
				);
			}

			if (preview) {
				continue;
			}

			// extract the file

			readStream = await entry.openReadStream({
				decompress: true,
			});
			writeStream = createWriteStream(
				resolve(dirname(filePath), targetUnzipFilename)
			);

			await pipeline(readStream, writeStream);
		}
	} catch (error: any) {
		console.log(`Error when unzipping file [${filePath}]: ${error.message}`);
	} finally {
		// close the zip file
		await zip.close();
	}

	return unzippedFiles;
};

export const renameFile = async (
	file: string,
	targetFilename: string,
	preview?: boolean,
	nameOnly?: boolean
) => {
	if (nameOnly) {
		console.log(targetFilename);
	} else {
		console.log(
			`Renamed${preview ? " preview" : ""}: ${file} -> ${targetFilename}`
		);
	}

	if (preview) {
		return;
	}
	await rename(file, targetFilename);
};

export const fetchTitleUsingAI = async (
	apiKey: string | Boolean | null,
	originTitle: string
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

	const chatGPT = new ChatGPTAPI({
		apiKey: apiKey as string,
		completionParams: {
			model: "gpt-4o-mini",
		},
	});

	try {
		// check if cache is available
		const cachedTitle: RomData = titleCache.getSync(originTitle);

		if (cachedTitle) {
			return cachedTitle;
		}

		let res = await chatGPT.sendMessage(
			`
			what is "${originTitle}"'s official English title`,
			{
				systemMessage:
					"you are ChatGPT， only serve to fetch the English title of the emulation rom ，return the response as [Game Title]|[Game Platform]|[Game release year], without anything extra.",
			}
		);

		let romDataList = res.text.split("|");
		const romData: RomData = {
			title: romDataList[0],
			platform: romDataList[1],
			year: romDataList[2],
		};

		// cache the title
		titleCache.putSync(originTitle, romData);

		return romData;
	} catch (error: any) {
		console.log(
			`Error happened using chatgpt for file ${originTitle}: not applied.`
		);
		console.log(error.message);
		// clear the cached api key
		apiKeyCache.deleteSync("apiKey");
		titleCache.deleteSync(originTitle);

		return null;
	}
};
