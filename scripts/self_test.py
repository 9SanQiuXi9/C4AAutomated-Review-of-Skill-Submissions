#!/usr/bin/env python3
"""self_test.py — Self-test suite for C4A Skill Submission Evaluator.

50+ assertions covering scanner, completeness, evaluator, benchmark, and reporter.
Run: python self_test.py
"""

import json
import sys
import tempfile
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scanner import scan_folder, extract_author_from_filename, extract_author_from_folder, is_c4_file, group_by_author, scan_and_group
from completeness import read_file_text, match_filename_signals, match_content_signals, match_extension, check_deliverable, check_completeness
from evaluator import has_skill_file, has_skill_md, count_signal_hits, check_regex_pattern, evaluate_check_item, evaluate_criterion, evaluate_quality, has_demo_file_by_name
from benchmark import load_golden_labels, compare_completeness, compare_quality, compute_metrics, RATING_MAP, RATING_SCORE
from main import load_rubric, run_evaluation

passed = 0
failed = 0

def assert_test(condition, description):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {description}", file=sys.stderr)

# ============================================================
# 1. Scanner tests
# ============================================================
print("=== Scanner ===")

assert_test(extract_author_from_filename("张三_C4_skill说明") == "张三", "extract author from filename (Chinese)")
assert_test(extract_author_from_filename("Alice_C4A_skill.py") == "Alice", "extract author from filename (C4A)")
assert_test(extract_author_from_filename("Bob_C4_demo_v2.mp4") == "Bob", "extract author with version")
assert_test(extract_author_from_filename("readme.md") is None, "no author from non-C4 filename")
assert_test(extract_author_from_filename("test_C4_skill.md") is None, "blacklisted author returns None")

assert_test(extract_author_from_folder("张三") == "张三", "extract author from folder")
assert_test(extract_author_from_folder("test") is None, "blacklisted folder returns None")
assert_test(extract_author_from_folder("") is None, "empty folder returns None")

assert_test(is_c4_file({"name": "user_c4_skill", "path": "user_c4_skill.md", "ext": ".md"}), "is_c4_file: _c4_ in name")
assert_test(is_c4_file({"name": "user_c4a_skill", "path": "user_c4a_skill.md", "ext": ".md"}), "is_c4_file: _c4a_ in name")
assert_test(is_c4_file({"name": "skill", "path": "skill.py", "ext": ".skill"}), "is_c4_file: .skill extension")
assert_test(not is_c4_file({"name": "readme", "path": "readme.md", "ext": ".md"}), "is_c4_file: non-C4 file")

files = [
    {"name": "alice_c4_skill", "path": "alice_c4_skill.md", "ext": ".md", "abs_path": "/tmp/a.md", "parent": "sub"},
    {"name": "alice_c4_demo", "path": "alice_c4_demo.mp4", "ext": ".mp4", "abs_path": "/tmp/a.mp4", "parent": "sub"},
    {"name": "bob_c4_skill", "path": "bob_c4_skill.py", "ext": ".py", "abs_path": "/tmp/b.py", "parent": "sub"},
    {"name": "readme", "path": "readme.md", "ext": ".md", "abs_path": "/tmp/r.md", "parent": "sub"},
]
groups = group_by_author(files)
assert_test("alice" in groups, "group_by_author: alice present")
assert_test("bob" in groups, "group_by_author: bob present")
assert_test(len(groups["alice"]) == 2, "group_by_author: alice has 2 files")
assert_test(len(groups["bob"]) == 1, "group_by_author: bob has 1 file")

# ============================================================
# 2. Completeness tests
# ============================================================
print("=== Completeness ===")

assert_test(match_filename_signals({"name": "skill说明", "path": "skill说明.md", "ext": ".md"}, ["skill说明"]), "match_filename_signals: exact match")
assert_test(match_filename_signals({"name": "skill_doc", "path": "skill_doc.md", "ext": ".md"}, ["skill说明", "skill_doc"]), "match_filename_signals: second pattern")
assert_test(not match_filename_signals({"name": "readme", "path": "readme.md", "ext": ".md"}, ["skill说明"]), "match_filename_signals: no match")

assert_test(match_extension({"ext": ".md"}, [".md", ".txt"]), "match_extension: .md in list")
assert_test(not match_extension({"ext": ".py"}, [".md", ".txt"]), "match_extension: .py not in list")

rubric_path = SCRIPT_DIR.parent / "references" / "rubric.json"
rubric = load_rubric(rubric_path)

skill_files = [
    {"name": "skill说明", "path": "skill说明.md", "ext": ".md", "abs_path": "/tmp/skill说明.md"},
    {"name": "技能", "path": "技能.py", "ext": ".py", "abs_path": "/tmp/技能.py"},
    {"name": "demo", "path": "demo.mp4", "ext": ".mp4", "abs_path": "/tmp/demo.mp4"},
    {"name": "教学说明", "path": "教学说明.md", "ext": ".md", "abs_path": "/tmp/教学说明.md"},
    {"name": "AI日志", "path": "AI日志.md", "ext": ".md", "abs_path": "/tmp/AI日志.md"},
]
comp = check_completeness(skill_files, rubric)
assert_test(comp["files_present"] == 5, "check_completeness: 5/5 found")
assert_test(comp["status"] == "full", "check_completeness: status=full")
assert_test(len(comp["missing"]) == 0, "check_completeness: no missing")

partial_files = skill_files[:3]
comp2 = check_completeness(partial_files, rubric)
assert_test(comp2["files_present"] == 3, "check_completeness partial: 3/5")
assert_test(comp2["status"] == "partial", "check_completeness partial: status=partial")
assert_test(len(comp2["missing"]) == 2, "check_completeness partial: 2 missing")

# ============================================================
# 3. Evaluator tests
# ============================================================
print("=== Evaluator ===")

assert_test(count_signal_hits("安装 pip install", ["安装", "install"]) == 2, "count_signal_hits: 2 hits")
assert_test(count_signal_hits("nothing here", ["安装", "install"]) == 0, "count_signal_hits: 0 hits")

assert_test(check_regex_pattern("输入文件路径，输出结果", "输入.*输出"), "check_regex_pattern: match")
assert_test(not check_regex_pattern("no match here", "输入.*输出"), "check_regex_pattern: no match")

assert_test(has_skill_file([{"ext": ".skill", "name": "s", "path": "s.skill"}]), "has_skill_file: .skill ext")
assert_test(has_skill_file([{"ext": ".md", "name": "SKILL", "path": "SKILL.md"}]), "has_skill_file: SKILL.md name")
assert_test(not has_skill_file([{"ext": ".md", "name": "readme", "path": "readme.md"}]), "has_skill_file: no skill file")

assert_test(has_demo_file_by_name([{"name": "demo", "path": "demo.png", "ext": ".png"}]), "has_demo_file_by_name: demo.png")
assert_test(has_demo_file_by_name([{"name": "截图", "path": "截图.jpg", "ext": ".jpg"}]), "has_demo_file_by_name: 截图.jpg")
assert_test(not has_demo_file_by_name([{"name": "readme", "path": "readme.md", "ext": ".md"}]), "has_demo_file_by_name: no demo file")

pos_item = {"id": "test_pos", "label": "test", "positive_signals": ["安装", "install"], "min_hits": 1}
result = evaluate_check_item("运行 pip install", pos_item, [])
assert_test(result["passed"], "evaluate_check_item: positive passes")

neg_item = {"id": "test_neg", "label": "test", "type": "negative", "negative_signals": ["TODO", "FIXME"], "max_hits": 0}
result2 = evaluate_check_item("clean code", neg_item, [])
assert_test(result2["passed"], "evaluate_check_item: negative passes (clean)")
result3 = evaluate_check_item("TODO: fix this", neg_item, [])
assert_test(not result3["passed"], "evaluate_check_item: negative fails (TODO found)")

# ============================================================
# 4. Quality evaluation integration
# ============================================================
print("=== Quality Integration ===")

text_with_io = "功能：输入文件路径，输出统计报告。安装：pip install xxx。环境要求：Python 3.10。通用工具，任意路径可用。"
text_with_io += "\n```python\ndef process(path): return report\n```\n测试用例：输入 test.txt，输出 report.md。预期输出：统计报告。demo截图展示效果。成功则输出正确。"

qual = evaluate_quality(skill_files, rubric)
assert_test("criteria" in qual, "evaluate_quality: has criteria")
assert_test("total_score" in qual, "evaluate_quality: has total_score")
assert_test("max_score" in qual, "evaluate_quality: has max_score")
assert_test(qual["max_score"] == 12, "evaluate_quality: max_score=12 (4 criteria × 3)")

# ============================================================
# 5. Benchmark tests
# ============================================================
print("=== Benchmark ===")

assert_test(RATING_MAP["✅"] == "pass", "RATING_MAP: ✅ → pass")
assert_test(RATING_MAP["⚠️"] == "partial", "RATING_MAP: ⚠️ → partial")
assert_test(RATING_MAP["❌"] == "fail", "RATING_MAP: ❌ → fail")
assert_test(RATING_SCORE["✅"] == 3, "RATING_SCORE: ✅ = 3")
assert_test(RATING_SCORE["❌"] == 0, "RATING_SCORE: ❌ = 0")

golden_dir = SCRIPT_DIR.parent / "benchmark" / "golden_set"
labels = load_golden_labels(golden_dir)
assert_test(len(labels) == 12, "load_golden_labels: 12 samples")
assert_test("sample_01_perfect" in labels, "load_golden_labels: sample_01 present")

expected_comp = {"expected_status": "full"}
actual_comp = {"status": "full"}
comp_match = compare_completeness(expected_comp, actual_comp)
assert_test(comp_match["match"], "compare_completeness: match")

expected_qual = {"reusable": "pass", "executable": "pass", "verifiable": "pass", "clear_io": "pass"}
actual_qual = {"criteria": {
    "reusable": {"rating": "✅"}, "executable": {"rating": "✅"},
    "verifiable": {"rating": "✅"}, "clear_io": {"rating": "✅"}
}}
qual_match = compare_quality(expected_qual, actual_qual)
assert_test(all(v["match"] for v in qual_match.values()), "compare_quality: all match")

# ============================================================
# 6. Full pipeline test
# ============================================================
print("=== Full Pipeline ===")

scan_result, evaluations = run_evaluation(golden_dir, rubric)
assert_test(scan_result["author_count"] >= 10, "run_evaluation: at least 10 authors")
assert_test(len(evaluations) >= 10, "run_evaluation: at least 10 evaluations")

for author, eval_data in evaluations.items():
    assert_test("completeness" in eval_data, f"run_evaluation: {author} has completeness")
    assert_test("quality" in eval_data, f"run_evaluation: {author} has quality")

# ============================================================
# 7. Rubric structure tests
# ============================================================
print("=== Rubric Structure ===")

assert_test("required_deliverables" in rubric, "rubric: has required_deliverables")
assert_test("quality_criteria" in rubric, "rubric: has quality_criteria")
assert_test(len(rubric["required_deliverables"]) == 5, "rubric: 5 required deliverables")
assert_test(len(rubric["quality_criteria"]) == 4, "rubric: 4 quality criteria")
assert_test("reusable" in rubric["quality_criteria"], "rubric: has reusable")
assert_test("executable" in rubric["quality_criteria"], "rubric: has executable")
assert_test("verifiable" in rubric["quality_criteria"], "rubric: has verifiable")
assert_test("clear_io" in rubric["quality_criteria"], "rubric: has clear_io")

for key, config in rubric["quality_criteria"].items():
    assert_test("check_items" in config, f"rubric: {key} has check_items")
    assert_test("scoring" in config, f"rubric: {key} has scoring")
    assert_test(len(config["check_items"]) >= 3, f"rubric: {key} has at least 3 check_items")

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*50}")
print(f"Self-test complete: {passed} passed, {failed} failed, {passed + failed} total")
if failed > 0:
    print(f"WARNING: {failed} tests failed!", file=sys.stderr)
    sys.exit(1)
else:
    print("All tests passed!")
