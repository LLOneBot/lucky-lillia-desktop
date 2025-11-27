"""镜像管理器测试"""

import pytest
from unittest.mock import Mock, patch
from utils.mirror_manager import MirrorManager


class TestMirrorManager:
    """镜像管理器测试类"""
    
    def test_initialization(self):
        """测试镜像管理器初始化"""
        manager = MirrorManager()
        assert manager.timeout == 5
        assert len(manager.mirrors) > 0
        assert manager._available_mirror is None
    
    def test_get_all_mirrors(self):
        """测试获取所有镜像列表"""
        manager = MirrorManager()
        mirrors = manager.get_all_mirrors()
        assert isinstance(mirrors, list)
        assert len(mirrors) > 0
        assert "https://github.com/" in mirrors
    
    def test_transform_url_with_direct_github(self):
        """测试直连GitHub时URL转换"""
        manager = MirrorManager()
        original_url = "https://github.com/owner/repo/releases/download/v1.0/file.exe"
        transformed = manager.transform_url(original_url, "https://github.com/")
        assert transformed == original_url
    
    def test_transform_url_with_mirror(self):
        """测试使用镜像时URL转换"""
        manager = MirrorManager()
        original_url = "https://github.com/owner/repo/releases/download/v1.0/file.exe"
        mirror = "https://gh-proxy.com/https://github.com/"
        transformed = manager.transform_url(original_url, mirror)
        assert transformed == "https://gh-proxy.com/https://github.com/owner/repo/releases/download/v1.0/file.exe"
    
    def test_transform_url_auto_select_mirror(self):
        """测试自动选择镜像时URL转换"""
        manager = MirrorManager()
        manager._available_mirror = "https://github.com/"
        original_url = "https://github.com/owner/repo/releases/download/v1.0/file.exe"
        transformed = manager.transform_url(original_url)
        assert transformed == original_url
    
    def test_reset_cache(self):
        """测试重置缓存"""
        manager = MirrorManager()
        manager._available_mirror = "https://github.com/"
        manager.reset_cache()
        assert manager._available_mirror is None
    
    @patch('utils.mirror_manager.requests.head')
    def test_get_available_mirror_success(self, mock_head):
        """测试获取可用镜像成功"""
        # 模拟第一个镜像可用
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        manager = MirrorManager()
        mirror = manager.get_available_mirror()
        
        assert mirror is not None
        assert mirror in manager.mirrors
        assert manager._available_mirror == mirror
    
    @patch('utils.mirror_manager.requests.head')
    def test_get_available_mirror_cached(self, mock_head):
        """测试获取可用镜像使用缓存"""
        manager = MirrorManager()
        manager._available_mirror = "https://github.com/"
        
        # 不应该调用requests.head
        mirror = manager.get_available_mirror()
        
        assert mirror == "https://github.com/"
        mock_head.assert_not_called()
    
    @patch('utils.mirror_manager.requests.head')
    def test_get_available_mirror_all_fail(self, mock_head):
        """测试所有镜像都不可用时返回第一个"""
        import requests
        # 模拟所有镜像都不可用
        mock_head.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        manager = MirrorManager()
        mirror = manager.get_available_mirror()
        
        # 应该返回第一个镜像
        assert mirror == manager.mirrors[0]
    
    @patch('utils.mirror_manager.requests.head')
    def test_test_mirror_success(self, mock_head):
        """测试镜像可用性检测成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        manager = MirrorManager()
        result = manager._test_mirror("https://github.com/")
        
        assert result is True
    
    @patch('utils.mirror_manager.requests.head')
    def test_test_mirror_redirect(self, mock_head):
        """测试镜像返回重定向状态码"""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_head.return_value = mock_response
        
        manager = MirrorManager()
        result = manager._test_mirror("https://github.com/")
        
        assert result is True
    
    @patch('utils.mirror_manager.requests.head')
    def test_test_mirror_timeout(self, mock_head):
        """测试镜像超时"""
        import requests
        mock_head.side_effect = requests.exceptions.Timeout()
        
        manager = MirrorManager()
        result = manager._test_mirror("https://github.com/")
        
        assert result is False
    
    @patch('utils.mirror_manager.requests.head')
    def test_test_mirror_connection_error(self, mock_head):
        """测试镜像连接错误"""
        import requests
        mock_head.side_effect = requests.exceptions.ConnectionError()
        
        manager = MirrorManager()
        result = manager._test_mirror("https://github.com/")
        
        assert result is False
    
    @patch('utils.mirror_manager.requests.head')
    def test_test_mirror_not_found(self, mock_head):
        """测试镜像返回404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        manager = MirrorManager()
        result = manager._test_mirror("https://github.com/")
        
        assert result is False
    
    def test_transform_url_non_github_url(self):
        """测试转换非GitHub URL"""
        manager = MirrorManager()
        non_github_url = "https://example.com/file.exe"
        transformed = manager.transform_url(non_github_url, "https://gh-proxy.com/https://github.com/")
        
        # 非GitHub URL应该保持不变
        assert transformed == non_github_url
