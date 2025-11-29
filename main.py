"""QQ机器人管理器 - 主入口文件

这是应用的主入口点，负责：
1. 初始化所有管理器（ProcessManager、LogCollector、ConfigManager等）
2. 创建Flet应用实例
3. 设置应用标题、图标、窗口大小
4. 启动主窗口
5. 实现优雅的错误处理和日志记录
"""

import flet as ft
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime

from core.process_manager import ProcessManager, is_admin
from core.log_collector import LogCollector
from core.config_manager import ConfigManager
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from utils.storage import Storage
from utils.constants import (
    SETTINGS_FILE, 
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


# 配置日志系统
def setup_logging():
    """配置应用日志系统"""
    # 创建logs目录（使用应用程序所在目录）
    app_dir = get_app_dir()
    log_dir = app_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名（包含日期）
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
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
        
        # 初始化本地存储
        logger.info(f"初始化本地存储（文件: {SETTINGS_FILE}）...")
        storage = Storage(SETTINGS_FILE)
        
        logger.info("所有管理器初始化完成")
        
        return {
            'process_manager': process_manager,
            'log_collector': log_collector,
            'config_manager': config_manager,
            'version_detector': version_detector,
            'update_checker': update_checker,
            'storage': storage
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
        
        # 初始化所有管理器
        managers = initialize_managers()
        
        # 创建主窗口
        logger.info("创建主窗口...")
        main_window = MainWindow(
            process_manager=managers['process_manager'],
            log_collector=managers['log_collector'],
            config_manager=managers['config_manager'],
            version_detector=managers['version_detector'],
            update_checker=managers['update_checker'],
            storage=managers['storage']
        )
        
        # 构建UI
        logger.info("构建用户界面...")
        main_window.build(page)
        
        logger.info("应用启动成功")
        
    except Exception as e:
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
        
        page.overlay.append(error_dialog)
        error_dialog.open = True
        page.update()


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
