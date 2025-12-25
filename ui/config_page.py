"""系统配置页面"""

import flet as ft
import tkinter as tk
from tkinter import filedialog
import threading
from typing import Optional, Callable
from pathlib import Path
from core.config_manager import ConfigManager, ConfigError


def _pick_file_native(callback, title="选择文件", filetypes=None, initial_dir=None):
    """使用 tkinter 原生文件对话框（Flet 0.80 的 FilePicker 在 desktop 模式有 bug）"""
    def _pick():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        kwargs = {"title": title}
        if filetypes:
            kwargs["filetypes"] = filetypes
        if initial_dir:
            kwargs["initialdir"] = initial_dir
        
        file_path = filedialog.askopenfilename(**kwargs)
        root.destroy()
        if file_path:
            callback(file_path)
    
    threading.Thread(target=_pick, daemon=True).start()


class ConfigPage:
    def __init__(self, config_manager: ConfigManager,
                 on_config_saved: Optional[Callable] = None):
        self.config_manager = config_manager
        self.on_config_saved = on_config_saved
        self.control = None
        self.current_config = {}
        self._page = None
        
    def build(self):
        # 加载当前配置
        try:
            self.current_config = self.config_manager.load_config()
        except ConfigError as e:
            self.current_config = self.config_manager.get_default_config()
        
        # 创建输入字段
        self.qq_path_field = ft.TextField(
            label="QQ路径",
            hint_text="QQ可执行文件的路径",
            value=self.current_config.get("qq_path", ""),
            expand=True,
            read_only=False,
            disabled=False,
        )
        
        self.qq_path_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择文件",
            on_click=self._on_select_qq_path
        )
        
        self.pmhq_path_field = ft.TextField(
            label="PMHQ路径",
            hint_text="pmhq.exe的路径",
            value=self.current_config.get("pmhq_path", ""),
            expand=True,
            read_only=False,
            disabled=False,
        )
        
        self.pmhq_path_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择文件",
            on_click=self._on_select_pmhq_path
        )
        
        self.llbot_path_field = ft.TextField(
            label="LLBot路径",
            hint_text="llbot.js的路径",
            value=self.current_config.get("llbot_path", ""),
            expand=True,
            read_only=False,
            disabled=False,
        )
        
        self.llbot_path_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择文件",
            on_click=self._on_select_llbot_path
        )
        
        self.node_path_field = ft.TextField(
            label="Node.js路径",
            hint_text="node.exe的路径",
            value=self.current_config.get("node_path", ""),
            expand=True,
            read_only=False,
            disabled=False,
        )
        
        self.node_path_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择文件",
            on_click=self._on_select_node_path
        )
        
        self.auto_login_qq_field = ft.TextField(
            label="自动登录QQ号",
            hint_text="启动时自动登录的QQ号",
            value=self.current_config.get("auto_login_qq", ""),
            width=250,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        self.auto_start_bot_checkbox = ft.Checkbox(
            label="启动软件后自动启动bot",
            value=self.current_config.get("auto_start_bot", False),
        )
        
        self.headless_checkbox = ft.Checkbox(
            label="无头模式（不显示QQ窗口，可能有掉线风险）",
            value=self.current_config.get("headless", False),
        )
        
        self.minimize_to_tray_on_start_checkbox = ft.Checkbox(
            label="启动后自动缩进托盘",
            value=self.current_config.get("minimize_to_tray_on_start", False),
        )
        
        # 日志设置字段
        self.log_save_enabled_checkbox = ft.Checkbox(
            label="保存日志到文件",
            value=self.current_config.get("log_save_enabled", True),
        )
        
        # 配置文件存秒数，UI显示小时数
        retention_seconds = self.current_config.get("log_retention_seconds", 604800)
        retention_hours = retention_seconds // 3600 if retention_seconds > 0 else 0
        self.log_retention_hours_field = ft.TextField(
            label="日志保存时长（小时）",
            hint_text="0 表示永久保存",
            value=str(retention_hours),
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        # 悬浮保存按钮
        self.save_button = ft.FloatingActionButton(
            icon=ft.Icons.SAVE,
            tooltip="保存配置",
            on_click=self._on_save_config,
        )
        
        floating_buttons = ft.Container(
            content=self.save_button,
            right=20,
            bottom=20,
        )
        
        # 主界面内容
        main_content = ft.Column([
            ft.Row([
                ft.Icon(
                    ft.Icons.SETTINGS,
                    size=36,
                    color=ft.Colors.PRIMARY
                ),
                ft.Text(
                    "系统配置",
                    size=32,
                    weight=ft.FontWeight.BOLD
                ),
            ], spacing=12),
            ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
            
            # 启动选项区域
            ft.Row([
                ft.Icon(ft.Icons.PLAY_CIRCLE, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    "启动选项",
                    size=22,
                    weight=ft.FontWeight.W_600
                ),
            ], spacing=10),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        self.auto_login_qq_field,
                        self.auto_start_bot_checkbox,
                        self.headless_checkbox,
                        self.minimize_to_tray_on_start_checkbox,
                    ], spacing=16),
                    padding=24,
                ),
                elevation=3,
            ),
            
            # 日志设置区域
            ft.Row([
                ft.Icon(ft.Icons.ARTICLE, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    "日志设置",
                    size=22,
                    weight=ft.FontWeight.W_600
                ),
            ], spacing=10),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        self.log_save_enabled_checkbox,
                        ft.Row([
                            self.log_retention_hours_field,
                            ft.Text("（0 表示永久保存）", size=12, color=ft.Colors.GREY_500),
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=16),
                    padding=24,
                ),
                elevation=3,
            ),
            
            # 路径配置区域
            ft.Row([
                ft.Icon(ft.Icons.FOLDER, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    "路径配置",
                    size=22,
                    weight=ft.FontWeight.W_600
                ),
            ], spacing=10),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            self.qq_path_field,
                            self.qq_path_button,
                        ], spacing=8),
                        ft.Row([
                            self.pmhq_path_field,
                            self.pmhq_path_button,
                        ], spacing=8),
                        ft.Row([
                            self.llbot_path_field,
                            self.llbot_path_button,
                        ], spacing=8),
                        ft.Row([
                            self.node_path_field,
                            self.node_path_button,
                        ], spacing=8),
                    ], spacing=16),
                    padding=24,
                ),
                elevation=3,
            ),
            
            # 底部留白
            ft.Container(height=60),
        ], spacing=20)
        
        # 使用Stack叠加内容和悬浮按钮
        scrollable_content = ft.Container(
            content=ft.ListView(
                controls=[main_content],
                spacing=0,
                padding=28,
                expand=True,
            ),
            expand=True,
        )
        
        self.control = ft.Stack([
            scrollable_content,
            floating_buttons,
        ], expand=True)
        
        # 明确设置所有路径字段为可编辑状态
        self.qq_path_field.read_only = False
        self.qq_path_field.disabled = False
        self.pmhq_path_field.read_only = False
        self.pmhq_path_field.disabled = False
        self.llbot_path_field.read_only = False
        self.llbot_path_field.disabled = False
        self.node_path_field.read_only = False
        self.node_path_field.disabled = False
        
        return self.control

    
    def _get_initial_directory(self, current_path: str) -> str:
        import os
        if not current_path:
            return os.getcwd()
        
        # 将路径转换为绝对路径
        path = Path(current_path)
        if not path.is_absolute():
            path = Path(os.getcwd()) / path
        
        # 如果是文件路径，返回其父目录
        if path.is_file():
            return str(path.parent)
        elif path.is_dir():
            return str(path)
        elif path.parent.exists():
            return str(path.parent)
        else:
            return os.getcwd()
    
    def _on_select_qq_path(self, e):
        initial_dir = self._get_initial_directory(self.qq_path_field.value)
        def on_selected(path):
            self.qq_path_field.value = path
            if self._page:
                self._page.update()
        _pick_file_native(
            on_selected,
            title="选择QQ可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initial_dir=initial_dir
        )
    
    def _on_select_pmhq_path(self, e):
        initial_dir = self._get_initial_directory(self.pmhq_path_field.value)
        def on_selected(path):
            self.pmhq_path_field.value = path
            if self._page:
                self._page.update()
        _pick_file_native(
            on_selected,
            title="选择PMHQ可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initial_dir=initial_dir
        )
    
    def _on_select_llbot_path(self, e):
        initial_dir = self._get_initial_directory(self.llbot_path_field.value)
        def on_selected(path):
            self.llbot_path_field.value = path
            if self._page:
                self._page.update()
        _pick_file_native(
            on_selected,
            title="选择LLBot脚本文件",
            filetypes=[("JavaScript文件", "*.js"), ("所有文件", "*.*")],
            initial_dir=initial_dir
        )
    
    def _on_select_node_path(self, e):
        initial_dir = self._get_initial_directory(self.node_path_field.value)
        def on_selected(path):
            self.node_path_field.value = path
            if self._page:
                self._page.update()
        _pick_file_native(
            on_selected,
            title="选择Node.js可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initial_dir=initial_dir
        )
    
    def _on_save_config(self, e):
        try:
            config = self.config_manager.load_config()
        except ConfigError:
            config = self.config_manager.get_default_config()
        
        try:
            config["qq_path"] = self.qq_path_field.value.strip()
            config["pmhq_path"] = self.pmhq_path_field.value.strip()
            config["llbot_path"] = self.llbot_path_field.value.strip()
            config["node_path"] = self.node_path_field.value.strip()
            config["auto_login_qq"] = self.auto_login_qq_field.value.strip()
            config["auto_start_bot"] = self.auto_start_bot_checkbox.value
            config["headless"] = self.headless_checkbox.value
            config["minimize_to_tray_on_start"] = self.minimize_to_tray_on_start_checkbox.value
            config["log_save_enabled"] = self.log_save_enabled_checkbox.value
            # 解析日志保存时长（UI输入小时，保存为秒）
            retention_hours_str = self.log_retention_hours_field.value.strip()
            retention_hours = int(retention_hours_str) if retention_hours_str else 168
            config["log_retention_seconds"] = retention_hours * 3600
        except ValueError:
            self._show_error("配置数据无效")
            return
        
        # 验证配置
        is_valid, error_msg = self.config_manager.validate_config(config)
        if not is_valid:
            self._show_error(f"配置验证失败: {error_msg}")
            return
        
        # 保存配置
        success = self.config_manager.save_config(config)
        if success:
            self.current_config = config
            self._show_success("配置保存成功")
            
            # 触发日志清理（如果保存天数有变化）
            self._trigger_log_cleanup()
            
            # 调用回调函数
            if self.on_config_saved:
                self.on_config_saved(config)
        else:
            self._show_error("配置保存失败，请检查文件权限")
    
    def _trigger_log_cleanup(self):
        try:
            from main import LogCleaner
            log_cleaner = LogCleaner()
            # 在后台线程中执行清理，避免阻塞UI
            import threading
            threading.Thread(target=log_cleaner.cleanup_now, daemon=True).start()
        except Exception:
            pass  # 忽略清理失败
    
    def _show_error(self, message: str):
        if self._page:
            snack = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600,
                duration=2000,
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
    
    def _show_success(self, message: str):
        if self._page:
            snack = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_600,
                duration=2000,
            )
            self._page.overlay.append(snack)
            snack.open = True
            self._page.update()
    
    def refresh(self):
        try:
            self.current_config = self.config_manager.load_config()
            
            self.qq_path_field.value = self.current_config.get("qq_path", "")
            self.pmhq_path_field.value = self.current_config.get("pmhq_path", "")
            self.llbot_path_field.value = self.current_config.get("llbot_path", "")
            self.node_path_field.value = self.current_config.get("node_path", "")
            self.auto_login_qq_field.value = self.current_config.get("auto_login_qq", "")
            self.auto_start_bot_checkbox.value = self.current_config.get("auto_start_bot", False)
            self.headless_checkbox.value = self.current_config.get("headless", False)
            self.minimize_to_tray_on_start_checkbox.value = self.current_config.get("minimize_to_tray_on_start", False)
            self.log_save_enabled_checkbox.value = self.current_config.get("log_save_enabled", True)
            retention_seconds = self.current_config.get("log_retention_seconds", 604800)
            retention_hours = retention_seconds // 3600 if retention_seconds > 0 else 0
            self.log_retention_hours_field.value = str(retention_hours)
            
            if self._page:
                try:
                    self._page.update()
                except Exception:
                    pass
        except ConfigError as e:
            self._show_error(f"加载配置失败: {str(e)}")
