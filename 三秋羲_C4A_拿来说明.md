# C4A 拿来说明 — 从 wechat-doc-mapper 借鉴了什么

**作者**：三秋羲  
**日期**：2026-10-05

---

## 一、wechat-doc-mapper 是什么

wechat-doc-mapper 是一个将微信公众号文章转换为结构化 Markdown 的技能。它的核心能力是：

1. **文件扫描与识别**：扫描指定文件夹，识别微信文章文件（HTML / MHTML 格式）
2. **内容提取**：从 HTML 中提取标题、正文、图片、元数据
3. **结构化输出**：将提取的内容转换为带 frontmatter 的 Markdown 文件
4. **批量处理**：支持一次处理多篇文章，按日期 / 标题分组

这个技能的代码组织方式和设计思路，对本项目有直接参考价值。

---

## 二、拿了什么

### 2.1 模块划分思路

**wechat-doc-mapper 的做法**：
```
scanner.py      → 扫描文件夹，识别文件类型
extractor.py    → 提取内容（标题、正文、图片）
transformer.py  → 转换格式（HTML → Markdown）
writer.py       → 输出文件
main.py         → CLI 入口
```

**我们的借鉴**：
```
scanner.py      → 扫描文件夹，识别作者（直接沿用了模块名和职责）
completeness.py → 检查完整性（对应 extractor 的"提取"角色，但功能不同）
evaluator.py    → 评审质量（对应 transformer 的"转换"角色，但功能不同）
reporter.py     → 生成报告（对应 writer.py）
main.py         → CLI 入口（直接沿用）
```

**具体借鉴点**：
- 模块命名风格一致（scanner.py / writer.py → reporter.py）
- 流水线架构一致（扫描 → 处理 → 输出）
- CLI 参数设计风格一致（`<folder>` 位置参数 + `--output` 选项参数）

**没有直接复制的部分**：
- 我们没有 extractor / transformer，因为我们的任务不是内容提取，而是质量评审
- 我们的 completeness.py 和 evaluator.py 是全新设计的，逻辑完全不同

### 2.2 文件分组策略

**wechat-doc-mapper 的做法**：
```python
# 从文件名中提取日期，按日期分组
date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
for f in files:
    m = date_pattern.search(f.name)
    if m:
        date = m.group(1)
        groups[date].append(f)
```

**我们的借鉴**：
```python
# 从文件名中提取作者名，按作者分组
author_pattern = re.compile(r'^(?P<author>.+?)_C4(?:A)?[_\-]')
for f in files:
    m = author_pattern.match(f.name)
    if m:
        author = m.group("author")
        groups[author].append(f)
```

**借鉴点**：
- 正则匹配文件名提取元数据的思路
- 按元数据分组的策略
- 分组失败时的 fallback 逻辑（wechat-doc-mapper 用"未分类"，我们用"Unknown"）

**改进点**：
- wechat-doc-mapper 只从文件名提取，我们增加了从文件夹名提取的 fallback
- 我们增加了作者黑名单（过滤 "unknown"、"test" 等无效名称）

### 2.3 四级置信度匹配

**wechat-doc-mapper 的做法**：
```python
# 识别文件类型时的四级匹配
if f.ext in [".html", ".htm"]:
    if has_wechat_meta(f):
        confidence = "high"
    elif has_wechat_content(f):
        confidence = "medium"
    else:
        confidence = "low"
```

**我们的借鉴**：
```python
# 识别交付物时的四级匹配
if match_filename_and_ext(files, deliverable):
    confidence = "high"
elif match_filename_only(files, deliverable):
    confidence = "medium"
elif match_content_signals(files, deliverable):
    confidence = "medium"
else:
    confidence = "none"
```

**借鉴点**：
- 多级置信度的概念（不是简单的"是 / 否"，而是"高 / 中 / 低"）
- 文件名 + 扩展名 → 仅文件名 → 内容信号的优先级顺序

**改进点**：
- wechat-doc-mapper 只有 3 级，我们扩展到 4 级（增加了"内容信号匹配"）
- 我们的置信度直接体现在评审报告中，让评审结果可解释

### 2.4 负向信号检测

**wechat-doc-mapper 的做法**：
```python
# 检测非微信文章的特征（排除误识别）
negative_signals = ["<script>", "iframe", "advertisement"]
if any(sig in text for sig in negative_signals):
    return False  # 不是微信文章
```

**我们的借鉴**：
```python
# 检测低质量代码的特征（负向评审）
negative_signals = ["C:\\Users\\", "/home/", "TODO", "FIXME"]
if any(sig in text for sig in negative_signals):
    fatal_vetoed = True  # 直接否决
```

**借鉴点**：
- 负向信号的概念——不仅检查"有没有好东西"，还要检查"有没有坏东西"
- 负向信号触发时的 veto 机制

**改进点**：
- wechat-doc-mapper 的负向信号只是排除误识别，我们的负向信号直接影响评分
- 我们的负向信号配置化（在 rubric.json 中定义），可以灵活调整

---

## 三、改了什么

### 3.1 核心逻辑完全不同

| 方面 | wechat-doc-mapper | 我们的实现 |
|------|-------------------|-----------|
| **任务** | 内容提取与转换 | 质量评审 |
| **输入** | HTML / MHTML 文件 | 任意格式的 C4 提交 |
| **输出** | 结构化 Markdown | 评审报告（Markdown / Excel / JSON） |
| **核心算法** | HTML 解析、内容提取 | 信号匹配、阈值判断 |
| **质量保障** | 单元测试 | 基准测试（黄金集 + 精确率 / 召回率） |

### 3.2 评审维度是原创设计

wechat-doc-mapper 没有"评审"概念，我们的 4 维度评审体系（可复用、可执行、可验证、IO 明确）是完全原创的：

- 维度定义来自 C4 评审标准
- 信号列表来自对真实提交的分析
- 阈值设定来自基准测试的调优

### 3.3 配置驱动是原创设计

wechat-doc-mapper 的评审标准硬编码在代码中，我们将其外置到 `rubric.json`：

- 新增评审维度只需加配置块
- 调整信号列表不需要改代码
- 配置本身可以被测试

### 3.4 基准测试是原创设计

wechat-doc-mapper 没有基准测试模块，我们的 `benchmark.py` 是全新设计的：

- 12 组黄金集覆盖各种边界情况
- 精确率 / 召回率 / F1 量化评审准确性
- 混淆矩阵展示评审结果的分布

---

## 四、为什么拿

### 4.1 降低设计成本

wechat-doc-mapper 已经验证了"扫描 → 处理 → 输出"的流水线架构适用于文件处理类技能。我们直接借鉴这个架构，不需要从零设计。

### 4.2 提高代码可读性

评审人可能看过 wechat-doc-mapper 的代码。我们的模块命名、代码组织与之保持一致，评审人可以快速理解我们的代码结构。

### 4.3 站在巨人肩膀上

wechat-doc-mapper 的文件分组策略、置信度匹配、负向信号检测都是经过验证的设计。我们借鉴这些设计，可以避免重复踩坑。

---

## 五、拿的边界

### 5.1 没有复制代码

我们的代码是全新编写的，没有复制 wechat-doc-mapper 的任何代码片段。借鉴的是设计思路和架构模式，不是具体实现。

### 5.2 没有复制配置

我们的 `rubric.json` 是完全原创的，评审维度、信号列表、阈值都是根据 C4 评审需求设计的。

### 5.3 没有复制测试

我们的黄金集和基准测试是完全原创的，测试用例覆盖了 C4 评审的各种边界情况。

---

## 六、总结

| 类别 | 借鉴内容 | 原创内容 |
|------|----------|----------|
| **架构** | 流水线架构、模块命名 | 评审逻辑、配置驱动 |
| **算法** | 文件分组策略、置信度匹配 | 4 维度评审、负向信号 veto |
| **代码** | 无 | 100% 原创 |
| **测试** | 无 | 12 组黄金集、99 项自测 |

借鉴比例约 30%（架构和思路），70% 是原创设计（评审逻辑、配置系统、基准测试）。

---

*文档作者：三秋羲*  
*最后更新：2026-10-05*
