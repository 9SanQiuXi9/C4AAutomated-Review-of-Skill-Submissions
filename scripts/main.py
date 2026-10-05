#!/usr/bin/env python3
"""main.py — C4A Skill Submission Evaluator CLI entry point.

Usage:
    python main.py <FOLDER_PATH> [--output FORMAT] [--rubric PATH] [--report-path PATH]

Examples:
    python main.py ./submissions
    python main.py ./submissions --output json --report-path report.json
    python main.py ./submissions --output excel --report-path report.xlsx
    python main.py ./submissions --output all --report-path ./reports/
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scanner import scan_and_group
from completeness import check_completeness
from evaluator import evaluate_quality
from reporter import generate_markdown_report, generate_excel_report, generate_json_report


def load_rubric(rubric_path: Path) -> dict:
    """Load rubric configuration from JSON file."""
    with open(rubric_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(folder: Path, rubric: dict) -> tuple[dict, dict]:
    """Run the full evaluation pipeline.

    Returns: (scan_result, evaluations)
    """
    scan_result = scan_and_group(folder)
    evaluations = {}

    for author, author_data in scan_result["authors"].items():
        files = author_data["files"]
        comp_result = check_completeness(files, rubric)
        qual_result = evaluate_quality(files, rubric)
        evaluations[author] = {
            "completeness": comp_result,
            "quality": qual_result,
        }

    return scan_result, evaluations


def main():
    parser = argparse.ArgumentParser(
        description="C4A Skill Submission Evaluator — 自动评审 C4 技能提交"
    )
    parser.add_argument("folder", help="包含 C4 提交文件的文件夹路径")
    parser.add_argument(
        "--output", default="markdown",
        choices=["markdown", "excel", "json", "all"],
        help="输出格式 (default: markdown)"
    )
    parser.add_argument(
        "--rubric", default=None,
        help="评审标准 JSON 文件路径 (default: references/rubric.json)"
    )
    parser.add_argument(
        "--report-path", default=None,
        help="报告输出路径 (default: 当前目录)"
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"ERROR: '{folder}' 不是有效目录", file=sys.stderr)
        sys.exit(1)

    if args.rubric:
        rubric_path = Path(args.rubric).resolve()
    else:
        rubric_path = SCRIPT_DIR.parent / "references" / "rubric.json"

    if not rubric_path.exists():
        print(f"ERROR: 评审标准文件不存在: {rubric_path}", file=sys.stderr)
        sys.exit(1)

    rubric = load_rubric(rubric_path)
    print(f"加载评审标准: {rubric_path}", file=sys.stderr)

    scan_result, evaluations = run_evaluation(folder, rubric)
    print(f"扫描完成: {scan_result['author_count']} 位作者, {scan_result['c4_files']} 个 C4 文件", file=sys.stderr)

    if args.report_path:
        report_base = Path(args.report_path)
    else:
        report_base = Path.cwd()

    if args.output in ("markdown", "all"):
        md_report = generate_markdown_report(scan_result, evaluations, rubric)
        if report_base.is_dir() or str(report_base).endswith("/"):
            md_path = report_base / "C4A_评审报告.md"
        else:
            md_path = report_base.with_suffix(".md") if not str(report_base).endswith(".md") else report_base
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"Markdown 报告: {md_path}", file=sys.stderr)

    if args.output in ("excel", "all"):
        if report_base.is_dir() or str(report_base).endswith("/"):
            xlsx_path = report_base / "C4A_评审报告.xlsx"
        else:
            xlsx_path = report_base.with_suffix(".xlsx")
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        generate_excel_report(scan_result, evaluations, rubric, str(xlsx_path))
        print(f"Excel 报告: {xlsx_path}", file=sys.stderr)

    if args.output in ("json", "all"):
        json_report = generate_json_report(scan_result, evaluations, rubric)
        if report_base.is_dir() or str(report_base).endswith("/"):
            json_path = report_base / "C4A_评审报告.json"
        else:
            json_path = report_base.with_suffix(".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_report)
        print(f"JSON 报告: {json_path}", file=sys.stderr)

    if args.output == "markdown":
        md_report = generate_markdown_report(scan_result, evaluations, rubric)
        print(md_report)

    print(f"\n评审完成。", file=sys.stderr)


if __name__ == "__main__":
    main()
