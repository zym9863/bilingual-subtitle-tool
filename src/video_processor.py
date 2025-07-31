"""
视频字幕烧录模块
使用ffmpeg将生成的双语字幕烧录到原视频中
"""

import os
import subprocess
import logging
from typing import Optional, Dict
import ffmpeg
from .config import config
from .utils import create_temp_file, sanitize_filename, ProgressCallback

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self):
        self.temp_files = []
    
    def _check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def burn_subtitles(
        self, 
        video_path: str, 
        subtitle_path: str,
        output_path: Optional[str] = None,
        subtitle_style: Optional[Dict] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> str:
        """
        将字幕烧录到视频中
        
        Args:
            video_path: 输入视频文件路径
            subtitle_path: 字幕文件路径
            output_path: 输出视频文件路径，如果为None则创建临时文件
            subtitle_style: 字幕样式配置
            progress_callback: 进度回调函数
            
        Returns:
            str: 输出视频文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
        
        if not self._check_ffmpeg():
            raise Exception("ffmpeg未安装或不可用")
        
        if progress_callback:
            progress_callback.update(5, "准备烧录字幕...")
        
        # 创建输出路径
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = create_temp_file(
                suffix=f"_with_subtitles.mp4", 
                prefix=f"{sanitize_filename(base_name)}_"
            )
            self.temp_files.append(output_path)
        
        # 默认字幕样式
        default_style = {
            "font_size": config.SUBTITLE_FONT_SIZE,
            "font_color": config.SUBTITLE_FONT_COLOR,
            "outline_color": config.SUBTITLE_OUTLINE_COLOR,
            "outline_width": config.SUBTITLE_OUTLINE_WIDTH,
            "position": "bottom"  # top, bottom, center
        }
        
        if subtitle_style:
            default_style.update(subtitle_style)
        
        try:
            if progress_callback:
                progress_callback.update(10, "开始字幕烧录...")
            
            # 构建ffmpeg命令
            input_video = ffmpeg.input(video_path)
            
            # 字幕滤镜配置
            subtitle_filter = self._build_subtitle_filter(subtitle_path, default_style)
            
            # 应用字幕滤镜
            output = ffmpeg.output(
                input_video.video.filter('subtitles', subtitle_path, **subtitle_filter),
                input_video.audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                **{'crf': '23', 'preset': 'medium'}
            )
            
            if progress_callback:
                progress_callback.update(20, "正在处理视频...")
            
            # 执行ffmpeg命令
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            if progress_callback:
                progress_callback.update(100, f"字幕烧录完成: {output_path}")
            
            logger.info(f"字幕烧录成功: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = f"ffmpeg处理失败: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"字幕烧录失败: {e}")
            raise Exception(f"字幕烧录失败: {str(e)}")
    
    def _build_subtitle_filter(self, subtitle_path: str, style: Dict) -> Dict:
        """
        构建字幕滤镜参数
        
        Args:
            subtitle_path: 字幕文件路径
            style: 字幕样式配置
            
        Returns:
            Dict: ffmpeg字幕滤镜参数
        """
        filter_params = {}
        
        # 字体大小
        if 'font_size' in style:
            filter_params['force_style'] = f"FontSize={style['font_size']}"
        
        # 字体颜色和描边
        style_parts = []
        if 'font_color' in style:
            style_parts.append(f"PrimaryColour=&H{self._color_to_hex(style['font_color'])}")
        if 'outline_color' in style:
            style_parts.append(f"OutlineColour=&H{self._color_to_hex(style['outline_color'])}")
        if 'outline_width' in style:
            style_parts.append(f"Outline={style['outline_width']}")
        
        if style_parts:
            if 'force_style' in filter_params:
                filter_params['force_style'] += ',' + ','.join(style_parts)
            else:
                filter_params['force_style'] = ','.join(style_parts)
        
        return filter_params
    
    def _color_to_hex(self, color: str) -> str:
        """
        将颜色名称转换为十六进制格式
        
        Args:
            color: 颜色名称或十六进制值
            
        Returns:
            str: 十六进制颜色值
        """
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': 'FF0000',
            'green': '00FF00',
            'blue': '0000FF',
            'yellow': 'FFFF00',
            'cyan': '00FFFF',
            'magenta': 'FF00FF'
        }
        
        color = color.lower()
        if color in color_map:
            return color_map[color]
        elif color.startswith('#'):
            return color[1:].upper()
        elif len(color) == 6 and all(c in '0123456789ABCDEFabcdef' for c in color):
            return color.upper()
        else:
            return 'FFFFFF'  # 默认白色
    
    def add_soft_subtitles(
        self, 
        video_path: str, 
        subtitle_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> str:
        """
        添加软字幕到视频中（不烧录）
        
        Args:
            video_path: 输入视频文件路径
            subtitle_path: 字幕文件路径
            output_path: 输出视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            str: 输出视频文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
        
        if not self._check_ffmpeg():
            raise Exception("ffmpeg未安装或不可用")
        
        if progress_callback:
            progress_callback.update(10, "准备添加软字幕...")
        
        # 创建输出路径
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = create_temp_file(
                suffix=f"_soft_subs.mkv", 
                prefix=f"{sanitize_filename(base_name)}_"
            )
            self.temp_files.append(output_path)
        
        try:
            if progress_callback:
                progress_callback.update(30, "正在添加软字幕...")
            
            # 构建ffmpeg命令
            input_video = ffmpeg.input(video_path)
            input_subtitle = ffmpeg.input(subtitle_path)
            
            output = ffmpeg.output(
                input_video['v'],
                input_video['a'],
                input_subtitle,
                output_path,
                vcodec='copy',
                acodec='copy',
                scodec='srt',
                **{'metadata:s:s:0': 'language=eng'}
            )
            
            # 执行ffmpeg命令
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            if progress_callback:
                progress_callback.update(100, f"软字幕添加完成: {output_path}")
            
            logger.info(f"软字幕添加成功: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = f"ffmpeg处理失败: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"软字幕添加失败: {e}")
            raise Exception(f"软字幕添加失败: {str(e)}")
    
    def cleanup(self):
        """清理临时文件"""
        from .utils import cleanup_temp_files
        if self.temp_files:
            cleanup_temp_files(*self.temp_files)
            self.temp_files.clear()
    
    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup()
