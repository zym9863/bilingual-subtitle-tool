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

# 🎬 Bilingual Subtitle Tool

[🇨🇳 中文](README.md) | 🇺🇸 English

A lightweight tool for adding bilingual subtitles to videos with English audio. Supports both local GPU and Hugging Face Spaces CPU environments.

## ✨ Features

- 🎵 **Auto Audio Extraction**: Extract audio from videos using MoviePy
- 🎤 **AI Speech Recognition**: Integrated faster-whisper with GPU acceleration support
- 🌐 **Smart Translation**: English-Chinese translation using Baidu Translate API
- 📝 **Subtitle Generation**: Generate bilingual subtitles in SRT format
- 🔥 **Subtitle Burning**: Optional permanent subtitle embedding into video
- 🖥️ **User-Friendly Interface**: Gradio-based web interface
- ⚡ **Environment Adaptation**: Auto-detect and adapt to different runtime environments

## 🛠️ Tech Stack

- **Web Interface**: Gradio
- **Package Manager**: uv (recommended) or pip
- **Audio/Video Processing**: MoviePy, ffmpeg
- **Speech Recognition**: faster-whisper
- **Text Translation**: Baidu Translate API
- **Subtitle Processing**: pysrt
- **Video Processing**: ffmpeg-python

## 📋 System Requirements

- Python 3.8+
- ffmpeg
- Baidu Translate API keys (APPID and APPKEY)
- Optional: NVIDIA GPU (for accelerated speech recognition)

## 🚀 Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/zym9863/bilingual-subtitle-tool.git
cd bilingual-subtitle-tool
```

### 2. Auto Installation

```bash
python install.py
```

Or manual installation:

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 3. Configure API Keys

Edit the `.env` file and fill in your Baidu Translate API keys:

```env
BAIDU_APPID=your_baidu_appid_here
BAIDU_APPKEY=your_baidu_appkey_here
```

### 4. Run the Application

```bash
python main.py
```

Then open the displayed address in your browser (usually http://localhost:7860)

## 🔧 Configuration Options

### Environment Variables

Configure the following options in the `.env` file:

```env
# Baidu Translate API Configuration
BAIDU_APPID=your_baidu_appid_here
BAIDU_APPKEY=your_baidu_appkey_here

# Whisper Model Configuration
WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large
WHISPER_DEVICE=auto      # auto, cpu, cuda

# Subtitle Style Configuration
SUBTITLE_FONT_SIZE=24
SUBTITLE_FONT_COLOR=white
SUBTITLE_OUTLINE_COLOR=black
SUBTITLE_OUTLINE_WIDTH=2

# File Configuration
TEMP_DIR=temp
MAX_FILE_SIZE=500        # MB
```

### Whisper Model Size Guide

| Model Size | Parameters | Memory | Speed | Accuracy |
|------------|------------|---------|-------|----------|
| tiny       | 39M        | ~1GB    | Fastest | Lower |
| base       | 74M        | ~1GB    | Fast | Medium |
| small      | 244M       | ~2GB    | Medium | Good |
| medium     | 769M       | ~5GB    | Slow | Very Good |
| large      | 1550M      | ~10GB   | Slowest | Best |

## 📱 Usage

1. **Upload Video**: Supports MP4, AVI, MOV, MKV, WMV, FLV, WebM formats
2. **Configure Options**:
   - Select Whisper model size
   - Enter Baidu Translate API keys
   - Choose subtitle type (Bilingual/English only/Chinese only)
   - Choose whether to burn subtitles into video
   - Adjust font size and color
3. **Start Processing**: Click the "Start Processing" button
4. **Download Results**: Download generated subtitle files and video files after processing

## 🌐 Deploy to Hugging Face Spaces

1. Fork this project to your GitHub account
2. Create a new Space on Hugging Face Spaces
3. Connect your GitHub repository
4. Add environment variables in Space settings:
   - `BAIDU_APPID`: Your Baidu Translate APPID
   - `BAIDU_APPKEY`: Your Baidu Translate APPKEY
5. The Space will automatically deploy and run

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python run_tests.py test_config
python run_tests.py test_utils
python run_tests.py test_translator
```

## 📁 Project Structure

```
bilingual-subtitle-tool/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── utils.py           # Utility functions
│   ├── environment.py     # Environment detection
│   ├── audio_extractor.py # Audio extraction
│   ├── speech_recognizer.py # Speech recognition
│   ├── translator.py      # Translation service
│   ├── subtitle_generator.py # Subtitle generation
│   └── video_processor.py # Video processing
├── tests/                 # Test files
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_utils.py
│   └── test_translator.py
├── main.py               # Main application file
├── install.py            # Installation script
├── run_tests.py          # Test runner script
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
├── .env.example          # Environment variables example
└── README.md             # Project documentation
```

## 🔑 Getting Baidu Translate API Keys

1. Visit [Baidu Translate Open Platform](https://fanyi-api.baidu.com/)
2. Register and login to your account
3. Create an application to get APPID and secret key
4. Fill the keys into the `.env` file

## ⚠️ Important Notes

- **First Run**: Will automatically download Whisper models, please be patient
- **GPU Acceleration**: If you have an NVIDIA GPU, it's recommended to install CUDA version of PyTorch
- **File Size**: Default limit is 500MB, adjustable in configuration
- **API Limits**: Baidu Translate API has call frequency limits, please use reasonably
- **Network Connection**: Requires stable network connection for model download and translation API calls

## 🐛 Common Issues

### Q: "ffmpeg not installed" error?
A: Please install ffmpeg:
- Windows: Download and add to PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### Q: GPU not available?
A: The program will automatically switch to CPU mode, but processing will be slower. To enable GPU:
1. Ensure NVIDIA GPU drivers are installed
2. Install CUDA version of PyTorch
3. Restart the application

### Q: Translation failed?
A: Check:
1. Baidu Translate API keys are correct
2. Network connection is normal
3. API calls haven't exceeded limits

### Q: Out of memory when processing large files?
A: Try:
1. Use smaller Whisper models
2. Reduce maximum file size limit
3. Close other memory-intensive programs

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [Gradio](https://gradio.app/) - Web interface framework
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing library
- [Baidu Translate API](https://fanyi-api.baidu.com/) - Translation service

## 📞 Contact

If you have questions or suggestions, please contact via:

- Submit [GitHub Issue](https://github.com/zym9863/bilingual-subtitle-tool/issues)
- Send email to: ym214413520@gmail.com

---

**⭐ If this project helps you, please give it a Star!**