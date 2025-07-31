"""
配置管理模块
管理应用程序的配置参数，支持环境变量和配置文件
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入环境检测器
try:
    from .environment import EnvironmentDetector
except ImportError:
    # 如果导入失败，创建一个简单的替代类
    class EnvironmentDetector:
        @staticmethod
        def is_huggingface_spaces():
            return os.getenv("SPACE_ID") is not None

        @staticmethod
        def has_gpu():
            try:
                import torch
                return torch.cuda.is_available()
            except ImportError:
                return False


class Config:
    """应用程序配置类"""
    
    # 百度翻译API配置
    BAIDU_APPID: Optional[str] = os.getenv("BAIDU_APPID")
    BAIDU_APPKEY: Optional[str] = os.getenv("BAIDU_APPKEY")
    
    # Whisper模型配置
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")  # auto, cpu, cuda
    
    # 字幕配置
    SUBTITLE_FONT_SIZE: int = int(os.getenv("SUBTITLE_FONT_SIZE", "24"))
    SUBTITLE_FONT_COLOR: str = os.getenv("SUBTITLE_FONT_COLOR", "white")
    SUBTITLE_OUTLINE_COLOR: str = os.getenv("SUBTITLE_OUTLINE_COLOR", "black")
    SUBTITLE_OUTLINE_WIDTH: int = int(os.getenv("SUBTITLE_OUTLINE_WIDTH", "2"))
    
    # 临时文件目录
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    
    # 最大文件大小 (MB)
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "500"))
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
    
    @classmethod
    def is_gpu_available(cls) -> bool:
        """检查GPU是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @classmethod
    def get_device(cls) -> str:
        """获取推荐的设备类型"""
        if cls.WHISPER_DEVICE == "auto":
            # 在Hugging Face Spaces中强制使用CPU
            if EnvironmentDetector.is_huggingface_spaces():
                return "cpu"
            return "cuda" if cls.is_gpu_available() else "cpu"
        return cls.WHISPER_DEVICE

    @classmethod
    def get_optimized_model_size(cls) -> str:
        """根据环境获取优化的模型大小"""
        if EnvironmentDetector.is_huggingface_spaces():
            # Hugging Face Spaces使用较小的模型
            return "base"
        elif cls.is_gpu_available():
            # 有GPU时使用更大的模型
            return "large" if cls.WHISPER_MODEL_SIZE == "auto" else cls.WHISPER_MODEL_SIZE
        else:
            # CPU环境使用中等模型
            return "medium" if cls.WHISPER_MODEL_SIZE == "auto" else cls.WHISPER_MODEL_SIZE
    
    @classmethod
    def validate_baidu_config(cls) -> bool:
        """验证百度翻译API配置"""
        return bool(cls.BAIDU_APPID and cls.BAIDU_APPKEY)


# 创建全局配置实例
config = Config()
