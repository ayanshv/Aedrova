"""Verify official offline model data without user content or inference API calls."""

import argparse
import hashlib
import json
import tempfile
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

INDEX = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"


def audit(row):
    pair = row["from_code"] + "_" + row["to_code"]
    url = next(u for u in row["links"] if u.startswith("https://argos-net.com/v1/"))
    digest, size = hashlib.sha256(), 0
    with tempfile.TemporaryFile() as file:
        with urllib.request.urlopen(url, timeout=90) as response:
            if not response.url.startswith("https://argos-net.com/v1/"):
                raise ValueError("Unexpected model host")
            while data := response.read(262144):
                size += len(data)
                if size > 700_000_000:
                    raise ValueError("Archive oversized")
                digest.update(data)
                file.write(data)
        file.seek(0)
        with zipfile.ZipFile(file) as bundle:
            names = bundle.namelist()
            metadata = next(n for n in names if n.count("/") == 1 and n.endswith("/metadata.json"))
            folder = metadata.split("/")[0]
            data = json.loads(bundle.read(metadata))
            if data.get("from_code") != row["from_code"] or data.get("to_code") != row["to_code"]:
                raise ValueError("Language metadata mismatch")
            tokenizer = next(
                (n for n in ("sentencepiece.model", "bpe.model") if folder + "/" + n in names), None
            )
            if not tokenizer or folder + "/model/model.bin" not in names:
                raise ValueError("Unsupported model/tokenizer")
            total = sum(
                info.file_size
                for info in bundle.infolist()
                if info.filename.startswith(folder + "/model/")
                or info.filename in {folder + "/" + tokenizer, metadata, folder + "/README.md"}
            )
            if total > 900_000_000:
                raise ValueError("Model oversized")
    return {
        "pair": pair,
        "url": url,
        "sha256": digest.hexdigest(),
        "bytes": size,
        "root": folder,
        "uncompressed_bytes": total + 8192,
        "tokenizer": tokenizer,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    with urllib.request.urlopen(INDEX, timeout=30) as response:
        rows = json.load(response)
    pairs = {(r["from_code"], r["to_code"]): r for r in rows}
    languages = sorted({b for a, b in pairs if a == "en"} & {a for a, b in pairs if b == "en"})
    selected = [
        pairs[key] for language in languages for key in (("en", language), (language, "en"))
    ]
    known = {
        r["pair"]: r for r in json.loads(Path("src/aedrova/localization/models.json").read_text())
    }
    verified, errors = [], {}
    with ThreadPoolExecutor(max_workers=min(16, max(1, args.workers))) as pool:
        jobs = {pool.submit(audit, row): row for row in selected}
        for future in as_completed(jobs):
            row = jobs[future]
            key = row["from_code"] + "_" + row["to_code"]
            try:
                value = future.result()
                if key in known and known[key]["sha256"] != value["sha256"]:
                    raise ValueError("Previously pinned model changed")
                verified.append(value)
                print(f"Verified {key}: {value['bytes']} bytes", flush=True)
            except Exception as error:
                errors[key] = type(error).__name__ + ": " + str(error)[:120]
    complete = [l for l in languages if {"en_" + l, l + "_en"} <= {r["pair"] for r in verified}]
    result = {
        "index": INDEX,
        "languages": ["en", *complete],
        "models": sorted(verified, key=lambda r: r["pair"]),
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Complete languages: {len(complete) + 1}; failed packages: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
