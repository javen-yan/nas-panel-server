#!/bin/bash

# NAS Panel Server 构建脚本

set -e

echo "=========================================="
echo "NAS Panel Server 构建脚本"
echo "=========================================="

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查 PyInstaller 是否安装
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 清理旧的构建文件
echo "清理旧的构建文件..."
rm -rf build/ dist/ __pycache__/
find . -name "*.pyc" -delete

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt

# 构建可执行文件
echo "构建可执行文件..."
python3 -m PyInstaller nas_panel_server.spec --clean --noconfirm

# 复制配置文件到 dist 目录
echo "复制配置文件..."
cp -f *.yaml dist/ 2>/dev/null || true

# 创建发布包
echo "创建发布包..."
mkdir -p release
cp dist/nas-panel-server release/ 2>/dev/null || true
cp *.yaml release/ 2>/dev/null || true
cp README.md requirements.txt install.sh start.sh stop.sh nas-panel-server.service release/ 2>/dev/null || true

echo "=========================================="
echo "构建完成!"
echo "可执行文件: dist/nas-panel-server"
echo "发布包: release/"
echo "=========================================="
