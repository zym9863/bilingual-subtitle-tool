# HuggingFace Spaces 部署指南

## 文件说明

本项目已创建以下文件来解决HF Spaces上中文字符显示问题：

### 1. Dockerfile
- 基于Python 3.10-slim镜像
- 安装多个中文字体包（Noto CJK、文泉驿等）
- 配置字体优先级，确保中文字符正确显示
- 设置UTF-8语言环境
- 针对HF Spaces优化内存和CPU使用

### 2. .dockerignore
- 优化Docker构建，减少镜像大小
- 排除不必要的文件和目录

### 3. start.sh
- 启动脚本，包含环境检查
- 确保字体和FFmpeg正确配置

## 部署步骤

1. **创建新的HuggingFace Space**
   - 访问 https://huggingface.co/new-space
   - 选择 Docker SDK
   - 设置空间名称和描述

2. **上传文件**
   - 将所有项目文件上传到Space
   - 确保包含以上创建的Docker相关文件

3. **重命名配置文件**
   - 将 `README_SPACES.md` 重命名为 `README.md`
   - 这样HF Spaces会读取其中的配置

4. **等待构建**
   - HF Spaces会自动构建Docker镜像
   - 构建时间约5-10分钟

## 中文字符显示优化

### 字体安装
```dockerfile
# 安装多个中文字体包确保兼容性
fonts-noto-cjk \
fonts-noto-cjk-extra \
fonts-wqy-zenhei \
fonts-wqy-microhei \
fonts-arphic-ukai \
fonts-arphic-uming \
```

### 字体配置
```xml
<!-- 设置中文字体优先级 -->
<alias>
  <family>sans-serif</family>
  <prefer>
    <family>Noto Sans CJK SC</family>
    <family>WenQuanYi Zen Hei</family>
  </prefer>
</alias>
```

### 环境变量
```bash
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV FONTCONFIG_PATH=/etc/fonts
ENV FC_LANG=zh-cn
```

## 性能优化

### 内存优化
- 设置较小的Whisper模型（base）
- 限制最大文件大小为200MB
- 强制使用CPU避免GPU内存不足

### 启动优化
- 使用start.sh脚本预检查环境
- 健康检查确保服务正常

## 故障排除

### 中文字符仍显示为方块
1. 检查字体是否正确安装：`fc-list | grep -i cjk`
2. 检查字体配置：`fc-match sans-serif`
3. 检查环境变量设置

### 构建失败
1. 检查Dockerfile语法
2. 检查requirements.txt依赖
3. 查看HF Spaces构建日志

### 运行时错误
1. 检查启动脚本权限
2. 检查FFmpeg安装
3. 查看应用日志

## 测试建议

1. 上传包含中文文件名的测试视频
2. 生成双语字幕并检查中文显示
3. 测试字幕烧录功能
4. 验证下载的字幕文件编码正确