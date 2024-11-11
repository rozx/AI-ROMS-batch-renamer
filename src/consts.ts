import packageJson from "../package.json";

export const version = packageJson.version;

export const fileNameDuplicateRegEx = /-\s*\(\d\)(|.\w{1,})$/g;

export const indexMatchRegEx = /^\d+\s?-\s?/g;

export const chineseMatchRegEx = /(汉化|润色)/g;

export const regionMatchRegEx =
	/((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|简&繁|简繁|繁简|(SC&TC|sc&tc)|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww)|(UE|ue))(?=[\)\]]))/g;

export const hackMatchRegEx = /((\(|\[)([Hh]ack|H)(\)|\]))|(盗版|非官方)/g;

export const invalidFileNameMatchRegEx = /[\*\?\"\<\>\|\:|：|？]/g;

export const ignoredUnzipExt = [".txt"];
