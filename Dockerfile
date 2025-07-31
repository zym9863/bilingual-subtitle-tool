# 使用官方Python 3.10镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860
# 设置语言环境支持中文
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
# FFmpeg字体配置
ENV FONTCONFIG_PATH=/etc/fonts
ENV FC_LANG=zh-cn
# HuggingFace Spaces优化
ENV WHISPER_MODEL_SIZE=base
ENV WHISPER_DEVICE=cpu
ENV MAX_FILE_SIZE=200
# 设置HuggingFace缓存目录到应用目录
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets

# 更新包管理器并安装系统依赖
RUN apt-get update && apt-get install -y \
    # FFmpeg支持
    ffmpeg \
    # 字体相关工具
    fontconfig \
    # 中文字体支持 - 安装多个字体以确保兼容性
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    # 其他必要工具
    wget \
    curl \
    git \
    locales \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 生成中文语言环境
RUN echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen

# 设置字体配置，确保中文字体被正确识别和优先使用
RUN fc-cache -fv && \
    # 创建字体配置文件，优先使用中文字体
    mkdir -p /root/.config/fontconfig && \
    echo '<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n  <alias>\n    <family>sans-serif</family>\n    <prefer>\n      <family>Noto Sans CJK SC</family>\n      <family>WenQuanYi Zen Hei</family>\n      <family>WenQuanYi Micro Hei</family>\n    </prefer>\n  </alias>\n  <alias>\n    <family>serif</family>\n    <prefer>\n      <family>Noto Serif CJK SC</family>\n      <family>AR PL UMing CN</family>\n    </prefer>\n  </alias>\n  <alias>\n    <family>monospace</family>\n    <prefer>\n      <family>Noto Sans Mono CJK SC</family>\n      <family>WenQuanYi Zen Hei Mono</family>\n    </prefer>\n  </alias>\n</fontconfig>' > /root/.config/fontconfig/fonts.conf

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建应用用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到应用用户
USER appuser

# 复制并设置启动脚本权限
RUN chmod +x start.sh main.py test_environment.sh

# 创建缓存和临时目录，设置权限
RUN mkdir -p /app/.cache/huggingface temp

# 暴露端口
EXPOSE 7860

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# 启动应用
CMD ["./start.sh"]