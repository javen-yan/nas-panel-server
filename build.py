#!/usr/bin/env python3
"""
构建脚本用于使用 PyInstaller 打包 NAS Panel Server
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理 .pyc 文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def install_dependencies():
    """安装依赖"""
    print("安装依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False
    return True

def build_executable(clean=True, onefile=True):
    """构建可执行文件"""
    if clean:
        clean_build_dirs()
    
    # 构建命令
    cmd = [sys.executable, '-m', 'PyInstaller']
    
    if onefile:
        cmd.append('--onefile')
    
    cmd.extend([
        '--name', 'nas-panel-server',
        '--console',
        '--clean',
        '--noconfirm',
        'main.py'
    ])
    
    print(f"执行构建命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("构建完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def build_with_spec(clean=True):
    """使用 .spec 文件构建"""
    if clean:
        clean_build_dirs()
    
    cmd = [sys.executable, '-m', 'PyInstaller', 'nas_panel_server.spec']
    
    if clean:
        cmd.append('--clean')
    
    cmd.append('--noconfirm')
    
    print(f"执行构建命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("构建完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def copy_config_files():
    """复制配置文件到 dist 目录"""
    config_files = [
        'config_example.yaml',
        'config_external_mqtt.yaml',
        'config.yaml'
    ]
    
    dist_dir = Path('dist')
    if dist_dir.exists():
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, dist_dir)
                print(f"复制配置文件: {config_file} -> dist/")

def create_release_package():
    """创建发布包"""
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("dist 目录不存在，请先构建")
        return False
    
    # 创建发布目录
    release_dir = Path('release')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # 复制可执行文件
    exe_name = 'nas-panel-server'
    if sys.platform == 'win32':
        exe_name += '.exe'
    
    exe_path = dist_dir / exe_name
    if exe_path.exists():
        shutil.copy2(exe_path, release_dir)
        print(f"复制可执行文件: {exe_name}")
    else:
        print(f"可执行文件不存在: {exe_path}")
        return False
    
    # 复制配置文件
    copy_config_files()
    
    # 复制其他必要文件
    files_to_copy = [
        'README.md',
        'requirements.txt',
        'install.sh',
        'start.sh',
        'stop.sh',
        'nas-panel-server.service'
    ]
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy2(file_name, release_dir)
            print(f"复制文件: {file_name}")
    
    print(f"发布包已创建: {release_dir.absolute()}")
    return True

def main():
    parser = argparse.ArgumentParser(description='NAS Panel Server 构建脚本')
    parser.add_argument('--clean', action='store_true', help='清理构建目录')
    parser.add_argument('--no-clean', action='store_true', help='不清理构建目录')
    parser.add_argument('--onefile', action='store_true', help='构建单文件可执行文件')
    parser.add_argument('--spec', action='store_true', help='使用 .spec 文件构建')
    parser.add_argument('--package', action='store_true', help='创建发布包')
    parser.add_argument('--install-deps', action='store_true', help='安装依赖')
    
    args = parser.parse_args()
    
    # 确定是否清理
    clean = args.clean or not args.no_clean
    
    print("=" * 60)
    print("NAS Panel Server 构建脚本")
    print("=" * 60)
    
    # 安装依赖
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # 构建
    success = False
    if args.spec:
        success = build_with_spec(clean)
    else:
        success = build_executable(clean, args.onefile)
    
    if not success:
        print("构建失败!")
        sys.exit(1)
    
    # 创建发布包
    if args.package:
        if not create_release_package():
            print("创建发布包失败!")
            sys.exit(1)
    
    print("\n构建完成! 可执行文件位于 dist/ 目录")

if __name__ == '__main__':
    main()
