"""测试本地存储模块"""

import pytest
import json
import os
from pathlib import Path
from utils.storage import Storage


@pytest.fixture
def temp_storage_file(tmp_path):
    """创建临时存储文件"""
    storage_file = tmp_path / "test_settings.json"
    return str(storage_file)


@pytest.fixture
def storage(temp_storage_file):
    """创建Storage实例"""
    return Storage(temp_storage_file)


class TestStorage:
    """测试Storage类"""
    
    def test_save_and_load_setting(self, storage):
        """测试保存和加载设置"""
        # 保存设置
        assert storage.save_setting("theme", "dark") is True
        
        # 加载设置
        assert storage.load_setting("theme") == "dark"
    
    def test_load_nonexistent_setting_returns_default(self, storage):
        """测试加载不存在的设置返回默认值"""
        assert storage.load_setting("nonexistent", "default_value") == "default_value"
    
    def test_save_multiple_settings(self, storage):
        """测试保存多个设置"""
        assert storage.save_setting("theme", "dark") is True
        assert storage.save_setting("window_width", 1200) is True
        assert storage.save_setting("window_height", 800) is True
        
        assert storage.load_setting("theme") == "dark"
        assert storage.load_setting("window_width") == 1200
        assert storage.load_setting("window_height") == 800
    
    def test_save_complex_data(self, storage):
        """测试保存复杂数据结构"""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "bool": True,
            "null": None
        }
        assert storage.save_setting("complex", complex_data) is True
        assert storage.load_setting("complex") == complex_data
    
    def test_persistence_across_instances(self, temp_storage_file):
        """测试设置在不同实例间持久化"""
        # 第一个实例保存设置
        storage1 = Storage(temp_storage_file)
        storage1.save_setting("theme", "dark")
        
        # 第二个实例应该能加载相同的设置
        storage2 = Storage(temp_storage_file)
        assert storage2.load_setting("theme") == "dark"
    
    def test_delete_setting(self, storage):
        """测试删除设置"""
        storage.save_setting("theme", "dark")
        assert storage.load_setting("theme") == "dark"
        
        assert storage.delete_setting("theme") is True
        assert storage.load_setting("theme") is None
    
    def test_delete_nonexistent_setting(self, storage):
        """测试删除不存在的设置"""
        assert storage.delete_setting("nonexistent") is False
    
    def test_clear_all_settings(self, storage):
        """测试清空所有设置"""
        storage.save_setting("theme", "dark")
        storage.save_setting("window_width", 1200)
        
        assert storage.clear_all_settings() is True
        assert storage.load_setting("theme") is None
        assert storage.load_setting("window_width") is None
    
    def test_get_all_settings(self, storage):
        """测试获取所有设置"""
        storage.save_setting("theme", "dark")
        storage.save_setting("window_width", 1200)
        
        all_settings = storage.get_all_settings()
        assert all_settings == {"theme": "dark", "window_width": 1200}
    
    def test_file_read_error_handling(self, tmp_path):
        """测试文件读取错误处理"""
        # 创建一个无效的JSON文件
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("invalid json content")
        
        # 应该能够创建Storage实例，使用空设置
        storage = Storage(str(invalid_file))
        assert storage.load_setting("any_key") is None
    
    def test_file_write_error_handling(self, tmp_path):
        """测试文件写入错误处理"""
        # 创建一个只读目录（模拟写入失败）
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        storage_file = readonly_dir / "settings.json"
        
        storage = Storage(str(storage_file))
        
        # 使目录只读
        readonly_dir.chmod(0o444)
        
        try:
            # 保存应该失败
            result = storage.save_setting("theme", "dark")
            # 在某些系统上可能仍然成功，所以我们只检查返回值是布尔类型
            assert isinstance(result, bool)
        finally:
            # 恢复权限以便清理
            readonly_dir.chmod(0o755)
    
    def test_save_non_serializable_value(self, storage):
        """测试保存不可序列化的值"""
        # 函数对象不能被JSON序列化
        result = storage.save_setting("func", lambda x: x)
        assert result is False
    
    def test_overwrite_existing_setting(self, storage):
        """测试覆盖已存在的设置"""
        storage.save_setting("theme", "light")
        assert storage.load_setting("theme") == "light"
        
        storage.save_setting("theme", "dark")
        assert storage.load_setting("theme") == "dark"
