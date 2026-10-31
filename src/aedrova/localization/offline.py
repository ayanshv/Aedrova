"""Device-only translation. Network access is confined to explicit model installation."""

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import zipfile
from collections import OrderedDict
from pathlib import Path

from aedrova.localization import LANGUAGES, normalize

MANIFEST = json.loads(Path(__file__).with_name("models.json").read_text())
SUPPORTED = set(LANGUAGES)
PROTECTED = re.compile(
    r"```[\s\S]*?```|`[^`\n]*`|<@[^>\n]+>|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|@[\w.-]+|https?://[^\s<>\)]+|\[(?:message|file|source):[^\]\n]+\]|\b(?:Aedrova|Buds)\b|\*\*"
)
_LOCK = threading.RLock()
_ENGINES = OrderedDict()


class Unavailable(ValueError):
    pass


def model_root():
    override = os.getenv("AEDROVA_TRANSLATION_MODELS")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Aedrova/Translation"
    if sys.platform == "win32":
        return (
            Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Aedrova/Translation"
        )
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")) / "aedrova/translation"


def required(language):
    if language == "en":
        return []
    pairs = {"en_" + language, language + "_en"}
    rows = [row for row in MANIFEST if row["pair"] in pairs]
    if len(rows) != 2:
        raise Unavailable("This offline language pack is not available yet.")
    return rows


def ready(language="hi"):
    try:
        return all(
            (model_root() / row["pair"] / "ready.json").is_file() for row in required(language)
        )
    except Unavailable:
        return False


def download_size(language):
    try:
        return sum(row["bytes"] for row in required(language))
    except Unavailable:
        return 0


def install_archive(archive, row):
    """Only pinned official data files are accepted; extraction cannot execute code."""
    archive = Path(archive)
    if archive.stat().st_size != row["bytes"]:
        raise ValueError("Language download is incomplete. Retry the download.")
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
            raise ValueError("Language download failed verification. Retry the download.")
    root = model_root()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / row["pair"]
    with _LOCK, tempfile.TemporaryDirectory(dir=root) as temporary:
        if destination.is_dir():
            if (destination / "ready.json").is_file():
                return
            raise ValueError("Offline language files need repair before installation.")
        stage = Path(temporary) / row["pair"]
        stage.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            entries = [
                item
                for item in bundle.infolist()
                if item.filename.startswith(row.get("root", row["pair"]) + "/model/")
                or item.filename
                in {
                    row.get("root", row["pair"]) + "/sentencepiece.model",
                    row.get("root", row["pair"]) + "/bpe.model",
                    row.get("root", row["pair"]) + "/README.md",
                    row.get("root", row["pair"]) + "/metadata.json",
                }
            ]
            if sum(item.file_size for item in entries) > min(
                900_000_000, row.get("uncompressed_bytes", 180_000_000)
            ):
                raise ValueError("Offline language files exceeded the size limit.")
            for item in entries:
                parts = Path(item.filename).parts
                if ".." in parts or Path(item.filename).is_absolute() or item.is_dir():
                    if item.is_dir():
                        continue
                    raise ValueError("Invalid offline language files.")
                target = stage.joinpath(*parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(item) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        if not (stage / "model/model.bin").is_file() or not any(
            (stage / name).is_file() for name in ("sentencepiece.model", "bpe.model")
        ):
            raise ValueError("Offline language files are missing model data.")
        (stage / "ready.json").write_text(json.dumps(row))
        stage.rename(destination)


def download(language="hi"):
    """Explicit one-time download; sends no message, identity or workspace data."""
    import httpx

    for row in required(language):
        if (model_root() / row["pair"] / "ready.json").is_file():
            continue
        with tempfile.TemporaryDirectory(prefix="aedrova-language-") as temporary:
            archive = Path(temporary) / "language.argosmodel"
            with httpx.stream("GET", row["url"], timeout=60, follow_redirects=False) as response:
                response.raise_for_status()
                size = 0
                with archive.open("wb") as output:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > row["bytes"]:
                            raise ValueError("Language download exceeded the expected size.")
                        output.write(chunk)
            install_archive(archive, row)


def source_language(text, *, interface=False):
    if interface:
        return "en"
    prose = PROTECTED.sub("", text)
    if re.search(r"[\u0900-\u097f]", prose):
        return "hi"
    lowered = prose.strip().lower().strip(".!? ")
    greetings = {
        "bonjour": "fr",
        "hola": "es",
        "gracias": "es",
        "merci": "fr",
        "hallo": "de",
        "danke": "de",
        "ciao": "it",
        "olá": "pt",
    }
    if lowered in greetings:
        return greetings[lowered]
    if lowered in {"hello", "hi", "hey", "thanks", "thank you", "yes", "no", "ok", "okay", "test"}:
        return "en"
    try:
        import py3langid

        code = py3langid.classify(prose)[0]
        if code == "zh" and any(
            c in "體國學愛會這與臺灣說頁書間後萬對為來們當過還麼樣場長" for c in prose
        ):
            return "zt"
        return normalize(code) if code in LANGUAGES or code in {"no"} else code
    except Exception:
        return "en"


class BPETokenizer:
    def __init__(self, path, source, target):
        from sacremoses import MosesDetokenizer, MosesPunctNormalizer, MosesTokenizer
        from subword_nmt.apply_bpe import BPE

        aliases = {"pb": "pt", "zt": "zh"}
        self.normalizer = MosesPunctNormalizer(aliases.get(source, source))
        self.tokenizer = MosesTokenizer(aliases.get(source, source))
        self.detokenizer = MosesDetokenizer(aliases.get(target, target))
        with path.open(encoding="utf-8") as file:
            self.bpe = BPE(file)

    def encode(self, text, out_type=str):
        text = " ".join(self.tokenizer.tokenize(self.normalizer.normalize(text)))
        return self.bpe.process_line(text).split()

    def decode(self, tokens):
        return self.detokenizer.detokenize(" ".join(tokens).replace("@@ ", "").split())


class Model:
    def __init__(self, root):
        import ctranslate2

        self.prefix = json.loads((root / "metadata.json").read_text(encoding="utf-8")).get(
            "target_prefix", ""
        )
        self.translator = ctranslate2.Translator(
            str(root / "model"), device="cpu", compute_type="int8", intra_threads=2
        )

    def translate_batch(self, tokens, **kwargs):
        return self.translator.translate_batch(
            tokens,
            target_prefix=[[self.prefix]] * len(tokens) if self.prefix else None,
            replace_unknowns=True,
            **kwargs,
        )


def _engine(source, target):
    root = model_root() / (source + "_" + target)
    aliases = {"pt": "pb", "pb": "pt", "zh": "zt", "zt": "zh"}
    if not (root / "ready.json").is_file() and target == "en" and source in aliases:
        root = model_root() / (aliases[source] + "_en")
    key = str(root)
    if key not in _ENGINES:
        if not (root / "ready.json").is_file():
            raise Unavailable(
                "Add the required offline language pack in View → Language & translation."
            )
        import sentencepiece

        tokenizer = (
            sentencepiece.SentencePieceProcessor(model_file=str(root / "sentencepiece.model"))
            if (root / "sentencepiece.model").is_file()
            else BPETokenizer(root / "bpe.model", source, target)
        )
        _ENGINES[key] = (Model(root), tokenizer)
        while len(_ENGINES) > 2:
            _, (old, _) = _ENGINES.popitem(last=False)
            old.translator.unload_model()
    _ENGINES.move_to_end(key)
    return _ENGINES[key]


def translate(text, target, *, interface=False):
    if not isinstance(text, str) or len(text.encode()) > 24000:
        raise ValueError("Translate a smaller message.")
    with _LOCK:
        source = source_language(text, interface=interface)
        if source == target or not any(c.isalpha() for c in PROTECTED.sub("", text)):
            return text
        if source not in SUPPORTED or target not in SUPPORTED:
            raise Unavailable("This offline language pair is not installed. Showing original text.")
        if source != "en" and target != "en":
            return translate(translate(text, "en"), target, interface=True)
        translator, tokenizer = _engine(source, target)

        def prose(value):
            match = re.fullmatch(r"(\s*)(.*?)(\s*)", value, re.S)
            start, body, end = match.groups()
            if not body or not any(c.isalpha() for c in body):
                return value
            tokens = tokenizer.encode(body, out_type=str)
            results = []
            for offset in range(0, len(tokens), 256):
                result = translator.translate_batch(
                    [tokens[offset : offset + 256]],
                    beam_size=2,
                    max_decoding_length=min(
                        384, max(32, len(tokens[offset : offset + 256]) * 3 + 16)
                    ),
                    no_repeat_ngram_size=3,
                )[0]
                decoded = tokenizer.decode(result.hypotheses[0]).replace("▁", " ").strip()
                prefix = getattr(translator, "prefix", "")
                if prefix and decoded.startswith(prefix):
                    decoded = decoded[len(prefix) :].lstrip()
                if not decoded.strip() or len(decoded) > max(120, len(body) * 12):
                    raise Unavailable("Translation was not reliable. Showing original text.")
                results.append(decoded)
            return start + " ".join(results) + end

        matches = list(PROTECTED.finditer(text))
        if matches:
            # Preserve sentence context instead of translating fragments such as
            # "please" in isolation. Only use this result if every marker survives
            # exactly once; otherwise fall back to untranslated technical spans.
            prefix = "ZXQ"
            while prefix in text:
                prefix += "X"
            markers = {}

            def hide(match):
                marker = f"{prefix}{len(markers)}QXZ"
                markers[marker] = match[0]
                return marker

            masked = PROTECTED.sub(hide, text)
            translated = "\n".join(prose(line) for line in masked.split("\n"))
            if all(translated.count(marker) == 1 for marker in markers):
                for marker, original in markers.items():
                    translated = translated.replace(marker, original)
                return translated
        pieces, position = [], 0
        for match in PROTECTED.finditer(text):
            pieces.append(
                "\n".join(prose(line) for line in text[position : match.start()].split("\n"))
            )
            pieces.append(match[0])
            position = match.end()
        pieces.append("\n".join(prose(line) for line in text[position:].split("\n")))
        return "".join(pieces)


def batch(items, target):
    texts, failed = [], []
    for i, (text, interface) in enumerate(items):
        try:
            texts.append(translate(text, target, interface=interface))
        except (Unavailable, ValueError, RuntimeError):
            texts.append(text)
            failed.append(i)
    return {"texts": texts, "unavailable": failed}
