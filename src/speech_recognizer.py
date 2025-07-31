"""
语音识别模块
使用faster-whisper进行英文语音转文字
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from faster_whisper import WhisperModel
from .config import config
from .utils import ProgressCallback

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """语音识别器类"""
    
    def __init__(self, model_size: Optional[str] = None, device: Optional[str] = None):
        """
        初始化语音识别器
        
        Args:
            model_size: Whisper模型大小 (tiny, base, small, medium, large)
            device: 设备类型 (cpu, cuda, auto)
        """
        self.model_size = model_size or config.WHISPER_MODEL_SIZE
        self.device = device or config.get_device()
        self.model = None
        
        logger.info(f"初始化语音识别器: 模型={self.model_size}, 设备={self.device}")
    
    def _load_model(self) -> None:
        """加载Whisper模型"""
        if self.model is None:
            try:
                logger.info(f"正在加载Whisper模型: {self.model_size}")
                
                # 设置缓存目录
                cache_dir = os.environ.get('HF_HOME', '/app/.cache/huggingface')
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                    os.chmod(cache_dir, 0o755)
                
                self.model = WhisperModel(
                    self.model_size, 
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8",
                    download_root=cache_dir
                )
                logger.info("Whisper模型加载成功")
            except Exception as e:
                logger.error(f"Whisper模型加载失败: {e}")
                # 如果GPU加载失败，尝试使用CPU
                if self.device == "cuda":
                    logger.info("尝试使用CPU加载模型...")
                    self.device = "cpu"
                    self.model = WhisperModel(
                        self.model_size, 
                        device="cpu",
                        compute_type="int8",
                        download_root=cache_dir
                    )
                else:
                    raise Exception(f"模型加载失败: {str(e)}")
    
    def transcribe(
        self, 
        audio_path: str, 
        language: str = "en",
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[Dict]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码 (默认为英文 "en")
            progress_callback: 进度回调函数
            
        Returns:
            List[Dict]: 包含转录结果的列表，每个元素包含start, end, text字段
        """
        self._load_model()
        
        if progress_callback:
            progress_callback.update(10, "开始语音识别...")
        
        try:
            logger.info(f"开始转录音频文件: {audio_path}")
            
            # 执行转录
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                word_timestamps=True
            )
            
            if progress_callback:
                progress_callback.update(30, f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
            
            # 处理转录结果
            transcription_results = []
            total_segments = 0
            processed_segments = 0
            
            # 首先计算总段数（用于进度显示）
            segments_list = list(segments)
            total_segments = len(segments_list)
            
            if progress_callback:
                progress_callback.update(40, f"处理 {total_segments} 个音频段...")
            
            for segment in segments_list:
                transcription_results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ] if segment.words else []
                })
                
                processed_segments += 1
                if progress_callback and total_segments > 0:
                    progress = 40 + (processed_segments / total_segments) * 50
                    progress_callback.update(
                        int(progress), 
                        f"已处理 {processed_segments}/{total_segments} 个音频段"
                    )
            
            if progress_callback:
                progress_callback.update(100, f"语音识别完成，共识别 {len(transcription_results)} 个段落")
            
            logger.info(f"转录完成，共 {len(transcription_results)} 个段落")
            return transcription_results
            
        except Exception as e:
            logger.error(f"语音转录失败: {e}")
            raise Exception(f"语音转录失败: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "is_loaded": self.model is not None
        }
