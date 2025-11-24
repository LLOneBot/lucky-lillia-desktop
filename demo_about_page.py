"""演示关于/版本页面"""

import flet as ft
from ui.about_page import AboutPage
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from core.config_manager import ConfigManager


def main(page: ft.Page):
    """主函数"""
    page.title = "关于页面演示"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 900
    page.window.height = 700
    
    # 创建实例
    version_detector = VersionDetector()
    update_checker = UpdateChecker()
    config_manager = ConfigManager()
    
    # 创建关于页面
    about_page = AboutPage(
        version_detector=version_detector,
        update_checker=update_checker,
        config_manager=config_manager
    )
    
    # 构建并添加到页面
    page.add(about_page.build(page))


if __name__ == "__main__":
    ft.app(target=main)
