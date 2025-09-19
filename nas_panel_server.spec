# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path.cwd()

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(project_root))

# 数据文件列表 - 包含配置文件
datas = [
    ('config_example.yaml', '.'),
    ('config_external_mqtt.yaml', '.'),
    ('*.yaml', '.'),
]

# 隐藏导入 - 确保所有依赖都被包含
hiddenimports = [
    'paho.mqtt.client',
    'paho.mqtt.publish',
    'paho.mqtt.subscribe',
    'psutil',
    'yaml',
    'schedule',
    'nas_panel_server',
    'nas_panel_server.config_manager',
    'nas_panel_server.data_collector',
    'nas_panel_server.server',
    'nas_panel_server.collectors',
    'nas_panel_server.collectors.system_collector',
    'nas_panel_server.mqtt',
]

# 排除的模块 - 减少打包大小
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'jupyter',
    'notebook',
    'IPython',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='nas-panel-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
