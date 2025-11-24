"""GitHub API模块的测试"""

import pytest
from unittest.mock import patch, MagicMock
from utils.github_api import (
    get_latest_release,
    extract_version_from_tag,
    NetworkError,
    TimeoutError,
    ParseError
)


class TestGitHubAPI:
    """GitHub API函数的单元测试"""
    
    def test_extract_version_from_tag_with_v_prefix(self):
        """测试从带v前缀的tag提取版本号"""
        assert extract_version_from_tag("v1.0.0") == "1.0.0"
        assert extract_version_from_tag("V2.3.4") == "2.3.4"
    
    def test_extract_version_from_tag_without_prefix(self):
        """测试从不带前缀的tag提取版本号"""
        assert extract_version_from_tag("1.0.0") == "1.0.0"
        assert extract_version_from_tag("2.3.4-beta") == "2.3.4-beta"
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_success(self, mock_get):
        """测试成功获取最新release"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "html_url": "https://github.com/test/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_get.return_value = mock_response
        
        result = get_latest_release("test/repo")
        
        assert result is not None
        assert result["tag_name"] == "v1.0.0"
        assert result["name"] == "Release 1.0.0"
        assert result["html_url"] == "https://github.com/test/repo/releases/tag/v1.0.0"
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_not_found(self, mock_get):
        """测试仓库不存在或没有release"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = get_latest_release("test/nonexistent")
        
        assert result is None
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_timeout(self, mock_get):
        """测试请求超时"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(TimeoutError):
            get_latest_release("test/repo")
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_connection_error(self, mock_get):
        """测试连接错误"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(NetworkError):
            get_latest_release("test/repo")
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_invalid_json(self, mock_get):
        """测试无效的JSON响应"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            get_latest_release("test/repo")
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_missing_tag_name(self, mock_get):
        """测试响应缺少tag_name字段"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Release",
            "html_url": "https://github.com/test/repo/releases"
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            get_latest_release("test/repo")
    
    @patch('utils.github_api.requests.get')
    def test_get_latest_release_custom_timeout(self, mock_get):
        """测试自定义超时时间"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "html_url": "https://github.com/test/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_get.return_value = mock_response
        
        get_latest_release("test/repo", timeout=5)
        
        # 验证timeout参数被正确传递
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
