"""常量定义 - GitHub仓库URL、默认配置等"""

# GitHub仓库URL
GITHUB_REPOS = {
    "pmhq": "linyuchen/pmhq",
    "llonebot": "LLOneBot/LLOneBot",
    "app": "LLOneBot/lucky-lillia-desktop"
}

# 默认配置
DEFAULT_CONFIG = {
    "qq_path": "",
    "pmhq_path": "bin/pmhq/pmhq-win-x64.exe",
    "llonebot_path": "llonebot.js",
    "node_path": "node.exe",
    "auto_start_pmhq": False,
    "auto_start_llonebot": False,
    "log_level": "info",
    "port": 3000,
    "github_repos": {
        "pmhq": "linyuchen/pmhq",
        "llonebot": "LLOneBot/LLOneBot",
        "app": "LLOneBot/lucky-lillia-desktop"
    }
}

# 应用设置
APP_NAME = "幸运莉莉娅"
CONFIG_FILE = "pmhq_config.json"
SETTINGS_FILE = "app_settings.json"

# PMHQ路径设置
PMHQ_DIR = "bin/pmhq"
PMHQ_EXECUTABLE = "pmhq-win-x64.exe"

# 日志设置
MAX_LOG_LINES = 1000
LOG_REFRESH_INTERVAL_MS = 100

# 更新检查设置
UPDATE_CHECK_TIMEOUT = 10  # 秒

# GitHub镜像列表（用于加速访问）
GITHUB_MIRRORS = [
    "https://gh-proxy.com/https://github.com/",
    "https://github.com/",
    
]

# 资源监控设置
RESOURCE_MONITOR_INTERVAL = 5  # 秒

# UI设置
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_THEME = "light"
