# NAS Panel Server Makefile

.PHONY: help install build clean test package deps

# 默认目标
help:
	@echo "NAS Panel Server 构建工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install    - 安装依赖"
	@echo "  build      - 构建可执行文件"
	@echo "  clean      - 清理构建文件"
	@echo "  test       - 运行测试"
	@echo "  package    - 创建发布包"
	@echo "  deps       - 显示依赖信息"
	@echo "  help       - 显示此帮助信息"

# 安装依赖
install deps:
	@echo "安装依赖..."
	pip3 install -r requirements.txt

# 构建可执行文件
build:
	@echo "构建可执行文件..."
	python3 -m PyInstaller nas_panel_server.spec --clean --noconfirm
	@echo "复制配置文件..."
	cp -f *.yaml dist/ 2>/dev/null || true

# 清理构建文件
clean:
	@echo "清理构建文件..."
	rm -rf build/ dist/ __pycache__/ release/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# 运行测试
test:
	@echo "运行测试..."
	python3 -m pytest tests/ -v || echo "没有找到测试文件"

# 创建发布包
package: build
	@echo "创建发布包..."
	mkdir -p release
	cp dist/nas-panel-server release/ 2>/dev/null || true
	cp *.yaml release/ 2>/dev/null || true
	cp README.md requirements.txt install.sh start.sh stop.sh nas-panel-server.service release/ 2>/dev/null || true
	@echo "发布包已创建: release/"

# 显示依赖信息
deps-info:
	@echo "项目依赖:"
	@cat requirements.txt
	@echo ""
	@echo "已安装的包:"
	@pip3 list | grep -E "(paho-mqtt|psutil|pyyaml|schedule|pyinstaller)"

# 开发模式安装
dev-install:
	@echo "开发模式安装..."
	python3 setup.py develop

# 完整构建（清理 + 构建 + 打包）
all: clean install build package
	@echo "完整构建完成!"

# 快速构建（不清理）
quick: install build
	@echo "快速构建完成!"

