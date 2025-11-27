"""更新检查模块的测试"""

import pytest
from unittest.mock import patch, MagicMock
from core.update_checker import UpdateChecker, UpdateInfo
from utils.npm_api import NetworkError, TimeoutError, ParseError, NpmAPIError


class TestUpdateChecker:
    """UpdateChecker类的单元测试"""
    
    def test_check_update_has_update(self):
        """测试检测到有更新的情况"""
        checker = UpdateChecker()
        
        # Mock NPM API响应
        mock_package = {
            "name": "test-package",
            "version": "2.0.0",
            "description": "Test package",
            "dist": {"tarball": "https://registry.npmjs.org/test-package/-/test-package-2.0.0.tgz"},
            "repository": {"url": "https://github.com/test/repo"}
        }
        
        with patch('core.update_checker.get_package_info', return_value=mock_package):
            result = checker.check_update("test-package", "1.0.0", "test/repo")
        
        assert result.has_update is True
        assert result.current_version == "1.0.0"
        assert result.latest_version == "2.0.0"
        assert result.release_url == "https://github.com/test/repo/releases"
        assert result.error is None
    
    def test_check_update_no_update(self):
        """测试当前版本已是最新的情况"""
        checker = UpdateChecker()
        
        mock_package = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test package",
            "dist": {},
            "repository": {}
        }
        
        with patch('core.update_checker.get_package_info', return_value=mock_package):
            result = checker.check_update("test-package", "1.0.0")
        
        assert result.has_update is False
        assert result.current_version == "1.0.0"
        assert result.latest_version == "1.0.0"
    
    def test_check_update_network_error(self):
        """测试网络错误处理"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_package_info', side_effect=NetworkError("连接失败")):
            result = checker.check_update("test-package", "1.0.0")
        
        assert result.has_update is False
        assert result.error is not None
        assert "连接失败" in result.error
    
    def test_check_update_timeout(self):
        """测试超时处理"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_package_info', side_effect=TimeoutError("请求超时")):
            result = checker.check_update("test-package", "1.0.0")
        
        assert result.has_update is False
        assert result.error is not None
        assert "请求超时" in result.error
    
    def test_check_update_no_package(self):
        """测试npm包不存在的情况"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_package_info', return_value=None):
            result = checker.check_update("test-package", "1.0.0")
        
        assert result.has_update is False
        assert result.latest_version == "未知"
        assert "未找到npm包信息" in result.error
    
    def test_check_all_updates(self):
        """测试检查所有组件更新"""
        checker = UpdateChecker()
        
        versions = {
            "pmhq": "1.0.0",
            "llonebot": "2.0.0",
            "app": "1.0.0"
        }
        
        mock_packages = {
            "pmhq": {
                "name": "pmhq",
                "version": "1.5.0",
                "dist": {},
                "repository": {}
            },
            "llonebot": {
                "name": "llonebot",
                "version": "2.0.0",
                "dist": {},
                "repository": {}
            },
            "lucky-lillia-desktop": {
                "name": "lucky-lillia-desktop",
                "version": "2.0.0",
                "dist": {},
                "repository": {}
            }
        }
        
        def mock_get_package(package_name, timeout=10, registry_mirrors=None):
            return mock_packages.get(package_name)
        
        # 明确传递packages参数
        packages = {
            "pmhq": "pmhq",
            "llonebot": "llonebot",
            "app": "lucky-lillia-desktop"
        }
        
        repos = {
            "pmhq": "linyuchen/pmhq",
            "llonebot": "LLOneBot/LLOneBot",
            "app": "LLOneBot/lucky-lillia-desktop"
        }
        
        with patch('core.update_checker.get_package_info', side_effect=mock_get_package):
            results = checker.check_all_updates(versions, packages, repos)
        
        assert len(results) == 3
        assert results["pmhq"].has_update is True
        assert results["llonebot"].has_update is False
        assert results["app"].has_update is True
    
    def test_version_comparison_with_prerelease(self):
        """测试预发布版本的比较"""
        checker = UpdateChecker()
        
        mock_package = {
            "name": "test-package",
            "version": "2.0.0-beta.1",
            "dist": {},
            "repository": {}
        }
        
        with patch('core.update_checker.get_package_info', return_value=mock_package):
            result = checker.check_update("test-package", "1.0.0")
        
        # 预发布版本应该被认为比稳定版本新
        assert result.has_update is True
        assert result.latest_version == "2.0.0-beta.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
