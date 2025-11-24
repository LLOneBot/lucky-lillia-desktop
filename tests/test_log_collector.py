"""日志收集器测试"""

import pytest
from datetime import datetime
from core.log_collector import LogCollector, LogEntry


def test_log_collector_creation():
    """测试日志收集器创建"""
    collector = LogCollector(max_lines=1000)
    assert collector.max_lines == 1000
    assert len(collector.get_logs()) == 0


def test_log_collector_custom_max_lines():
    """测试自定义最大行数"""
    collector = LogCollector(max_lines=500)
    assert collector.max_lines == 500


def test_get_all_logs():
    """测试获取所有日志"""
    collector = LogCollector()
    
    # 添加日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Message 1"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llonebot",
        level="stderr",
        message="Message 2"
    )
    
    collector._logs.append(entry1)
    collector._logs.append(entry2)
    
    logs = collector.get_logs()
    assert len(logs) == 2
    assert logs[0].message == "Message 1"
    assert logs[1].message == "Message 2"


def test_get_logs_by_process():
    """测试按进程名获取日志"""
    collector = LogCollector()
    
    # 添加不同进程的日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="PMHQ message"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llonebot",
        level="stdout",
        message="LLOneBot message"
    )
    entry3 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Another PMHQ message"
    )
    
    collector._logs.append(entry1)
    collector._logs.append(entry2)
    collector._logs.append(entry3)
    
    # 获取pmhq日志
    pmhq_logs = collector.get_logs("pmhq")
    assert len(pmhq_logs) == 2
    assert all(log.process_name == "pmhq" for log in pmhq_logs)
    
    # 获取llonebot日志
    llonebot_logs = collector.get_logs("llonebot")
    assert len(llonebot_logs) == 1
    assert llonebot_logs[0].process_name == "llonebot"


def test_clear_all_logs():
    """测试清空所有日志"""
    collector = LogCollector()
    
    # 添加日志
    entry = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Test message"
    )
    collector._logs.append(entry)
    
    # 清空所有日志
    collector.clear_logs()
    
    assert len(collector.get_logs()) == 0


def test_clear_logs_by_process():
    """测试按进程清空日志"""
    collector = LogCollector()
    
    # 添加不同进程的日志
    entry1 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="PMHQ message"
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        process_name="llonebot",
        level="stdout",
        message="LLOneBot message"
    )
    entry3 = LogEntry(
        timestamp=datetime.now(),
        process_name="pmhq",
        level="stdout",
        message="Another PMHQ message"
    )
    
    collector._logs.append(entry1)
    collector._logs.append(entry2)
    collector._logs.append(entry3)
    
    # 清空pmhq日志
    collector.clear_logs("pmhq")
    
    # 只有llonebot日志应该保留
    remaining_logs = collector.get_logs()
    assert len(remaining_logs) == 1
    assert remaining_logs[0].process_name == "llonebot"


def test_callback_registration():
    """测试回调函数注册"""
    collector = LogCollector()
    
    called = []
    
    def callback(entry: LogEntry):
        called.append(entry)
    
    collector.set_callback(callback)
    
    # 验证回调已注册
    assert len(collector._callbacks) == 1


def test_log_entry_dataclass():
    """测试LogEntry数据类"""
    timestamp = datetime.now()
    entry = LogEntry(
        timestamp=timestamp,
        process_name="pmhq",
        level="stdout",
        message="Test message"
    )
    
    assert entry.timestamp == timestamp
    assert entry.process_name == "pmhq"
    assert entry.level == "stdout"
    assert entry.message == "Test message"
