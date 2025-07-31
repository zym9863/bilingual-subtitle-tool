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
        
        # 额外验证字幕文件
        if not self._validate_subtitle_file(subtitle_path):
            raise Exception(f"字幕文件格式无效或损坏: {subtitle_path}")
        
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

            # 明确字幕编码，生成器保存为UTF-8，这里声明以减少平台差异
            subtitle_filter = dict(subtitle_filter)  # 复制以避免副作用
            subtitle_filter.setdefault('charenc', 'UTF-8')

            # 应用字幕滤镜 - 修复Windows路径与引号/转义问题
            subtitle_path_normalized = self._normalize_path_for_ffmpeg(subtitle_path)

            # 验证字幕文件是否存在且可读
            exists = os.path.isfile(subtitle_path)
            readable = os.access(subtitle_path, os.R_OK)
            logger.debug(f"字幕路径检查 | 原始: {subtitle_path} | 规范化: {subtitle_path_normalized} | exists={exists} readable={readable}")
            if not exists or not readable:
                raise Exception(f"字幕文件无法访问或不存在: {subtitle_path}")

            # 使用键值形式传递文件名，避免位置参数在Windows上因冒号/斜杠解析失败
            video_with_subs = input_video.video.filter('subtitles', filename=subtitle_path_normalized, **subtitle_filter)

            output = ffmpeg.output(
                video_with_subs,
                input_video.audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                **{'crf': '23', 'preset': 'medium'}
            )

            # 输出编译后的命令行用于调试复现
            try:
                compiled_cmd = ffmpeg.compile(output, overwrite_output=True)
                logger.debug(f"FFmpeg命令: {' '.join(compiled_cmd)}")
            except Exception as _e:
                logger.debug(f"FFmpeg命令编译失败: {_e}")

            if progress_callback:
                progress_callback.update(20, "正在处理视频...")
            
            # 执行ffmpeg命令
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            if progress_callback:
                progress_callback.update(100, f"字幕烧录完成: {output_path}")
            
            logger.info(f"字幕烧录成功: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            # 改进FFmpeg错误信息处理
            error_msg = self._parse_ffmpeg_error(e)
            logger.error(f"ffmpeg处理失败: {error_msg}")
            raise Exception(f"ffmpeg处理失败: {error_msg}")
        except Exception as e:
            logger.error(f"字幕烧录失败: {e}")
            raise Exception(f"字幕烧录失败: {str(e)}")
    
    def _validate_subtitle_file(self, subtitle_path: str) -> bool:
        """
        验证字幕文件是否有效
        
        Args:
            subtitle_path: 字幕文件路径
            
        Returns:
            bool: 文件是否有效
        """
        try:
            # 检查文件是否可读
            if not os.access(subtitle_path, os.R_OK):
                logger.warning(f"字幕文件无读取权限: {subtitle_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(subtitle_path)
            if file_size == 0:
                logger.warning(f"字幕文件为空: {subtitle_path}")
                return False
            
            # 检查文件扩展名
            _, ext = os.path.splitext(subtitle_path.lower())
            if ext not in ['.srt', '.ass', '.ssa', '.sub', '.vtt']:
                logger.warning(f"不支持的字幕文件格式: {ext}")
                return False
            
            # 尝试读取文件开头几行验证编码
            try:
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if not first_line.strip():
                        logger.warning(f"字幕文件第一行为空: {subtitle_path}")
                        return False
            except UnicodeDecodeError:
                # 尝试其他编码
                try:
                    with open(subtitle_path, 'r', encoding='gbk') as f:
                        f.readline()
                except UnicodeDecodeError:
                    logger.warning(f"字幕文件编码无法识别: {subtitle_path}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"验证字幕文件时出错: {e}")
            return False
    
    def _parse_ffmpeg_error(self, error: ffmpeg.Error) -> str:
        """
        解析FFmpeg错误信息
        
        Args:
            error: FFmpeg错误对象
            
        Returns:
            str: 解析后的错误信息
        """
        try:
            if error.stderr:
                stderr_text = error.stderr.decode('utf-8', errors='ignore')
                
                # 提取关键错误信息
                if "Unable to open" in stderr_text:
                    return "无法打开字幕文件，请检查文件路径和权限"
                elif "Invalid argument" in stderr_text and "filter_complex" in stderr_text:
                    return "字幕滤镜参数错误，可能是样式设置问题"
                elif "No such file or directory" in stderr_text:
                    return "找不到指定的文件"
                elif "Permission denied" in stderr_text:
                    return "文件访问权限被拒绝"
                else:
                    # 返回最后几行关键错误信息
                    lines = stderr_text.strip().split('\n')
                    error_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['error', 'failed', 'invalid', 'unable'])]
                    if error_lines:
                        return error_lines[-1].strip()
                    else:
                        return stderr_text.split('\n')[-1].strip() if lines else "未知FFmpeg错误"
            else:
                return str(error)
        except Exception:
            return str(error)
    
    def _normalize_path_for_ffmpeg(self, path: str) -> str:
        """
        为FFmpeg标准化文件路径
        
        Args:
            path: 原始文件路径
            
        Returns:
            str: 标准化后的路径
        """
        # 获取绝对路径
        abs_path = os.path.abspath(path)
        
        # 在Windows系统上处理路径
        if os.name == 'nt':
            # 将反斜杠替换为正斜杠
            normalized = abs_path.replace('\\', '/')
            # 如果是Windows绝对路径，确保格式正确
            if len(normalized) > 1 and normalized[1] == ':':
                normalized = normalized
        else:
            normalized = abs_path
            
        logger.debug(f"路径标准化: {path} -> {normalized}")
        return normalized
    
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
        
        # 构建样式字符串列表
        style_parts = []
        
        # 字体大小
        if 'font_size' in style:
            style_parts.append(f"FontSize={style['font_size']}")
        
        # 字体颜色和描边
        if 'font_color' in style:
            color_hex = self._color_to_hex(style['font_color'])
            style_parts.append(f"PrimaryColour=&H{color_hex}")
            
        if 'outline_color' in style:
            outline_hex = self._color_to_hex(style['outline_color'])
            style_parts.append(f"OutlineColour=&H{outline_hex}")
            
        if 'outline_width' in style:
            style_parts.append(f"Outline={style['outline_width']}")
        
        # 如果有样式参数，则设置force_style
        if style_parts:
            # 使用逗号连接样式参数，确保正确的转义
            force_style = ','.join(style_parts)
            filter_params['force_style'] = force_style
            logger.debug(f"字幕样式参数: {force_style}")
        
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
            # 改进FFmpeg错误信息处理
            error_msg = self._parse_ffmpeg_error(e)
            logger.error(f"ffmpeg处理失败: {error_msg}")
            raise Exception(f"ffmpeg处理失败: {error_msg}")
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
