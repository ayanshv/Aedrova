"""Explicit native-language coding verbs; ordinary conversation stays tool-free."""

import re

LATIN = re.compile(
    r"^(?:(?:por favor|s’il vous plaît|bitte|per favore|tolong|lütfen)\s+)?"
    r"(?:crea|construye|implementa|arregla|añade|crée|construis|corrige|ajoute|"
    r"erstelle|implementiere|behebe|füge|crie|construa|corrija|adicione|"
    r"crea|costruisci|correggi|aggiungi|buat|perbaiki|tambahkan|"
    r"tạo|sửa|สร้าง|แก้ไข|oluştur|düzelt|ekle|создай|исправь|добавь)\b",
    re.I,
)
NATIVE = re.compile(
    r"बनाओ|बनाइए|बनाएँ|बनाएं|ठीक करो|ठीक करें|लागू करो|जोड़ो|"
    r"بنائیں|بنا دو|درست کریں|তৈরি কর|তৈরি করুন|ঠিক কর|"
    r"உருவாக்கு|உருவாக்கவும்|సృష్టించు|సృష్టించండి|"
    r"作成して|作って|修正して|创建|建立|修复|수정해|만들어|أنشئ|أصلح"
)


def localized_build(text):
    # Quoted examples and translation questions are content, not coding instructions.
    if re.match(
        r"^\s*(?:translate\b|what does\b|what is the meaning\b|explain the (?:word|phrase)\b)",
        text,
        re.I,
    ):
        return False
    text = re.sub(r'```[\s\S]*?```|`[^`]*`|"[^"\n]*"|“[^”\n]*”', "", text)
    if re.search(r"\b(?:don't|do not)\b|मत\s|न\s+बना|不要|하지\s*마", text, re.I):
        return False
    return bool(LATIN.search(text.strip()) or NATIVE.search(text))
