"""Reader-specific localization; stored conversations always retain their source text."""

LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "ar": "العربية",
    "az": "Azərbaycanca",
    "bg": "Български",
    "bn": "বাংলা",
    "ca": "Català",
    "cs": "Čeština",
    "da": "Dansk",
    "de": "Deutsch",
    "el": "Ελληνικά",
    "eo": "Esperanto",
    "es": "Español",
    "et": "Eesti",
    "eu": "Euskara",
    "fa": "فارسی",
    "fi": "Suomi",
    "fr": "Français",
    "ga": "Gaeilge",
    "gl": "Galego",
    "he": "עברית",
    "hu": "Magyar",
    "id": "Bahasa Indonesia",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "ky": "Кыргызча",
    "lt": "Lietuvių",
    "lv": "Latviešu",
    "ms": "Bahasa Melayu",
    "nb": "Norsk bokmål",
    "nl": "Nederlands",
    "pb": "Português (Brasil)",
    "pl": "Polski",
    "pt": "Português",
    "ro": "Română",
    "ru": "Русский",
    "sk": "Slovenčina",
    "sl": "Slovenščina",
    "sq": "Shqip",
    "sv": "Svenska",
    "sw": "Kiswahili",
    "th": "ไทย",
    "tl": "Filipino",
    "tr": "Türkçe",
    "uk": "Українська",
    "ur": "اردو",
    "vi": "Tiếng Việt",
    "zh": "简体中文",
    "zt": "繁體中文",
}
RTL = {"ar", "ur", "fa", "he"}


def normalize(value):
    if not isinstance(value, str):
        return "en"
    code = value.strip().replace("_", "-").lower()
    aliases = {"pt-br": "pb", "zh-tw": "zt", "zh-hant": "zt", "no": "nb"}
    code = aliases.get(code, code.split("-")[0])
    return code if code in LANGUAGES else "en"


def preference(user):
    metadata = getattr(user, "user_metadata", None) or {}
    return normalize(metadata.get("aedrova_language", "en")), metadata.get(
        "aedrova_translate", True
    ) is True


def chunks(text, maximum=6000):
    """Split prose at whitespace; fenced code remains byte-for-byte intact."""
    import re

    parts = []
    for block in re.split(r"(```[\s\S]*?```)", text):
        if block.startswith("```") and block.endswith("```"):
            parts.append((block, False))
            continue
        while len(block.encode()) > maximum:
            end = maximum
            while len(block[:end].encode()) > maximum:
                end -= 1
            boundary = max(block.rfind("\n", 0, end), block.rfind(" ", 0, end))
            if boundary > end // 2:
                end = boundary + 1
            parts.append((block[:end], True))
            block = block[end:]
        if block:
            parts.append((block, True))
    return parts


def choice_source(choice):
    """Canonical enum caption; localized presentation never changes submitted values."""
    index = choice.currentIndex()
    values = choice.property("i18n_items") or []
    if 0 <= index < len(values) and choice.currentText() == values[index][1]:
        return values[index][0]
    return choice.currentText()
