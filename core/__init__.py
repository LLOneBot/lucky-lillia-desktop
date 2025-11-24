"""核心模块 - 包含业务逻辑组件"""

from .config_manager import ConfigManager, ConfigError
from .process_manager import ProcessManager, ProcessStatus
from .version_detector import VersionDetector

__all__ = ['ConfigManager', 'ConfigError', 'ProcessManager', 'ProcessStatus', 'VersionDetector']
