"""开机自启管理模块"""

import os
import sys
import winreg
import logging

logger = logging.getLogger(__name__)

APP_NAME = "LuckyLilliaDesktop"
REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_path() -> str:
    """获取当前可执行文件路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return sys.executable
    else:
        # 开发环境
        return os.path.abspath(sys.argv[0])


def is_startup_enabled() -> bool:
    """检查是否已启用开机自启"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logger.warning(f"检查开机自启状态失败: {e}")
        return False


def enable_startup() -> bool:
    """启用开机自启"""
    try:
        exe_path = get_executable_path()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            logger.info(f"已启用开机自启: {exe_path}")
            return True
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"启用开机自启失败: {e}")
        return False


def disable_startup() -> bool:
    """禁用开机自启"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
            logger.info("已禁用开机自启")
            return True
        except FileNotFoundError:
            return True
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"禁用开机自启失败: {e}")
        return False
