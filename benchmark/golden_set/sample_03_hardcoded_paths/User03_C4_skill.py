import shutil
from pathlib import Path

# 默认备份到我的电脑上的备份文件夹
SOURCE = "D:\\Users\\User03\\Documents"
DEST = "C:\\Users\\User03\\Backup"

def backup():
    shutil.copytree(SOURCE, DEST)
    print(f"已备份到 {DEST}")
