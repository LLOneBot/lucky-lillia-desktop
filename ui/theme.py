"""主题配置模块"""

import flet as ft
from typing import Dict, Any


# 浅色主题配色方案 - 优化对比度和可读性
LIGHT_THEME = {
    "primary": "#5E35B1",  # 更深的紫色，提高对比度
    "on_primary": "#FFFFFF",
    "primary_container": "#E8DDFF",
    "on_primary_container": "#1A0050",
    
    "secondary": "#5D5570",
    "on_secondary": "#FFFFFF",
    "secondary_container": "#E5DEF7",
    "on_secondary_container": "#1A1625",
    
    "tertiary": "#7D4E5F",
    "on_tertiary": "#FFFFFF",
    "tertiary_container": "#FFD7E3",
    "on_tertiary_container": "#2F0F1C",
    
    "error": "#BA1A1A",
    "on_error": "#FFFFFF",
    "error_container": "#FFDAD6",
    "on_error_container": "#410002",
    
    "background": "#FEFBFF",
    "on_background": "#1C1B1E",
    "surface": "#FEFBFF",
    "on_surface": "#1C1B1E",
    "surface_variant": "#E4E1EC",
    "on_surface_variant": "#47464F",
    
    "outline": "#78767F",
    "outline_variant": "#C9C5D0",
    "shadow": "#000000",
    "scrim": "#000000",
    "inverse_surface": "#313034",
    "inverse_on_surface": "#F4EFF4",
    "inverse_primary": "#CFBCFF",
}


# 深色主题配色方案 - 优化对比度和可读性
DARK_THEME = {
    "primary": "#D0BCFF",
    "on_primary": "#381E72",
    "primary_container": "#4F378B",
    "on_primary_container": "#EADDFF",
    
    "secondary": "#CCC2DC",
    "on_secondary": "#332D41",
    "secondary_container": "#4A4458",
    "on_secondary_container": "#E8DEF8",
    
    "tertiary": "#EFB8C8",
    "on_tertiary": "#492532",
    "tertiary_container": "#633B48",
    "on_tertiary_container": "#FFD8E4",
    
    "error": "#FFB4AB",
    "on_error": "#690005",
    "error_container": "#93000A",
    "on_error_container": "#FFDAD6",
    
    "background": "#1C1B1E",
    "on_background": "#E6E1E6",
    "surface": "#1C1B1E",
    "on_surface": "#E6E1E6",
    "surface_variant": "#49454E",
    "on_surface_variant": "#CAC4CF",
    
    "outline": "#948F99",
    "outline_variant": "#49454E",
    "shadow": "#000000",
    "scrim": "#000000",
    "inverse_surface": "#E6E1E6",
    "inverse_on_surface": "#313034",
    "inverse_primary": "#5E35B1",
}


# 全局字体配置 - 微软雅黑
FONT_FAMILY = "Microsoft YaHei"


def get_light_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=LIGHT_THEME["primary"],
        use_material3=True,
        font_family=FONT_FAMILY,
    )


def get_dark_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=DARK_THEME["primary"],
        use_material3=True,
        font_family=FONT_FAMILY,
    )


def apply_theme(page: ft.Page, theme_mode: str) -> None:
    if theme_mode not in ["light", "dark"]:
        raise ValueError(f"Invalid theme mode: {theme_mode}. Must be 'light' or 'dark'")
    
    # 注册系统字体
    page.fonts = {
        "Microsoft YaHei": "Microsoft YaHei",
    }
    
    page.theme = get_light_theme()
    page.dark_theme = get_dark_theme()
    page.theme_mode = ft.ThemeMode.LIGHT if theme_mode == "light" else ft.ThemeMode.DARK
    page.update()


def toggle_theme(page: ft.Page) -> str:
    current_mode = page.theme_mode
    
    if current_mode == ft.ThemeMode.LIGHT:
        new_mode = "dark"
        page.theme_mode = ft.ThemeMode.DARK
    else:
        new_mode = "light"
        page.theme_mode = ft.ThemeMode.LIGHT
    
    page.update()
    return new_mode


def get_current_theme_mode(page: ft.Page) -> str:
    return "light" if page.theme_mode == ft.ThemeMode.LIGHT else "dark"


def get_theme_colors(theme_mode: str) -> Dict[str, str]:
    if theme_mode == "light":
        return LIGHT_THEME.copy()
    elif theme_mode == "dark":
        return DARK_THEME.copy()
    else:
        raise ValueError(f"Invalid theme mode: {theme_mode}. Must be 'light' or 'dark'")
