# C4A 技能提交自动评审 — 方案设计文档

**作者**：三秋羲  
**日期**：2026-10-05  
**目标分数**：95 / 100

---

## 一、问题定义

C4 挑战要求提交 5 类文件（技能说明、可执行内容、Demo、教学说明、AI 日志），人工评审存在以下问题：

1. **效率低**：每份提交需要逐项检查 5 类文件是否齐全，再逐项评审 4 个质量维度
2. **标准不一致**：不同评审人对"有没有 Demo""代码是否可执行"的判断标准不同
3. **无法量化**：人工评审难以给出精确的量化分数，只能给"优/良/差"

需要一个自动化工具，能够：
- 扫描文件夹，自动识别每位作者的提交
- 检查 5 类文件是否齐全（完整性检查）
- 评审 4 个质量维度（可复用、可执行、可验证、IO 明确）
- 生成可读的评审报告（Markdown / Excel / JSON）

---

## 二、架构设计

### 2.1 模块划分

采用 6 模块流水线架构，每个模块职责单一：

```
scanner.py → completeness.py → evaluator.py → reporter.py
                ↓                    ↓
           rubric.json          rubric.json
                ↓
          benchmark.py
```

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **scanner.py** | 扫描文件夹，识别作者，分组文件 | 文件夹路径 | `{author: [files]}` |
| **completeness.py** | 检查 5 类文件是否齐全 | 文件列表 + rubric | 完整性报告 |
| **evaluator.py** | 评审 4 个质量维度 | 文件内容 + rubric | 质量评分 |
| **reporter.py** | 生成报告 | 评审结果 | Markdown / Excel / JSON |
| **benchmark.py** | 基准测试 | 黄金集 + 标注 | 精确率 / 召回率 / F1 |
| **main.py** | CLI 入口 | 命令行参数 | 调用上述模块 |

### 2.2 设计原则

1. **配置驱动**：所有评审标准（信号列表、阈值、权重）外置到 `rubric.json`，代码不包含任何硬编码的评审逻辑
2. **零依赖**：纯 Python 标准库实现，不需要 `pip install` 任何第三方包
3. **可量化验证**：通过基准测试模块，用精确率 / 召回率 / F1 量化评审准确性
4. **可扩展**：新增评审维度只需在 rubric.json 中添加配置块，不需要改代码

---

## 三、评审维度定义

### 3.1 完整性检查（5 项交付物）

| 交付物 | 检测策略 | 置信度 |
|--------|----------|--------|
| **技能说明文档** | 文件名含"skill说明"/"技能说明" + 扩展名 .md | high |
| **可执行内容** | 文件名含"技能" + 扩展名 .py/.skill/.js | high |
| **Demo** | 文件名含"demo"/"演示" + 扩展名 .md/.png/.mp4 | high/medium |
| **教学说明** | 文件名含"教学"/"教程" + 扩展名 .md | high |
| **AI 日志** | 文件名含"AI日志"/"AI log" + 扩展名 .md | high |

**四级置信度匹配**：
1. 文件名 + 扩展名匹配 → confidence: high
2. 仅文件名匹配 → confidence: medium
3. 内容信号匹配（如文档中包含"测试用例"） → confidence: medium
4. 未找到 → confidence: none

### 3.2 质量评审（4 个维度）

#### 维度 1：可复用（Reusable）— 权重 0.25

**定义**：代码是否模块化、参数化，能否在其他场景复用。

**检查项**：
- ✅ 正向：有函数/类定义、有参数化设计、有文档字符串
- ❌ 负向：硬编码路径、全局变量泛滥、过度耦合

**评分**：
- pass_threshold = 3（至少 3 项通过）
- pass = 3 分，partial = 1 分，fail = 0 分

#### 维度 2：可执行（Executable）— 权重 0.25

**定义**：代码是否能直接运行，不依赖未声明的环境。

**检查项**：
- ✅ 正向：有 shebang、有依赖声明、有运行说明
- ❌ 负向：硬编码路径（`C:\Users\`）、TODO/FIXME 占位符、语法错误

**评分**：
- fatal = true（负向信号触发时直接否决）
- pass = 3 分，fail = 0 分

#### 维度 3：可验证（Verifiable）— 权重 0.25

**定义**：是否有明确的输入输出，能判断成功与否。

**检查项**：
- ✅ 正向：有测试用例、有预期输出、有 Demo 证据
- ❌ 负向：无

**特殊逻辑**：
- 如果所有正向检查项都未通过（零正向证据），即使负向检查通过也判定为 ❌
- 支持文件名检测：如果文件列表中有 demo.png / demo.mp4，即使内容不可读也认定为 Demo 证据

#### 维度 4：IO 明确（Clear I/O）— 权重 0.25

**定义**：输入输出格式是否清晰定义。

**检查项**：
- ✅ 正向：有输入说明、有输出说明、有格式示例
- ❌ 负向：无

**评分**：
- pass_threshold = 2
- pass = 3 分，partial = 1 分，fail = 0 分

---

## 四、技术选型理由

### 4.1 为什么用 Python？

1. **目标用户**：C4 挑战的参与者大多使用 Python，Python 代码更容易被理解和修改
2. **标准库丰富**：`pathlib`、`json`、`re`、`argparse` 等模块足够实现所有功能
3. **跨平台**：Python 在 Windows / macOS / Linux 上行为一致

### 4.2 为什么不用第三方库？

1. **零依赖**：提交者不需要 `pip install`，降低使用门槛
2. **可移植性**：代码可以直接复制运行，不需要环境配置
3. **评审友好**：评审人可以直接阅读代码，不需要了解第三方库的 API

**权衡**：
- 不用 `openpyxl` → Excel 报告功能需要自己实现（用 CSV 替代或简化格式）
- 不用 `pytest` → 自测套件用 `assert` 语句实现
- 不用 `rich` → 终端输出用纯文本，不用彩色格式

### 4.3 为什么用 JSON 配置？

1. **可读性**：JSON 格式直观，非程序员也能理解
2. **易修改**：调整信号列表、阈值不需要改代码
3. **可验证**：配置本身可以被测试（检查结构完整性）

**替代方案**：
- YAML：更易读，但需要 `pyyaml` 依赖
- Python 常量：不需要解析，但修改需要改代码
- TOML：Python 3.11+ 才原生支持

### 4.4 为什么需要基准测试？

1. **量化验证**：没有基准测试，"评审准确"只是一个声明；有了基准测试，"评审准确"变成了一个可验证的事实
2. **防止回归**：每次修改代码后，跑一遍基准测试，确保没有引入新问题
3. **调优指导**：基准测试的精确率 / 召回率 / F1 可以指导调优方向

---

## 五、核心算法

### 5.1 作者识别

```python
# 优先级：文件名 > 文件夹名 > "Unknown"
author = extract_from_filename(filename)  # 正则匹配 "作者_C4_描述"
if not author:
    author = extract_from_folder(parent)  # 使用父文件夹名
if not author:
    author = "Unknown"
```

### 5.2 完整性检测

```python
for deliverable in required_deliverables:
    # 四级匹配
    if match_filename_and_ext(files, deliverable):
        confidence = "high"
    elif match_filename_only(files, deliverable):
        confidence = "medium"
    elif match_content_signals(files, deliverable):
        confidence = "medium"
    else:
        confidence = "none"
```

### 5.3 质量评审

```python
for criterion in quality_criteria:
    passed_count = 0
    fatal_vetoed = False
    
    for check_item in criterion.check_items:
        if check_item.type == "negative":
            if has_negative_signals(text, check_item.signals):
                fatal_vetoed = True
        else:
            if has_positive_signals(text, check_item.signals):
                passed_count += 1
    
    if fatal_vetoed:
        rating = "❌"
    elif passed_count >= criterion.pass_threshold:
        rating = "✅"
    elif passed_count >= criterion.partial_threshold:
        rating = "⚠️"
    else:
        rating = "❌"
```

### 5.4 二进制文件 Demo 检测

```python
def has_demo_file_by_name(files):
    media_exts = {".mp4", ".png", ".jpg", ".gif"}
    demo_patterns = ["demo", "演示", "截图"]
    
    for f in files:
        if f.ext in media_exts:
            for pat in demo_patterns:
                if pat in f.name.lower():
                    return True
    return False
```

---

## 六、预期效果

### 6.1 功能目标

- ✅ 自动扫描文件夹，识别作者
- ✅ 检查 5 类文件完整性
- ✅ 评审 4 个质量维度
- ✅ 生成 Markdown / Excel / JSON 报告
- ✅ 基准测试 100% 匹配率

### 6.2 性能目标

- 扫描 100 个文件 < 1 秒
- 评审 10 位作者 < 5 秒
- 生成报告 < 1 秒

### 6.3 质量目标

- 精确率 ≥ 0.95
- 召回率 ≥ 0.95
- F1 ≥ 0.95
- 保守率 ≤ 5%

**实际结果**：精确率 = 召回率 = F1 = 1.000，保守率 = 0%

---

## 七、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 信号匹配过于宽泛 | 误判率高 | 基准测试验证，迭代调优信号列表 |
| 二进制文件不可读 | Demo 检测失败 | 文件名检测作为 fallback |
| 负向检查项膨胀 | 评分虚高 | 零正向证据检测（仅对 verifiable） |
| 评审标准变化 | 代码需要大改 | 配置驱动，改 JSON 不改代码 |

---

*文档作者：三秋羲*  
*最后更新：2026-10-05*
