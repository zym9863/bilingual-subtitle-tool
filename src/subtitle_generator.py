"""
字幕文件处理模块
使用pysrt库处理SRT字幕文件的生成、编辑和格式化
"""

import os
import logging
from typing import List, Dict, Optional
import pysrt
from .utils import create_temp_file, sanitize_filename, ProgressCallback

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """字幕生成器类"""
    
    def __init__(self):
        self.temp_files = []
    
    def _seconds_to_subriptime(self, seconds: float) -> pysrt.SubRipTime:
        """将秒数转换为SubRipTime对象"""
        total_seconds = int(seconds)
        milliseconds = int((seconds - total_seconds) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return pysrt.SubRipTime(hours, minutes, seconds, milliseconds)
    
    def _format_subtitle_text(
        self, 
        original_text: str, 
        translated_text: str = "", 
        subtitle_type: str = "bilingual"
    ) -> str:
        """
        格式化字幕文本
        
        Args:
            original_text: 原文
            translated_text: 译文
            subtitle_type: 字幕类型 ("original", "translated", "bilingual")
            
        Returns:
            str: 格式化后的字幕文本
        """
        original_text = original_text.strip()
        translated_text = translated_text.strip()
        
        if subtitle_type == "original":
            return original_text
        elif subtitle_type == "translated":
            return translated_text
        elif subtitle_type == "bilingual":
            if translated_text:
                return f"{original_text}\n{translated_text}"
            else:
                return original_text
        else:
            return original_text
    
    def create_srt_from_segments(
        self, 
        segments: List[Dict], 
        output_path: Optional[str] = None,
        subtitle_type: str = "bilingual",
        progress_callback: Optional[ProgressCallback] = None
    ) -> str:
        """
        从转录段落创建SRT字幕文件
        
        Args:
            segments: 包含时间戳和文本的段落列表
            output_path: 输出文件路径，如果为None则创建临时文件
            subtitle_type: 字幕类型 ("original", "translated", "bilingual")
            progress_callback: 进度回调函数
            
        Returns:
            str: 生成的SRT文件路径
        """
        if not segments:
            raise ValueError("段落列表不能为空")
        
        if progress_callback:
            progress_callback.update(10, "开始生成字幕文件...")
        
        # 创建输出路径
        if output_path is None:
            output_path = create_temp_file(suffix=".srt", prefix="subtitle_")
            self.temp_files.append(output_path)
        
        try:
            # 创建SRT字幕对象
            subs = pysrt.SubRipFile()
            
            total_segments = len(segments)
            
            for i, segment in enumerate(segments):
                # 获取时间戳
                start_time = self._seconds_to_subriptime(segment['start'])
                end_time = self._seconds_to_subriptime(segment['end'])
                
                # 获取文本
                original_text = segment.get('original_text', segment.get('text', ''))
                translated_text = segment.get('translated_text', '')
                
                # 格式化字幕文本
                subtitle_text = self._format_subtitle_text(
                    original_text, 
                    translated_text, 
                    subtitle_type
                )
                
                # 创建字幕项
                if subtitle_text.strip():
                    subtitle_item = pysrt.SubRipItem(
                        index=i + 1,
                        start=start_time,
                        end=end_time,
                        text=subtitle_text
                    )
                    subs.append(subtitle_item)
                
                # 更新进度
                if progress_callback:
                    progress = 10 + int((i + 1) / total_segments * 80)
                    progress_callback.update(
                        progress, 
                        f"已处理 {i + 1}/{total_segments} 个字幕段落"
                    )
            
            if progress_callback:
                progress_callback.update(95, "正在保存字幕文件...")
            
            # 保存SRT文件
            subs.save(output_path, encoding='utf-8')
            
            if progress_callback:
                progress_callback.update(100, f"字幕文件已保存: {output_path}")
            
            logger.info(f"SRT字幕文件生成成功: {output_path}, 共 {len(subs)} 个字幕项")
            return output_path
            
        except Exception as e:
            logger.error(f"生成SRT字幕文件失败: {e}")
            raise Exception(f"生成SRT字幕文件失败: {str(e)}")
    
    def create_multiple_subtitle_files(
        self, 
        segments: List[Dict], 
        base_filename: str = "subtitle",
        output_dir: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, str]:
        """
        创建多种类型的字幕文件
        
        Args:
            segments: 包含时间戳和文本的段落列表
            base_filename: 基础文件名
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            Dict[str, str]: 包含不同类型字幕文件路径的字典
        """
        if not segments:
            raise ValueError("段落列表不能为空")
        
        if progress_callback:
            progress_callback.update(0, "开始生成多种字幕文件...")
        
        # 清理文件名
        base_filename = sanitize_filename(base_filename)
        
        subtitle_files = {}
        subtitle_types = [
            ("original", "英文字幕"),
            ("translated", "中文字幕"), 
            ("bilingual", "双语字幕")
        ]
        
        for i, (subtitle_type, description) in enumerate(subtitle_types):
            try:
                if progress_callback:
                    progress_callback.update(
                        i * 30, 
                        f"正在生成{description}..."
                    )
                
                # 构建文件名
                if output_dir:
                    filename = f"{base_filename}_{subtitle_type}.srt"
                    output_path = os.path.join(output_dir, filename)
                else:
                    output_path = create_temp_file(
                        suffix=f"_{subtitle_type}.srt", 
                        prefix=f"{base_filename}_"
                    )
                    self.temp_files.append(output_path)
                
                # 生成字幕文件
                self.create_srt_from_segments(
                    segments, 
                    output_path, 
                    subtitle_type
                )
                
                subtitle_files[subtitle_type] = output_path
                
            except Exception as e:
                logger.error(f"生成{description}失败: {e}")
                subtitle_files[subtitle_type] = None
        
        if progress_callback:
            progress_callback.update(100, "所有字幕文件生成完成")
        
        logger.info(f"生成了 {len([f for f in subtitle_files.values() if f])} 个字幕文件")
        return subtitle_files
    
    def validate_srt_file(self, srt_path: str) -> bool:
        """
        验证SRT文件格式
        
        Args:
            srt_path: SRT文件路径
            
        Returns:
            bool: 文件是否有效
        """
        try:
            subs = pysrt.open(srt_path, encoding='utf-8')
            return len(subs) > 0
        except Exception as e:
            logger.error(f"SRT文件验证失败: {e}")
            return False
    
    def get_subtitle_info(self, srt_path: str) -> Dict:
        """
        获取字幕文件信息
        
        Args:
            srt_path: SRT文件路径
            
        Returns:
            Dict: 字幕文件信息
        """
        try:
            subs = pysrt.open(srt_path, encoding='utf-8')
            
            if not subs:
                return {"count": 0, "duration": 0}
            
            total_duration = (subs[-1].end - subs[0].start).total_seconds()
            
            return {
                "count": len(subs),
                "duration": total_duration,
                "first_subtitle": subs[0].text if subs else "",
                "last_subtitle": subs[-1].text if subs else ""
            }
            
        except Exception as e:
            logger.error(f"获取字幕信息失败: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """清理临时文件"""
        from .utils import cleanup_temp_files
        if self.temp_files:
            cleanup_temp_files(*self.temp_files)
            self.temp_files.clear()
    
    def __del__(self):
        """析构函数，自动清理临时文件"""
        self.cleanup()
