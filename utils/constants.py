"""常量定义 - GitHub仓库URL、默认配置等"""

# GitHub仓库URL
GITHUB_REPOS = {
    "pmhq": "owner/pmhq",  # 替换为实际的PMHQ仓库
    "llonebot": "LLOneBot/LLOneBot",
    "app": "owner/qq-bot-manager"  # 替换为实际的应用仓库
}

# 默认配置
DEFAULT_CONFIG = {
    "qq_path": "",
    "pmhq_path": "pmhq.exe",
    "llonebot_path": "llonebot.js",
    "node_path": "node.exe",
    "auto_start_pmhq": False,
    "auto_start_llonebot": False,
    "log_level": "info",
    "port": 3000
}

# 应用设置
APP_NAME = "QQ机器人管理器"
CONFIG_FILE = "pmhq_config.json"
SETTINGS_FILE = "app_settings.json"

# 日志设置
MAX_LOG_LINES = 1000
LOG_REFRESH_INTERVAL_MS = 100

# 更新检查设置
UPDATE_CHECK_TIMEOUT = 10  # 秒

# 资源监控设置
RESOURCE_MONITOR_INTERVAL = 5  # 秒

# UI设置
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_THEME = "light"
