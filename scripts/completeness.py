#!/usr/bin/env python3
"""completeness.py — Check whether each author's submission has all 5 required files."""

import re
from pathlib import Path


def read_file_text(abs_path: str, max_bytes: int = 50_000) -> str:
    """Read text content from a file, with size limit."""
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except (OSError, IOError):
        return ""


def match_filename_signals(item: dict, patterns: list[str]) -> bool:
    """Check if filename matches any of the given patterns."""
    name_lower = item["name"].lower()
    path_lower = item["path"].lower()
    for pat in patterns:
        pat_lower = pat.lower()
        if pat_lower in name_lower or pat_lower in path_lower:
            return True
    return False


def match_content_signals(abs_path: str, signals: list[str], ext: str) -> bool:
    """Check if file content contains any of the given signals."""
    text_exts = {".md", ".txt", ".py", ".js", ".yaml", ".yml", ".json", ".sh", ".html", ".css", ".tex", ".skill"}
    if ext not in text_exts:
        return False

    text = read_file_text(abs_path)
    if not text:
        return False

    text_lower = text.lower()
    for sig in signals:
        if sig.lower() in text_lower:
            return True
    return False


def match_extension(item: dict, extensions: list[str]) -> bool:
    """Check if file extension matches any of the given extensions."""
    return item["ext"] in [e.lower() for e in extensions]


def check_deliverable(files: list[dict], deliverable_key: str, deliverable_config: dict) -> dict:
    """Check if a set of files satisfies one required deliverable.

    Returns: {
        'found': bool,
        'confidence': 'high' | 'medium' | 'low' | 'none',
        'matched_file': str | None,
        'match_reason': str,
    }
    """
    detection = deliverable_config.get("detection", {})
    fn_patterns = detection.get("filename_patterns", [])
    content_signals = detection.get("content_signals", [])
    extensions = detection.get("extensions", [])

    for f in files:
        fn_match = match_filename_signals(f, fn_patterns)
        ext_match = match_extension(f, extensions) if extensions else True

        if fn_match and ext_match:
            return {
                "found": True,
                "confidence": "high",
                "matched_file": f["path"],
                "match_reason": f"文件名+扩展名匹配: {f['name']}",
            }

    for f in files:
        fn_match = match_filename_signals(f, fn_patterns)
        if fn_match:
            return {
                "found": True,
                "confidence": "medium",
                "matched_file": f["path"],
                "match_reason": f"文件名匹配: {f['name']}",
            }

    for f in files:
        if content_signals:
            content_match = match_content_signals(f["abs_path"], content_signals, f["ext"])
            if content_match:
                return {
                    "found": True,
                    "confidence": "medium",
                    "matched_file": f["path"],
                    "match_reason": f"内容信号匹配: {f['name']}",
                }

    return {
        "found": False,
        "confidence": "none",
        "matched_file": None,
        "match_reason": "未找到匹配文件",
    }


def check_completeness(files: list[dict], rubric: dict) -> dict:
    """Check completeness of one author's submission against all required deliverables.

    Returns: {
        'deliverables': {key: check_result, ...},
        'files_present': int,
        'total_required': int,
        'status': 'full' | 'partial' | 'insufficient',
        'missing': [str, ...],
    }
    """
    required = rubric.get("required_deliverables", {})
    results = {}
    missing = []

    for key, config in required.items():
        result = check_deliverable(files, key, config)
        results[key] = result
        if not result["found"]:
            missing.append(config.get("label", key))

    files_present = sum(1 for r in results.values() if r["found"])
    total_required = len(required)

    if files_present == total_required:
        status = "full"
    elif files_present >= 3:
        status = "partial"
    else:
        status = "insufficient"

    return {
        "deliverables": results,
        "files_present": files_present,
        "total_required": total_required,
        "status": status,
        "missing": missing,
    }
