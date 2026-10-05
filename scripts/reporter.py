#!/usr/bin/env python3
"""reporter.py — Generate evaluation reports in Markdown, Excel, HTML, JSON."""

import json
import os
from datetime import datetime
from pathlib import Path


STATUS_EMOJI = {"full": "✅", "partial": "⚠️", "insufficient": "❌"}


def generate_markdown_report(scan_result: dict, evaluations: dict, rubric: dict) -> str:
    """Generate a full Markdown evaluation report."""
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    folder = scan_result["folder"]
    n_authors = scan_result["author_count"]
    n_files = scan_result["c4_files"]

    lines.append(f"# C4 提交自动评审报告\n")
    lines.append(f"生成时间：{timestamp}")
    lines.append(f"扫描路径：`{folder}`")
    lines.append(f"识别提交：{n_authors} 位作者，{n_files} 个 C4 文件\n")

    total_full = sum(1 for e in evaluations.values() if e["completeness"]["status"] == "full")
    total_partial = sum(1 for e in evaluations.values() if e["completeness"]["status"] == "partial")
    total_insufficient = sum(1 for e in evaluations.values() if e["completeness"]["status"] == "insufficient")

    all_quality_scores = []
    for e in evaluations.values():
        q = e["quality"]
        all_quality_scores.append(q["total_score"] / q["max_score"] if q["max_score"] > 0 else 0)
    avg_quality = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0

    lines.append("## 一、班级总览\n")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总提交人数 | {n_authors} |")
    lines.append(f"| 完整提交（5/5） | {total_full} |")
    lines.append(f"| 部分提交 | {total_partial} |")
    lines.append(f"| 严重缺失 | {total_insufficient} |")
    lines.append(f"| 平均质量分 | {avg_quality:.1%} |\n")

    lines.append("## 二、作者详情\n")
    for author, eval_data in sorted(evaluations.items()):
        if author == "Unknown":
            continue
        lines.append(f"### {author}\n")

        comp = eval_data["completeness"]
        lines.append("**完整性检查：**\n")
        lines.append("| 文件 | 状态 | 匹配文件 | 置信度 |")
        lines.append("|------|------|----------|--------|")
        for key, result in comp["deliverables"].items():
            status = "✅" if result["found"] else "❌"
            matched = result["matched_file"] or "—"
            conf = result.get("confidence", "none")
            lines.append(f"| {key} | {status} | {matched} | {conf} |")
        lines.append(f"\n完整性：{comp['files_present']}/{comp['total_required']} — {STATUS_EMOJI[comp['status']]} {comp['status']}\n")

        if comp["missing"]:
            lines.append(f"缺失文件：{', '.join(comp['missing'])}\n")

        quality = eval_data["quality"]
        lines.append("**质量评审：**\n")
        lines.append("| 条件 | 评级 | 得分 | 证据摘要 |")
        lines.append("|------|------|------|----------|")
        for key, cr in quality["criteria"].items():
            lines.append(f"| {cr['label']} | {cr['rating']} | {cr['score']}/{3} | {cr['evidence_summary'][:80]} |")
        lines.append(f"\n质量总分：{quality['total_score']}/{quality['max_score']} — {quality['quality_rating']}")
        lines.append(f"保守率：{quality['conservative_rate']:.0%}\n")

        all_suggestions = []
        for key, cr in quality["criteria"].items():
            all_suggestions.extend(cr["suggestions"])
        if all_suggestions:
            lines.append("**改进建议：**\n")
            for i, s in enumerate(all_suggestions, 1):
                lines.append(f"{i}. {s}")
            lines.append("")

        composite = comp["files_present"] / comp["total_required"] * 0.4 + \
                    (quality["total_score"] / quality["max_score"]) * 0.6 if quality["max_score"] > 0 else 0
        lines.append(f"**综合分：{composite:.1%}**（完整性 40% + 质量 60%）\n")
        lines.append("---\n")

    lines.append("## 三、排名\n")
    ranking = []
    for author, eval_data in evaluations.items():
        if author == "Unknown":
            continue
        comp = eval_data["completeness"]
        quality = eval_data["quality"]
        comp_score = comp["files_present"] / comp["total_required"]
        qual_score = quality["total_score"] / quality["max_score"] if quality["max_score"] > 0 else 0
        composite = comp_score * 0.4 + qual_score * 0.6
        ranking.append((author, comp_score, qual_score, composite))

    ranking.sort(key=lambda x: -x[3])
    lines.append("| 排名 | 作者 | 完整性 | 质量分 | 综合分 |")
    lines.append("|------|------|--------|--------|--------|")
    for i, (author, comp_s, qual_s, comp_total) in enumerate(ranking, 1):
        lines.append(f"| {i} | {author} | {comp_s:.0%} | {qual_s:.0%} | {comp_total:.0%} |")
    lines.append("")

    lines.append("## 四、全班改进建议\n")
    all_missing = []
    for eval_data in evaluations.values():
        all_missing.extend(eval_data["completeness"]["missing"])
    if all_missing:
        from collections import Counter
        missing_counts = Counter(all_missing)
        most_missing = missing_counts.most_common(3)
        lines.append(f"最常见缺失：{', '.join(f'{m} ({c}人)' for m, c in most_missing)}\n")

    weakest = None
    weakest_score = float("inf")
    for key in rubric.get("quality_criteria", {}):
        scores = [e["quality"]["criteria"][key]["score"] for e in evaluations.values() if key in e["quality"]["criteria"]]
        if scores:
            avg = sum(scores) / len(scores)
            if avg < weakest_score:
                weakest_score = avg
                weakest = rubric["quality_criteria"][key]["label"]
    if weakest:
        lines.append(f"最弱维度：{weakest}（平均 {weakest_score:.1f}/3）\n")

    return "\n".join(lines)


def generate_excel_report(scan_result: dict, evaluations: dict, rubric: dict, output_path: str):
    """Generate an Excel evaluation report."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return

    wb = Workbook()

    header_font = Font(name="Arial", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    cell_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    ws1 = wb.active
    ws1.title = "评审总览"
    headers = ["排名", "作者", "完整性", "质量分", "综合分", "缺失文件", "质量评级"]
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    ranking = []
    for author, eval_data in evaluations.items():
        if author == "Unknown":
            continue
        comp = eval_data["completeness"]
        quality = eval_data["quality"]
        comp_score = comp["files_present"] / comp["total_required"]
        qual_score = quality["total_score"] / quality["max_score"] if quality["max_score"] > 0 else 0
        composite = comp_score * 0.4 + qual_score * 0.6
        ranking.append((author, comp, quality, composite))

    ranking.sort(key=lambda x: -x[3])

    for i, (author, comp, quality, composite) in enumerate(ranking, 1):
        row = i + 1
        missing_str = ", ".join(comp["missing"]) if comp["missing"] else "无"
        values = [
            i, author,
            f"{comp['files_present']}/{comp['total_required']}",
            f"{quality['total_score']}/{quality['max_score']}",
            f"{composite:.1%}",
            missing_str,
            quality["quality_rating"],
        ]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=row, column=col, value=val)
            cell.font = cell_font
            cell.border = thin_border

    for col in range(1, len(headers) + 1):
        ws1.column_dimensions[get_column_letter(col)].width = 18
    ws1.freeze_panes = "A2"

    ws2 = wb.create_sheet("质量详情")
    criteria_headers = ["作者", "可复用", "可执行", "可验证", "IO明确", "质量总分"]
    for col, h in enumerate(criteria_headers, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    for i, (author, comp, quality, composite) in enumerate(ranking, 2):
        ws2.cell(row=i, column=1, value=author).font = cell_font
        col_idx = 2
        for key in ["reusable", "executable", "verifiable", "clear_io"]:
            cr = quality["criteria"].get(key, {})
            rating = cr.get("rating", "—")
            cell = ws2.cell(row=i, column=col_idx, value=f"{rating} {cr.get('score', 0)}/3")
            cell.font = cell_font
            cell.border = thin_border
            col_idx += 1
        cell = ws2.cell(row=i, column=col_idx, value=f"{quality['total_score']}/{quality['max_score']}")
        cell.font = cell_font
        cell.border = thin_border

    for col in range(1, len(criteria_headers) + 1):
        ws2.column_dimensions[get_column_letter(col)].width = 16
    ws2.freeze_panes = "A2"

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    wb.save(output_path)


def generate_json_report(scan_result: dict, evaluations: dict, rubric: dict) -> str:
    """Generate a JSON evaluation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "folder": scan_result["folder"],
        "summary": {
            "total_authors": scan_result["author_count"],
            "total_c4_files": scan_result["c4_files"],
        },
        "evaluations": {},
    }
    for author, eval_data in evaluations.items():
        comp = eval_data["completeness"]
        quality = eval_data["quality"]
        comp_score = comp["files_present"] / comp["total_required"]
        qual_score = quality["total_score"] / quality["max_score"] if quality["max_score"] > 0 else 0
        report["evaluations"][author] = {
            "completeness": {
                "files_present": comp["files_present"],
                "total_required": comp["total_required"],
                "status": comp["status"],
                "missing": comp["missing"],
                "score": comp_score,
            },
            "quality": {
                "total_score": quality["total_score"],
                "max_score": quality["max_score"],
                "rating": quality["quality_rating"],
                "criteria": {
                    k: {"label": v["label"], "rating": v["rating"], "score": v["score"]}
                    for k, v in quality["criteria"].items()
                },
                "score": qual_score,
            },
            "composite": comp_score * 0.4 + qual_score * 0.6,
        }
    return json.dumps(report, indent=2, ensure_ascii=False)
