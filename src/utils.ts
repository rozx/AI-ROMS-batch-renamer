import path from "path";

// Reg Ex

export const fileNameDuplicateRegEx = /-\s*\(\d\)(|.\w{1,})$/g;

export const indexMatchRegEx = /^\d+\s?-\s?/g;

export const regionMatchRegEx =
	/((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww))(?=[\)\]]))/g;

export const hackMatchRegEx = /(\(|\[)([Hh]ack|H)[\)|\]]/g;

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

	// remove leading and trailing spaces
	const extName = path.extname(fileName);

	const baseName = fileName.substring(0, fileName.indexOf(extName)).trim();

	// adds hack to the file name
	if (hackMatch) {
		fileName = `${baseName} (Hack)`;
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
