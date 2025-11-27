"""常量定义 - NPM包名、默认配置等"""

# NPM包名配置
NPM_PACKAGES = {
    "pmhq": "pmhq-dist-win-x64",
    "llonebot": "llonebot-dist",
    "node": "llonebot-node-win-x64",
    "ffmpeg": "llonebot-ffmpeg-win-x64",
    "app": "lucky-lillia-desktop-win-x64"
}

# GitHub仓库URL（保留用于查看详情链接）
GITHUB_REPOS = {
    "pmhq": "linyuchen/pmhq",
    "llonebot": "LLOneBot/LLOneBot",
    "app": "LLOneBot/lucky-lillia-desktop"
}

# 默认配置
DEFAULT_CONFIG = {
    "qq_path": "",
    "pmhq_path": "bin/pmhq/pmhq-win-x64.exe",
    "llonebot_path": "bin/llonebot/llonebot.js",
    "node_path": "bin/llonebot/node.exe",
    "ffmpeg_path": "bin/llonebot/ffmpeg.exe",
    "ffprobe_path": "bin/llonebot/ffprobe.exe",
    "auto_start_pmhq": False,
    "auto_start_llonebot": False,
    "log_level": "info",
    "port": 3000,
    "npm_packages": {
        "pmhq": "pmhq",
        "llonebot": "llonebot",
        "app": "lucky-lillia-desktop"
    }
}

# 应用设置
APP_NAME = "幸运莉莉娅"
CONFIG_FILE = "pmhq_config.json"
SETTINGS_FILE = "app_settings.json"

# PMHQ路径设置
PMHQ_DIR = "bin/pmhq"
PMHQ_EXECUTABLE = "pmhq-win-x64.exe"

# LLOneBot路径设置
LLONEBOT_DIR = "bin/llonebot"
LLONEBOT_MAIN = "llonebot.js"

# 日志设置
MAX_LOG_LINES = 1000
LOG_REFRESH_INTERVAL_MS = 100

# 更新检查设置
UPDATE_CHECK_TIMEOUT = 10  # 秒

# GitHub镜像列表（用于加速访问，保留用于兼容）
GITHUB_MIRRORS = [
    "https://ghfast.top/https://github.com/",
    "https://gh-proxy.com/https://github.com/",
    "https://mirror.ghproxy.com/https://github.com/",
    "https://github.com/",
]

# NPM Registry镜像列表（用于加速访问）
NPM_REGISTRY_MIRRORS = [
    "https://registry.npmjs.org",       # 官方源
    "https://registry.npmmirror.com",  # 淘宝镜像
]

# 资源监控设置
RESOURCE_MONITOR_INTERVAL = 5  # 秒

# UI设置
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_THEME = "light"
