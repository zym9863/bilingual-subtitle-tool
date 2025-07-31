"""
工具函数模块
提供通用的工具函数和辅助方法
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_dir(directory: str) -> None:
    """确保目录存在，如果不存在则创建"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def is_video_file(filename: str) -> bool:
    """检查文件是否为支持的视频格式"""
    from .config import config
    return get_file_extension(filename) in config.SUPPORTED_VIDEO_FORMATS


def get_file_size_mb(filepath: str) -> float:
    """获取文件大小（MB）"""
    return os.path.getsize(filepath) / (1024 * 1024)


def validate_file_size(filepath: str, max_size_mb: Optional[int] = None) -> bool:
    """验证文件大小是否在允许范围内"""
    from .config import config
    max_size = max_size_mb or config.MAX_FILE_SIZE
    return get_file_size_mb(filepath) <= max_size


def create_temp_file(suffix: str = "", prefix: str = "subtitle_tool_") -> str:
    """创建临时文件并返回路径"""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def create_temp_dir(prefix: str = "subtitle_tool_") -> str:
    """创建临时目录并返回路径"""
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_files(*paths: str) -> None:
    """清理临时文件和目录"""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            logger.warning(f"清理临时文件失败 {path}: {e}")


def format_time(seconds: float) -> str:
    """将秒数格式化为时:分:秒格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    import re
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除多余的空格和点
    filename = re.sub(r'\s+', ' ', filename).strip('. ')
    return filename


class ProgressCallback:
    """进度回调类，用于在Gradio界面中显示进度"""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.status_message = ""
    
    def update(self, step: int, message: str = "") -> Tuple[int, str]:
        """更新进度"""
        self.current_step = min(step, self.total_steps)
        self.status_message = message
        progress = (self.current_step / self.total_steps) * 100
        return progress, self.status_message
    
    def increment(self, message: str = "") -> Tuple[int, str]:
        """递增进度"""
        return self.update(self.current_step + 1, message)
