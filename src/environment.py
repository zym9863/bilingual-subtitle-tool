"""
环境检测和适配模块
自动检测运行环境并进行相应配置
"""

import os
import platform
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """环境检测器"""
    
    @staticmethod
    def is_huggingface_spaces() -> bool:
        """检测是否在Hugging Face Spaces环境中运行"""
        return os.getenv("SPACE_ID") is not None
    
    @staticmethod
    def is_colab() -> bool:
        """检测是否在Google Colab环境中运行"""
        try:
            import google.colab
            return True
        except ImportError:
            return False
    
    @staticmethod
    def is_kaggle() -> bool:
        """检测是否在Kaggle环境中运行"""
        return os.getenv("KAGGLE_KERNEL_RUN_TYPE") is not None
    
    @staticmethod
    def has_gpu() -> bool:
        """检测是否有可用的GPU"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "is_huggingface_spaces": EnvironmentDetector.is_huggingface_spaces(),
            "is_colab": EnvironmentDetector.is_colab(),
            "is_kaggle": EnvironmentDetector.is_kaggle(),
            "has_gpu": EnvironmentDetector.has_gpu(),
        }
    
    @staticmethod
    def get_recommended_config() -> Dict[str, Any]:
        """根据环境获取推荐配置"""
        config = {}
        
        # 检测环境类型
        if EnvironmentDetector.is_huggingface_spaces():
            # Hugging Face Spaces通常是CPU环境
            config.update({
                "whisper_model_size": "base",  # 使用较小的模型
                "whisper_device": "cpu",
                "max_file_size": 100,  # 限制文件大小
                "batch_size": 1,
                "enable_gpu": False
            })
            logger.info("检测到Hugging Face Spaces环境，使用CPU优化配置")
            
        elif EnvironmentDetector.is_colab():
            # Google Colab通常有GPU
            config.update({
                "whisper_model_size": "medium" if EnvironmentDetector.has_gpu() else "base",
                "whisper_device": "cuda" if EnvironmentDetector.has_gpu() else "cpu",
                "max_file_size": 500,
                "batch_size": 4 if EnvironmentDetector.has_gpu() else 1,
                "enable_gpu": EnvironmentDetector.has_gpu()
            })
            logger.info("检测到Google Colab环境")
            
        elif EnvironmentDetector.is_kaggle():
            # Kaggle环境
            config.update({
                "whisper_model_size": "medium" if EnvironmentDetector.has_gpu() else "base",
                "whisper_device": "cuda" if EnvironmentDetector.has_gpu() else "cpu",
                "max_file_size": 300,
                "batch_size": 2 if EnvironmentDetector.has_gpu() else 1,
                "enable_gpu": EnvironmentDetector.has_gpu()
            })
            logger.info("检测到Kaggle环境")
            
        else:
            # 本地环境
            config.update({
                "whisper_model_size": "large" if EnvironmentDetector.has_gpu() else "medium",
                "whisper_device": "cuda" if EnvironmentDetector.has_gpu() else "cpu",
                "max_file_size": 1000,  # 本地环境可以处理更大文件
                "batch_size": 8 if EnvironmentDetector.has_gpu() else 2,
                "enable_gpu": EnvironmentDetector.has_gpu()
            })
            logger.info("检测到本地环境")
        
        return config


class EnvironmentSetup:
    """环境设置类"""
    
    @staticmethod
    def setup_for_huggingface_spaces():
        """为Hugging Face Spaces环境进行设置"""
        # 设置环境变量
        os.environ["WHISPER_DEVICE"] = "cpu"
        os.environ["WHISPER_MODEL_SIZE"] = "base"
        os.environ["MAX_FILE_SIZE"] = "100"
        
        # 创建必要的目录
        os.makedirs("temp", exist_ok=True)
        
        logger.info("Hugging Face Spaces环境设置完成")
    
    @staticmethod
    def setup_for_local():
        """为本地环境进行设置"""
        # 检测GPU并设置相应配置
        if EnvironmentDetector.has_gpu():
            os.environ.setdefault("WHISPER_DEVICE", "cuda")
            os.environ.setdefault("WHISPER_MODEL_SIZE", "large")
        else:
            os.environ.setdefault("WHISPER_DEVICE", "cpu")
            os.environ.setdefault("WHISPER_MODEL_SIZE", "medium")
        
        # 创建必要的目录
        os.makedirs("temp", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        logger.info("本地环境设置完成")
    
    @staticmethod
    def auto_setup():
        """自动设置环境"""
        if EnvironmentDetector.is_huggingface_spaces():
            EnvironmentSetup.setup_for_huggingface_spaces()
        else:
            EnvironmentSetup.setup_for_local()
        
        # 打印系统信息
        system_info = EnvironmentDetector.get_system_info()
        logger.info(f"系统信息: {system_info}")
        
        # 打印推荐配置
        recommended_config = EnvironmentDetector.get_recommended_config()
        logger.info(f"推荐配置: {recommended_config}")


def initialize_environment():
    """初始化环境"""
    logger.info("开始环境初始化...")
    EnvironmentSetup.auto_setup()
    logger.info("环境初始化完成")
