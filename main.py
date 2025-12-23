import os
import sys
import flet as ft
import traceback
import logging
import glob
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import BaseRotatingHandler

from core.process_manager import ProcessManager, is_admin
from core.log_collector import LogCollector
from core.config_manager import ConfigManager
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from core.migration_manager import MigrationManager
from utils.constants import (
    CONFIG_FILE,
    APP_NAME, 
    DEFAULT_WINDOW_WIDTH, 
    DEFAULT_WINDOW_HEIGHT,
    MAX_LOG_LINES
)
from ui.main_window import MainWindow
from __version__ import __version__



# 获取应用程序所在目录
def get_app_dir() -> Path:
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe
        return Path(sys.executable).parent
    else:
        # 开发模式
        return Path(__file__).parent


class TimedRotatingFileHandler(BaseRotatingHandler):
    """根据配置的保留时长自动切换日志文件的Handler"""
    
    def __init__(self, log_dir: Path, config_path: str = CONFIG_FILE, encoding='utf-8'):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.config_path = config_path
        
        # 记录文件创建时间
        self._file_created_time = time.time()
        self._current_filename = self._generate_filename()
        
        # 初始文件名
        super().__init__(self._current_filename, mode='a', encoding=encoding)
    
    def _generate_filename(self) -> str:
        """生成新的日志文件名"""
        now = datetime.now()
        return str(self.log_dir / f"{now.strftime('%Y%m%d_%H%M%S')}.log")
    
    def _get_retention_seconds(self) -> int:
        """获取配置的保留时长（秒）"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('log_retention_seconds', 604800)
        except Exception:
            pass
        return 604800  # 默认7天
    
    def _get_rollover_interval(self) -> int:
        """获取轮转间隔（秒）
        
        轮转间隔 = 保留时长 / 2，确保至少有一个完整的旧文件可以被清理
        最小间隔5秒，最大间隔1天
        """
        retention = self._get_retention_seconds()
        if retention <= 0:
            return 86400  # 永久保存时，每天轮转一次
        interval = max(5, retention // 2)
        return min(interval, 86400)
    
    def shouldRollover(self, record) -> bool:
        """检查是否需要切换到新文件"""
        elapsed = time.time() - self._file_created_time
        return elapsed >= self._get_rollover_interval()
    
    def doRollover(self):
        # 关闭当前文件
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # 生成新文件名
        self._current_filename = self._generate_filename()
        self._file_created_time = time.time()
        
        # 打开新文件
        self.baseFilename = self._current_filename
        self.stream = self._open()


class ConditionalFileHandler(logging.Handler):
    """根据配置决定是否写入文件的Handler"""
    
    def __init__(self, log_dir: Path, config_path: str = CONFIG_FILE, encoding='utf-8'):
        super().__init__()
        self.log_dir = log_dir
        self.config_path = config_path
        self.encoding = encoding
        self._file_handler = None
        self._log_enabled = True
        self._last_config_check = 0
        self._config_check_interval = 5
        
        # 初始化时读取配置
        self._update_config()
        
        # 如果启用日志，创建文件handler
        if self._log_enabled:
            self._create_file_handler()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _update_config(self):
        config = self._load_config()
        self._log_enabled = config.get('log_save_enabled', True)
    
    def _create_file_handler(self):
        if self._file_handler is None:
            self._file_handler = TimedRotatingFileHandler(self.log_dir, self.config_path, encoding=self.encoding)
            self._file_handler.setFormatter(self.formatter)
    
    def emit(self, record):
        # 定期检查配置
        current_time = time.time()
        if current_time - self._last_config_check > self._config_check_interval:
            self._update_config()
            self._last_config_check = current_time
        
        if not self._log_enabled:
            return
        
        # 确保文件handler存在
        if self._file_handler is None:
            self._create_file_handler()
        
        # 委托给文件handler
        if self._file_handler:
            self._file_handler.emit(record)
    
    def setFormatter(self, fmt):
        super().setFormatter(fmt)
        if self._file_handler:
            self._file_handler.setFormatter(fmt)
    
    def close(self):
        if self._file_handler:
            self._file_handler.close()
        super().close()


class LogCleaner:
    """日志清理器 - 负责定时清理过期日志"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._stop_event = threading.Event()
        self._cleanup_thread = None
        self._app_dir = get_app_dir()
    
    def _get_cleanup_interval(self) -> int:
        """获取清理检查间隔（秒）
        
        根据配置的保留时长动态调整：
        - 保留时长 < 60秒：每5秒检查一次
        - 保留时长 < 1小时：每30秒检查一次
        - 保留时长 < 1天：每10分钟检查一次
        - 其他：每小时检查一次
        """
        _, retention_seconds = get_log_config()
        if retention_seconds <= 0:
            return 3600  # 永久保存，每小时检查一次
        elif retention_seconds < 60:
            return 5
        elif retention_seconds < 3600:
            return 30
        elif retention_seconds < 86400:
            return 600
        else:
            return 3600
    
    def start(self):
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_event.clear()
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()
    
    def stop(self):
        self._stop_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1)
    
    def _cleanup_loop(self):
        while not self._stop_event.is_set():
            self.cleanup_now()
            # 动态获取清理间隔，等待下一次清理
            interval = self._get_cleanup_interval()
            self._stop_event.wait(interval)
    
    def cleanup_now(self):
        _, retention_seconds = get_log_config()
        
        # 清理应用日志目录
        app_log_dir = self._app_dir / "logs"
        if app_log_dir.exists():
            cleanup_old_logs(app_log_dir, retention_seconds)
        
        # 清空 LLBot 日志目录（直接删除所有文件）
        llbot_log_dir = self._app_dir / "bin" / "llbot" / "data" / "logs"
        if llbot_log_dir.exists():
            cleanup_llbot_logs(llbot_log_dir)


def cleanup_old_logs(log_dir: Path, retention_seconds: int):
    """清理过期的日志文件
    
    Args:
        log_dir: 日志目录
        retention_seconds: 保留秒数，0表示永久保存
    """
    if retention_seconds <= 0:
        return  # 永久保存，不清理
    
    try:
        cutoff_time = datetime.now() - timedelta(seconds=retention_seconds)
        
        # 查找所有日志文件
        for log_file in log_dir.glob('*.log'):
            try:
                filename = log_file.stem
                file_datetime = None
                
                # 从文件名提取日期时间
                if filename.startswith('app_'):
                    # app_YYYYMMDD 格式
                    date_str = filename[4:12]
                    if len(date_str) == 8 and date_str.isdigit():
                        file_datetime = datetime.strptime(date_str, '%Y%m%d')
                elif '_' in filename:
                    # YYYYMMDD_HHMMSS 格式
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        date_str = parts[0]
                        time_str = parts[1]
                        if len(date_str) == 8 and date_str.isdigit() and len(time_str) == 6 and time_str.isdigit():
                            file_datetime = datetime.strptime(f"{date_str}{time_str}", '%Y%m%d%H%M%S')
                else:
                    # YYYYMMDD 格式
                    date_str = filename[:8]
                    if len(date_str) == 8 and date_str.isdigit():
                        file_datetime = datetime.strptime(date_str, '%Y%m%d')
                
                # 如果解析成功且已过期，尝试删除文件
                if file_datetime and file_datetime < cutoff_time:
                    try:
                        log_file.unlink()
                        print(f"已删除过期日志: {log_file.name}")
                    except PermissionError:
                        # 文件被占用，跳过（当前正在写入的文件）
                        pass
            except Exception as e:
                print(f"清理日志文件失败 {log_file}: {e}")
    except Exception as e:
        print(f"清理日志目录失败: {e}")


def cleanup_llbot_logs(log_dir: Path):
    """清空 LLBot 日志目录"""
    try:
        for log_file in log_dir.glob('*'):
            try:
                if log_file.is_file():
                    log_file.unlink()
                    print(f"已删除 LLBot 日志: {log_file.name}")
            except PermissionError:
                pass
            except Exception as e:
                print(f"清理 LLBot 日志失败 {log_file}: {e}")
    except Exception as e:
        print(f"清理 LLBot 日志目录失败: {e}")


def get_log_config() -> tuple:
    """获取日志配置
    
    Returns:
        (log_save_enabled, log_retention_seconds)
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return (
                    config.get('log_save_enabled', True),
                    config.get('log_retention_seconds', 604800)  # 默认7天
                )
    except Exception:
        pass
    return (True, 604800)


# 配置日志系统
def setup_logging():
    """配置应用日志系统"""
    # 创建logs目录（使用应用程序所在目录）
    app_dir = get_app_dir()
    log_dir = app_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 获取日志配置
    log_save_enabled, log_retention_seconds = get_log_config()
    
    # 清理过期日志并启动定时清理
    cleanup_old_logs(log_dir, log_retention_seconds)
    log_cleaner = LogCleaner()
    log_cleaner.start()
    
    # 配置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # 根据配置决定是否添加文件handler
    if log_save_enabled:
        file_handler = ConditionalFileHandler(log_dir, CONFIG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # 配置根logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger(__name__)


# 初始化日志
logger = setup_logging()


def initialize_managers():
    """初始化所有管理器
    
    Returns:
        包含所有管理器实例的字典
        
    Raises:
        Exception: 如果任何管理器初始化失败
    """
    logger.info("开始初始化管理器...")
    
    # 检查管理员权限
    if is_admin():
        logger.info("当前以管理员权限运行，可以获取PMHQ的日志输出")
    else:
        logger.info("当前以普通用户权限运行，如果PMHQ需要管理员权限，将无法获取其日志输出")
        logger.info("提示：以管理员身份运行本管理器可以获取完整的日志输出")
    
    try:
        # 初始化进程管理器
        logger.info("初始化进程管理器...")
        process_manager = ProcessManager()
        
        # 初始化日志收集器
        logger.info(f"初始化日志收集器（最大行数: {MAX_LOG_LINES}）...")
        log_collector = LogCollector(max_lines=MAX_LOG_LINES)
        
        # 初始化配置管理器
        logger.info("初始化配置管理器...")
        config_manager = ConfigManager()
        
        # 尝试加载配置（如果失败，使用默认配置）
        try:
            config = config_manager.load_config()
            logger.info("配置加载成功")
        except Exception as e:
            logger.warning(f"配置加载失败，使用默认配置: {e}")
        
        # 初始化版本检测器
        logger.info("初始化版本检测器...")
        version_detector = VersionDetector()
        
        # 初始化更新检查器
        logger.info("初始化更新检查器...")
        update_checker = UpdateChecker()
        
        logger.info("所有管理器初始化完成")
        
        return {
            'process_manager': process_manager,
            'log_collector': log_collector,
            'config_manager': config_manager,
            'version_detector': version_detector,
            'update_checker': update_checker
        }
        
    except Exception as e:
        logger.error(f"管理器初始化失败: {e}", exc_info=True)
        raise


def get_resource_path(relative_path: str) -> Path:
    """获取资源文件的绝对路径（支持 PyInstaller 打包）
    
    Args:
        relative_path: 相对路径
        
    Returns:
        资源文件的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，资源文件在 _MEIPASS 临时目录中
        base_path = Path(sys._MEIPASS)
    else:
        # 开发模式，使用当前目录
        base_path = Path(__file__).parent
    return base_path / relative_path


def get_icon_path() -> str | None:
    """获取应用图标路径
    
    Returns:
        图标文件路径，如果不存在则返回 None
    """
    icon_names = ["icon.ico", "icon.png", "icon.jpg", "icon.jpeg"]
    
    for name in icon_names:
        icon_path = get_resource_path(name)
        if icon_path.exists():
            return str(icon_path)
    
    return None


def check_and_show_migration_dialog(page: ft.Page, on_complete: callable):
    """检查并显示配置迁移对话框
    
    Args:
        page: Flet页面对象
        on_complete: 迁移完成或跳过后的回调函数
    """
    app_dir = get_app_dir()
    migration_manager = MigrationManager(app_dir)
    
    has_old_data, config_files, has_token, db_files, _ = (
        migration_manager.check_migration_needed()
    )
    
    # 只有当有需要迁移的文件时才弹窗
    if not has_old_data or (not config_files and not has_token and not db_files):
        on_complete()
        return
    
    # 构建迁移文件列表描述（使用相对路径）
    files_desc = []
    if config_files:
        for f in config_files:
            files_desc.append(f"data/{f}")
    if has_token:
        files_desc.append("data/webui_token.txt")
    if db_files:
        for f in db_files:
            files_desc.append(f"data/database/{f}")
    
    files_text = "\n".join(files_desc)
    
    def on_confirm(e):
        page.close(migration_dialog)
        success, error_msg = migration_manager.migrate_configs(config_files, has_token, db_files)
        page.overlay.clear()
        if success:
            logger.info("配置迁移成功")
            success_snackbar = ft.SnackBar(
                content=ft.Text("配置迁移成功！"),
                bgcolor=ft.Colors.GREEN_700
            )
            page.overlay.append(success_snackbar)
            success_snackbar.open = True
            page.update()
        else:
            logger.error(f"配置迁移失败: {error_msg}")
            error_snackbar = ft.SnackBar(
                content=ft.Text(f"配置迁移失败: {error_msg}"),
                bgcolor=ft.Colors.RED_700
            )
            page.overlay.append(error_snackbar)
            error_snackbar.open = True
            page.update()
        on_complete()
    
    def on_cancel(e):
        page.close(migration_dialog)
        logger.info("用户取消配置迁移")
        on_complete()
    
    migration_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("发现旧配置", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ft.Text("检测到旧版本的配置文件，是否迁移到新位置？"),
                ft.Container(height=10),
                ft.Text("将迁移以下文件:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(files_text, selectable=True),
                    bgcolor=ft.Colors.GREY_200,
                    padding=10,
                    border_radius=5,
                ),
                ft.Container(height=10),
                ft.Text(
                    "迁移后，旧文件将被删除。",
                    size=12,
                    color=ft.Colors.GREY_600
                ),
            ]),
            width=400,
        ),
        actions=[
            ft.TextButton("取消", on_click=on_cancel),
            ft.ElevatedButton("确定迁移", on_click=on_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    # 确保页面已初始化
    page.add(ft.Container())
    page.open(migration_dialog)


def main(page: ft.Page):
    """应用主入口函数
    
    Args:
        page: Flet页面对象
    """
    logger.info(f"启动 {APP_NAME} v{__version__}")
    
    try:
        # 设置页面基本属性
        page.title = f"{APP_NAME} v{__version__}"
        page.window.width = DEFAULT_WINDOW_WIDTH
        page.window.height = DEFAULT_WINDOW_HEIGHT
        page.window.min_width = 800
        page.window.min_height = 600
        
        # 设置窗口图标
        icon_path = get_icon_path()
        if icon_path:
            page.window.icon = icon_path
            logger.info(f"已设置窗口图标: {icon_path}")
        
        def continue_startup():
            """继续启动流程（迁移检查完成后调用）"""
            try:
                # 初始化所有管理器
                managers = initialize_managers()
                
                # 创建主窗口
                logger.info("创建主窗口...")
                main_window = MainWindow(
                    process_manager=managers['process_manager'],
                    log_collector=managers['log_collector'],
                    config_manager=managers['config_manager'],
                    version_detector=managers['version_detector'],
                    update_checker=managers['update_checker']
                )
                
                # 构建UI
                logger.info("构建用户界面...")
                main_window.build(page)
                
                logger.info("应用启动成功")
            except Exception as e:
                show_startup_error(page, e)
        
        # 检查配置迁移
        logger.info("检查配置迁移...")
        check_and_show_migration_dialog(page, continue_startup)
        
        return  # 让迁移对话框处理后续流程
        
    except Exception as e:
        show_startup_error(page, e)


def show_startup_error(page: ft.Page, e: Exception):
    """显示启动错误对话框
    
    Args:
        page: Flet页面对象
        e: 异常对象
    """
    # 记录错误
    logger.error(f"应用启动失败: {e}", exc_info=True)
    
    # 显示用户友好的错误对话框
    error_message = (
        f"应用启动时发生错误，请检查以下可能的原因：\n\n"
        f"• 配置文件格式是否正确\n"
        f"• 应用是否有足够的文件访问权限\n"
        f"• 依赖的库是否正确安装\n\n"
        f"错误详情：{str(e)}\n\n"
        f"完整的错误信息已记录到日志文件中。"
    )
    
    # 创建错误对话框
    error_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("启动错误", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ft.Text(error_message, selectable=True),
                ft.Divider(),
                ft.Text(
                    "技术详情（可复制）：",
                    size=12,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(
                    content=ft.Text(
                        traceback.format_exc(),
                        selectable=True,
                        size=10
                    ),
                    bgcolor=ft.Colors.GREY_200,
                    padding=10,
                    border_radius=5,
                )
            ], scroll=ft.ScrollMode.AUTO),
            width=600,
            height=400,
        ),
        actions=[
            ft.TextButton(
                "退出",
                on_click=lambda e: sys.exit(1)
            )
        ],
    )
    
    # 确保页面已初始化
    page.add(ft.Container())
    page.open(error_dialog)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info(f"启动 {APP_NAME} v{__version__}")
    logger.info("="*60)
    
    try:
        # 启动Flet应用
        ft.app(target=main)
        
    except KeyboardInterrupt:
        logger.info("应用被用户中断")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"应用启动失败: {e}", exc_info=True)
        print(f"\n应用启动失败: {e}", file=sys.stderr)
        print("\n请查看日志文件获取详细信息。", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        logger.info("应用已退出")
        logger.info("="*60)
