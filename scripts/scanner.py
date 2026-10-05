#!/usr/bin/env python3
"""scanner.py — Scan a folder for C4 submissions, extract authors, group files."""

import os
import re
from collections import defaultdict
from pathlib import Path


C4_PATTERN = re.compile(
    r'^(?P<author>.+?)_C4(?:A)?[_\-](?P<part>.+)$',
    re.IGNORECASE,
)

AUTHOR_BLACKLIST = {"unknown", "untitled", "noname", "test", "tmp", "temp"}


def scan_folder(folder: Path) -> list[dict]:
    """Recursively list all files in folder, returning file info dicts."""
    items = []
    for f in sorted(folder.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            try:
                stat = f.stat()
            except OSError:
                continue
            items.append({
                "path": str(f.relative_to(folder)),
                "name": f.stem,
                "ext": f.suffix.lower(),
                "size_kb": round(stat.st_size / 1024, 1),
                "abs_path": str(f),
                "parent": f.parent.name,
            })
    return items


def extract_author_from_filename(filename_stem: str) -> str | None:
    """Extract author from filename following naming convention."""
    m = C4_PATTERN.match(filename_stem)
    if m:
        author = m.group("author").strip()
        if author.lower() not in AUTHOR_BLACKLIST:
            return author
    return None


def extract_author_from_folder(parent_name: str) -> str | None:
    """Use parent folder name as author fallback."""
    if parent_name and parent_name.lower() not in AUTHOR_BLACKLIST:
        cleaned = parent_name.strip()
        if re.match(r'^[A-Za-z\u4e00-\u9fff\-_]+$', cleaned):
            return cleaned
    return None


def is_c4_file(item: dict) -> bool:
    """Check if a file is a C4 submission based on filename or path."""
    name_lower = item["name"].lower()
    path_lower = item["path"].lower()
    if "_c4_" in name_lower or "_c4a_" in name_lower:
        return True
    if "_c4_" in path_lower or "_c4a_" in path_lower:
        return True
    if item["ext"] == ".skill":
        return True
    return False


def group_by_author(items: list[dict]) -> dict[str, list[dict]]:
    """Group C4 files by author. Returns {author: [file_info, ...]}."""
    bundles = defaultdict(list)
    unassigned = []

    for item in items:
        if not is_c4_file(item):
            continue

        author = extract_author_from_filename(item["name"])
        if not author:
            author = extract_author_from_folder(item["parent"])
        if not author:
            author = "Unknown"
            unassigned.append(item)

        item["author"] = author
        item["convention_match"] = author != "Unknown"
        bundles[author].append(item)

    if unassigned:
        bundles["Unknown"] = unassigned

    return dict(bundles)


def detect_version(item: dict) -> str | None:
    """Detect version markers like _v2, _v3 in filename."""
    m = re.search(r'_v(\d+)', item["name"], re.IGNORECASE)
    if m:
        return f"v{m.group(1)}"
    return None


def scan_and_group(folder: Path) -> dict:
    """Full scan pipeline: inventory → filter C4 → group by author."""
    all_items = scan_folder(folder)
    bundles = group_by_author(all_items)

    for author, files in bundles.items():
        for f in files:
            f["version"] = detect_version(f)

    non_c4 = [item for item in all_items if not is_c4_file(item)]

    return {
        "folder": str(folder),
        "total_files": len(all_items),
        "c4_files": sum(len(files) for files in bundles.values()),
        "authors": {a: {"files": fs, "count": len(fs)} for a, fs in bundles.items()},
        "non_c4_files": [{"path": i["path"], "name": i["name"]} for i in non_c4],
        "author_count": len([a for a in bundles if a != "Unknown"]),
    }
