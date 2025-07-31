#!/bin/bash

# 快速测试脚本 - 验证HF Spaces部署修复

echo "🧪 开始测试环境配置..."

# 测试1: 检查环境变量
echo "1️⃣ 检查HuggingFace缓存环境变量..."
echo "HF_HOME: ${HF_HOME:-未设置}"
echo "TRANSFORMERS_CACHE: ${TRANSFORMERS_CACHE:-未设置}"

# 测试2: 检查缓存目录权限
echo "2️⃣ 检查缓存目录..."
if [ -d "/app/.cache/huggingface" ]; then
    echo "✅ 缓存目录存在: /app/.cache/huggingface"
    ls -la /app/.cache/
else
    echo "❌ 缓存目录不存在"
    mkdir -p /app/.cache/huggingface
    echo "✅ 已创建缓存目录"
fi

# 测试3: 检查写入权限
echo "3️⃣ 测试写入权限..."
test_file="/app/.cache/huggingface/test_write.txt"
if echo "test" > "$test_file" 2>/dev/null; then
    echo "✅ 缓存目录可写入"
    rm -f "$test_file"
else
    echo "❌ 缓存目录无法写入"
fi

# 测试4: 检查中文字体
echo "4️⃣ 检查中文字体..."
if fc-list | grep -i "noto\|wqy" >/dev/null 2>&1; then
    echo "✅ 中文字体已安装"
    fc-list | grep -i "noto\|wqy" | head -3
else
    echo "❌ 未找到中文字体"
fi

# 测试5: 检查FFmpeg
echo "5️⃣ 检查FFmpeg..."
if command -v ffmpeg >/dev/null 2>&1; then
    echo "✅ FFmpeg已安装"
    ffmpeg -version | head -1
else
    echo "❌ FFmpeg未安装"
fi

echo "🎉 环境检查完成！"