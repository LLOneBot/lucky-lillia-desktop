"""配置页面UI测试"""

import pytest
import flet as ft
from ui.config_page import ConfigPage
from core.config_manager import ConfigManager
import tempfile
import os


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    # 清理
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def config_manager(temp_config_file):
    """创建配置管理器实例"""
    return ConfigManager(temp_config_file)


def test_config_page_initialization(config_manager):
    """测试配置页面初始化"""
    page = ConfigPage(config_manager)
    assert page.config_manager == config_manager
    assert page.control is None
    assert page.current_config == {}


def test_config_page_build(config_manager):
    """测试配置页面构建"""
    page = ConfigPage(config_manager)
    control = page.build()
    
    assert control is not None
    assert page.control is not None
    assert isinstance(page.current_config, dict)
    
    # 验证输入字段已创建
    assert page.qq_path_field is not None
    assert page.pmhq_path_field is not None
    assert page.llbot_path_field is not None
    assert page.node_path_field is not None
    assert page.auto_start_pmhq_checkbox is not None
    assert page.auto_start_llbot_checkbox is not None
    assert page.log_level_dropdown is not None
    assert page.port_field is not None


def test_config_page_loads_default_config(config_manager):
    """测试配置页面加载默认配置"""
    page = ConfigPage(config_manager)
    page.build()
    
    # 验证加载了默认配置
    assert page.pmhq_path_field.value == "bin/pmhq/pmhq-win-x64.exe"
    assert page.llbot_path_field.value == "bin/llbot/llbot.js"
    assert page.node_path_field.value == "bin/llbot/node.exe"
    assert page.ffmpeg_path_field.value == "bin/llbot/ffmpeg.exe"
    assert page.ffprobe_path_field.value == "bin/llbot/ffprobe.exe"
    assert page.auto_start_pmhq_checkbox.value == False
    assert page.auto_start_llbot_checkbox.value == False
    assert page.log_level_dropdown.value == "info"
    assert page.port_field.value == "3000"


def test_config_page_loads_existing_config(config_manager):
    """测试配置页面加载现有配置"""
    # 保存一个配置
    test_config = {
        "qq_path": "/path/to/qq.exe",
        "pmhq_path": "/path/to/pmhq.exe",
        "llbot_path": "/path/to/llbot.js",
        "node_path": "/path/to/node.exe",
        "auto_start_pmhq": True,
        "auto_start_llbot": True,
        "log_level": "debug",
        "port": 8080
    }
    config_manager.save_config(test_config)
    
    # 创建页面并构建
    page = ConfigPage(config_manager)
    page.build()
    
    # 验证加载了保存的配置
    assert page.qq_path_field.value == "/path/to/qq.exe"
    assert page.pmhq_path_field.value == "/path/to/pmhq.exe"
    assert page.llbot_path_field.value == "/path/to/llbot.js"
    assert page.node_path_field.value == "/path/to/node.exe"
    assert page.auto_start_pmhq_checkbox.value == True
    assert page.auto_start_llbot_checkbox.value == True
    assert page.log_level_dropdown.value == "debug"
    assert page.port_field.value == "8080"


def test_config_page_reset_to_default(config_manager):
    """测试重置为默认配置"""
    page = ConfigPage(config_manager)
    page.build()
    
    # 修改一些字段
    page.qq_path_field.value = "/custom/path.exe"
    page.auto_start_pmhq_checkbox.value = True
    page.port_field.value = "9999"
    
    # 重置
    page._on_reset_config(None)
    
    # 验证已重置为默认值
    assert page.qq_path_field.value == ""
    assert page.pmhq_path_field.value == "bin/pmhq/pmhq-win-x64.exe"
    assert page.auto_start_pmhq_checkbox.value == False
    assert page.port_field.value == "3000"


def test_config_page_show_error(config_manager):
    """测试显示错误提示"""
    page = ConfigPage(config_manager)
    page.build()
    
    # 初始状态
    assert page.error_text.visible == False
    assert page.success_text.visible == False
    
    # 显示错误
    page._show_error("测试错误")
    
    assert page.error_text.visible == True
    assert page.error_text.value == "测试错误"
    assert page.success_text.visible == False


def test_config_page_show_success(config_manager):
    """测试显示成功提示"""
    page = ConfigPage(config_manager)
    page.build()
    
    # 初始状态
    assert page.error_text.visible == False
    assert page.success_text.visible == False
    
    # 显示成功
    page._show_success("测试成功")
    
    assert page.success_text.visible == True
    assert page.success_text.value == "测试成功"
    assert page.error_text.visible == False


def test_config_page_refresh(config_manager):
    """测试刷新配置"""
    # 保存初始配置
    initial_config = {
        "qq_path": "/initial/qq.exe",
        "pmhq_path": "pmhq.exe",
        "llbot_path": "llbot.js",
        "node_path": "node.exe",
        "auto_start_pmhq": False,
        "auto_start_llbot": False,
        "log_level": "info",
        "port": 3000
    }
    config_manager.save_config(initial_config)
    
    page = ConfigPage(config_manager)
    page.build()
    
    assert page.qq_path_field.value == "/initial/qq.exe"
    
    # 外部修改配置文件
    updated_config = initial_config.copy()
    updated_config["qq_path"] = "/updated/qq.exe"
    updated_config["port"] = 5000
    config_manager.save_config(updated_config)
    
    # 刷新页面
    page.refresh()
    
    # 验证已加载新配置
    assert page.qq_path_field.value == "/updated/qq.exe"
    assert page.port_field.value == "5000"


def test_config_page_callback_on_save(config_manager):
    """测试保存配置时调用回调函数"""
    callback_called = False
    saved_config = None
    
    def on_config_saved(config):
        nonlocal callback_called, saved_config
        callback_called = True
        saved_config = config
    
    page = ConfigPage(config_manager, on_config_saved=on_config_saved)
    page.build()
    
    # 模拟保存配置
    page.qq_path_field.value = ""
    page.pmhq_path_field.value = "pmhq.exe"
    page.llbot_path_field.value = "llbot.js"
    page.node_path_field.value = "node.exe"
    page.port_field.value = "3000"
    
    page._on_save_config(None)
    
    # 验证回调被调用
    assert callback_called == True
    assert saved_config is not None
    assert saved_config["pmhq_path"] == "pmhq.exe"
