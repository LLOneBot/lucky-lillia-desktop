"""GitHub API模块的测试"""

import pytest
from unittest.mock import patch, MagicMock
from utils.github_api import (
    get_latest_release,
    extract_version_from_tag,
    _get_release_from_api,
    _get_release_from_mirror,
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
    def test_get_release_from_api_success(self, mock_get):
        """测试通过API成功获取release"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "html_url": "https://github.com/test/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_get.return_value = mock_response
        
        result = _get_release_from_api("test/repo", timeout=10)
        
        assert result is not None
        assert result["tag_name"] == "v1.0.0"
        assert result["name"] == "Release 1.0.0"
    
    @patch('utils.github_api.requests.get')
    def test_get_release_from_api_not_found(self, mock_get):
        """测试API返回404"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = _get_release_from_api("test/nonexistent", timeout=10)
        
        assert result is None
    
    @patch('utils.github_api.requests.get')
    def test_get_release_from_api_invalid_json(self, mock_get):
        """测试API返回无效JSON"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            _get_release_from_api("test/repo", timeout=10)
    
    @patch('utils.github_api.requests.get')
    def test_get_release_from_api_missing_tag_name(self, mock_get):
        """测试API响应缺少tag_name"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Release"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            _get_release_from_api("test/repo", timeout=10)
    
    @patch('utils.github_api.requests.get')
    def test_get_release_from_mirror_success(self, mock_get):
        """测试通过镜像成功获取release"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://mirror.com/test/repo/releases/tag/v2.0.0"
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        result = _get_release_from_mirror("test/repo", "https://mirror.com/", timeout=10)
        
        assert result is not None
        assert result["tag_name"] == "v2.0.0"
    
    @patch('utils.github_api.requests.get')
    def test_get_release_from_mirror_not_found(self, mock_get):
        """测试镜像返回404"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = _get_release_from_mirror("test/repo", "https://mirror.com/", timeout=10)
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
