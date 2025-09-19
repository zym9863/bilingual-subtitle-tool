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


class SpeechRecognitionError(Exception):
    """语音识别相关错误的基类"""
    pass


class ModelLoadError(SpeechRecognitionError):
    """模型加载错误"""
    pass


class AudioProcessingError(SpeechRecognitionError):
    """音频处理错误"""
    pass


class InsufficientResourceError(SpeechRecognitionError):
    """资源不足错误"""
    pass


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
                
            except ImportError as e:
                error_msg = f"模型依赖库缺失: {str(e)}"
                logger.error(error_msg)
                raise ModelLoadError(f"请安装必要的依赖: {error_msg}")
                
            except FileNotFoundError as e:
                error_msg = f"模型文件未找到: {str(e)}"
                logger.error(error_msg)
                raise ModelLoadError(f"模型下载可能不完整，请检查网络连接并重试")
                
            except MemoryError as e:
                error_msg = f"内存不足: {str(e)}"
                logger.error(error_msg)
                raise InsufficientResourceError("内存不足，请尝试使用更小的模型或释放内存")
                
            except RuntimeError as e:
                error_msg = str(e).lower()
                if "cuda" in error_msg or "gpu" in error_msg:
                    logger.warning(f"GPU加载失败: {e}")
                    # 如果GPU加载失败，尝试使用CPU
                    if self.device == "cuda":
                        logger.info("尝试使用CPU加载模型...")
                        try:
                            self.device = "cpu"
                            self.model = WhisperModel(
                                self.model_size, 
                                device="cpu",
                                compute_type="int8",
                                download_root=cache_dir
                            )
                            logger.info("已切换到CPU模式")
                        except Exception as cpu_error:
                            raise ModelLoadError(f"CPU加载也失败: {str(cpu_error)}")
                    else:
                        raise ModelLoadError(f"运行时错误: {str(e)}")
                else:
                    raise ModelLoadError(f"模型加载运行时错误: {str(e)}")
                    
            except Exception as e:
                error_msg = f"未知错误: {str(e)}"
                logger.error(error_msg)
                raise ModelLoadError(f"模型加载失败: {error_msg}")
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "en",
        progress_callback: Optional[ProgressCallback] = None,
        chunk_duration: int = 600,  # 10分钟分块
        enable_memory_optimization: bool = True
    ) -> List[Dict]:
        """
        转录音频文件，支持大文件分块处理以优化内存使用

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (支持 "en" 英文, "zh" 中文，等)
            progress_callback: 进度回调函数
            chunk_duration: 分块时长（秒），大文件会被分块处理
            enable_memory_optimization: 是否启用内存优化

        Returns:
            List[Dict]: 包含转录结果的列表，每个元素包含start, end, text字段
        """
        import gc
        import os
        
        self._load_model()
        
        if progress_callback:
            progress_callback.update(10, "开始语音识别...")
        
        # 检查文件大小并决定是否分块处理
        audio_size_mb = os.path.getsize(audio_path) / (1024**2)
        logger.info(f"音频文件大小: {audio_size_mb:.1f}MB")
        
        # 检查可用内存（可选，如果psutil可用）
        available_memory_gb = None
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            logger.info(f"可用内存: {available_memory_gb:.1f}GB")
        except ImportError:
            logger.info("psutil未安装，使用文件大小判断是否分块处理")
        
        # 如果文件很大或内存可能不足，启用分块处理
        if enable_memory_optimization:
            should_chunk = audio_size_mb > 100
            if available_memory_gb is not None:
                should_chunk = should_chunk or (available_memory_gb < 4)
        else:
            should_chunk = False
        
        try:
            logger.info(f"开始转录音频文件: {audio_path}")
            
            if should_chunk:
                return self._transcribe_chunked(
                    audio_path, 
                    language, 
                    progress_callback, 
                    chunk_duration
                )
            else:
                return self._transcribe_direct(audio_path, language, progress_callback)
                
        except FileNotFoundError as e:
            error_msg = f"音频文件未找到: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError("无法找到音频文件，请确认文件路径正确")
            
        except MemoryError as e:
            error_msg = f"内存不足: {str(e)}"
            logger.error(error_msg)
            raise InsufficientResourceError("内存不足以处理此音频文件，请尝试使用更小的模型或分段处理")
            
        except PermissionError as e:
            error_msg = f"文件权限错误: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError("无法访问音频文件，请检查文件权限")
            
        except RuntimeError as e:
            error_msg = str(e).lower()
            if "cuda" in error_msg or "gpu" in error_msg:
                logger.error(f"GPU运行时错误: {e}")
                raise InsufficientResourceError("GPU资源不足或驱动问题，请尝试使用CPU模式")
            else:
                logger.error(f"运行时错误: {e}")
                raise AudioProcessingError(f"音频处理过程中发生错误: {str(e)}")
                
        except KeyboardInterrupt:
            logger.info("用户取消了转录操作")
            raise AudioProcessingError("转录操作被用户取消")
            
        except ModelLoadError:
            # 重新抛出模型加载错误
            raise
            
        except Exception as e:
            error_msg = f"转录失败，未知错误: {str(e)}"
            logger.error(error_msg)
            
            # 尝试提供更友好的错误信息
            if "timeout" in str(e).lower():
                raise AudioProcessingError("转录超时，文件可能过大或网络不稳定")
            elif "format" in str(e).lower() or "codec" in str(e).lower():
                raise AudioProcessingError("音频格式不支持或已损坏")
            else:
                raise SpeechRecognitionError(f"语音转录失败: {error_msg}")
                
        finally:
            # 强制垃圾回收以释放内存
            if enable_memory_optimization:
                gc.collect()
    
    def _transcribe_direct(
        self,
        audio_path: str,
        language: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[Dict]:
        """
        直接转录音频文件（小文件或内存充足时使用）
        """
        # 根据语言优化参数
        beam_size = 5
        if language == "zh":
            # 中文语音识别优化参数
            beam_size = 3  # 中文可以使用较小的beam_size

        # 执行转录
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            word_timestamps=True
        )
        
        if progress_callback:
            progress_callback.update(30, f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
        
        # 处理转录结果
        transcription_results = []
        segments_list = list(segments)
        total_segments = len(segments_list)
        
        if progress_callback:
            progress_callback.update(40, f"处理 {total_segments} 个音频段...")
        
        for i, segment in enumerate(segments_list):
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
            
            if progress_callback and total_segments > 0:
                progress = 40 + int((i + 1) / total_segments * 50)
                progress_callback.update(
                    progress, 
                    f"已处理 {i + 1}/{total_segments} 个音频段"
                )
        
        if progress_callback:
            progress_callback.update(100, f"语音识别完成，共识别 {len(transcription_results)} 个段落")
        
        logger.info(f"转录完成，共 {len(transcription_results)} 个段落")
        return transcription_results
    
    def _transcribe_chunked(
        self,
        audio_path: str,
        language: str,
        progress_callback: Optional[ProgressCallback] = None,
        chunk_duration: int = 600
    ) -> List[Dict]:
        """
        分块转录音频文件（大文件或内存不足时使用）
        """
        import subprocess
        import tempfile
        import gc
        
        logger.info(f"使用分块模式转录，分块时长: {chunk_duration}秒")
        
        # 获取音频时长
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', audio_path
            ], capture_output=True, text=True, check=True)
            total_duration = float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"无法获取音频时长: {e}，使用直接转录模式")
            return self._transcribe_direct(audio_path, language, progress_callback)
        
        transcription_results = []
        chunk_count = int((total_duration + chunk_duration - 1) // chunk_duration)  # 向上取整
        
        for chunk_idx in range(chunk_count):
            start_time = chunk_idx * chunk_duration
            end_time = min((chunk_idx + 1) * chunk_duration, total_duration)
            
            if progress_callback:
                chunk_progress = int((chunk_idx / chunk_count) * 90)
                progress_callback.update(chunk_progress, f"处理分块 {chunk_idx + 1}/{chunk_count}")
            
            # 提取音频分块
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as chunk_file:
                try:
                    subprocess.run([
                        'ffmpeg', '-i', audio_path, 
                        '-ss', str(start_time), '-t', str(end_time - start_time),
                        '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                        chunk_file.name, '-y'
                    ], check=True, capture_output=True)
                    
                    # 根据语言优化参数
                    beam_size = 3  # 分块模式默认使用较小beam size以节省内存
                    if language == "zh":
                        # 中文语音识别特殊优化
                        beam_size = 2  # 中文可以使用更小的beam_size

                    # 转录分块
                    segments, info = self.model.transcribe(
                        chunk_file.name,
                        language=language,
                        beam_size=beam_size,
                        word_timestamps=True
                    )
                    
                    # 处理分块结果并调整时间戳
                    for segment in segments:
                        transcription_results.append({
                            "start": segment.start + start_time,
                            "end": segment.end + start_time,
                            "text": segment.text.strip(),
                            "words": [
                                {
                                    "start": word.start + start_time,
                                    "end": word.end + start_time,
                                    "word": word.word,
                                    "probability": word.probability
                                }
                                for word in segment.words
                            ] if segment.words else []
                        })
                    
                    # 强制垃圾回收
                    gc.collect()
                    
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(chunk_file.name)
                    except Exception:
                        pass
        
        if progress_callback:
            progress_callback.update(100, f"语音识别完成，共识别 {len(transcription_results)} 个段落")
        
        logger.info(f"分块转录完成，共 {len(transcription_results)} 个段落")
        return transcription_results
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "is_loaded": self.model is not None
        }
