"""测试主入口模块"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

from main import initialize_managers, setup_logging


class TestSetupLogging:
    """测试日志系统设置"""
    
    def test_setup_logging_creates_logger(self):
        """测试日志系统创建logger"""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "main"
    
    @patch('main.Path.mkdir')
    def test_setup_logging_creates_log_directory(self, mock_mkdir):
        """测试日志系统创建日志目录"""
        setup_logging()
        mock_mkdir.assert_called_once_with(exist_ok=True)


class TestInitializeManagers:
    """测试管理器初始化"""
    
    def test_initialize_managers_returns_all_managers(self):
        """测试初始化返回所有必需的管理器"""
        managers = initialize_managers()
        
        # 验证所有管理器都存在
        assert 'process_manager' in managers
        assert 'log_collector' in managers
        assert 'config_manager' in managers
        assert 'version_detector' in managers
        assert 'update_checker' in managers
        assert 'storage' in managers
    
    def test_initialize_managers_creates_correct_types(self):
        """测试初始化创建正确类型的管理器"""
        from core.process_manager import ProcessManager
        from core.log_collector import LogCollector
        from core.config_manager import ConfigManager
        from core.version_detector import VersionDetector
        from core.update_checker import UpdateChecker
        from utils.storage import Storage
        
        managers = initialize_managers()
        
        assert isinstance(managers['process_manager'], ProcessManager)
        assert isinstance(managers['log_collector'], LogCollector)
        assert isinstance(managers['config_manager'], ConfigManager)
        assert isinstance(managers['version_detector'], VersionDetector)
        assert isinstance(managers['update_checker'], UpdateChecker)
        assert isinstance(managers['storage'], Storage)
    
    @patch('main.ConfigManager.load_config')
    def test_initialize_managers_handles_config_load_failure(self, mock_load_config):
        """测试初始化处理配置加载失败"""
        # 模拟配置加载失败
        mock_load_config.side_effect = Exception("Config load failed")
        
        # 应该不抛出异常，而是使用默认配置
        managers = initialize_managers()
        assert managers is not None
        assert 'config_manager' in managers


class TestMainFunction:
    """测试主函数"""
    
    @patch('main.MainWindow')
    @patch('main.initialize_managers')
    def test_main_initializes_managers(self, mock_init_managers, mock_main_window):
        """测试main函数初始化管理器"""
        from main import main
        
        # 创建模拟的管理器
        mock_managers = {
            'process_manager': Mock(),
            'log_collector': Mock(),
            'config_manager': Mock(),
            'version_detector': Mock(),
            'update_checker': Mock(),
            'storage': Mock()
        }
        mock_init_managers.return_value = mock_managers
        
        # 创建模拟的页面
        mock_page = Mock()
        mock_page.window = Mock()
        
        # 调用main函数
        main(mock_page)
        
        # 验证初始化被调用
        mock_init_managers.assert_called_once()
    
    @patch('main.MainWindow')
    @patch('main.initialize_managers')
    def test_main_sets_page_properties(self, mock_init_managers, mock_main_window):
        """测试main函数设置页面属性"""
        from main import main
        from utils.constants import APP_NAME, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
        from __version__ import __version__
        
        # 创建模拟的管理器
        mock_managers = {
            'process_manager': Mock(),
            'log_collector': Mock(),
            'config_manager': Mock(),
            'version_detector': Mock(),
            'update_checker': Mock(),
            'storage': Mock()
        }
        mock_init_managers.return_value = mock_managers
        
        # 创建模拟的页面
        mock_page = Mock()
        mock_page.window = Mock()
        
        # 调用main函数
        main(mock_page)
        
        # 验证页面属性被设置
        assert mock_page.title == f"{APP_NAME} v{__version__}"
        assert mock_page.window.width == DEFAULT_WINDOW_WIDTH
        assert mock_page.window.height == DEFAULT_WINDOW_HEIGHT
        assert mock_page.window.min_width == 800
        assert mock_page.window.min_height == 600
    
    @patch('main.MainWindow')
    @patch('main.initialize_managers')
    def test_main_creates_main_window(self, mock_init_managers, mock_main_window_class):
        """测试main函数创建主窗口"""
        from main import main
        
        # 创建模拟的管理器
        mock_managers = {
            'process_manager': Mock(),
            'log_collector': Mock(),
            'config_manager': Mock(),
            'version_detector': Mock(),
            'update_checker': Mock(),
            'storage': Mock()
        }
        mock_init_managers.return_value = mock_managers
        
        # 创建模拟的主窗口实例
        mock_main_window = Mock()
        mock_main_window_class.return_value = mock_main_window
        
        # 创建模拟的页面
        mock_page = Mock()
        mock_page.window = Mock()
        
        # 调用main函数
        main(mock_page)
        
        # 验证MainWindow被创建
        mock_main_window_class.assert_called_once_with(
            process_manager=mock_managers['process_manager'],
            log_collector=mock_managers['log_collector'],
            config_manager=mock_managers['config_manager'],
            version_detector=mock_managers['version_detector'],
            update_checker=mock_managers['update_checker'],
            storage=mock_managers['storage']
        )
        
        # 验证build方法被调用
        mock_main_window.build.assert_called_once_with(mock_page)
    
    @patch('main.initialize_managers')
    def test_main_handles_initialization_error(self, mock_init_managers):
        """测试main函数处理初始化错误"""
        from main import main
        import flet as ft
        
        # 模拟初始化失败
        mock_init_managers.side_effect = Exception("Initialization failed")
        
        # 创建模拟的页面
        mock_page = Mock()
        mock_page.window = Mock()
        mock_page.overlay = []
        
        # 调用main函数（应该不抛出异常）
        main(mock_page)
        
        # 验证错误对话框被添加到overlay
        assert len(mock_page.overlay) > 0
        error_dialog = mock_page.overlay[0]
        assert hasattr(error_dialog, 'open')
        assert error_dialog.open is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestProcessManager:
    """测试进程管理器"""
    
    def test_get_pid_returns_none_when_no_process(self):
        """测试没有进程时get_pid返回None"""
        from core.process_manager import ProcessManager
        
        pm = ProcessManager()
        assert pm.get_pid("pmhq") is None
        assert pm.get_pid("llbot") is None
    
    def test_get_all_pids_returns_dict(self):
        """测试get_all_pids返回字典"""
        from core.process_manager import ProcessManager
        
        pm = ProcessManager()
        pids = pm.get_all_pids()
        
        assert isinstance(pids, dict)
        assert "pmhq" in pids
        assert "llbot" in pids
        assert pids["pmhq"] is None
        assert pids["llbot"] is None
    
    def test_get_process_status_default_stopped(self):
        """测试默认进程状态为STOPPED"""
        from core.process_manager import ProcessManager, ProcessStatus
        
        pm = ProcessManager()
        assert pm.get_process_status("pmhq") == ProcessStatus.STOPPED
        assert pm.get_process_status("llbot") == ProcessStatus.STOPPED
    
    def test_stop_all_handles_empty_processes(self):
        """测试stop_all处理空进程列表"""
        from core.process_manager import ProcessManager
        
        pm = ProcessManager()
        # 应该不抛出异常
        pm.stop_all()
