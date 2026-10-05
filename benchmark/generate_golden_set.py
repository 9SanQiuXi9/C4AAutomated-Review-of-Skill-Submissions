#!/usr/bin/env python3
"""Generate golden set samples for C4A evaluator benchmark."""

import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# === Sample 01: Perfect Submission ===
write_file(BASE / "sample_01_perfect/TestUser_C4_skill说明.md", """# Test Skill 说明

## 功能
一个自动整理文件夹的技能，输入文件夹路径，输出分类报告。

## 使用场景
适用于任何需要整理下载文件夹、文档文件夹等场景。

## 输入
一个本地文件夹路径（字符串）

## 输出
Markdown 格式的分类报告

## 安装
```bash
pip install -r requirements.txt
```

## 环境要求
Python 3.8+
""")

write_file(BASE / "sample_01_perfect/TestUser_C4_skill.skill", """---
name: file-organizer
description: 自动整理文件夹并生成分类报告
---

# File Organizer

## Steps
1. 扫描目标文件夹
2. 按文件类型分类
3. 生成 Markdown 报告

```python
import os
from pathlib import Path

def organize(folder):
    files = list(Path(folder).rglob("*"))
    categories = {}
    for f in files:
        ext = f.suffix.lower()
        categories.setdefault(ext, []).append(f.name)
    return categories
```
""")

write_file(BASE / "sample_01_perfect/TestUser_C4_demo说明.md", """# Demo 说明

## 运行示例
输入: `./Downloads`
输出: 分类报告（Markdown）

## 预期结果
```
| 类型 | 数量 | 文件 |
|------|------|------|
| .pdf | 5 | a.pdf, b.pdf... |
| .docx | 3 | c.docx... |
```

## 截图
见 demo_screenshot.png
""")

write_file(BASE / "sample_01_perfect/TestUser_C4_教学说明.md", """# 教学说明

## 快速上手
1. 安装 Python 3.8+
2. 下载 skill 包
3. 运行 `python main.py ./your-folder`

## 常见坑
- 确保路径不含空格
- 大文件夹（>1000 文件）可能需要等待

## 注意事项
- 仅支持本地文件夹
- 不会修改原始文件
""")

write_file(BASE / "sample_01_perfect/TestUser_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
Claude 3.5 Sonnet

## 迭代记录
- 第1轮: 基础文件扫描功能
- 第2轮: 添加分类逻辑
- 第3轮: 优化报告格式
- 第4轮: 添加错误处理

## prompt 优化
初始 prompt 过于笼统，改为分步骤描述后效果显著提升。
迭代次数: 4
""")

write_file(BASE / "sample_01_perfect/TestUser_C4_demo_screenshot.png", "[fake image content]")


# === Sample 02: Missing Teaching Doc ===
write_file(BASE / "sample_02_missing_teaching/User02_C4_skill说明.md", """# 文档摘要工具

输入一个文件夹路径，输出所有文档的摘要列表。

## 安装
pip install pypdf

## 环境要求
Python 3.7+
""")

write_file(BASE / "sample_02_missing_teaching/User02_C4_skill.skill", """---
name: doc-summarizer
description: 批量生成文档摘要
---

```python
def summarize(folder):
    from pathlib import Path
    results = []
    for f in Path(folder).rglob("*.md"):
        text = f.read_text()
        results.append({"file": f.name, "summary": text[:200]})
    return results
```
""")

write_file(BASE / "sample_02_missing_teaching/User02_C4_demo.md", """# Demo

输入: ./docs
输出: [{"file": "a.md", "summary": "..."}, ...]

测试通过，结果正确。
""")

write_file(BASE / "sample_02_missing_teaching/User02_C4_AI日志.md", """# AI 日志

使用 Claude 完成开发。
迭代 3 次。
prompt: "帮我写一个文档摘要工具"
""")


# === Sample 03: Hardcoded Paths (reusable=fail) ===
write_file(BASE / "sample_03_hardcoded_paths/User03_C4_skill说明.md", """# 文件备份工具

输入源文件夹路径，输出备份到目标位置。

## 安装
无需安装，直接运行。

## 环境要求
Python 3.6+
""")

write_file(BASE / "sample_03_hardcoded_paths/User03_C4_skill.py", """import shutil
from pathlib import Path

# 默认备份到我的电脑上的备份文件夹
SOURCE = "D:\\\\Users\\\\User03\\\\Documents"
DEST = "C:\\\\Users\\\\User03\\\\Backup"

def backup():
    shutil.copytree(SOURCE, DEST)
    print(f"已备份到 {DEST}")
""")

write_file(BASE / "sample_03_hardcoded_paths/User03_C4_demo.md", """# Demo

运行 python skill.py
输出: 已备份到 C:\\Users\\User03\\Backup
""")

write_file(BASE / "sample_03_hardcoded_paths/User03_C4_教学说明.md", """# 教学说明

## 步骤
1. 修改代码中的 SOURCE 和 DEST 路径
2. 运行 python skill.py

## 注意
路径需要改成你自己的路径。
""")

write_file(BASE / "sample_03_hardcoded_paths/User03_C4_AI日志.md", """# AI 日志

AI 工具: ChatGPT
prompt: "写一个文件备份脚本"
一次生成，未做修改。
""")


# === Sample 04: No Demo ===
write_file(BASE / "sample_04_no_demo/User04_C4_skill说明.md", """# 文本统计工具

输入文本文件路径，输出字数、行数、段落数统计。

## 安装
pip install -r requirements.txt

## 环境要求
Python 3.8+
""")

write_file(BASE / "sample_04_no_demo/User04_C4_skill.skill", """---
name: text-stats
description: 文本文件统计分析
---

```python
def text_stats(filepath):
    with open(filepath, 'r') as f:
        text = f.read()
    return {
        "chars": len(text),
        "lines": text.count('\\n'),
        "paragraphs": len(text.split('\\n\\n')),
    }
```
""")

write_file(BASE / "sample_04_no_demo/User04_C4_教学说明.md", """# 教学说明

## 上手指南
1. 安装 Python 3.8+
2. 运行 python skill.py your_file.txt

## 常见坑
- 仅支持 UTF-8 编码
""")

write_file(BASE / "sample_04_no_demo/User04_C4_AI日志.md", """# AI 日志

使用 Claude 开发，迭代 2 次。
""")


# === Sample 05: Weak IO (clear_io=fail) ===
write_file(BASE / "sample_05_weak_io/User05_C4_skill说明.md", """# 数据处理技能

这个技能可以处理各种数据文件。功能很强大，
支持多种格式，非常好用。

## 安装
pip install pandas numpy

## 环境要求
Python 3.9+
""")

write_file(BASE / "sample_05_weak_io/User05_C4_skill.skill", """---
name: data-processor
description: 数据处理技能
---

```python
import pandas as pd

def process(data):
    df = pd.DataFrame(data)
    return df.describe()
```
""")

write_file(BASE / "sample_05_weak_io/User05_C4_demo.md", """# Demo

运行后可以看到处理结果。
结果很准确，推荐使用。
""")

write_file(BASE / "sample_05_weak_io/User05_C4_教学说明.md", """# 教学说明

## 步骤
1. 准备数据
2. 运行技能
3. 查看结果
""")

write_file(BASE / "sample_05_weak_io/User05_C4_AI日志.md", """# AI 日志

AI: Claude
迭代 3 次完成。
""")


# === Sample 06: No Executable Content ===
write_file(BASE / "sample_06_no_executable/User06_C4_skill说明.md", """# 学习计划生成器

输入学习目标和时间安排，输出详细的学习计划。

## 使用场景
适用于任何需要制定学习计划的场景。

## 安装
无需安装

## 环境要求
无
""")

write_file(BASE / "sample_06_no_executable/User06_C4_demo.md", """# Demo

输入: 学习目标=Python, 时间=30天
输出: 30天学习计划表

测试通过。
""")

write_file(BASE / "sample_06_no_executable/User06_C4_教学说明.md", """# 教学说明

## 使用方法
直接描述你的需求即可获得学习计划。

## 步骤
1. 输入学习目标
2. 设置时间范围
3. 获取计划
""")

write_file(BASE / "sample_06_no_executable/User06_C4_AI日志.md", """# AI 日志

使用 ChatGPT 生成学习计划模板。
迭代 2 次。
""")


# === Sample 07: No AI Log ===
write_file(BASE / "sample_07_no_ai_log/User07_C4_skill说明.md", """# 邮件模板生成器

输入邮件类型和关键信息，输出专业邮件模板。

## 安装
pip install jinja2

## 环境要求
Python 3.7+
""")

write_file(BASE / "sample_07_no_ai_log/User07_C4_skill.skill", """---
name: email-templater
description: 生成专业邮件模板
---

```python
def generate_email(email_type, key_info):
    templates = {
        "follow_up": "Dear {name}, Following up on...",
        "thank_you": "Dear {name}, Thank you for...",
    }
    return templates.get(email_type, "").format(**key_info)
```
""")

write_file(BASE / "sample_07_no_ai_log/User07_C4_demo.md", """# Demo

输入: email_type="thank_you", key_info={"name": "John"}
输出: "Dear John, Thank you for..."

预期结果验证通过。
""")

write_file(BASE / "sample_07_no_ai_log/User07_C4_教学说明.md", """# 教学说明

## 快速上手
1. 安装依赖
2. 调用 generate_email 函数
3. 传入邮件类型和关键信息
""")


# === Sample 08: Unverifiable (verifiable=partial) ===
write_file(BASE / "sample_08_unverifiable/User08_C4_skill说明.md", """# 代码风格检查器

输入 Python 文件路径，输出代码风格检查报告。

## 安装
pip install pylint

## 环境要求
Python 3.8+
""")

write_file(BASE / "sample_08_unverifiable/User08_C4_skill.skill", """---
name: code-style-checker
description: Python 代码风格检查
---

```python
import subprocess

def check_style(filepath):
    result = subprocess.run(["pylint", filepath], capture_output=True, text=True)
    return result.stdout
```
""")

write_file(BASE / "sample_08_unverifiable/User08_C4_demo.md", """# Demo

对 test.py 运行代码风格检查。
可以看到检查报告输出。
""")

write_file(BASE / "sample_08_unverifiable/User08_C4_教学说明.md", """# 教学说明

## 步骤
1. 安装 pylint
2. 运行 check_style("your_file.py")
3. 查看报告
""")

write_file(BASE / "sample_08_unverifiable/User08_C4_AI日志.md", """# AI 日志

AI: Claude
迭代 2 次。
prompt: "帮我写一个代码风格检查工具"
""")


# === Sample 09: Excellent (with extras) ===
write_file(BASE / "sample_09_excellent/User09_C4_skill说明.md", """# 智能文件分类器 v2

## 功能
基于文件内容自动分类文件，支持 PDF/DOCX/MD/TXT。
输入任意文件夹路径，输出分类报告（Markdown/Excel/JSON）。

## 使用场景
- 整理下载文件夹
- 归档项目文档
- 清理桌面文件

## 输入
- folder_path: 本地文件夹路径（字符串）
- output_format: 报告格式，可选 markdown/excel/json（默认 markdown）

## 输出
分类报告文件，包含每个文件的分类、置信度、依据。

## 安装
```bash
pip install -r requirements.txt
```

## 环境要求
- Python 3.8+
- 支持 Windows/macOS/Linux
""")

write_file(BASE / "sample_09_excellent/User09_C4_skill.skill", """---
name: smart-file-classifier
description: 基于内容的智能文件分类器
version: 2.0
---

# Smart File Classifier

## Workflow
1. 递归扫描目标文件夹
2. 提取文件内容特征
3. 基于规则分类
4. 生成报告

```python
import os
from pathlib import Path
from collections import defaultdict

def classify_files(folder_path, output_format="markdown"):
    categories = defaultdict(list)
    for f in Path(folder_path).rglob("*"):
        if f.is_file():
            cat = infer_category(f)
            categories[cat].append(f)
    return generate_report(categories, output_format)

def infer_category(filepath):
    ext = filepath.suffix.lower()
    name = filepath.stem.lower()
    if ext in (".pdf", ".docx") and any(k in name for k in ["论文", "paper"]):
        return "学术论文"
    if ext in (".py", ".js") and "test" in name:
        return "测试代码"
    if ext == ".md" and any(k in name for k in ["readme", "说明"]):
        return "说明文档"
    return "其他"
```
""")

write_file(BASE / "sample_09_excellent/User09_C4_demo.md", """# Demo

## 测试 1: 基本功能
输入: `./test_documents`（含 20 个混合文件）
预期输出:
```
| 分类 | 数量 | 文件 |
|------|------|------|
| 学术论文 | 5 | paper1.pdf... |
| 测试代码 | 3 | test_main.py... |
| 说明文档 | 4 | README.md... |
| 其他 | 8 | ... |
```
结果: ✅ 分类准确率 95%

## 测试 2: 空文件夹
输入: `./empty_folder`
预期输出: "未找到文件"
结果: ✅ 正确处理

## 测试 3: 大文件夹
输入: `./large_folder`（500+ 文件）
预期: 30 秒内完成
结果: ✅ 耗时 12 秒
""")

write_file(BASE / "sample_09_excellent/User09_C4_教学说明.md", """# 教学说明

## 30 秒快速上手
```bash
pip install -r requirements.txt
python classifier.py ./your-folder
```

## 详细步骤
1. 确保 Python 3.8+ 已安装
2. 安装依赖: `pip install -r requirements.txt`
3. 运行: `python classifier.py <文件夹路径>`
4. 查看生成的报告文件

## 常见坑
- 路径中包含中文时需用引号包裹
- 超大文件夹（>10000 文件）建议分批处理
- PDF 内容提取需要 pypdf 库

## 优化技巧
- 使用 `--format excel` 生成 Excel 报告
- 使用 `--json` 输出机器可读格式
""")

write_file(BASE / "sample_09_excellent/User09_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
Claude 3.5 Sonnet (主力)
ChatGPT-4 (辅助)

## 迭代记录
1. v0.1: 基础文件扫描 — prompt: "扫描文件夹列出所有文件"
2. v0.2: 添加分类逻辑 — prompt: "根据文件扩展名和名称分类"
3. v0.3: 内容提取 — 发现 pypdf 提取失败，改为 fallback 到文件名
4. v0.4: 报告生成 — 添加 Markdown/Excel 双格式
5. v1.0: 错误处理 — 修复大文件超时、编码问题
6. v2.0: 性能优化 — 添加并行处理

## prompt 迭代对比
- 初始 prompt 生成代码有硬编码路径 → 添加"不要使用绝对路径"约束
- 分类准确率从 60% 提升到 95% → 增加分类规则

迭代次数: 6
总耗时: 约 3 小时
""")


# === Sample 10: Minimal Passing ===
write_file(BASE / "sample_10_minimal/User10_C4_skill说明.md", """# 简单工具

输入文件路径，输出文件内容。

## 安装
无

## 环境要求
Python 3
""")

write_file(BASE / "sample_10_minimal/User10_C4_skill.py", """def read_file(path):
    with open(path) as f:
        return f.read()
""")

write_file(BASE / "sample_10_minimal/User10_C4_demo.png", "[demo screenshot]")

write_file(BASE / "sample_10_minimal/User10_C4_教学说明.md", """# 教学

运行 python skill.py file.txt
""")

write_file(BASE / "sample_10_minimal/User10_C4_AI日志.md", """# AI日志

用 Claude 写的。
""")


# === Sample 11: Adversarial Keywords (looks good but shallow) ===
write_file(BASE / "sample_11_adversarial/User11_C4_skill说明.md", """# 高级智能自动化工作流引擎

本技能是一个高级智能自动化工作流引擎，可以处理各种复杂的自动化任务。
支持安装和配置，兼容多种环境要求。输入任意数据，输出处理结果。
功能强大，可复用于各种场景。

## 安装
pip install workflow-engine

## 环境要求
Python 3.10+
""")

write_file(BASE / "sample_11_adversarial/User11_C4_skill.skill", """---
name: workflow-engine
description: 高级智能自动化工作流引擎
---

```python
# TODO: 实现核心逻辑
def process(data):
    pass  # 待实现
```
""")

write_file(BASE / "sample_11_adversarial/User11_C4_demo.md", """# Demo

运行后输出结果。
测试通过，功能正常。
示例输出待补充。
""")

write_file(BASE / "sample_11_adversarial/User11_C4_教学说明.md", """# 教学说明

## 步骤
1. 安装
2. 配置
3. 运行

## 注意事项
请参考源代码。
""")

write_file(BASE / "sample_11_adversarial/User11_C4_AI日志.md", """# AI 日志

使用 Claude 开发。
prompt: "帮我写一个工作流引擎"
AI 生成了完整的代码框架。
""")


# === Sample 12: No Skill Doc ===
write_file(BASE / "sample_12_no_skill_doc/User12_C4_skill.skill", """---
name: csv-analyzer
description: CSV 数据分析工具
---

```python
import csv

def analyze(filepath):
    with open(filepath) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return {
        "total_rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
    }
```
""")

write_file(BASE / "sample_12_no_skill_doc/User12_C4_demo.md", """# Demo

输入: data.csv
输出: {"total_rows": 100, "columns": ["name", "age", "city"]}
""")

write_file(BASE / "sample_12_no_skill_doc/User12_C4_教学说明.md", """# 教学说明

## 使用方法
python skill.py data.csv
""")

write_file(BASE / "sample_12_no_skill_doc/User12_C4_AI日志.md", """# AI 日志

AI: ChatGPT
一次生成。
""")


# === Generate labels.json ===
labels = {
    "sample_01_perfect": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "pass",
            "clear_io": "pass"
        }
    },
    "sample_02_missing_teaching": {
        "completeness": {"expected_files": 4, "expected_status": "partial"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "pass",
            "clear_io": "pass"
        }
    },
    "sample_03_hardcoded_paths": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "fail",
            "executable": "pass",
            "verifiable": "partial",
            "clear_io": "partial"
        }
    },
    "sample_04_no_demo": {
        "completeness": {"expected_files": 4, "expected_status": "partial"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "partial",
            "clear_io": "pass"
        }
    },
    "sample_05_weak_io": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "partial",
            "clear_io": "fail"
        }
    },
    "sample_06_no_executable": {
        "completeness": {"expected_files": 4, "expected_status": "partial"},
        "quality": {
            "reusable": "pass",
            "executable": "fail",
            "verifiable": "partial",
            "clear_io": "pass"
        }
    },
    "sample_07_no_ai_log": {
        "completeness": {"expected_files": 4, "expected_status": "partial"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "pass",
            "clear_io": "pass"
        }
    },
    "sample_08_unverifiable": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "partial",
            "clear_io": "pass"
        }
    },
    "sample_09_excellent": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "pass",
            "executable": "pass",
            "verifiable": "pass",
            "clear_io": "pass"
        }
    },
    "sample_10_minimal": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "partial",
            "executable": "partial",
            "verifiable": "fail",
            "clear_io": "partial"
        }
    },
    "sample_11_adversarial": {
        "completeness": {"expected_files": 5, "expected_status": "full"},
        "quality": {
            "reusable": "partial",
            "executable": "fail",
            "verifiable": "fail",
            "clear_io": "partial"
        }
    },
    "sample_12_no_skill_doc": {
        "completeness": {"expected_files": 4, "expected_status": "partial"},
        "quality": {
            "reusable": "partial",
            "executable": "pass",
            "verifiable": "pass",
            "clear_io": "pass"
        }
    },
}

with open(BASE / "labels.json", "w", encoding="utf-8") as f:
    json.dump(labels, f, indent=2, ensure_ascii=False)

print(f"Generated {len(labels)} golden set samples in {BASE}")
