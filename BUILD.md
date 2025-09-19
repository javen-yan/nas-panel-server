# NAS Panel Server 构建说明

本文档说明如何使用 PyInstaller 构建 NAS Panel Server 的可执行文件。

## 前置要求

- Python 3.7 或更高版本
- pip 包管理器
- 足够的磁盘空间（至少 500MB）

## 快速开始

### 方法一：使用构建脚本（推荐）

```bash
# 使用 Python 构建脚本
python3 build.py --install-deps --package

# 或使用 Shell 构建脚本
./build.sh
```

### 方法二：手动构建

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 清理旧的构建文件
rm -rf build/ dist/ __pycache__/

# 3. 使用 PyInstaller 构建
python3 -m PyInstaller nas_panel_server.spec --clean --noconfirm

# 4. 复制配置文件
cp *.yaml dist/
```

## 构建选项

### 使用 Python 构建脚本

```bash
# 基本构建
python3 build.py

# 清理构建并创建发布包
python3 build.py --clean --package

# 使用 .spec 文件构建
python3 build.py --spec

# 构建单文件可执行文件
python3 build.py --onefile

# 只安装依赖
python3 build.py --install-deps
```

### 使用 Shell 构建脚本

```bash
# 给脚本添加执行权限
chmod +x build.sh

# 运行构建脚本
./build.sh
```

### 使用 setup.py

```bash
# 开发模式安装（会询问是否构建 PyInstaller 版本）
python3 setup.py develop

# 直接构建 PyInstaller 版本
python3 setup.py build_py
```

## 构建输出

构建完成后，您会得到以下文件：

- `dist/nas-panel-server` - 主要的可执行文件
- `release/` - 包含所有必要文件的发布包目录

## 配置文件

构建过程会自动包含以下配置文件：

- `config_example.yaml` - 示例配置文件
- `config_external_mqtt.yaml` - 外部 MQTT 配置示例
- `config.yaml` - 默认配置文件（如果存在）

## 自定义构建

### 修改 .spec 文件

如果需要自定义构建过程，可以编辑 `nas_panel_server.spec` 文件：

```python
# 添加额外的数据文件
datas = [
    ('config_example.yaml', '.'),
    ('your_custom_file.txt', '.'),
]

# 添加隐藏导入
hiddenimports = [
    'your_custom_module',
]

# 排除不需要的模块
excludes = [
    'unused_module',
]
```

### 构建参数

PyInstaller 支持多种构建参数：

```bash
# 构建单文件可执行文件
python3 -m PyInstaller --onefile main.py

# 构建目录版本（默认）
python3 -m PyInstaller main.py

# 不显示控制台窗口（仅 Windows）
python3 -m PyInstaller --noconsole main.py

# 添加图标
python3 -m PyInstaller --icon=icon.ico main.py
```

## 故障排除

### 常见问题

1. **模块未找到错误**
   - 检查 `hiddenimports` 列表是否包含所有需要的模块
   - 在 `.spec` 文件中添加缺失的模块

2. **配置文件未找到**
   - 确保配置文件在 `datas` 列表中
   - 检查文件路径是否正确

3. **构建失败**
   - 清理构建目录：`rm -rf build/ dist/`
   - 重新安装依赖：`pip3 install -r requirements.txt`
   - 检查 Python 版本兼容性

4. **可执行文件过大**
   - 在 `excludes` 列表中添加不需要的模块
   - 使用 `--exclude-module` 参数排除特定模块

### 调试模式

```bash
# 启用调试模式
python3 -m PyInstaller --debug=all main.py

# 查看详细输出
python3 -m PyInstaller --log-level=DEBUG main.py
```

## 分发

构建完成后，您可以将 `release/` 目录打包分发：

```bash
# 创建压缩包
tar -czf nas-panel-server.tar.gz release/

# 或创建 ZIP 文件
zip -r nas-panel-server.zip release/
```

## 系统服务

构建的可执行文件可以配置为系统服务：

```bash
# 复制服务文件
sudo cp nas-panel-server.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable nas-panel-server

# 启动服务
sudo systemctl start nas-panel-server
```

## 性能优化

- 使用 `--onefile` 参数创建单文件可执行文件，便于分发
- 使用 `--exclude-module` 排除不需要的模块以减小文件大小
- 考虑使用 UPX 压缩可执行文件（如果可用）

## 支持

如果遇到构建问题，请检查：

1. Python 版本是否符合要求
2. 所有依赖是否正确安装
3. 构建脚本是否有执行权限
4. 磁盘空间是否充足

更多信息请参考 [PyInstaller 官方文档](https://pyinstaller.readthedocs.io/)。
