# 教学说明

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
