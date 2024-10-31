import { file } from "bun";
import { writeFile } from "fs/promises";
import { rename } from "fs/promises";
import { basename, extname, dirname, resolve } from "path";
import unzipper from "unzipper";

// Reg Ex

export const fileNameDuplicateRegEx = /-\s*\(\d\)(|.\w{1,})$/g;

export const indexMatchRegEx = /^\d+\s?-\s?/g;

export const chineseMatchRegEx = /(汉化|润色)/g;

export const regionMatchRegEx =
	/((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww)|(UE|ue))(?=[\)\]]))/g;

export const hackMatchRegEx = /((\(|\[)([Hh]ack|H)(\)|\]))|(盗版|非官方)/g;

export const ignoredUnzipExt = [".txt"];

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

	const extName = extname(fileName);

	// remove leading and trailing spaces
	const baseName = fileName.substring(0, fileName.indexOf(extName)).trim();

	// remove file name after _, excluding the extension
	fileName = fileName.replace(/_.+?(?=\.\w{1,})/g, "");

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

	const zip = await unzipper.Open.file(filePath);

	for (const file of zip.files) {
		// skip if the file should be ignored
		if (ignoredUnzipExt.includes(extname(file.path))) continue;

		const targetUnzipFilename = `${basename(targetFilename, extName)}${extname(
			file.path
		)}`;

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
		const extracted = await file.buffer(password);

		// write the file
		await writeFile(
			resolve(dirname(filePath), targetUnzipFilename),
			new Uint8Array(extracted)
		);
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
