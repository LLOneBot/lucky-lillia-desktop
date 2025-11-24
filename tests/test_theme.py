"""测试主题配置模块"""

import pytest
import flet as ft
from ui.theme import (
    get_light_theme,
    get_dark_theme,
    apply_theme,
    toggle_theme,
    get_current_theme_mode,
    get_theme_colors,
    LIGHT_THEME,
    DARK_THEME,
)


def test_get_light_theme():
    """测试获取浅色主题"""
    theme = get_light_theme()
    assert isinstance(theme, ft.Theme)
    assert theme.use_material3 is True


def test_get_dark_theme():
    """测试获取深色主题"""
    theme = get_dark_theme()
    assert isinstance(theme, ft.Theme)
    assert theme.use_material3 is True


def test_get_theme_colors_light():
    """测试获取浅色主题颜色"""
    colors = get_theme_colors("light")
    assert colors == LIGHT_THEME
    assert colors["primary"] == "#5E35B1"
    assert colors["background"] == "#FEFBFF"


def test_get_theme_colors_dark():
    """测试获取深色主题颜色"""
    colors = get_theme_colors("dark")
    assert colors == DARK_THEME
    assert colors["primary"] == "#D0BCFF"
    assert colors["background"] == "#1C1B1E"


def test_get_theme_colors_invalid():
    """测试无效主题模式"""
    with pytest.raises(ValueError, match="Invalid theme mode"):
        get_theme_colors("invalid")


def test_theme_colors_structure():
    """测试主题颜色结构完整性"""
    required_keys = [
        "primary", "on_primary", "primary_container", "on_primary_container",
        "secondary", "on_secondary", "secondary_container", "on_secondary_container",
        "background", "on_background", "surface", "on_surface",
        "error", "on_error",
    ]
    
    for key in required_keys:
        assert key in LIGHT_THEME, f"Missing {key} in LIGHT_THEME"
        assert key in DARK_THEME, f"Missing {key} in DARK_THEME"


def test_color_format():
    """测试颜色格式正确性"""
    import re
    color_pattern = re.compile(r'^#[0-9A-F]{6}$')
    
    for color_value in LIGHT_THEME.values():
        assert color_pattern.match(color_value), f"Invalid color format: {color_value}"
    
    for color_value in DARK_THEME.values():
        assert color_pattern.match(color_value), f"Invalid color format: {color_value}"
