# 智能文件分类器 v2

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
