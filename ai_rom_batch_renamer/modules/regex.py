hackMatchRegex = r"((\(|\[)([Hh]ack|H)(\)|\]))|(盗版|非官方)"

regionMatchRegex = r"((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|简&繁|简繁|繁简|(SC&TC|sc&tc)|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww)|(UE|ue))(?=[\)\]]))"

pinyinInitialMatchRegex = r"^\d+\w"

chineseMatchRegex = r"汉化|润色"

indexMatchRegex = r"^\d+\s?-\s?"

fileNameDuplicateRegEx = r"-\s*\(\d\)(|.\w{1,})$"

invalidFileNameMatchRegEx = r'[\*\?"\<\>\|\:|：|？]'

bracketsAndContentMatchRegEx = r"(\(.+\)|\[.+\]|\{.+\})"

extraSpaceMatchRegEx = r"\s{2,}"

contentAfterUnderscoreMatchRegEx = r"_.+?(?=\.\w{1,})"

titleInitialMatchRegEx = r"^\w\s"

copyMatchRegEx = r"\scopy\s?\d{0,}$"
