"""
配置模块测试
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from src.config import Config


class TestConfig(unittest.TestCase):
    """配置类测试"""
    
    def test_default_values(self):
        """测试默认配置值"""
        self.assertEqual(Config.WHISPER_MODEL_SIZE, "small")
        self.assertEqual(Config.WHISPER_DEVICE, "auto")
        self.assertEqual(Config.SUBTITLE_FONT_SIZE, 24)
        self.assertEqual(Config.SUBTITLE_FONT_COLOR, "white")
        self.assertEqual(Config.MAX_FILE_SIZE, 500)
    
    @patch.dict(os.environ, {
        'WHISPER_MODEL_SIZE': 'large',
        'MAX_FILE_SIZE': '1000'
    })
    def test_environment_variables(self):
        """测试环境变量覆盖"""
        # 重新导入配置以应用环境变量
        from importlib import reload
        from src import config
        reload(config)
        
        self.assertEqual(config.Config.WHISPER_MODEL_SIZE, "large")
        self.assertEqual(config.Config.MAX_FILE_SIZE, 1000)
    
    @patch('torch.cuda.is_available')
    def test_gpu_detection(self, mock_cuda):
        """测试GPU检测"""
        # 测试有GPU的情况
        mock_cuda.return_value = True
        self.assertTrue(Config.is_gpu_available())
        
        # 测试没有GPU的情况
        mock_cuda.return_value = False
        self.assertFalse(Config.is_gpu_available())
    
    def test_device_selection(self):
        """测试设备选择逻辑"""
        with patch.object(Config, 'is_gpu_available', return_value=True):
            device = Config.get_device()
            self.assertIn(device, ["cuda", "cpu"])
        
        with patch.object(Config, 'is_gpu_available', return_value=False):
            device = Config.get_device()
            self.assertEqual(device, "cpu")
    
    def test_baidu_config_validation(self):
        """测试百度翻译配置验证"""
        # 测试配置不完整的情况
        with patch.object(Config, 'BAIDU_APPID', None):
            self.assertFalse(Config.validate_baidu_config())
        
        # 测试配置完整的情况
        with patch.object(Config, 'BAIDU_APPID', 'test_appid'), \
             patch.object(Config, 'BAIDU_APPKEY', 'test_appkey'):
            self.assertTrue(Config.validate_baidu_config())


if __name__ == '__main__':
    unittest.main()
