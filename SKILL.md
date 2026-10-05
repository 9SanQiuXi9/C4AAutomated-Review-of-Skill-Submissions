---
name: c4a-skill-evaluator
description: C4 技能提交自动评审工具 — 扫描提交文件夹，检查完整性（5 项必备交付物），评审质量（可复用/可执行/可验证/IO明确四维度），生成 Markdown/Excel/JSON 评审报告
version: 1.0.0
author: 三秋羲
tags: [education, evaluation, automation, skill-review, C4]
---

# C4A Skill Submission Evaluator

C4 技能提交自动评审工具。纯 Python 标准库实现，零第三方依赖。

## 功能概述

输入一个包含多人 C4 技能提交的文件夹，自动完成：

1. **文件扫描与作者识别** — 递归扫描目录，按 `作者名_C4_文件描述` 命名规则拆分并归属到对应作者
2. **完整性检查** — 对每位作者的提交检查 5 项必备交付物：Skill 说明文档、可执行内容、Demo 演示、教学说明、AI 生成日志
3. **质量评审** — 基于可配置评审标准（rubric.json），从四个维度打分：
   - 可复用（Reusable）：安装说明、无硬编码路径、环境要求、泛化说明
   - 可执行（Executable）：可运行代码、.skill 包结构、无语法错误、YAML frontmatter
   - 可验证（Verifiable）：测试用例、预期输出、Demo 证据、成功标准
   - IO 明确（Clear I/O）：输入输出描述、类型格式、一句话功能说明
4. **报告生成** — 输出 Markdown（终端可读）、Excel（带格式排名表）、JSON（程序可解析）三种格式

## 核心架构

```
scripts/
├── main.py           # CLI 入口，串联完整评审流程
├── scanner.py        # 文件扫描、作者识别、文件分组
├── completeness.py   # 完整性检查（5 项交付物匹配）
├── evaluator.py      # 质量评审（四维度信号匹配 + 评分）
├── reporter.py       # 报告生成（Markdown / Excel / JSON）
└── benchmark.py      # 黄金集基准测试（精确率/召回率/F1）

references/
└── rubric.json       # 评审标准配置（信号列表、阈值、权重）

benchmark/
└── golden_set/       # 12 组标注样本 + labels.json
```

## 评审流程

```
输入文件夹
    │
    ▼
scanner.py ── 递归扫描 → 文件名正则匹配 → 按作者分组
    │
    ▼
completeness.py ── 四轮检测（文件名+扩展名 → 文件名 → 内容信号 → 未找到）
    │                对 5 项交付物逐一匹配
    ▼
evaluator.py ── 拼接全部文件文本 → 逐维度逐检查项信号匹配
    │             负向信号 veto / 正向信号计数 / 条件检查跳过
    ▼
reporter.py ── 汇总排名 → 生成报告
```

## 信号匹配机制

评审标准完全由 `rubric.json` 驱动，不硬编码任何判断逻辑：

- **正向信号**：在文本中搜索关键词，命中数 ≥ min_hits 则通过
- **负向信号**：在文本中搜索禁词，命中数 ≤ max_hits 则通过（超出则 veto）
- **条件信号**：仅在特定条件满足时生效（如存在 .skill 文件时才检查包结构）
- **IO 模式**：正则匹配输入输出配对描述
- **必填检查**：标记为 required 的检查项未通过时，该维度直接判定为 ❌

## 完整性检测策略

对每项交付物采用四级置信度匹配：

1. **high** — 文件名模式 + 扩展名同时匹配
2. **medium** — 仅文件名模式匹配
3. **medium** — 文件内容信号匹配
4. **未找到** — 无匹配

## 基准测试

内置 12 组黄金集标注样本，覆盖典型场景：

- 完美提交、缺失文件、硬编码路径、无 Demo、弱 IO、无代码、无 AI 日志
- 不可验证、优秀提交、最小提交、对抗样本、缺失 Skill 文档

基准指标：12 样本 100% 匹配率，四维度精确率/召回率均 1.000。

## 运行方式

```bash
# 基本用法
python scripts/main.py <提交文件夹路径>

# 指定输出格式
python scripts/main.py ./submissions --output excel
python scripts/main.py ./submissions --output json
python scripts/main.py ./submissions --output all

# 自定义评审标准和输出路径
python scripts/main.py ./submissions --rubric my_rubric.json --report-path ./reports/

# 运行基准测试
python scripts/benchmark.py --verbose
```

## 环境要求

- Python 3.10+（仅使用标准库：pathlib, re, json, argparse, collections, datetime）
- Excel 输出需要 openpyxl（可选，缺失时跳过 Excel 生成）

## 许可

MIT License
