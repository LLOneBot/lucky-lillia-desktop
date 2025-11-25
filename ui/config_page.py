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
        
        self.auto_start_pmhq_checkbox = ft.Checkbox(
            label="自动启动PMHQ",
            value=self.current_config.get("auto_start_pmhq", False),
        )
        
        self.auto_start_llonebot_checkbox = ft.Checkbox(
            label="自动启动LLOneBot",
            value=self.current_config.get("auto_start_llonebot", False),
        )
        
        self.log_level_dropdown = ft.Dropdown(
            label="日志级别",
            options=[
                ft.dropdown.Option("debug", "Debug"),
                ft.dropdown.Option("info", "Info"),
                ft.dropdown.Option("warning", "Warning"),
                ft.dropdown.Option("error", "Error"),
            ],
            value=self.current_config.get("log_level", "info"),
            width=200,
        )
        
        self.port_field = ft.TextField(
            label="端口",
            hint_text="服务端口号",
            value=str(self.current_config.get("port", 3000)),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
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
        
        # 保存和重置按钮
        self.save_button = ft.ElevatedButton(
            "保存配置",
            icon=ft.Icons.SAVE,
            on_click=self._on_save_config,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        )
        
        self.reset_button = ft.OutlinedButton(
            "重置为默认",
            icon=ft.Icons.RESTORE,
            on_click=self._on_reset_config,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        )
        
        # 文件选择器
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picker_result
        )
        
        # 构建主界面
        self.control = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        name=ft.Icons.SETTINGS,
                        size=36,
                        color=ft.Colors.PRIMARY
                    ),
                    ft.Text(
                        "配置管理",
                        size=32,
                        weight=ft.FontWeight.BOLD
                    ),
                ], spacing=12),
                ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                
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
                            self.auto_start_pmhq_checkbox,
                            self.auto_start_llonebot_checkbox,
                        ], spacing=16),
                        padding=24,
                    ),
                    elevation=3,
                    surface_tint_color=ft.Colors.PRIMARY,
                ),
                
                # 其他设置区域
                ft.Row([
                    ft.Icon(ft.Icons.TUNE, size=24, color=ft.Colors.PRIMARY),
                    ft.Text(
                        "其他设置",
                        size=22,
                        weight=ft.FontWeight.W_600
                    ),
                ], spacing=10),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            self.log_level_dropdown,
                            self.port_field,
                        ], spacing=16),
                        padding=24,
                    ),
                    elevation=3,
                    surface_tint_color=ft.Colors.PRIMARY,
                ),
                
                # 提示信息
                self.error_text,
                self.success_text,
                
                # 操作按钮
                ft.Row([
                    self.save_button,
                    self.reset_button,
                ], spacing=20),
                
                # 文件选择器（隐藏）
                self.file_picker,
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=28,
        )
        
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

    
    def _on_select_qq_path(self, e):
        """QQ路径选择按钮点击处理"""
        self._current_field = "qq_path"
        self.file_picker.pick_files(
            dialog_title="选择QQ可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False
        )
    
    def _on_select_pmhq_path(self, e):
        """PMHQ路径选择按钮点击处理"""
        self._current_field = "pmhq_path"
        self.file_picker.pick_files(
            dialog_title="选择PMHQ可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False
        )
    
    def _on_select_llonebot_path(self, e):
        """LLOneBot路径选择按钮点击处理"""
        self._current_field = "llonebot_path"
        self.file_picker.pick_files(
            dialog_title="选择LLOneBot脚本文件",
            allowed_extensions=["js"],
            allow_multiple=False
        )
    
    def _on_select_node_path(self, e):
        """Node.js路径选择按钮点击处理"""
        self._current_field = "node_path"
        self.file_picker.pick_files(
            dialog_title="选择Node.js可执行文件",
            allowed_extensions=["exe"],
            allow_multiple=False
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
        
        # 收集配置数据
        try:
            config = {
                "qq_path": self.qq_path_field.value.strip(),
                "pmhq_path": self.pmhq_path_field.value.strip(),
                "llonebot_path": self.llonebot_path_field.value.strip(),
                "node_path": self.node_path_field.value.strip(),
                "auto_start_pmhq": self.auto_start_pmhq_checkbox.value,
                "auto_start_llonebot": self.auto_start_llonebot_checkbox.value,
                "log_level": self.log_level_dropdown.value,
                "port": int(self.port_field.value),
            }
        except ValueError:
            self._show_error("端口必须是有效的整数")
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
            
            # 调用回调函数
            if self.on_config_saved:
                self.on_config_saved(config)
        else:
            self._show_error("配置保存失败，请检查文件权限")
    
    def _on_reset_config(self, e):
        """重置配置按钮点击处理"""
        # 获取默认配置
        default_config = self.config_manager.get_default_config()
        
        # 更新所有输入字段
        self.qq_path_field.value = default_config.get("qq_path", "")
        self.pmhq_path_field.value = default_config.get("pmhq_path", "")
        self.llonebot_path_field.value = default_config.get("llonebot_path", "")
        self.node_path_field.value = default_config.get("node_path", "")
        self.auto_start_pmhq_checkbox.value = default_config.get("auto_start_pmhq", False)
        self.auto_start_llonebot_checkbox.value = default_config.get("auto_start_llonebot", False)
        self.log_level_dropdown.value = default_config.get("log_level", "info")
        self.port_field.value = str(default_config.get("port", 3000))
        
        # 隐藏提示
        self.error_text.visible = False
        self.success_text.visible = False
        
        # 更新UI（如果已添加到页面）
        try:
            self.control.update()
        except (AssertionError, AttributeError):
            pass  # 控件未添加到页面，跳过更新
    
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
            self.auto_start_pmhq_checkbox.value = self.current_config.get("auto_start_pmhq", False)
            self.auto_start_llonebot_checkbox.value = self.current_config.get("auto_start_llonebot", False)
            self.log_level_dropdown.value = self.current_config.get("log_level", "info")
            self.port_field.value = str(self.current_config.get("port", 3000))
            
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
