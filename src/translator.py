"""
翻译服务模块
集成百度翻译API实现英文到中文的翻译功能
"""

import requests
import random
import json
import time
import logging
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
        self.appid = appid or config.BAIDU_APPID
        self.appkey = appkey or config.BAIDU_APPKEY
        self.endpoint = "http://api.fanyi.baidu.com"
        self.path = "/api/trans/vip/translate"
        self.url = self.endpoint + self.path
        
        if not self.appid or not self.appkey:
            logger.warning("百度翻译API配置不完整，请设置BAIDU_APPID和BAIDU_APPKEY环境变量")
    
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
        if not self.appid or not self.appkey:
            raise Exception("百度翻译API配置不完整")
        
        if not text.strip():
            return ""
        
        for attempt in range(max_retries + 1):
            try:
                # 生成随机数和签名
                salt = random.randint(32768, 65536)
                sign = self._build_sign(text, salt)
                
                # 构建请求参数
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                payload = {
                    'appid': self.appid,
                    'q': text,
                    'from': from_lang,
                    'to': to_lang,
                    'salt': salt,
                    'sign': sign
                }
                
                # 发送请求
                response = requests.post(
                    self.url, 
                    params=payload, 
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 检查错误
                if 'error_code' in result:
                    error_msg = f"翻译API错误: {result.get('error_msg', '未知错误')} (代码: {result['error_code']})"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg}, 第{attempt + 1}次重试...")
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(error_msg)
                
                # 提取翻译结果
                if 'trans_result' in result and result['trans_result']:
                    translated_text = result['trans_result'][0]['dst']
                    return translated_text
                else:
                    raise Exception("翻译结果为空")
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    logger.warning(f"网络请求失败: {e}, 第{attempt + 1}次重试...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception(f"网络请求失败: {str(e)}")
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"翻译失败: {e}, 第{attempt + 1}次重试...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception(f"翻译失败: {str(e)}")
        
        raise Exception("翻译失败，已达到最大重试次数")
    
    def translate_segments(
        self, 
        segments: List[Dict], 
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[Dict]:
        """
        翻译多个文本段落
        
        Args:
            segments: 包含文本段落的列表
            progress_callback: 进度回调函数
            
        Returns:
            List[Dict]: 包含原文和译文的段落列表
        """
        if not segments:
            return []
        
        if progress_callback:
            progress_callback.update(0, "开始翻译文本...")
        
        translated_segments = []
        total_segments = len(segments)
        
        for i, segment in enumerate(segments):
            try:
                original_text = segment.get('text', '').strip()
                
                if original_text:
                    # 翻译文本
                    translated_text = self.translate_text(original_text)
                    
                    # 创建新的段落对象
                    translated_segment = segment.copy()
                    translated_segment['original_text'] = original_text
                    translated_segment['translated_text'] = translated_text
                    translated_segment['text'] = f"{original_text}\n{translated_text}"
                else:
                    # 空文本段落
                    translated_segment = segment.copy()
                    translated_segment['original_text'] = ""
                    translated_segment['translated_text'] = ""
                
                translated_segments.append(translated_segment)
                
                # 更新进度
                if progress_callback:
                    progress = int((i + 1) / total_segments * 100)
                    progress_callback.update(
                        progress, 
                        f"已翻译 {i + 1}/{total_segments} 个段落"
                    )
                
                # 添加延迟以避免API限制
                if i < total_segments - 1:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"翻译第{i + 1}个段落失败: {e}")
                # 保留原文
                translated_segment = segment.copy()
                translated_segment['original_text'] = segment.get('text', '')
                translated_segment['translated_text'] = f"[翻译失败: {str(e)}]"
                translated_segment['text'] = translated_segment['original_text']
                translated_segments.append(translated_segment)
        
        if progress_callback:
            progress_callback.update(100, f"翻译完成，共处理 {len(translated_segments)} 个段落")
        
        logger.info(f"翻译完成，共处理 {len(translated_segments)} 个段落")
        return translated_segments
    
    def is_configured(self) -> bool:
        """检查翻译器是否已正确配置"""
        return bool(self.appid and self.appkey)
