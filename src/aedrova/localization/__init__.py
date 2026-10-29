"""Reader-specific localization; stored conversations always retain their source text."""

LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
    "ar": "العربية",
    "ur": "اردو",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "id": "Bahasa Indonesia",
    "vi": "Tiếng Việt",
    "th": "ไทย",
    "tr": "Türkçe",
    "ru": "Русский",
}
RTL = {"ar", "ur"}


def normalize(value):
    if not isinstance(value, str):
        return "en"
    return (
        value.split("-")[0].split("_")[0].lower()
        if value.split("-")[0].split("_")[0].lower() in LANGUAGES
        else "en"
    )


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
