import { createWriteStream, WriteStream } from "fs";

import { rename } from "fs/promises";
import { basename, extname, dirname, resolve } from "path";
import { pipeline } from "stream/promises";
import pinyin from "pinyin";

import {
	chineseMatchRegEx,
	ignoredUnzipExt,
	indexMatchRegEx,
	regionMatchRegEx,
} from "./consts";
import { renameHistoryCache } from "./cacheUtils";
import type { RomRenameHistory } from "./types";
import md5File from "md5-file";

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

	// remove all brackets and their contents
	fileName = fileName.replaceAll(/(\(.+\)|\[.+\]|\{.+\})/g, "");

	// remove extra spaces
	fileName = fileName.replaceAll(/\s{2,}/g, " ");

	// remove file name after _, excluding the extension
	fileName = fileName.replace(/_.+?(?=\.\w{1,})/g, "");

	const extName = extname(fileName);

	// remove leading and trailing spaces
	const baseName = fileName.substring(0, fileName.indexOf(extName)).trim();

	fileName = baseName + extName;

	return fileName;
};

export const addsPinyinInitials = (fileName: string) => {
	const pinyinInitials = pinyin(fileName, {
		style: pinyin.STYLE_FIRST_LETTER,
		heteronym: false,
	})[0][0]
		.substring(0, 1)
		.toUpperCase();

	fileName = `${pinyinInitials} ${fileName}`;

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

export const renameFile = async (
	file: string,
	targetFilename: string,
	md5: string,
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

	// save rename history
	renameHistoryCache.putSync(md5, {
		originalName: basename(file),
		newName: basename(targetFilename),
	} as RomRenameHistory);

	await rename(file, targetFilename);
};
