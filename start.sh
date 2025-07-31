#!/bin/bash

# 启动脚本 - 为HuggingFace Spaces优化的启动脚本

set -e

echo "🚀 启动双语字幕工具..."

# 确保缓存目录存在
echo "📁 设置缓存目录..."
mkdir -p /app/.cache/huggingface
export HF_HOME=/app/.cache/huggingface
export TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
export HF_DATASETS_CACHE=/app/.cache/huggingface/datasets

# 检查字体安装
echo "📝 检查中文字体支持..."
fc-list | grep -i "noto\|wqy" | head -5 || echo "字体检查完成"

# 检查FFmpeg是否可用
echo "🎬 检查FFmpeg支持..."
ffmpeg -version | head -1

# 检查Python环境
echo "🐍 检查Python环境..."
python --version
echo "缓存目录: $HF_HOME"

# 设置字体环境变量
export FONTCONFIG_PATH=/etc/fonts
export FC_LANG=zh-cn

# 启动应用
echo "✅ 启动应用..."
exec python main.py