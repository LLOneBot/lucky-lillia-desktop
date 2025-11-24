"""本地持久化存储模块 - 使用JSON文件存储应用设置"""

import json
import os
from typing import Any, Optional
from pathlib import Path


class Storage:
    """本地存储管理器，用于持久化应用设置"""
    
    def __init__(self, storage_file: str = "app_settings.json"):
        """初始化存储管理器
        
        Args:
            storage_file: 存储文件路径
        """
        self.storage_file = Path(storage_file)
        self._settings = {}
        self._load_all_settings()
    
    def _load_all_settings(self) -> None:
        """从文件加载所有设置到内存"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # 文件读取失败时使用空字典
                self._settings = {}
        else:
            self._settings = {}
    
    def _save_all_settings(self) -> bool:
        """将所有设置保存到文件
        
        Returns:
            保存成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            # 文件写入失败
            return False
    
    def save_setting(self, key: str, value: Any) -> bool:
        """保存单个设置项
        
        Args:
            key: 设置项的键
            value: 设置项的值（必须是JSON可序列化的）
            
        Returns:
            保存成功返回True，失败返回False
        """
        try:
            # 验证值是否可以JSON序列化
            json.dumps(value)
            
            # 更新内存中的设置
            self._settings[key] = value
            
            # 保存到文件
            return self._save_all_settings()
        except (TypeError, ValueError):
            # 值不可序列化
            return False
    
    def load_setting(self, key: str, default: Any = None) -> Any:
        """加载单个设置项
        
        Args:
            key: 设置项的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            设置项的值，如果不存在则返回default
        """
        return self._settings.get(key, default)
    
    def delete_setting(self, key: str) -> bool:
        """删除单个设置项
        
        Args:
            key: 设置项的键
            
        Returns:
            删除成功返回True，键不存在或保存失败返回False
        """
        if key in self._settings:
            del self._settings[key]
            return self._save_all_settings()
        return False
    
    def clear_all_settings(self) -> bool:
        """清空所有设置
        
        Returns:
            清空成功返回True，失败返回False
        """
        self._settings = {}
        return self._save_all_settings()
    
    def get_all_settings(self) -> dict:
        """获取所有设置的副本
        
        Returns:
            包含所有设置的字典
        """
        return self._settings.copy()
