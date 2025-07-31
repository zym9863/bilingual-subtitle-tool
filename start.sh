#!/bin/bash

# 启动脚本 - 为HuggingFace Spaces优化的启动脚本

set -e

echo "🚀 启动双语字幕工具..."

# 检查字体安装
echo "📝 检查中文字体支持..."
fc-list | grep -i "noto\|wqy" | head -5

# 检查FFmpeg是否可用
echo "🎬 检查FFmpeg支持..."
ffmpeg -version | head -1

# 检查Python环境
echo "🐍 检查Python环境..."
python --version
pip list | grep -E "(torch|gradio|ffmpeg|whisper)" || echo "正在安装依赖..."

# 设置字体环境变量
export FONTCONFIG_PATH=/etc/fonts
export FC_LANG=zh-cn

# 启动应用
echo "✅ 启动应用..."
exec python main.py