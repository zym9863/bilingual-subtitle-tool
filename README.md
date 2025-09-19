---
title: 双语字幕工具 - Bilingual Subtitle Tool
emoji: 🎬
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🎬 双语字幕工具 (Bilingual Subtitle Tool)

🇨🇳 中文 | [🇺🇸 English](README_EN.md)

一个轻量级的工具，为带中文或英文音频的视频添加中英双语字幕。支持本地GPU和Hugging Face Spaces CPU环境。

## ✨ 功能特点

- 🎵 **自动音频提取**: 使用MoviePy从视频中提取音频
- 🎤 **AI语音识别**: 集成faster-whisper，支持中文和英文语音识别，可GPU加速
- 🌐 **智能翻译**: 使用百度翻译API进行双向翻译（中译英、英译中）
- 📝 **字幕生成**: 生成SRT格式的双语字幕文件
- 🔥 **字幕烧录**: 可选将字幕永久嵌入视频
- 🖥️ **友好界面**: 基于Gradio的Web界面
- ⚡ **环境适配**: 自动检测并适配不同运行环境

## 🛠️ 技术栈

- **Web界面**: Gradio
- **包管理**: uv (推荐) 或 pip
- **音视频处理**: MoviePy, ffmpeg
- **语音识别**: faster-whisper
- **文本翻译**: 百度翻译API
- **字幕处理**: pysrt
- **视频处理**: ffmpeg-python

## 📋 系统要求

- Python 3.8+
- ffmpeg
- 百度翻译API密钥 (APPID和APPKEY)
- 可选: NVIDIA GPU (用于加速语音识别)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/zym9863/bilingual-subtitle-tool.git
cd bilingual-subtitle-tool
```

### 2. 自动安装

```bash
python install.py
```

或手动安装:

```bash
# 使用uv (推荐)
uv pip install -r requirements.txt

# 或使用pip
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑 `.env` 文件，填入您的百度翻译API密钥:

```env
BAIDU_APPID=your_baidu_appid_here
BAIDU_APPKEY=your_baidu_appkey_here
```

### 4. 运行应用

```bash
python main.py
```

然后在浏览器中打开显示的地址 (通常是 http://localhost:7860)

## 🔧 配置选项

### 环境变量配置

在 `.env` 文件中可以配置以下选项:

```env
# 百度翻译API配置
BAIDU_APPID=your_baidu_appid_here
BAIDU_APPKEY=your_baidu_appkey_here

# Whisper模型配置
WHISPER_MODEL_SIZE=small  # tiny, base, small, medium, large
WHISPER_DEVICE=auto      # auto, cpu, cuda

# 语言配置
DEFAULT_AUDIO_LANGUAGE=en  # 默认音频语言：en(英文), zh(中文)

# 字幕样式配置
SUBTITLE_FONT_SIZE=24
SUBTITLE_FONT_COLOR=white
SUBTITLE_OUTLINE_COLOR=black
SUBTITLE_OUTLINE_WIDTH=2

# 文件配置
TEMP_DIR=temp
MAX_FILE_SIZE=500        # MB
```

### Whisper模型大小说明

| 模型大小 | 参数量 | 内存需求 | 速度 | 准确度 |
|---------|--------|----------|------|--------|
| tiny    | 39M    | ~1GB     | 最快 | 较低   |
| base    | 74M    | ~1GB     | 快   | 中等   |
| small   | 244M   | ~2GB     | 中等 | 良好   |
| medium  | 769M   | ~5GB     | 慢   | 很好   |
| large   | 1550M  | ~10GB    | 最慢 | 最佳   |

## 📱 使用方法

1. **上传视频**: 支持 MP4, AVI, MOV, MKV, WMV, FLV, WebM 格式
2. **配置选项**:
   - **选择音频语言**: 中文或英文（影响语音识别和翻译方向）
   - 选择Whisper模型大小
   - 输入百度翻译API密钥
   - 选择字幕类型 (双语/仅原文/仅译文)
   - 选择是否烧录字幕到视频
   - 调整字体大小和颜色
3. **开始处理**: 点击"开始处理"按钮
4. **下载结果**: 处理完成后下载生成的字幕文件和视频文件

### 🎯 处理流程说明

**中文音频视频**：
1. 提取音频 → 2. 中文语音识别 → 3. 中译英翻译 → 4. 生成中英双语字幕

**英文音频视频**：
1. 提取音频 → 2. 英文语音识别 → 3. 英译中翻译 → 4. 生成英中双语字幕

## 🌐 部署到Hugging Face Spaces

1. Fork这个项目到您的GitHub账户
2. 在Hugging Face Spaces创建新的Space
3. 连接您的GitHub仓库
4. 在Space设置中添加环境变量:
   - `BAIDU_APPID`: 您的百度翻译APPID
   - `BAIDU_APPKEY`: 您的百度翻译APPKEY
5. Space会自动部署并运行

## 🧪 测试

运行测试套件:

```bash
# 运行所有测试
python run_tests.py

# 运行特定测试模块
python run_tests.py test_config
python run_tests.py test_utils
python run_tests.py test_translator
```

## 📁 项目结构

```
bilingual-subtitle-tool/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── utils.py           # 工具函数
│   ├── environment.py     # 环境检测
│   ├── audio_extractor.py # 音频提取
│   ├── speech_recognizer.py # 语音识别
│   ├── translator.py      # 翻译服务
│   ├── subtitle_generator.py # 字幕生成
│   └── video_processor.py # 视频处理
├── tests/                 # 测试文件
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_utils.py
│   └── test_translator.py
├── main.py               # 主应用文件
├── install.py            # 安装脚本
├── run_tests.py          # 测试运行脚本
├── requirements.txt      # Python依赖
├── pyproject.toml        # 项目配置
├── .env.example          # 环境变量示例
└── README.md             # 项目文档
```

## 🔑 获取百度翻译API密钥

1. 访问 [百度翻译开放平台](https://fanyi-api.baidu.com/)
2. 注册并登录账户
3. 创建应用，获取APPID和密钥
4. 将密钥填入 `.env` 文件

## ⚠️ 注意事项

- **首次运行**: 会自动下载Whisper模型，请耐心等待
- **GPU加速**: 如果有NVIDIA GPU，建议安装CUDA版本的PyTorch
- **文件大小**: 默认限制500MB，可在配置中调整
- **API限制**: 百度翻译API有调用频率限制，请合理使用
- **网络连接**: 需要稳定的网络连接用于下载模型和调用翻译API

## 🐛 常见问题

### Q: 提示"ffmpeg未安装"怎么办？
A: 请安装ffmpeg:
- Windows: 下载并添加到PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### Q: GPU不可用怎么办？
A: 程序会自动切换到CPU模式，但处理速度会较慢。要启用GPU:
1. 确保安装了NVIDIA GPU驱动
2. 安装CUDA版本的PyTorch
3. 重启应用

### Q: 翻译失败怎么办？
A: 检查:
1. 百度翻译API密钥是否正确
2. 网络连接是否正常
3. API调用是否超出限制

### Q: 处理大文件时内存不足？
A: 尝试:
1. 使用更小的Whisper模型
2. 减少最大文件大小限制
3. 关闭其他占用内存的程序

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别模型
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - 优化的Whisper实现
- [Gradio](https://gradio.app/) - Web界面框架
- [MoviePy](https://zulko.github.io/moviepy/) - 视频处理库
- [百度翻译API](https://fanyi-api.baidu.com/) - 翻译服务

## 📞 联系方式

如有问题或建议，请通过以下方式联系:

- 提交 [GitHub Issue](https://github.com/zym9863/bilingual-subtitle-tool/issues)
- 发送邮件到: ym214413520@gmail.com

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**
