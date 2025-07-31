"""
工具函数测试
"""

import unittest
import tempfile
import os
from pathlib import Path
from src.utils import (
    get_file_extension,
    is_video_file,
    get_file_size_mb,
    validate_file_size,
    sanitize_filename,
    format_time,
    ProgressCallback
)


class TestUtils(unittest.TestCase):
    """工具函数测试"""
    
    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        self.assertEqual(get_file_extension("test.mp4"), ".mp4")
        self.assertEqual(get_file_extension("TEST.MP4"), ".mp4")
        self.assertEqual(get_file_extension("video.avi"), ".avi")
        self.assertEqual(get_file_extension("no_extension"), "")
    
    def test_is_video_file(self):
        """测试视频文件检测"""
        self.assertTrue(is_video_file("test.mp4"))
        self.assertTrue(is_video_file("TEST.AVI"))
        self.assertTrue(is_video_file("video.mkv"))
        self.assertFalse(is_video_file("audio.mp3"))
        self.assertFalse(is_video_file("document.txt"))
    
    def test_get_file_size_mb(self):
        """测试文件大小获取"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # 写入1KB数据
            tmp.write(b"x" * 1024)
            tmp_path = tmp.name
        
        try:
            size_mb = get_file_size_mb(tmp_path)
            self.assertAlmostEqual(size_mb, 1/1024, places=3)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_file_size(self):
        """测试文件大小验证"""
        # 创建小文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"small file")
            small_file = tmp.name
        
        try:
            self.assertTrue(validate_file_size(small_file, max_size_mb=1))
            self.assertFalse(validate_file_size(small_file, max_size_mb=0.000001))
        finally:
            os.unlink(small_file)
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        self.assertEqual(sanitize_filename("normal_file.txt"), "normal_file.txt")
        self.assertEqual(sanitize_filename("file<>with|bad*chars"), "file__with_bad_chars")
        self.assertEqual(sanitize_filename("  spaced  file  "), "spaced file")
        self.assertEqual(sanitize_filename("file:with/path\\chars"), "file_with_path_chars")
    
    def test_format_time(self):
        """测试时间格式化"""
        self.assertEqual(format_time(0), "00:00:00")
        self.assertEqual(format_time(61), "00:01:01")
        self.assertEqual(format_time(3661), "01:01:01")
        self.assertEqual(format_time(3723.5), "01:02:03")
    
    def test_progress_callback(self):
        """测试进度回调"""
        callback = ProgressCallback(total_steps=100)
        
        # 测试更新
        progress, message = callback.update(50, "Half done")
        self.assertEqual(progress, 50.0)
        self.assertEqual(message, "Half done")
        
        # 测试递增
        progress, message = callback.increment("Next step")
        self.assertEqual(progress, 51.0)
        self.assertEqual(message, "Next step")
        
        # 测试超出范围
        progress, message = callback.update(150, "Over limit")
        self.assertEqual(progress, 100.0)
        self.assertEqual(callback.current_step, 100)


if __name__ == '__main__':
    unittest.main()
