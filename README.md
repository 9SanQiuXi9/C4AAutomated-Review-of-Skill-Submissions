# C4A Skill Submission Evaluator

> C4 技能提交自动评审工具 — 把一文件夹的提交丢进去，自动出一份完整的评审报告。

## 快速开始

```bash
# 评审一批提交
python scripts/main.py <提交文件夹路径>

# 输出 Excel 报告
python scripts/main.py ./submissions --output excel

# 运行基准测试
python scripts/benchmark.py --verbose

# 运行自测（99 项断言）
python scripts/self_test.py
```

## 它做什么

收到一个包含多人 C4 技能提交的文件夹后，自动完成：

1. **扫描与归属** — 递归扫描目录，按 `作者名_C4_文件描述` 命名规则拆分并归属到对应作者
2. **完整性检查** — 对每位作者检查 5 项必备交付物：Skill 说明文档、可执行内容、Demo、教学说明、AI 日志
3. **质量评审** — 从四个维度打分：可复用、可执行、可验证、IO 明确
4. **报告生成** — 输出 Markdown / Excel / JSON 三种格式，含排名、改进建议

## 项目结构

```
├── SKILL.md              # 技能定义（YAML frontmatter）
├── README.md             # 本文件
├── AAR.md                # 事后复盘
├── skill说明文档.md       # 详细功能说明
├── 教学说明.md            # 上手教程与 FAQ
├── AI日志.md             # AI 使用记录
├── demo说明.md            # 演示用例与预期输出
├── scripts/              # 核心代码
│   ├── main.py           #   CLI 入口
│   ├── scanner.py        #   文件扫描与作者识别
│   ├── completeness.py   #   完整性检查
│   ├── evaluator.py      #   质量评审
│   ├── reporter.py       #   报告生成
│   ├── benchmark.py      #   基准测试
│   └── self_test.py      #   自测套件
├── references/           # 评审标准配置
│   └── rubric.json       #   信号列表、阈值、权重
└── benchmark/            # 黄金集基准测试
    └── golden_set/       #   12 组标注样本 + labels.json
```

## 技术特点

- **零依赖** — 纯 Python 标准库，无需 pip install
- **配置驱动** — 评审标准全在 rubric.json，改配置不改代码
- **可验证** — 内置 12 组黄金集样本，基准测试 100% 匹配率
- **99 项自测** — 覆盖扫描、完整性、评审、基准测试全流程

## 评审维度

| 维度 | 检查内容 | 致命检查 |
|------|----------|----------|
| 可复用 | 安装说明、无硬编码路径、环境要求、泛化说明 | 否 |
| 可执行 | 可运行代码、.skill 包结构、无语法错误、frontmatter | 是 |
| 可验证 | 测试用例、预期输出、Demo 证据、成功标准 | 否 |
| IO 明确 | 输入输出描述、类型格式、一句话功能说明 | 是 |

## 环境要求

- Python 3.10+
- openpyxl（可选，Excel 输出需要）

## 许可

MIT License
