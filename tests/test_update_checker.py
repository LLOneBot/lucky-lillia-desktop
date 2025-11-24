"""更新检查模块的测试"""

import pytest
from unittest.mock import patch, MagicMock
from core.update_checker import UpdateChecker, UpdateInfo
from utils.github_api import NetworkError, TimeoutError, ParseError


class TestUpdateChecker:
    """UpdateChecker类的单元测试"""
    
    def test_check_update_has_update(self):
        """测试检测到有更新的情况"""
        checker = UpdateChecker()
        
        # Mock GitHub API响应
        mock_release = {
            "tag_name": "v2.0.0",
            "name": "Release 2.0.0",
            "html_url": "https://github.com/test/repo/releases/tag/v2.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('core.update_checker.get_latest_release', return_value=mock_release):
            result = checker.check_update("test/repo", "1.0.0")
        
        assert result.has_update is True
        assert result.current_version == "1.0.0"
        assert result.latest_version == "2.0.0"
        assert result.release_url == "https://github.com/test/repo/releases/tag/v2.0.0"
        assert result.error is None
    
    def test_check_update_no_update(self):
        """测试当前版本已是最新的情况"""
        checker = UpdateChecker()
        
        mock_release = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "html_url": "https://github.com/test/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('core.update_checker.get_latest_release', return_value=mock_release):
            result = checker.check_update("test/repo", "1.0.0")
        
        assert result.has_update is False
        assert result.current_version == "1.0.0"
        assert result.latest_version == "1.0.0"
    
    def test_check_update_network_error(self):
        """测试网络错误处理"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_latest_release', side_effect=NetworkError("连接失败")):
            result = checker.check_update("test/repo", "1.0.0")
        
        assert result.has_update is False
        assert result.error is not None
        assert "连接失败" in result.error
    
    def test_check_update_timeout(self):
        """测试超时处理"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_latest_release', side_effect=TimeoutError("请求超时")):
            result = checker.check_update("test/repo", "1.0.0")
        
        assert result.has_update is False
        assert result.error is not None
        assert "请求超时" in result.error
    
    def test_check_update_no_release(self):
        """测试仓库没有release的情况"""
        checker = UpdateChecker()
        
        with patch('core.update_checker.get_latest_release', return_value=None):
            result = checker.check_update("test/repo", "1.0.0")
        
        assert result.has_update is False
        assert result.latest_version == "未知"
        assert "未找到release信息" in result.error
    
    def test_check_all_updates(self):
        """测试检查所有组件更新"""
        checker = UpdateChecker()
        
        versions = {
            "pmhq": "1.0.0",
            "llonebot": "2.0.0",
            "app": "1.0.0"
        }
        
        mock_releases = {
            "owner/pmhq": {
                "tag_name": "v1.5.0",
                "name": "Release 1.5.0",
                "html_url": "https://github.com/owner/pmhq/releases/tag/v1.5.0",
                "published_at": "2024-01-01T00:00:00Z"
            },
            "LLOneBot/LLOneBot": {
                "tag_name": "v2.0.0",
                "name": "Release 2.0.0",
                "html_url": "https://github.com/LLOneBot/LLOneBot/releases/tag/v2.0.0",
                "published_at": "2024-01-01T00:00:00Z"
            },
            "owner/qq-bot-manager": {
                "tag_name": "v2.0.0",
                "name": "Release 2.0.0",
                "html_url": "https://github.com/owner/qq-bot-manager/releases/tag/v2.0.0",
                "published_at": "2024-01-01T00:00:00Z"
            }
        }
        
        def mock_get_release(repo, timeout):
            return mock_releases.get(repo)
        
        with patch('core.update_checker.get_latest_release', side_effect=mock_get_release):
            results = checker.check_all_updates(versions)
        
        assert len(results) == 3
        assert results["pmhq"].has_update is True
        assert results["llonebot"].has_update is False
        assert results["app"].has_update is True
    
    def test_version_comparison_with_prerelease(self):
        """测试预发布版本的比较"""
        checker = UpdateChecker()
        
        mock_release = {
            "tag_name": "v2.0.0-beta.1",
            "name": "Release 2.0.0 Beta 1",
            "html_url": "https://github.com/test/repo/releases/tag/v2.0.0-beta.1",
            "published_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('core.update_checker.get_latest_release', return_value=mock_release):
            result = checker.check_update("test/repo", "1.0.0")
        
        # 预发布版本应该被认为比稳定版本新
        assert result.has_update is True
        assert result.latest_version == "2.0.0-beta.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
