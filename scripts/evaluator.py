#!/usr/bin/env python3
"""evaluator.py — Rule-based quality evaluator for C4 four conditions.

Evaluates each submission against: Reusable, Executable, Verifiable, Clear I/O.
Uses configurable signals from rubric.yaml. Supports fatal checks (veto).
"""

import re
from pathlib import Path

from completeness import read_file_text


def read_all_text(files: list[dict]) -> str:
    """Concatenate text content from all readable files."""
    parts = []
    for f in files:
        text = read_file_text(f["abs_path"])
        if text:
            parts.append(text)
    return "\n".join(parts)


def has_skill_file(files: list[dict]) -> bool:
    """Check if the submission contains a .skill file or SKILL.md."""
    for f in files:
        if f["ext"] == ".skill":
            return True
        if f["name"].lower() in ("skill", "skill_md", "skill-md"):
            return True
        if "skill.md" in f["path"].lower():
            return True
    return False


def has_skill_md(files: list[dict]) -> bool:
    """Check if the submission contains a SKILL.md file."""
    for f in files:
        name_lower = f["name"].lower()
        if name_lower in ("skill", "skill_md", "skill-md"):
            return True
        if "skill.md" in f["path"].lower():
            return True
    return False


def count_signal_hits(text: str, signals: list[str]) -> int:
    """Count how many distinct signals are found in text."""
    text_lower = text.lower()
    hits = 0
    for sig in signals:
        if sig.lower() in text_lower:
            hits += 1
    return hits


def check_regex_pattern(text: str, pattern: str) -> bool:
    """Check if a regex pattern matches in text."""
    try:
        return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL))
    except re.error:
        return False


def has_demo_file_by_name(files: list[dict]) -> bool:
    """Check if any file has a demo-related name with media extension."""
    media_exts = {".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"}
    demo_patterns = ["demo", "演示", "截图", "screen", "录屏", "效果"]
    for f in files:
        name_lower = f["name"].lower()
        path_lower = f["path"].lower()
        if f["ext"].lower() in media_exts:
            for pat in demo_patterns:
                if pat in name_lower or pat in path_lower:
                    return True
    return False


def evaluate_check_item(text: str, item_config: dict, files: list[dict]) -> dict:
    """Evaluate a single check_item against the submission text.

    Returns: {
        'id': str,
        'label': str,
        'passed': bool,
        'hits': int,
        'evidence': str,
    }
    """
    item_type = item_config.get("type", "positive")
    item_id = item_config.get("id", "")
    label = item_config.get("label", "")

    if item_type == "conditional":
        condition = item_config.get("condition", "")
        if condition == "has_skill_file" and not has_skill_file(files):
            return {"id": item_id, "label": label, "passed": True, "hits": 0,
                    "evidence": "条件不适用（无 .skill 文件）", "skipped": True}
        if condition == "has_skill_md" and not has_skill_md(files):
            return {"id": item_id, "label": label, "passed": True, "hits": 0,
                    "evidence": "条件不适用（无 SKILL.md）", "skipped": True}

    if item_type == "negative":
        neg_signals = item_config.get("negative_signals", [])
        max_hits = item_config.get("max_hits", 0)
        hits = count_signal_hits(text, neg_signals)
        passed = hits <= max_hits
        evidence = f"发现 {hits} 处负向信号（阈值: ≤{max_hits}）"
        if hits > 0 and not passed:
            found = [s for s in neg_signals if s.lower() in text.lower()]
            evidence += f"，匹配: {found[:3]}"
        return {"id": item_id, "label": label, "passed": passed, "hits": hits, "evidence": evidence}

    pos_signals = item_config.get("positive_signals", [])
    min_hits = item_config.get("min_hits", 1)
    hits = count_signal_hits(text, pos_signals)

    io_pattern = item_config.get("io_pattern")
    if io_pattern:
        regex_match = check_regex_pattern(text, io_pattern)
        if regex_match:
            hits = max(hits, min_hits)

    if item_id == "has_demo_evidence" and hits < min_hits:
        if has_demo_file_by_name(files):
            hits = max(hits, min_hits)

    passed = hits >= min_hits
    evidence = f"发现 {hits} 处正向信号（阈值: ≥{min_hits}）"
    if passed and hits > 0:
        found = [s for s in pos_signals if s.lower() in text.lower()]
        evidence += f"，匹配: {found[:5]}"

    return {"id": item_id, "label": label, "passed": passed, "hits": hits, "evidence": evidence}


def evaluate_criterion(text: str, criterion_key: str, criterion_config: dict, files: list[dict]) -> dict:
    """Evaluate one quality criterion (e.g., reusable, executable).

    Returns: {
        'criterion': str,
        'label': str,
        'rating': '✅' | '⚠️' | '❌',
        'score': int,
        'check_results': [dict, ...],
        'fatal_vetoed': bool,
        'evidence_summary': str,
        'suggestions': [str, ...],
    }
    """
    check_items = criterion_config.get("check_items", [])
    scoring = criterion_config.get("scoring", {})
    is_fatal = criterion_config.get("fatal", False)

    pass_threshold = scoring.get("pass_threshold", 3)
    partial_threshold = scoring.get("partial_threshold", 1)

    check_results = []
    passed_count = 0
    positive_passed_count = 0
    positive_available = 0
    fatal_vetoed = False
    required_failed = False

    for item_config in check_items:
        result = evaluate_check_item(text, item_config, files)
        check_results.append(result)
        if result.get("skipped"):
            continue
        is_negative = item_config.get("type") == "negative"
        if not is_negative:
            positive_available += 1
        if result["passed"]:
            passed_count += 1
            if not is_negative:
                positive_passed_count += 1
        elif is_fatal and not is_negative:
            pass
        elif is_negative and not result["passed"]:
            fatal_vetoed = True
        if item_config.get("required") and not result["passed"]:
            required_failed = True

    no_positive_evidence = (criterion_key == "verifiable" and 
                           positive_available > 0 and 
                           positive_passed_count == 0)

    if fatal_vetoed or required_failed or no_positive_evidence:
        rating = "❌"
        score = scoring.get("fail", 0)
    elif passed_count >= pass_threshold:
        rating = "✅"
        score = scoring.get("pass", 3)
    elif passed_count >= partial_threshold:
        rating = "⚠️"
        score = scoring.get("partial", 1)
    else:
        rating = "❌"
        score = scoring.get("fail", 0)

    failed_checks = [r for r in check_results if not r["passed"] and not r.get("skipped")]
    suggestions = []
    for fc in failed_checks:
        suggestions.append(f"改进: {fc['label']} — {fc['evidence']}")

    evidence_parts = [f"{r['label']}: {'✓' if r['passed'] else '✗'}" for r in check_results if not r.get("skipped")]
    evidence_summary = "; ".join(evidence_parts)

    return {
        "criterion": criterion_key,
        "label": criterion_config.get("label", criterion_key),
        "rating": rating,
        "score": score,
        "check_results": check_results,
        "fatal_vetoed": fatal_vetoed,
        "evidence_summary": evidence_summary,
        "suggestions": suggestions,
    }


def evaluate_quality(files: list[dict], rubric: dict) -> dict:
    """Evaluate all four quality criteria for one author's submission.

    Returns: {
        'criteria': {key: criterion_result, ...},
        'total_score': int,
        'max_score': int,
        'quality_rating': str,
        'conservative_count': int,
    }
    """
    criteria_config = rubric.get("quality_criteria", {})
    text = read_all_text(files)

    results = {}
    total_score = 0
    max_score = 0
    conservative_count = 0

    for key, config in criteria_config.items():
        result = evaluate_criterion(text, key, config, files)
        results[key] = result
        total_score += result["score"]
        max_score += config.get("scoring", {}).get("pass", 3)

        if result["rating"] == "⚠️":
            conservative_count += 1

    total_criteria = len(criteria_config)
    if total_score >= max_score * 0.8:
        quality_rating = "优秀"
    elif total_score >= max_score * 0.5:
        quality_rating = "合格"
    else:
        quality_rating = "不合格"

    return {
        "criteria": results,
        "total_score": total_score,
        "max_score": max_score,
        "quality_rating": quality_rating,
        "conservative_count": conservative_count,
        "conservative_rate": conservative_count / total_criteria if total_criteria > 0 else 0,
    }
