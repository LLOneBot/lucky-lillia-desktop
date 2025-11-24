"""测试关于/版本页面UI"""

import pytest
import flet as ft
from unittest.mock import Mock, MagicMock, patch
from ui.about_page import AboutPage, VersionInfoCard
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker, UpdateInfo
from core.config_manager import ConfigManager


class TestVersionInfoCard:
    """测试版本信息卡片组件"""
    
    def test_build_creates_card(self):
        """测试构建卡片"""
        card = VersionInfoCard("app", "测试应用")
        control = card.build()
        
        assert control is not None
        assert isinstance(control, ft.Card)
        assert card.current_version == "未知"
    
    def test_update_version(self):
        """测试更新版本显示"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        card.update_version("1.2.3")
        assert card.current_version == "1.2.3"
        assert "1.2.3" in card.version_text.value
    
    def test_update_version_with_none(self):
        """测试更新版本为None"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        card.update_version(None)
        assert card.current_version == "未知"
    
    def test_update_check_result_with_update(self):
        """测试有更新可用的情况"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        update_info = UpdateInfo(
            has_update=True,
            current_version="1.0.0",
            latest_version="2.0.0",
            release_url="https://github.com/test/repo/releases/tag/v2.0.0"
        )
        
        card.update_check_result(update_info)
        
        assert card.has_update is True
        assert card.latest_version == "2.0.0"
        assert card.update_status.visible is True
    
    def test_update_check_result_no_update(self):
        """测试已是最新版本的情况"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        update_info = UpdateInfo(
            has_update=False,
            current_version="2.0.0",
            latest_version="2.0.0",
            release_url=""
        )
        
        card.update_check_result(update_info)
        
        assert card.has_update is False
        assert card.update_status.visible is True
    
    def test_update_check_result_with_error(self):
        """测试检查更新失败的情况"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        update_info = UpdateInfo(
            has_update=False,
            current_version="1.0.0",
            latest_version="未知",
            release_url="",
            error="网络连接失败"
        )
        
        card.update_check_result(update_info)
        
        assert card.update_status.visible is True
    
    def test_clear_update_status(self):
        """测试清除更新状态"""
        card = VersionInfoCard("app", "测试应用")
        card.build()
        
        update_info = UpdateInfo(
            has_update=True,
            current_version="1.0.0",
            latest_version="2.0.0",
            release_url="https://github.com/test/repo"
        )
        card.update_check_result(update_info)
        
        card.clear_update_status()
        
        assert card.update_status.visible is False
        assert card.latest_version is None
        assert card.has_update is False


class TestAboutPage:
    """测试关于/版本页面组件"""
    
    @pytest.fixture
    def mock_version_detector(self):
        """创建模拟的版本检测器"""
        detector = Mock(spec=VersionDetector)
        detector.get_app_version.return_value = "1.0.0"
        detector.detect_pmhq_version.return_value = "2.0.0"
        detector.detect_llonebot_version.return_value = "3.0.0"
        return detector
    
    @pytest.fixture
    def mock_update_checker(self):
        """创建模拟的更新检查器"""
        checker = Mock(spec=UpdateChecker)
        return checker
    
    @pytest.fixture
    def mock_config_manager(self):
        """创建模拟的配置管理器"""
        manager = Mock(spec=ConfigManager)
        manager.load_config.return_value = {
            "pmhq_path": "pmhq.exe",
            "llonebot_path": "llonebot.js"
        }
        return manager
    
    def test_build_creates_page(self, mock_version_detector, mock_update_checker):
        """测试构建页面"""
        page = Mock(spec=ft.Page)
        about_page = AboutPage(mock_version_detector, mock_update_checker)
        
        control = about_page.build(page)
        
        assert control is not None
        assert isinstance(control, ft.Container)
        assert about_page.app_card is not None
        assert about_page.pmhq_card is not None
        assert about_page.llonebot_card is not None
    
    def test_load_versions(self, mock_version_detector, mock_update_checker, mock_config_manager):
        """测试加载版本信息"""
        page = Mock(spec=ft.Page)
        about_page = AboutPage(
            mock_version_detector,
            mock_update_checker,
            mock_config_manager
        )
        about_page.build(page)
        
        # 验证版本检测器被调用
        mock_version_detector.get_app_version.assert_called_once()
        mock_version_detector.detect_pmhq_version.assert_called_once()
        mock_version_detector.detect_llonebot_version.assert_called_once()
        
        # 验证版本信息被更新
        assert about_page.app_card.current_version == "1.0.0"
        assert about_page.pmhq_card.current_version == "2.0.0"
        assert about_page.llonebot_card.current_version == "3.0.0"
    
    def test_load_versions_without_config_manager(self, mock_version_detector, mock_update_checker):
        """测试没有配置管理器时加载版本"""
        page = Mock(spec=ft.Page)
        about_page = AboutPage(mock_version_detector, mock_update_checker)
        about_page.build(page)
        
        # 应该使用空路径调用版本检测
        mock_version_detector.detect_pmhq_version.assert_called_once_with("")
        mock_version_detector.detect_llonebot_version.assert_called_once_with("")
    
    def test_check_update_button_exists(self, mock_version_detector, mock_update_checker):
        """测试检查更新按钮存在"""
        page = Mock(spec=ft.Page)
        about_page = AboutPage(mock_version_detector, mock_update_checker)
        about_page.build(page)
        
        assert about_page.check_update_button is not None
        assert isinstance(about_page.check_update_button, ft.ElevatedButton)
    
    def test_refresh_reloads_versions(self, mock_version_detector, mock_update_checker):
        """测试刷新重新加载版本信息"""
        page = Mock(spec=ft.Page)
        about_page = AboutPage(mock_version_detector, mock_update_checker)
        about_page.build(page)
        
        # 重置调用计数
        mock_version_detector.get_app_version.reset_mock()
        
        # 调用刷新
        about_page.refresh()
        
        # 验证版本检测器再次被调用
        mock_version_detector.get_app_version.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
