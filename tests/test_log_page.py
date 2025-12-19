"""日志页面UI组件测试"""

import pytest
from datetime import datetime
from core.log_collector import LogCollector, LogEntry
from ui.log_page import LogPage


def test_log_page_creation():
    """测试日志页面创建"""
    log_collector = LogCollector()
    log_page = LogPage(log_collector)
    assert log_page.log_collector is log_collector
    assert log_page.current_filter == "all"
    assert log_page.auto_scroll is True


def test_log_page_filter_change():
    """测试日志过滤器切换"""
    log_collector = LogCollector()
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 测试切换到pmhq过滤器
    log_page._set_filter("pmhq")
    assert log_page.current_filter == "pmhq"
    
    # 测试切换到llbot过滤器
    log_page._set_filter("llbot")
    assert log_page.current_filter == "llbot"
    
    # 测试切换回all过滤器
    log_page._set_filter("all")
    assert log_page.current_filter == "all"


def test_log_page_displays_empty_message():
    """测试空日志显示"""
    log_collector = LogCollector()
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 应该显示"暂无日志"
    assert len(log_page.log_column.controls) == 1


def test_log_page_displays_logs():
    """测试日志显示"""
    log_collector = LogCollector()
    
    # 添加一些日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Test message 1"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llbot",
        level="stderr",
        message="Test message 2"
    )
    
    log_collector._logs.append(entry1)
    log_collector._logs.append(entry2)
    
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 应该显示2条日志
    assert len(log_page.log_column.controls) == 2


def test_log_page_filter_by_process():
    """测试按进程过滤日志"""
    log_collector = LogCollector()
    
    # 添加不同进程的日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="PMHQ message"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llbot",
        level="stdout",
        message="LLBot message"
    )
    entry3 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Another PMHQ message"
    )
    
    log_collector._logs.append(entry1)
    log_collector._logs.append(entry2)
    log_collector._logs.append(entry3)
    
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 过滤只显示pmhq
    log_page._set_filter("pmhq")
    assert len(log_page.log_column.controls) == 2
    
    # 过滤只显示llbot
    log_page._set_filter("llbot")
    assert len(log_page.log_column.controls) == 1
    
    # 显示所有
    log_page._set_filter("all")
    assert len(log_page.log_column.controls) == 3


def test_log_page_clear_all_logs():
    """测试清空所有日志"""
    log_collector = LogCollector()
    
    # 添加日志
    entry = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Test message"
    )
    log_collector._logs.append(entry)
    
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 清空所有日志
    log_page.current_filter = "all"
    log_page._on_clear_logs(None)
    
    # 日志应该被清空
    assert len(log_collector.get_logs()) == 0
    assert len(log_page.log_column.controls) == 1  # 显示"暂无日志"


def test_log_page_clear_filtered_logs():
    """测试清空过滤的日志"""
    log_collector = LogCollector()
    
    # 添加不同进程的日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="PMHQ message"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llbot",
        level="stdout",
        message="LLBot message"
    )
    
    log_collector._logs.append(entry1)
    log_collector._logs.append(entry2)
    
    log_page = LogPage(log_collector)
    log_page.build()
    
    # 清空pmhq日志
    log_page.current_filter = "pmhq"
    log_page._on_clear_logs(None)
    
    # 只有llbot日志应该保留
    all_logs = log_collector.get_logs()
    assert len(all_logs) == 1
    assert all_logs[0].process_name == "llbot"
