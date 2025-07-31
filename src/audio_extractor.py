"""
音频提取模块
使用MoviePy从视频文件中提取音频
"""

import os
import logging
from typing import Optional, Tuple
from moviepy import VideoFileClip
from .utils import create_temp_file, cleanup_temp_files, ProgressCallback

logger = logging.getLogger(__name__)


class AudioExtractor:
    """音频提取器类"""
    
    def __init__(self):
        self.temp_files = []
    
    def extract_audio(
        self, 
        video_path: str, 
        output_path: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> str:
        """
        从视频文件中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径，如果为None则创建临时文件
            progress_callback: 进度回调函数
            
        Returns:
            str: 提取的音频文件路径
            
        Raises:
            FileNotFoundError: 视频文件不存在
            Exception: 音频提取失败
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if progress_callback:
            progress_callback.update(10, "开始加载视频文件...")
        
        try:
            # 加载视频文件
            video = VideoFileClip(video_path)
            
            if progress_callback:
                progress_callback.update(30, "正在提取音频...")
            
            # 检查视频是否包含音频
            if video.audio is None:
                raise Exception("视频文件不包含音频轨道")
            
            # 创建输出路径
            if output_path is None:
                output_path = create_temp_file(suffix=".wav", prefix="extracted_audio_")
                self.temp_files.append(output_path)
            
            if progress_callback:
                progress_callback.update(50, "正在写入音频文件...")
            
            # 提取音频并保存
            audio = video.audio
            audio.write_audiofile(
                output_path,
                logger=None  # 禁用MoviePy的日志输出
            )
            
            if progress_callback:
                progress_callback.update(90, "音频提取完成")
            
            # 清理资源
            audio.close()
            video.close()
            
            if progress_callback:
                progress_callback.update(100, f"音频已保存到: {output_path}")
            
            logger.info(f"音频提取成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            raise Exception(f"音频提取失败: {str(e)}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            dict: 包含视频信息的字典
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        try:
            video = VideoFileClip(video_path)
            
            info = {
                "duration": video.duration,
                "fps": video.fps,
                "size": video.size,
                "has_audio": video.audio is not None,
                "filename": os.path.basename(video_path)
            }
            
            if video.audio:
                info["audio_fps"] = video.audio.fps
                info["audio_duration"] = video.audio.duration
            
            video.close()
            return info
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            raise Exception(f"获取视频信息失败: {str(e)}")
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_files:
            cleanup_temp_files(*self.temp_files)
            self.temp_files.clear()
    
    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup()
