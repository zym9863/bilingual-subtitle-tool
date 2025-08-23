"""
工具函数模块
提供通用的工具函数和辅助方法
"""

import os
import tempfile
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List
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


def validate_file_content(filepath: str) -> Tuple[bool, str]:
    """验证文件内容的真实性和安全性
    
    Args:
        filepath: 文件路径
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return False, "文件不存在"
        
        # 检查文件大小
        if os.path.getsize(filepath) == 0:
            return False, "文件为空"
        
        # 使用 magic 库检测真实文件类型
        try:
            import magic
            mime_type = magic.from_file(filepath, mime=True)
        except ImportError:
            logger.warning("python-magic 未安装，跳过文件类型检测")
            mime_type = None
        
        # 验证文件头部信息
        with open(filepath, 'rb') as f:
            header = f.read(32)  # 读取前32字节
            
        # 检查常见视频文件的魔数
        video_signatures = {
            b'\x00\x00\x00\x14ftyp': 'mp4',
            b'\x00\x00\x00\x18ftyp': 'mp4',
            b'\x00\x00\x00\x1cftyp': 'mp4',
            b'\x00\x00\x00\x20ftyp': 'mp4',
            b'FLV': 'flv',
            b'RIFF': 'avi',
            b'\x1aE\xdf\xa3': 'webm',
            b'OggS': 'ogv',
        }
        
        file_ext = get_file_extension(filepath)
        is_valid_header = False
        
        # 检查文件头是否匹配扩展名
        for signature, format_name in video_signatures.items():
            if header.startswith(signature):
                is_valid_header = True
                break
        
        # 对于AVI文件，需要特殊检查
        if file_ext == '.avi' and header.startswith(b'RIFF') and b'AVI ' in header[:32]:
            is_valid_header = True
        
        # 对于MOV文件，检查QuickTime格式
        if file_ext in ['.mov', '.qt'] and b'ftyp' in header:
            is_valid_header = True
        
        # 检查文件扩展名与内容的一致性
        if mime_type:
            expected_mimes = {
                '.mp4': ['video/mp4'],
                '.avi': ['video/x-msvideo', 'video/avi'],
                '.mov': ['video/quicktime'],
                '.mkv': ['video/x-matroska'],
                '.wmv': ['video/x-ms-wmv'],
                '.flv': ['video/x-flv'],
                '.webm': ['video/webm'],
            }
            
            if file_ext in expected_mimes:
                if not any(mime_type.startswith(mime) for mime in expected_mimes[file_ext]):
                    return False, f"文件内容与扩展名不匹配: 检测到 {mime_type}，期望 {file_ext}"
        
        # 检查文件是否可能是恶意文件
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'<?php',
            b'#!/bin/',
            b'MZ\x90\x00',  # PE executable header
            b'PK\x03\x04',  # ZIP archive
        ]
        
        for pattern in malicious_patterns:
            if pattern in header:
                return False, "检测到可疑的文件内容"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"文件验证失败: {e}")
        return False, f"文件验证过程出错: {str(e)}"


def calculate_file_hash(filepath: str) -> str:
    """计算文件的SHA256哈希值
    
    Args:
        filepath: 文件路径
        
    Returns:
        str: 文件哈希值
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败: {e}")
        return ""


def check_file_permissions(filepath: str) -> bool:
    """检查文件权限是否安全
    
    Args:
        filepath: 文件路径
        
    Returns:
        bool: 权限是否安全
    """
    try:
        # 检查文件是否可读
        if not os.access(filepath, os.R_OK):
            return False
        
        # 检查文件权限（Unix系统）
        if hasattr(os, 'stat'):
            stat_info = os.stat(filepath)
            # 检查是否有可执行权限（视频文件不应该有执行权限）
            if stat_info.st_mode & 0o111:
                logger.warning(f"文件 {filepath} 具有执行权限，可能不安全")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return False


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
