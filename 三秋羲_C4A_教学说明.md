# C4 技能提交自动评审 — 教学说明

## 快速上手

### 第一步：确认环境

需要 Python 3.10 或更高版本。打开终端运行：

```bash
python --version
```

如果显示 3.10+ 即可。无需安装任何第三方包。

### 第二步：获取工具

将 `c4a-skill-evaluator` 文件夹放到任意位置。目录结构如下：

```
c4a-skill-evaluator/
├── scripts/          # 核心代码（6 个 Python 文件）
├── references/       # 评审标准配置
│   └── rubric.json
├── benchmark/        # 基准测试（黄金集样本）
│   └── golden_set/
├── SKILL.md          # 技能定义
├── skill说明文档.md   # 功能说明
├── 教学说明.md        # 本文档
├── AI日志.md         # AI 使用记录
└── demo说明.md        # 演示说明
```

### 第三步：准备提交文件夹

将待评审的 C4 提交文件放入一个文件夹。文件命名规则：

```
作者名_C4_文件描述.ext
```

示例：
```
张三_C4_skill说明.md
张三_C4_skill.py
张三_C4_demo.mp4
张三_C4_教学说明.md
张三_C4_AI日志.md
李四_C4_skill说明.md
李四_C4_skill.skill
...
```

支持的文件类型：`.md`, `.py`, `.js`, `.skill`, `.txt`, `.json`, `.yaml`, `.sh`, `.mp4`, `.png`, `.jpg` 等。

### 第四步：运行评审

打开终端，进入工具所在目录，运行：

```bash
python scripts/main.py <提交文件夹路径>
```

例如提交文件夹在桌面的 `submissions` 目录：

```bash
python scripts/main.py ~/Desktop/submissions
```

默认输出 Markdown 格式报告到终端。

### 第五步：查看报告

#### Markdown 报告（默认）

直接在终端显示，包含：
- 班级总览（提交人数、完整率、平均质量分）
- 每位作者的完整性检查表和质量评审表
- 排名（按综合分降序）
- 全班改进建议

#### Excel 报告

```bash
python scripts/main.py ./submissions --output excel --report-path ./reports/
```

生成 `C4A_评审报告.xlsx`，包含两个工作表：
- **评审总览**：排名、完整性、质量分、综合分、缺失文件
- **质量详情**：每人四维度的评级和得分

#### JSON 报告

```bash
python scripts/main.py ./submissions --output json --report-path report.json
```

生成结构化 JSON，适合程序化处理。

#### 全部格式同时输出

```bash
python scripts/main.py ./submissions --output all --report-path ./reports/
```

## 进阶用法

### 自定义评审标准

编辑 `references/rubric.json` 可以调整：

**修改信号列表**：在对应检查项的 `positive_signals` 或 `negative_signals` 中添加/删除关键词。

**调整阈值**：
- `min_hits`：正向信号最少命中数
- `max_hits`：负向信号最多允许命中数
- `pass_threshold`：通过检查需要的最少通过检查项数
- `partial_threshold`：部分通过需要的最少通过检查项数

**调整权重**：
- `composite.formula`：综合分计算公式
- 当前默认：完整性 40% + 质量 60%

### 运行基准测试

验证评审准确性：

```bash
python scripts/benchmark.py --verbose
```

输出：
- 完全匹配率（期望与实际的匹配比例）
- 各维度精确率、召回率、F1
- 不一致样本详情

### 评审标准适配不同课程

如果需要为不同课程使用不同的评审标准：

1. 复制 `references/rubric.json` 为 `my_course_rubric.json`
2. 修改配置
3. 运行时指定：`python scripts/main.py ./submissions --rubric my_course_rubric.json`

## 常见问题

### Q: 文件名不符合命名规则怎么办？

工具会尝试使用父文件夹名作为作者标识。如果文件夹名也无法识别，文件会被归入 "Unknown" 类别。

### Q: Excel 输出报错？

Excel 生成依赖 `openpyxl` 库。如果未安装，工具会跳过 Excel 生成并输出提示。安装方式：

```bash
pip install openpyxl
```

其他格式（Markdown、JSON）不依赖任何第三方库。

### Q: 如何判断评审结果是否准确？

运行基准测试：

```bash
python scripts/benchmark.py --verbose
```

12 组黄金集样本的标注答案已知，基准测试会计算评审结果与标注答案的一致性。当前版本达到 100% 匹配率。

### Q: 提交文件中包含二进制文件（图片、视频）怎么办？

工具会尝试读取二进制文件的文本内容（失败时跳过）。对于完整性检查，二进制文件通过文件名和扩展名匹配。对于质量评审，二进制文件的内容不参与信号匹配，但文件名中的关键词（如 "demo"）会被识别。

### Q: 如何新增一个检查项？

在 `rubric.json` 的对应维度（如 `reusable`）的 `check_items` 数组中添加新项：

```json
{
  "id": "unique_check_id",
  "label": "检查项显示名称",
  "positive_signals": ["关键词1", "关键词2"],
  "min_hits": 1
}
```

负向检查项：

```json
{
  "id": "no_xxx",
  "label": "无 xxx",
  "type": "negative",
  "negative_signals": ["禁词1", "禁词2"],
  "max_hits": 0
}
```

### Q: 保守率是什么？

保守率衡量评审是否倾向于给出比期望更低的评分。具体来说，当期望为 "pass" 但实际为 "partial" 时，记为一次保守判断。保守率 = 保守判断次数 / 期望为 pass 的总次数。

理想的保守率应低于 15%。当前版本保守率为 0%。

## 注意事项

1. **文件编码**：工具默认使用 UTF-8 读取文本文件。如果提交文件使用其他编码（如 GBK），可能出现乱码，影响内容信号匹配。
2. **文件大小**：单个文件最多读取 50KB 内容。超大文件只检查前 50KB。
3. **路径分隔符**：工具使用 pathlib，自动适配 Windows/macOS/Linux 的路径分隔符。
4. **隐藏文件**：以 `.` 开头的文件（如 `.DS_Store`）会被自动忽略。
