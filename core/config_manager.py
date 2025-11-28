"""配置管理模块 - 负责读写和验证pmhq_config.json文件"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from utils.constants import DEFAULT_CONFIG, CONFIG_FILE


class ConfigError(Exception):
    """配置相关错误"""
    pass


class ConfigManager:
    """管理PMHQ配置文件"""
    
    def __init__(self, config_path: str = CONFIG_FILE):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典，如果文件不存在则返回默认配置
            
        Raises:
            ConfigError: 配置文件格式无效
        """
        # 如果文件不存在，返回默认配置
        if not os.path.exists(self.config_path):
            return self.get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置格式
            is_valid, error_msg = self.validate_config(config)
            if not is_valid:
                raise ConfigError(f"配置文件格式无效: {error_msg}")
            
            return config
        
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件JSON格式错误: {str(e)}")
        except IOError as e:
            raise ConfigError(f"无法读取配置文件: {str(e)}")
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件
        
        Args:
            config: 配置字典
            
        Returns:
            保存成功返回True，失败返回False
        """
        # 验证配置
        is_valid, error_msg = self.validate_config(config)
        if not is_valid:
            return False
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证配置有效性
        
        Returns:
            (是否有效, 错误消息)
        """
        if not isinstance(config, dict):
            return False, "配置必须是字典类型"
        
        # 检查必需字段
        required_fields = ["qq_path", "pmhq_path", "llonebot_path", "node_path"]
        for field in required_fields:
            if field not in config:
                return False, f"缺少必需字段: {field}"
        
        # 检查字段类型
        string_fields = ["qq_path", "pmhq_path", "llonebot_path", "node_path", "log_level"]
        for field in string_fields:
            if field in config and not isinstance(config[field], str):
                return False, f"字段 {field} 必须是字符串类型"
        
        bool_fields = ["auto_start_pmhq", "auto_start_llonebot", "auto_start_bot", "headless"]
        for field in bool_fields:
            if field in config and not isinstance(config[field], bool):
                return False, f"字段 {field} 必须是布尔类型"
        
        if "port" in config and not isinstance(config["port"], int):
            return False, "字段 port 必须是整数类型"
        
        # 验证路径有效性（对于非空路径）
        path_fields = ["qq_path", "pmhq_path", "llonebot_path", "node_path"]
        for field in path_fields:
            path_value = config.get(field, "")
            if path_value:  # 只验证非空路径
                is_valid, error = self._validate_path(path_value, field)
                if not is_valid:
                    return False, error
        
        return True, ""
    
    def _validate_path(self, path: str, field_name: str) -> Tuple[bool, str]:
        """验证路径是否指向有效的可执行文件
        
        Args:
            path: 文件路径
            field_name: 字段名称（用于错误消息）
            
        Returns:
            (是否有效, 错误消息)
        """
        # 对于可执行文件，检查扩展名（即使文件不存在也要检查）
        path_obj = Path(path)
        if field_name in ["pmhq_path", "node_path"]:
            # Windows可执行文件应该是.exe
            if os.name == 'nt' and path_obj.suffix.lower() != '.exe':
                return False, f"{field_name} 必须是.exe文件: {path}"
        elif field_name == "llonebot_path":
            # LLOneBot应该是.js文件
            if path_obj.suffix.lower() != '.js':
                return False, f"{field_name} 必须是.js文件: {path}"
        
        # 如果路径存在，检查是否是文件
        if os.path.exists(path):
            if not os.path.isfile(path):
                return False, f"{field_name} 必须指向文件而非目录: {path}"
        
        return True, ""
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return DEFAULT_CONFIG.copy()
