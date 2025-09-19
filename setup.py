"""
Setup script for NAS Panel Server.
"""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# 自定义构建命令，支持 PyInstaller
class BuildPyInstaller(build_py):
    """自定义构建命令，支持 PyInstaller 打包"""
    
    def run(self):
        """运行 PyInstaller 构建"""
        try:
            import PyInstaller
            print("使用 PyInstaller 构建...")
            
            # 运行 PyInstaller
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'PyInstaller', 
                'nas_panel_server.spec',
                '--clean',
                '--noconfirm'
            ], check=True)
            
            print("PyInstaller 构建完成!")
            
        except ImportError:
            print("PyInstaller 未安装，跳过构建")
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller 构建失败: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"构建过程中出现错误: {e}")
            sys.exit(1)

# 自定义开发命令
class DevelopPyInstaller(develop):
    """自定义开发命令，支持 PyInstaller 构建"""
    
    def run(self):
        """运行开发安装和 PyInstaller 构建"""
        super().run()
        
        # 询问是否要构建 PyInstaller 版本
        if input("是否要构建 PyInstaller 可执行文件? (y/N): ").lower() == 'y':
            BuildPyInstaller().run()

setup(
    name="nas-panel-server",
    version="1.0.0",
    author="NAS Panel Server",
    description="A system monitoring service with built-in MQTT broker for NAS panel displays",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "nas-panel-server=nas_panel_server.server:main",
        ],
    },
    include_package_data=True,
    cmdclass={
        'build_py': BuildPyInstaller,
        'develop': DevelopPyInstaller,
    },
    # 添加构建相关的数据文件
    data_files=[
        ('', ['nas_panel_server.spec']),
        ('', ['build.py', 'build.sh']),
        ('', ['*.yaml']),
    ],
)