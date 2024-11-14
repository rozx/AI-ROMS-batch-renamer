import re


def hackMatchRegex(text):
    return re.match("((\(|\[)([Hh]ack|H)(\)|\]))|(盗版|非官方)", text)


def regionMatchRegex(text):
    return re.findall(
        "((?<=[\(\[])(繁|繁体|繁體|繁中|简|简体|简體|简中|中文|简&繁|简繁|繁简|(SC&TC|sc&tc)|(SC|sc)|(TC|tc)|(USA|usa)|(US|us)|(EU|eu)|Europe|(JP|jp)|Japan|World|(WW|ww)|(UE|ue))(?=[\)\]]))",
        text,
        re.IGNORECASE,
    )


def pinyinInitialMatchRegex(text):
    return re.match("^\d+\w", text)


def chineseMatchRegex(text):
    return re.match("汉化|润色", text)


def indexMatchRegex(text):
    return re.match("^\d+\s?-\s?", text)


def fileNameDuplicateRegEx(text):
    return re.match("-\s*\(\d\)(|.\w{1,})$", text)


def invalidFileNameMatchRegEx(text):
    return re.match('[\*\?"\<\>\|\:|：|？]', text)
