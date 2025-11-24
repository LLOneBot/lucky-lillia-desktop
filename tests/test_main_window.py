"""测试主窗口模块"""

import pytest
from unittest.mock import Mock, MagicMock
from core.process_manager import ProcessManager
from core.log_collector import LogCollector
from core.config_manager import ConfigManager
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from utils.storage import Storage
from ui.main_window import MainWindow


@pytest.fixture
def mock_managers():
    """创建模拟的管理器实例"""
    return {
        'process_manager': Mock(spec=ProcessManager),
        'log_collector': Mock(spec=LogCollector),
        'config_manager': Mock(spec=ConfigManager),
        'version_detector': Mock(spec=VersionDetector),
        'update_checker': Mock(spec=UpdateChecker),
        'storage': Mock(spec=Storage),
    }


def test_main_window_initialization(mock_managers):
    """测试主窗口初始化"""
    main_window = MainWindow(**mock_managers)
    
    assert main_window.process_manager is not None
    assert main_window.log_collector is not None
    assert main_window.config_manager is not None
    assert main_window.version_detector is not None
    assert main_window.update_checker is not None
    assert main_window.storage is not None
    assert main_window.page is None
    assert main_window.current_page_index == 0


def test_main_window_cleanup(mock_managers):
    """测试主窗口清理逻辑"""
    main_window = MainWindow(**mock_managers)
    
    # 模拟页面
    mock_page = Mock()
    mock_page.window.width = 1200
    mock_page.window.height = 800
    main_window.page = mock_page
    
    # 执行清理
    main_window._cleanup()
    
    # 验证进程管理器的stop_all被调用
    mock_managers['process_manager'].stop_all.assert_called_once()
    
    # 验证窗口尺寸被保存
    assert mock_managers['storage'].save_setting.call_count >= 2


def test_main_window_navigation_indices(mock_managers):
    """测试导航索引对应正确的页面"""
    main_window = MainWindow(**mock_managers)
    
    # 创建模拟页面和UI组件
    mock_page = Mock()
    main_window.page = mock_page
    main_window.nav_rail = Mock()
    main_window.content_area = Mock()
    
    # 创建模拟的页面实例
    main_window.home_page = Mock()
    main_window.home_page.control = Mock()
    main_window.home_page.refresh_status = Mock()
    
    main_window.log_page = Mock()
    main_window.log_page.control = Mock()
    main_window.log_page.refresh = Mock()
    
    main_window.config_page = Mock()
    main_window.config_page.control = Mock()
    main_window.config_page.refresh = Mock()
    
    main_window.about_page = Mock()
    main_window.about_page.control = Mock()
    main_window.about_page.refresh = Mock()
    
    # 测试导航到首页
    main_window._navigate_to(0)
    assert main_window.current_page_index == 0
    main_window.home_page.refresh_status.assert_called_once()
    
    # 测试导航到日志页
    main_window._navigate_to(1)
    assert main_window.current_page_index == 1
    main_window.log_page.refresh.assert_called_once()
    
    # 测试导航到配置页
    main_window._navigate_to(2)
    assert main_window.current_page_index == 2
    main_window.config_page.refresh.assert_called_once()
    
    # 测试导航到关于页
    main_window._navigate_to(3)
    assert main_window.current_page_index == 3
    main_window.about_page.refresh.assert_called_once()


def test_storage_integration(mock_managers):
    """测试本地存储集成"""
    # 设置存储模拟返回值
    mock_managers['storage'].load_setting.side_effect = lambda key, default: {
        'window_width': 1024,
        'window_height': 768,
        'theme_mode': 'dark'
    }.get(key, default)
    
    main_window = MainWindow(**mock_managers)
    
    # 验证存储被正确使用
    assert main_window.storage is mock_managers['storage']
