---
title: Bilingual Subtitle Tool
emoji: 🎬
colorFrom: yellow
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: main.py
pinned: false
license: mit
---

# 🎬 双语字幕工具 (Bilingual Subtitle Tool)

一个轻量级的工具，为带英文音频的视频添加中英双语字幕。

## ✨ 功能特点

- 🎵 **自动音频提取**: 使用MoviePy从视频中提取音频
- 🎤 **AI语音识别**: 集成faster-whisper，支持GPU加速
- 🌐 **智能翻译**: 使用百度翻译API进行英中翻译
- 📝 **字幕生成**: 生成SRT格式的双语字幕文件
- 🔥 **字幕烧录**: 可选将字幕永久嵌入视频
- 🖥️ **友好界面**: 基于Gradio的Web界面

## 🚀 使用方法

1. **配置API密钥**: 在界面中输入您的百度翻译API密钥
2. **上传视频**: 支持 MP4, AVI, MOV, MKV 等格式
3. **选择选项**: 
   - Whisper模型大小 (推荐使用base模型)
   - 字幕类型 (双语/仅英文/仅中文)
   - 是否烧录字幕到视频
4. **开始处理**: 点击"开始处理"按钮
5. **下载结果**: 处理完成后下载生成的文件

## 🔑 获取百度翻译API密钥

1. 访问 [百度翻译开放平台](https://fanyi-api.baidu.com/)
2. 注册并登录账户
3. 创建应用，获取APPID和密钥
4. 在界面中输入密钥信息

## ⚠️ 注意事项

- 首次运行会下载Whisper模型，请耐心等待
- 文件大小限制为100MB (Spaces环境限制)
- 使用CPU进行处理，速度相对较慢
- 需要稳定的网络连接

## 🛠️ 技术栈

- **Web界面**: Gradio
- **音视频处理**: MoviePy, ffmpeg
- **语音识别**: faster-whisper
- **文本翻译**: 百度翻译API
- **字幕处理**: pysrt

## 📞 支持

如有问题，请访问 [GitHub仓库](https://github.com/zym9863/bilingual-subtitle-tool) 提交Issue。
