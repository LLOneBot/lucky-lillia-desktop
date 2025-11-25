"""首页UI组件测试"""

import pytest
from core.process_manager import ProcessManager, ProcessStatus
from core.config_manager import ConfigManager
from ui.home_page import (
    ProcessResourceCard,
    LogPreviewCard,
    HomePage
)


def test_process_resource_card_creation():
    """测试进程资源卡片创建"""
    card = ProcessResourceCard("pmhq", "PMHQ")
    assert card.process_name == "pmhq"
    assert card.display_name == "PMHQ"
    assert card.cpu_percent == 0.0
    assert card.memory_mb == 0.0
    assert card.is_running == False


def test_process_resource_card_update():
    """测试进程资源卡片更新"""
    card = ProcessResourceCard("pmhq", "PMHQ")
    card.build()
    card.update_resources(25.5, 512.0, True)
    assert card.cpu_percent == 25.5
    assert card.memory_mb == 512.0
    assert card.is_running == True


def test_log_preview_card_creation():
    """测试日志预览卡片创建"""
    card = LogPreviewCard()
    assert card.log_entries == []


def test_home_page_creation():
    """测试首页创建"""
    process_manager = ProcessManager()
    config_manager = ConfigManager()
    home_page = HomePage(process_manager, config_manager)
    assert home_page.process_manager is process_manager
    assert home_page.config_manager is config_manager


def test_log_preview_update_with_empty_logs():
    """测试空日志列表更新"""
    card = LogPreviewCard()
    card.build()
    card.update_logs([])
    assert len(card.log_entries) == 0


def test_log_preview_update_with_logs():
    """测试日志列表更新"""
    card = LogPreviewCard()
    card.build()
    
    logs = [
        {
            "timestamp": "2024-01-01 12:00:00",
            "process_name": "pmhq",
            "level": "stdout",
            "message": "Test message 1"
        },
        {
            "timestamp": "2024-01-01 12:00:01",
            "process_name": "llonebot",
            "level": "stderr",
            "message": "Test message 2"
        }
    ]
    
    card.update_logs(logs)
    assert len(card.log_entries) == 2


def test_log_preview_limits_to_10_entries():
    """测试日志预览限制为10条"""
    card = LogPreviewCard()
    card.build()
    
    # 创建15条日志
    logs = [
        {
            "timestamp": f"2024-01-01 12:00:{i:02d}",
            "process_name": "pmhq",
            "level": "stdout",
            "message": f"Test message {i}"
        }
        for i in range(15)
    ]
    
    card.update_logs(logs)
    # 应该只保留最新的10条
    assert len(card.log_entries) == 10
    # 验证是最新的10条（索引5-14）
    assert card.log_entries[0]["message"] == "Test message 5"
    assert card.log_entries[-1]["message"] == "Test message 14"
