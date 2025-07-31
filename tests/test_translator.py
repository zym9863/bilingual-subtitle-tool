"""
翻译模块测试
"""

import unittest
from unittest.mock import patch, MagicMock
from src.translator import BaiduTranslator


class TestBaiduTranslator(unittest.TestCase):
    """百度翻译器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.translator = BaiduTranslator(appid="test_appid", appkey="test_appkey")
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.translator.appid, "test_appid")
        self.assertEqual(self.translator.appkey, "test_appkey")
        self.assertTrue(self.translator.is_configured())
    
    def test_make_md5(self):
        """测试MD5生成"""
        result = self.translator._make_md5("test")
        self.assertEqual(len(result), 32)
        self.assertIsInstance(result, str)
    
    def test_build_sign(self):
        """测试签名构建"""
        sign = self.translator._build_sign("hello", 12345)
        self.assertEqual(len(sign), 32)
        self.assertIsInstance(sign, str)
    
    @patch('requests.post')
    def test_translate_text_success(self, mock_post):
        """测试成功翻译"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'trans_result': [{'dst': '你好'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.translator.translate_text("hello")
        self.assertEqual(result, "你好")
    
    @patch('requests.post')
    def test_translate_text_api_error(self, mock_post):
        """测试API错误"""
        # 模拟API错误响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'error_code': '52001',
            'error_msg': 'Request timeout'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.translator.translate_text("hello", max_retries=0)
        
        self.assertIn("翻译API错误", str(context.exception))
    
    @patch('requests.post')
    def test_translate_text_network_error(self, mock_post):
        """测试网络错误"""
        # 模拟网络错误
        mock_post.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception) as context:
            self.translator.translate_text("hello", max_retries=0)
        
        self.assertIn("翻译失败", str(context.exception))
    
    def test_translate_empty_text(self):
        """测试空文本翻译"""
        result = self.translator.translate_text("")
        self.assertEqual(result, "")
        
        result = self.translator.translate_text("   ")
        self.assertEqual(result, "")
    
    @patch.object(BaiduTranslator, 'translate_text')
    def test_translate_segments(self, mock_translate):
        """测试段落翻译"""
        mock_translate.return_value = "翻译结果"
        
        segments = [
            {'text': 'Hello', 'start': 0, 'end': 1},
            {'text': 'World', 'start': 1, 'end': 2}
        ]
        
        result = self.translator.translate_segments(segments)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['original_text'], 'Hello')
        self.assertEqual(result[0]['translated_text'], '翻译结果')
        self.assertIn('Hello', result[0]['text'])
        self.assertIn('翻译结果', result[0]['text'])
    
    def test_translate_empty_segments(self):
        """测试空段落列表"""
        result = self.translator.translate_segments([])
        self.assertEqual(result, [])
    
    def test_is_configured(self):
        """测试配置检查"""
        # 配置完整
        translator = BaiduTranslator(appid="test", appkey="test")
        self.assertTrue(translator.is_configured())
        
        # 配置不完整
        translator = BaiduTranslator(appid=None, appkey="test")
        self.assertFalse(translator.is_configured())
        
        translator = BaiduTranslator(appid="test", appkey=None)
        self.assertFalse(translator.is_configured())


if __name__ == '__main__':
    unittest.main()
