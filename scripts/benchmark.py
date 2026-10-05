#!/usr/bin/env python3
"""benchmark.py — Run evaluator against golden set with known labels.

Computes precision, recall, F1, confusion matrix, and conservative rate.
Reports per-criterion and overall metrics.

Usage:
    python benchmark.py [--golden-set PATH] [--rubric PATH] [--verbose]
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from main import load_rubric, run_evaluation


RATING_MAP = {"✅": "pass", "⚠️": "partial", "❌": "fail"}
RATING_SCORE = {"✅": 3, "⚠️": 1, "❌": 0}


def load_golden_labels(golden_dir: Path) -> dict:
    """Load golden set labels from labels.json.

    Expected format:
    {
        "sample_name": {
            "completeness": {"expected_files": int, "expected_status": "full|partial|insufficient"},
            "quality": {
                "reusable": "pass|partial|fail",
                "executable": "pass|partial|fail",
                "verifiable": "pass|partial|fail",
                "clear_io": "pass|partial|fail"
            }
        }
    }
    """
    labels_path = golden_dir / "labels.json"
    if not labels_path.exists():
        print(f"ERROR: 黄金集标签文件不存在: {labels_path}", file=sys.stderr)
        sys.exit(1)

    with open(labels_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_completeness(expected: dict, actual: dict) -> dict:
    """Compare expected vs actual completeness."""
    expected_status = expected.get("expected_status", "full")
    actual_status = actual.get("status", "insufficient")
    match = expected_status == actual_status
    return {
        "expected": expected_status,
        "actual": actual_status,
        "match": match,
    }


def compare_quality(expected: dict, actual: dict) -> dict:
    """Compare expected vs actual quality for each criterion."""
    results = {}
    for criterion_key in ["reusable", "executable", "verifiable", "clear_io"]:
        exp = expected.get(criterion_key, "pass")
        act_cr = actual.get("criteria", {}).get(criterion_key, {})
        act = RATING_MAP.get(act_cr.get("rating", "❌"), "fail")
        results[criterion_key] = {
            "expected": exp,
            "actual": act,
            "match": exp == act,
            "expected_score": {"pass": 3, "partial": 1, "fail": 0}[exp],
            "actual_score": RATING_SCORE.get(act_cr.get("rating", "❌"), 0),
        }
    return results


def compute_confusion_matrix(comparisons: list[dict], criterion_key: str) -> dict:
    """Compute confusion matrix for one criterion across all samples."""
    matrix = {
        "pass": {"pass": 0, "partial": 0, "fail": 0},
        "partial": {"pass": 0, "partial": 0, "fail": 0},
        "fail": {"pass": 0, "partial": 0, "fail": 0},
    }
    for comp in comparisons:
        q = comp["quality"]
        if criterion_key in q:
            exp = q[criterion_key]["expected"]
            act = q[criterion_key]["actual"]
            matrix[exp][act] += 1
    return matrix


def compute_metrics(comparisons: list[dict], criterion_key: str) -> dict:
    """Compute precision, recall, F1 for 'pass' class of one criterion."""
    tp = fp = fn = tn = 0
    conservative = 0

    for comp in comparisons:
        q = comp["quality"]
        if criterion_key not in q:
            continue
        exp = q[criterion_key]["expected"]
        act = q[criterion_key]["actual"]

        if exp == "pass" and act == "pass":
            tp += 1
        elif exp != "pass" and act == "pass":
            fp += 1
        elif exp == "pass" and act != "pass":
            fn += 1
            if act == "partial":
                conservative += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    conservative_rate = conservative / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "conservative_rate": conservative_rate,
        "accuracy": (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0.0,
    }


def run_benchmark(golden_dir: Path, rubric: dict, verbose: bool = False) -> dict:
    """Run full benchmark against golden set."""
    labels = load_golden_labels(golden_dir)
    comparisons = []
    disagreements = []

    for sample_name, expected in sorted(labels.items()):
        sample_path = golden_dir / sample_name
        if not sample_path.is_dir():
            if verbose:
                print(f"  SKIP: {sample_name} (目录不存在)", file=sys.stderr)
            continue

        scan_result, evaluations = run_evaluation(sample_path, rubric)

        authors = [a for a in evaluations if a != "Unknown"]
        if not authors:
            if verbose:
                print(f"  SKIP: {sample_name} (未识别到作者)", file=sys.stderr)
            continue

        author = authors[0]
        eval_data = evaluations[author]

        comp_comp = compare_completeness(expected.get("completeness", {}), eval_data["completeness"])
        qual_comp = compare_quality(expected.get("quality", {}), eval_data["quality"])

        comp_match = comp_comp["match"]
        qual_match = all(v["match"] for v in qual_comp.values())

        comparison = {
            "sample": sample_name,
            "completeness": comp_comp,
            "quality": qual_comp,
            "full_match": comp_match and qual_match,
        }
        comparisons.append(comparison)

        if not comp_match or not qual_match:
            disagreements.append(comparison)

    n = len(comparisons)
    full_matches = sum(1 for c in comparisons if c["full_match"])
    comp_matches = sum(1 for c in comparisons if c["completeness"]["match"])

    criterion_metrics = {}
    for ck in ["reusable", "executable", "verifiable", "clear_io"]:
        criterion_metrics[ck] = compute_metrics(comparisons, ck)

    avg_precision = sum(m["precision"] for m in criterion_metrics.values()) / len(criterion_metrics)
    avg_recall = sum(m["recall"] for m in criterion_metrics.values()) / len(criterion_metrics)
    avg_conservative = sum(m["conservative_rate"] for m in criterion_metrics.values()) / len(criterion_metrics)

    result = {
        "total_samples": n,
        "full_match_rate": full_matches / n if n > 0 else 0,
        "completeness_match_rate": comp_matches / n if n > 0 else 0,
        "criterion_metrics": criterion_metrics,
        "avg_precision": avg_precision,
        "avg_recall": avg_recall,
        "avg_conservative_rate": avg_conservative,
        "disagreements": [
            {"sample": d["sample"], "completeness": d["completeness"], "quality": d["quality"]}
            for d in disagreements
        ],
    }

    if verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"BENCHMARK RESULTS", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"样本数: {n}", file=sys.stderr)
        print(f"完全匹配率: {result['full_match_rate']:.1%}", file=sys.stderr)
        print(f"完整性匹配率: {result['completeness_match_rate']:.1%}", file=sys.stderr)
        print(f"平均精确率: {avg_precision:.3f}", file=sys.stderr)
        print(f"平均召回率: {avg_recall:.3f}", file=sys.stderr)
        print(f"平均保守率: {avg_conservative:.3f}", file=sys.stderr)
        print(f"\n各维度指标:", file=sys.stderr)
        for ck, m in criterion_metrics.items():
            print(f"  {ck}: P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} 保守率={m['conservative_rate']:.3f}", file=sys.stderr)
        if disagreements:
            print(f"\n不一致样本 ({len(disagreements)}):", file=sys.stderr)
            for d in disagreements:
                print(f"  {d['sample']}:", file=sys.stderr)
                if not d["completeness"]["match"]:
                    print(f"    完整性: 期望={d['completeness']['expected']} 实际={d['completeness']['actual']}", file=sys.stderr)
                for ck, cv in d["quality"].items():
                    if not cv["match"]:
                        print(f"    {ck}: 期望={cv['expected']} 实际={cv['actual']}", file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(description="C4A Evaluator Benchmark")
    parser.add_argument("--golden-set", default=None, help="黄金集目录")
    parser.add_argument("--rubric", default=None, help="评审标准 JSON")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--output", default=None, help="结果输出 JSON 路径")
    args = parser.parse_args()

    golden_dir = Path(args.golden_set).resolve() if args.golden_set else SCRIPT_DIR.parent / "benchmark" / "golden_set"
    rubric_path = Path(args.rubric).resolve() if args.rubric else SCRIPT_DIR.parent / "references" / "rubric.json"

    rubric = load_rubric(rubric_path)
    result = run_benchmark(golden_dir, rubric, verbose=args.verbose or True)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = json.loads(json.dumps(result, default=str))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
