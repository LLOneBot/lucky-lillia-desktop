"""配置页面演示脚本"""

import flet as ft
from ui.config_page import ConfigPage
from core.config_manager import ConfigManager


def main(page: ft.Page):
    """主函数"""
    page.title = "配置页面演示"
    page.window.width = 800
    page.window.height = 900
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 创建配置管理器
    config_manager = ConfigManager("demo_config.json")
    
    # 配置保存回调
    def on_config_saved(config):
        print(f"配置已保存: {config}")
    
    # 创建配置页面
    config_page = ConfigPage(config_manager, on_config_saved=on_config_saved)
    
    # 构建并添加到页面
    page.add(config_page.build())


if __name__ == "__main__":
    ft.app(target=main)
