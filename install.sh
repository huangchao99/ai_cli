#!/bin/bash
# Installation script for the AI CLI tool

set -e

# Determine if we're running as root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Configuration
INSTALL_DIR="/usr/local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
AI_SCRIPT="$BIN_DIR/ai"

echo "=== AI CLI 安装脚本 ==="
echo

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "错误: 未找到 Python 3。请安装 Python 3.6 或更高版本。"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$(echo "$PYTHON_VERSION < 3.6" | bc)" -eq 1 ]; then
    echo "错误: Python 版本过低 ($PYTHON_VERSION)。请安装 Python 3.6 或更高版本。"
    exit 1
fi

echo "Python 版本: $PYTHON_VERSION - 符合要求"

# Install dependencies
echo "正在安装依赖..."
pip3 install --user requests

# Make sure the AI script is executable
chmod +x "$AI_SCRIPT"

# Create symbolic link in INSTALL_DIR
echo "正在创建符号链接..."
if [ -f "$INSTALL_DIR/ai" ]; then
    echo "警告: $INSTALL_DIR/ai 已存在，将被覆盖。"
    $SUDO rm -f "$INSTALL_DIR/ai"
fi

$SUDO ln -sf "$AI_SCRIPT" "$INSTALL_DIR/ai"

echo "符号链接已创建: $INSTALL_DIR/ai -> $AI_SCRIPT"

# Check if API key is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo
    echo "未检测到 DEEPSEEK_API_KEY 环境变量。"
    echo "您需要设置 DeepSeek API 密钥才能使用此工具。"
    echo
    echo "您可以通过以下两种方式之一设置 API 密钥:"
    echo "1. 运行 'ai --configure' 进行交互式设置"
    echo "2. 在您的 shell 配置文件中设置环境变量:"
    echo "   export DEEPSEEK_API_KEY=\"your-api-key-here\""
    echo
fi

echo "安装完成! 现在您可以使用 'ai' 命令了。"
echo "示例: ai \"介绍下 Linux 的 open 系统调用\""
echo
echo "参考文档请查阅 README.md 文件。"
