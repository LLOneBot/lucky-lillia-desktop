"""配置页面UI模块 - 提供配置文件的图形化编辑界面"""

import flet as ft
from typing import Optional, Callable
from pathlib import Path
from core.config_manager import ConfigManager, ConfigError


class ConfigPage:
    """配置页面组件"""
    
    def __init__(self, config_manager: ConfigManager,
                 on_config_saved: Optional[Callable] = None):
        """初始化配置页面
        
        Args:
            config_manager: 配置管理器实例
            on_config_saved: 配置保存成功后的回调函数
        """
        self.config_manager = config_manager
        self.on_config_saved = on_config_saved
        self.control = None
        self.current_config = {}
        
    def build(self):
        """构建UI组件"""
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
        
        self.llonebot_path_field = ft.TextField(
            label="LLOneBot路径",
            hint_text="llonebot.js的路径",
            value=self.current_config.get("llonebot_path", ""),
            expand=True,
            read_only=False,
            disabled=False,
        )
        
        self.llonebot_path_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="选择文件",
            on_click=self._on_select_llonebot_path
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
        
        # 错误提示文本
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            size=14,
            visible=False
        )
        
        # 成功提示文本
        self.success_text = ft.Text(
            "",
            color=ft.Colors.GREEN_400,
            size=14,
            visible=False
        )
        
        # 悬浮保存按钮
        self.save_button = ft.FloatingActionButton(
            icon=ft.Icons.SAVE,
            tooltip="保存配置",
            on_click=self._on_save_config,
        )
        
        # 文件选择器
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picker_result
        )
        
        # 悬浮按钮容器
        floating_buttons = ft.Container(
            content=self.save_button,
            right=20,
            bottom=20,
        )
        
        # 主界面内容
        main_content = ft.Column([
            ft.Row([
                ft.Icon(
                    name=ft.Icons.SETTINGS,
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
                surface_tint_color=ft.Colors.PRIMARY,
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
                surface_tint_color=ft.Colors.PRIMARY,
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
                            self.llonebot_path_field,
                            self.llonebot_path_button,
                        ], spacing=8),
                        ft.Row([
                            self.node_path_field,
                            self.node_path_button,
                        ], spacing=8),
                    ], spacing=16),
                    padding=24,
                ),
                elevation=3,
                surface_tint_color=ft.Colors.PRIMARY,
            ),
            
            # 提示信息
            self.error_text,
            self.success_text,
            
            # 文件选择器（隐藏）
            self.file_picker,
        ], spacing=20)
        
        # 使用Stack叠加内容和悬浮按钮
        # 滚动容器需要放在Stack内部，并且使用ListView替代Column的scroll
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
        self.llonebot_path_field.read_only = False
        self.llonebot_path_field.disabled = False
        self.node_path_field.read_only = False
        self.node_path_field.disabled = False
        
        return self.control

    
    def _get_initial_directory(self, current_path: str) -> str:
        """获取文件选择器的初始目录
        
        Args:
            current_path: 当前路径值（可能是相对路径或绝对路径）
            
        Returns:
            初始目录的绝对路径
        """
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
        """QQ路径选择按钮点击处理"""
        self._current_field = "qq_path"
        initial_dir = self._get_initial_directory(self.qq_path_field.value)
        self.file_picker.pick_files(
            dialog_title="选择QQ可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False,
            initial_directory=initial_dir
        )
    
    def _on_select_pmhq_path(self, e):
        """PMHQ路径选择按钮点击处理"""
        self._current_field = "pmhq_path"
        initial_dir = self._get_initial_directory(self.pmhq_path_field.value)
        self.file_picker.pick_files(
            dialog_title="选择PMHQ可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False,
            initial_directory=initial_dir
        )
    
    def _on_select_llonebot_path(self, e):
        """LLOneBot路径选择按钮点击处理"""
        self._current_field = "llonebot_path"
        initial_dir = self._get_initial_directory(self.llonebot_path_field.value)
        self.file_picker.pick_files(
            dialog_title="选择LLOneBot脚本文件",
            allowed_extensions=["js"],
            allow_multiple=False,
            initial_directory=initial_dir
        )
    
    def _on_select_node_path(self, e):
        """Node.js路径选择按钮点击处理"""
        self._current_field = "node_path"
        initial_dir = self._get_initial_directory(self.node_path_field.value)
        self.file_picker.pick_files(
            dialog_title="选择Node.js可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False,
            initial_directory=initial_dir
        )
    
    def _on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """文件选择器结果处理
        
        Args:
            e: 文件选择器结果事件
        """
        if e.files and len(e.files) > 0:
            selected_path = e.files[0].path
            
            # 更新对应的输入字段
            if self._current_field == "qq_path":
                self.qq_path_field.value = selected_path
                self.qq_path_field.update()
            elif self._current_field == "pmhq_path":
                self.pmhq_path_field.value = selected_path
                self.pmhq_path_field.update()
            elif self._current_field == "llonebot_path":
                self.llonebot_path_field.value = selected_path
                self.llonebot_path_field.update()
            elif self._current_field == "node_path":
                self.node_path_field.value = selected_path
                self.node_path_field.update()
    
    def _on_save_config(self, e):
        """保存配置按钮点击处理"""
        # 隐藏之前的提示
        self.error_text.visible = False
        self.success_text.visible = False
        
        # 先加载现有配置，保留其他设置（如 UI 设置）
        try:
            config = self.config_manager.load_config()
        except ConfigError:
            config = self.config_manager.get_default_config()
        
        # 更新页面上的配置项
        try:
            config["qq_path"] = self.qq_path_field.value.strip()
            config["pmhq_path"] = self.pmhq_path_field.value.strip()
            config["llonebot_path"] = self.llonebot_path_field.value.strip()
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
        """触发日志清理"""
        try:
            from main import LogCleaner
            log_cleaner = LogCleaner()
            # 在后台线程中执行清理，避免阻塞UI
            import threading
            threading.Thread(target=log_cleaner.cleanup_now, daemon=True).start()
        except Exception:
            pass  # 忽略清理失败
    
    def _show_error(self, message: str):
        """显示错误提示
        
        Args:
            message: 错误消息
        """
        self.error_text.value = message
        self.error_text.visible = True
        self.success_text.visible = False
        try:
            self.control.update()
        except (AssertionError, AttributeError):
            pass  # 控件未添加到页面，跳过更新
    
    def _show_success(self, message: str):
        """显示成功提示
        
        Args:
            message: 成功消息
        """
        self.success_text.value = message
        self.success_text.visible = True
        self.error_text.visible = False
        try:
            self.control.update()
        except (AssertionError, AttributeError):
            pass  # 控件未添加到页面，跳过更新
    
    def refresh(self):
        """刷新配置显示，从文件重新加载配置"""
        try:
            self.current_config = self.config_manager.load_config()
            
            # 更新所有输入字段
            self.qq_path_field.value = self.current_config.get("qq_path", "")
            self.pmhq_path_field.value = self.current_config.get("pmhq_path", "")
            self.llonebot_path_field.value = self.current_config.get("llonebot_path", "")
            self.node_path_field.value = self.current_config.get("node_path", "")
            self.auto_login_qq_field.value = self.current_config.get("auto_login_qq", "")
            self.auto_start_bot_checkbox.value = self.current_config.get("auto_start_bot", False)
            self.headless_checkbox.value = self.current_config.get("headless", False)
            self.minimize_to_tray_on_start_checkbox.value = self.current_config.get("minimize_to_tray_on_start", False)
            self.log_save_enabled_checkbox.value = self.current_config.get("log_save_enabled", True)
            # 秒转小时显示
            retention_seconds = self.current_config.get("log_retention_seconds", 604800)
            retention_hours = retention_seconds // 3600 if retention_seconds > 0 else 0
            self.log_retention_hours_field.value = str(retention_hours)
            
            # 隐藏提示
            self.error_text.visible = False
            self.success_text.visible = False
            
            # 更新UI（如果已添加到页面）
            if self.control:
                try:
                    self.control.update()
                except (AssertionError, AttributeError):
                    pass  # 控件未添加到页面，跳过更新
        except ConfigError as e:
            self._show_error(f"加载配置失败: {str(e)}")
