"""NPM API模块的测试"""

import pytest
from unittest.mock import patch, MagicMock
from utils.npm_api import (
    get_package_info,
    get_package_tarball_url,
    extract_version_from_tag,
    _get_package_from_registry,
    NetworkError,
    TimeoutError,
    ParseError
)


class TestNpmAPI:
    """NPM API函数的单元测试"""
    
    def test_extract_version_from_tag_with_v_prefix(self):
        """测试从带v前缀的tag提取版本号"""
        assert extract_version_from_tag("v1.0.0") == "1.0.0"
        assert extract_version_from_tag("V2.3.4") == "2.3.4"
    
    def test_extract_version_from_tag_without_prefix(self):
        """测试从不带前缀的tag提取版本号"""
        assert extract_version_from_tag("1.0.0") == "1.0.0"
        assert extract_version_from_tag("2.3.4-beta") == "2.3.4-beta"
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_from_registry_success(self, mock_get):
        """测试成功获取npm包信息"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "A test package",
            "dist": {
                "tarball": "https://registry.npmjs.org/test-package/-/test-package-1.0.0.tgz"
            },
            "repository": {
                "url": "https://github.com/test/repo"
            }
        }
        mock_get.return_value = mock_response
        
        result = _get_package_from_registry("test-package", "https://registry.npmjs.org", timeout=10)
        
        assert result is not None
        assert result["name"] == "test-package"
        assert result["version"] == "1.0.0"
        assert "tarball" in result["dist"]
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_from_registry_not_found(self, mock_get):
        """测试npm包不存在"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = _get_package_from_registry("nonexistent-package", "https://registry.npmjs.org", timeout=10)
        
        assert result is None
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_from_registry_invalid_json(self, mock_get):
        """测试返回无效JSON"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            _get_package_from_registry("test-package", "https://registry.npmjs.org", timeout=10)
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_from_registry_missing_version(self, mock_get):
        """测试响应缺少version字段"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test-package"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ParseError):
            _get_package_from_registry("test-package", "https://registry.npmjs.org", timeout=10)
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_info_with_mirrors(self, mock_get):
        """测试使用镜像获取包信息"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-package",
            "version": "2.0.0",
            "dist": {"tarball": "https://registry.npmmirror.com/test-package/-/test-package-2.0.0.tgz"},
            "repository": {}
        }
        mock_get.return_value = mock_response
        
        result = get_package_info("test-package", registry_mirrors=["https://registry.npmmirror.com"])
        
        assert result is not None
        assert result["version"] == "2.0.0"
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_info_timeout(self, mock_get):
        """测试请求超时"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(TimeoutError):
            get_package_info("test-package")
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_info_connection_error(self, mock_get):
        """测试连接错误"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(NetworkError):
            get_package_info("test-package")
    
    @patch('utils.npm_api.get_package_info')
    def test_get_package_tarball_url_success(self, mock_get_info):
        """测试获取tarball URL"""
        mock_get_info.return_value = {
            "name": "test-package",
            "version": "1.0.0",
            "dist": {
                "tarball": "https://registry.npmjs.org/test-package/-/test-package-1.0.0.tgz"
            },
            "repository": {}
        }
        
        url = get_package_tarball_url("test-package")
        
        assert url == "https://registry.npmjs.org/test-package/-/test-package-1.0.0.tgz"
    
    @patch('utils.npm_api.get_package_info')
    def test_get_package_tarball_url_no_tarball(self, mock_get_info):
        """测试缺少tarball URL"""
        mock_get_info.return_value = {
            "name": "test-package",
            "version": "1.0.0",
            "dist": {},
            "repository": {}
        }
        
        with pytest.raises(NetworkError):
            get_package_tarball_url("test-package")
    
    @patch('utils.npm_api.get_package_info')
    def test_get_package_tarball_url_package_not_found(self, mock_get_info):
        """测试包不存在"""
        mock_get_info.return_value = None
        
        with pytest.raises(NetworkError):
            get_package_tarball_url("nonexistent-package")
    
    @patch('utils.npm_api.requests.get')
    def test_get_package_info_scoped_package(self, mock_get):
        """测试scoped包名（如 @scope/package）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "@scope/test-package",
            "version": "1.0.0",
            "dist": {"tarball": "https://registry.npmjs.org/@scope/test-package/-/test-package-1.0.0.tgz"},
            "repository": {}
        }
        mock_get.return_value = mock_response
        
        result = get_package_info("@scope/test-package", registry_mirrors=["https://registry.npmjs.org"])
        
        assert result is not None
        assert result["name"] == "@scope/test-package"
        
        # 验证URL编码正确
        call_args = mock_get.call_args
        assert "%2F" in call_args[0][0]  # / 应该被编码为 %2F


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
