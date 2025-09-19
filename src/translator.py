"""
翻译服务模块
集成百度翻译API实现英文到中文的翻译功能
"""

import requests
import random
import json
import time
import logging
import re
import asyncio
import concurrent.futures
from hashlib import md5
from typing import List, Dict, Optional
from .config import config
from .utils import ProgressCallback

logger = logging.getLogger(__name__)


class BaiduTranslator:
    """百度翻译API客户端"""
    
    def __init__(self, appid: Optional[str] = None, appkey: Optional[str] = None):
        """
        初始化翻译器
        
        Args:
            appid: 百度翻译API的APPID
            appkey: 百度翻译API的密钥
        """
        self.appid = self._sanitize_key(appid or config.BAIDU_APPID)
        self.appkey = self._sanitize_key(appkey or config.BAIDU_APPKEY)
        self.endpoint = "http://api.fanyi.baidu.com"
        self.path = "/api/trans/vip/translate"
        self.url = self.endpoint + self.path
        
        # 验证密钥格式和有效性
        if not self._validate_credentials():
            logger.warning("百度翻译API配置不完整或格式无效")
    
    def _sanitize_key(self, key: Optional[str]) -> Optional[str]:
        """清理和验证API密钥
        
        Args:
            key: 原始密钥
            
        Returns:
            str: 清理后的密钥，如果无效则返回None
        """
        if not key:
            return None
        
        # 移除空白字符和特殊字符
        sanitized = key.strip()
        
        # 基本长度和格式验证（百度API密钥通常为特定格式）
        if len(sanitized) < 8 or not re.match(r'^[A-Za-z0-9_-]+$', sanitized):
            logger.error("API密钥格式无效")
            return None
        
        return sanitized
    
    def _validate_credentials(self) -> bool:
        """验证API凭据的有效性
        
        Returns:
            bool: 凭据是否有效
        """
        if not self.appid or not self.appkey:
            return False
        
        # 检查密钥长度和格式
        if len(self.appid) < 8 or len(self.appkey) < 16:
            logger.error("API密钥长度不符合要求")
            return False
        
        return True
    
    def _make_md5(self, s: str, encoding: str = 'utf-8') -> str:
        """生成MD5哈希"""
        return md5(s.encode(encoding)).hexdigest()
    
    def _build_sign(self, query: str, salt: int) -> str:
        """构建签名"""
        sign_str = self.appid + query + str(salt) + self.appkey
        return self._make_md5(sign_str)
    
    def translate_text(
        self, 
        text: str, 
        from_lang: str = "en", 
        to_lang: str = "zh",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        翻译单个文本
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言代码
            to_lang: 目标语言代码
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            
        Returns:
            str: 翻译结果
        """
        if not self._validate_credentials():
            raise Exception("百度翻译API配置不完整或无效")
        
        if not text.strip():
            return ""
        
        # 日志中隐藏敏感信息
        masked_appid = self.appid[:4] + "*" * (len(self.appid) - 8) + self.appid[-4:] if len(self.appid) > 8 else "****"
        logger.debug(f"开始翻译文本，APPID: {masked_appid}")
        
        for attempt in range(max_retries + 1):
            try:
                # 生成随机数和签名
                salt = random.randint(32768, 65536)
                sign = self._build_sign(text, salt)
                
                # 构建请求参数（确保不在日志中记录完整密钥）
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                payload = {
                    'appid': self.appid,
                    'q': text,
                    'from': from_lang,
                    'to': to_lang,
                    'salt': salt,
                    'sign': sign
                }
                
                # 发送请求，确保错误时不泄露敏感信息
                try:
                    response = requests.post(
                        self.url, 
                        params=payload, 
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    
                except requests.exceptions.RequestException as e:
                    # 记录错误但不包含敏感信息
                    logger.warning(f"翻译API请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e).split('?')[0]}")
                    if attempt < max_retries:
                        time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                        continue
                    raise Exception(f"翻译API请求失败: 网络错误")
                
                # 解析响应
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    logger.error("翻译API返回无效的JSON响应")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    raise Exception("翻译API返回格式错误")
                
                # 检查API返回的错误
                if 'error_code' in result:
                    error_code = result.get('error_code', 'unknown')
                    error_msg = result.get('error_msg', '未知错误')
                    
                    # 根据错误码决定是否重试
                    if error_code in ['52003', '54003', '54005']:  # 频率限制等可重试错误
                        if attempt < max_retries:
                            logger.warning(f"翻译API限频，将在{retry_delay * 2}秒后重试")
                            time.sleep(retry_delay * 2)
                            continue
                    
                    raise Exception(f"翻译API错误 ({error_code}): {error_msg}")
                
                # 提取翻译结果
                if 'trans_result' in result and result['trans_result']:
                    translated = result['trans_result'][0].get('dst', '')
                    logger.debug(f"翻译成功: {text[:50]}... -> {translated[:50]}...")
                    return translated
                else:
                    logger.error("翻译API返回空结果")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    raise Exception("翻译API返回空结果")
                    
            except Exception as e:
                if attempt >= max_retries:
                    logger.error(f"翻译失败，已达最大重试次数: {str(e)}")
                    raise e
                else:
                    logger.warning(f"翻译尝试 {attempt + 1} 失败，将重试: {str(e)}")
                    time.sleep(retry_delay)
        
        raise Exception("翻译失败：超过最大重试次数")
    
    def translate_segments(
        self,
        segments: List[Dict],
        from_lang: str = "en",
        to_lang: str = "zh",
        progress_callback: Optional[ProgressCallback] = None,
        batch_size: int = 5,
        max_workers: int = 3
    ) -> List[Dict]:
        """
        翻译多个文本段落，支持批量和并发处理

        Args:
            segments: 包含文本段落的列表
            from_lang: 源语言代码 (en, zh等)
            to_lang: 目标语言代码 (zh, en等)
            progress_callback: 进度回调函数
            batch_size: 批处理大小
            max_workers: 最大并发工作线程数

        Returns:
            List[Dict]: 包含原文和译文的段落列表
        """
        if not segments:
            return []
        
        if progress_callback:
            progress_callback.update(0, "开始翻译文本...")
        
        # 过滤出需要翻译的段落
        segments_to_translate = []
        segments_map = {}
        
        for i, segment in enumerate(segments):
            original_text = segment.get('text', '').strip()
            if original_text:
                segments_to_translate.append((i, segment, original_text))
                segments_map[i] = segment
        
        if not segments_to_translate:
            return segments
        
        translated_segments = segments.copy()
        total_segments = len(segments_to_translate)
        processed = 0
        
        # 使用线程池进行并发翻译，但限制并发数以避免API限制
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 将任务分批处理
            for batch_start in range(0, len(segments_to_translate), batch_size):
                batch_end = min(batch_start + batch_size, len(segments_to_translate))
                batch = segments_to_translate[batch_start:batch_end]
                
                # 提交批次中的所有翻译任务
                future_to_segment = {}
                for idx, segment, original_text in batch:
                    future = executor.submit(
                        self._translate_with_retry,
                        original_text,
                        from_lang,
                        to_lang
                    )
                    future_to_segment[future] = (idx, segment, original_text)
                
                # 收集批次结果
                for future in concurrent.futures.as_completed(future_to_segment):
                    idx, segment, original_text = future_to_segment[future]
                    
                    try:
                        translated_text = future.result()
                        
                        # 创建翻译后的段落对象
                        translated_segment = segment.copy()
                        translated_segment['original_text'] = original_text
                        translated_segment['translated_text'] = translated_text

                        # 根据翻译方向生成双语字幕文本
                        if from_lang == "zh" and to_lang == "en":
                            # 中文音频：中文在上，英文在下
                            translated_segment['text'] = f"{original_text}\n{translated_text}"
                        else:
                            # 英文音频：英文在上，中文在下（原逻辑）
                            translated_segment['text'] = f"{original_text}\n{translated_text}"
                        
                        translated_segments[idx] = translated_segment
                        
                    except Exception as e:
                        logger.error(f"翻译段落失败: {e}")
                        # 保持原文本不变
                        translated_segment = segment.copy()
                        translated_segment['original_text'] = original_text
                        translated_segment['translated_text'] = f"[翻译失败: {str(e)}]"
                        translated_segment['text'] = original_text
                        translated_segments[idx] = translated_segment
                    
                    processed += 1
                    if progress_callback:
                        progress = int((processed / total_segments) * 100)
                        progress_callback.update(progress, f"已翻译 {processed}/{total_segments} 个段落")
                
                # 批次间延迟，避免API限制
                if batch_end < len(segments_to_translate):
                    time.sleep(1.0)  # 批次间1秒延迟
        
        if progress_callback:
            progress_callback.update(100, f"翻译完成，共处理 {total_segments} 个段落")
        
        logger.info(f"翻译完成，共处理 {total_segments} 个段落")
        return translated_segments
    
    def _translate_with_retry(
        self,
        text: str,
        from_lang: str = "en",
        to_lang: str = "zh",
        max_retries: int = 3
    ) -> str:
        """
        带重试的翻译方法（内部使用）

        Args:
            text: 要翻译的文本
            from_lang: 源语言代码
            to_lang: 目标语言代码
            max_retries: 最大重试次数

        Returns:
            str: 翻译结果
        """
        for attempt in range(max_retries + 1):
            try:
                return self.translate_text(text, from_lang, to_lang)
            except Exception as e:
                if attempt >= max_retries:
                    raise e
                
                # 根据错误类型决定重试延迟
                delay = 2 ** attempt  # 指数退避
                if "频率限制" in str(e) or "54003" in str(e):
                    delay *= 2  # 频率限制时延迟更长
                
                logger.warning(f"翻译重试 {attempt + 1}/{max_retries + 1}: {e}")
                time.sleep(delay)
        
        raise Exception("翻译重试失败")
    
    def translate_batch(self, texts: List[str], batch_size: int = 10) -> List[str]:
        """
        批量翻译文本列表
        
        Args:
            texts: 要翻译的文本列表
            batch_size: 批处理大小
            
        Returns:
            List[str]: 翻译结果列表
        """
        if not texts:
            return []
        
        results = [""] * len(texts)
        
        # 分批处理以优化API调用
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch_texts:
                try:
                    if text.strip():
                        translated = self.translate_text(text)
                        batch_results.append(translated)
                    else:
                        batch_results.append("")
                except Exception as e:
                    logger.error(f"批量翻译失败: {e}")
                    batch_results.append(f"[翻译失败: {str(e)}]")
            
            # 将批次结果写入结果列表
            for j, result in enumerate(batch_results):
                results[i + j] = result
            
            # 批次间延迟
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        return results
    
    def is_configured(self) -> bool:
        """检查翻译器是否已正确配置"""
        return bool(self.appid and self.appkey)
