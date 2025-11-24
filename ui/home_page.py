"""首页UI模块 - 显示进程状态、快速操作和系统监控"""

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
import psutil
from core.process_manager import ProcessManager, ProcessStatus


class ProcessStatusCard:
    """进程状态卡片组件"""
    
    def __init__(self, process_name: str, display_name: str, 
                 on_start: Optional[Callable] = None,
                 on_stop: Optional[Callable] = None):
        """初始化进程状态卡片
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
            display_name: 显示名称
            on_start: 启动按钮回调
            on_stop: 停止按钮回调
        """
        self.process_name = process_name
        self.display_name = display_name
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        self.status = ProcessStatus.STOPPED
        self.control = None
        
    def build(self):
        """构建UI组件"""
        self.status_icon = ft.Icon(
            name=ft.Icons.CIRCLE,
            color=ft.Colors.GREY_400,
            size=20
        )
        
        self.status_text = ft.Text(
            "已停止",
            size=15,
            color=ft.Colors.GREY_600,
            weight=ft.FontWeight.W_500
        )
        
        self.start_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            tooltip="启动",
            on_click=self._on_start_click,
            icon_color=ft.Colors.GREEN_600,
            icon_size=28,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        self.stop_button = ft.IconButton(
            icon=ft.Icons.STOP,
            tooltip="停止",
            on_click=self._on_stop_click,
            icon_color=ft.Colors.RED_600,
            icon_size=28,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            name=ft.Icons.COMPUTER,
                            size=24,
                            color=ft.Colors.PRIMARY
                        ),
                        ft.Text(
                            self.display_name,
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                    ], spacing=12),
                    ft.Divider(height=1, thickness=2),
                    ft.Row([
                        self.status_icon,
                        self.status_text,
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([
                        self.start_button,
                        self.stop_button,
                    ], spacing=12),
                ], spacing=16),
                padding=24,
            ),
            elevation=3,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def _on_start_click(self, e):
        """启动按钮点击处理"""
        if self.on_start_callback:
            self.on_start_callback(self.process_name)
    
    def _on_stop_click(self, e):
        """停止按钮点击处理"""
        if self.on_stop_callback:
            self.on_stop_callback(self.process_name)
    
    def update_status(self, status: ProcessStatus):
        """更新进程状态显示
        
        Args:
            status: 进程状态
        """
        self.status = status
        
        # 更新状态图标和文本
        if status == ProcessStatus.RUNNING:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE
            self.status_icon.color = ft.Colors.GREEN_600
            self.status_text.value = "运行中"
            self.status_text.color = ft.Colors.GREEN_700
            self.start_button.disabled = True
            self.stop_button.disabled = False
        elif status == ProcessStatus.STOPPED:
            self.status_icon.name = ft.Icons.CIRCLE
            self.status_icon.color = ft.Colors.GREY_500
            self.status_text.value = "已停止"
            self.status_text.color = ft.Colors.GREY_700
            self.start_button.disabled = False
            self.stop_button.disabled = True
        elif status == ProcessStatus.STARTING:
            self.status_icon.name = ft.Icons.HOURGLASS_EMPTY
            self.status_icon.color = ft.Colors.ORANGE_600
            self.status_text.value = "启动中..."
            self.status_text.color = ft.Colors.ORANGE_700
            self.start_button.disabled = True
            self.stop_button.disabled = True
        elif status == ProcessStatus.STOPPING:
            self.status_icon.name = ft.Icons.HOURGLASS_EMPTY
            self.status_icon.color = ft.Colors.ORANGE_600
            self.status_text.value = "停止中..."
            self.status_text.color = ft.Colors.ORANGE_700
            self.start_button.disabled = True
            self.stop_button.disabled = True
        elif status == ProcessStatus.ERROR:
            self.status_icon.name = ft.Icons.ERROR
            self.status_icon.color = ft.Colors.RED_600
            self.status_text.value = "错误"
            self.status_text.color = ft.Colors.RED_700
            self.start_button.disabled = False
            self.stop_button.disabled = True


class ResourceMonitorCard:
    """系统资源监控卡片组件"""
    
    def __init__(self):
        """初始化资源监控卡片"""
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.control = None
        
    def build(self):
        """构建UI组件"""
        self.cpu_text = ft.Text(
            "CPU: 0.0%",
            size=15,
            weight=ft.FontWeight.W_500
        )
        
        self.cpu_progress = ft.ProgressBar(
            value=0,
            height=8,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
            border_radius=4
        )
        
        self.memory_text = ft.Text(
            "内存: 0.0%",
            size=15,
            weight=ft.FontWeight.W_500
        )
        
        self.memory_progress = ft.ProgressBar(
            value=0,
            height=8,
            color=ft.Colors.GREEN_600,
            bgcolor=ft.Colors.GREEN_100,
            border_radius=4
        )
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            name=ft.Icons.MEMORY,
                            size=24,
                            color=ft.Colors.PRIMARY
                        ),
                        ft.Text(
                            "系统资源",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                    ], spacing=12),
                    ft.Divider(height=1, thickness=2),
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SPEED, size=18, color=ft.Colors.BLUE_600),
                            self.cpu_text,
                        ], spacing=8),
                        self.cpu_progress,
                    ], spacing=10),
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.STORAGE, size=18, color=ft.Colors.GREEN_600),
                            self.memory_text,
                        ], spacing=8),
                        self.memory_progress,
                    ], spacing=10),
                ], spacing=16),
                padding=24,
            ),
            elevation=3,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def update_resources(self, cpu_percent: float, memory_percent: float):
        """更新资源使用情况
        
        Args:
            cpu_percent: CPU使用率百分比
            memory_percent: 内存使用率百分比
        """
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        
        self.cpu_text.value = f"CPU: {cpu_percent:.1f}%"
        self.cpu_progress.value = cpu_percent / 100.0
        
        self.memory_text.value = f"内存: {memory_percent:.1f}%"
        self.memory_progress.value = memory_percent / 100.0


class LogPreviewCard:
    """日志预览卡片组件"""
    
    def __init__(self, on_view_all: Optional[Callable] = None):
        """初始化日志预览卡片
        
        Args:
            on_view_all: 查看全部日志按钮回调
        """
        self.on_view_all_callback = on_view_all
        self.log_entries = []
        self.control = None
        
    def build(self):
        """构建UI组件"""
        self.log_list = ft.Column(
            controls=[
                ft.Text(
                    "暂无日志",
                    size=14,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            name=ft.Icons.ARTICLE,
                            size=24,
                            color=ft.Colors.PRIMARY
                        ),
                        ft.Text(
                            "最近日志",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Container(expand=True),
                        ft.TextButton(
                            "查看全部",
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=self._on_view_all_click,
                            style=ft.ButtonStyle(
                                color=ft.Colors.PRIMARY
                            )
                        ),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Divider(height=1, thickness=2),
                    ft.Container(
                        content=self.log_list,
                        height=220,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
                        border_radius=8,
                        padding=12,
                        expand=True,
                    ),
                ], spacing=16),
                padding=24,
            ),
            elevation=3,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def _on_view_all_click(self, e):
        """查看全部按钮点击处理"""
        if self.on_view_all_callback:
            self.on_view_all_callback()
    
    def update_logs(self, log_entries: List[dict]):
        """更新日志显示
        
        Args:
            log_entries: 日志条目列表，每个条目包含timestamp, process_name, level, message
        """
        self.log_entries = log_entries[-10:]  # 只显示最新10条
        
        if not self.log_entries:
            self.log_list.controls = [
                ft.Container(
                    content=ft.Text(
                        "暂无日志",
                        size=14,
                        color=ft.Colors.GREY_600,
                        italic=True
                    ),
                    expand=True,
                    alignment=ft.alignment.center,
                )
            ]
        else:
            self.log_list.controls = []
            for entry in self.log_entries:
                timestamp = entry.get("timestamp", "")
                process_name = entry.get("process_name", "")
                level = entry.get("level", "stdout")
                message = entry.get("message", "")
                
                # 根据日志级别设置颜色和图标
                if level == "stderr":
                    color = ft.Colors.RED_700
                    icon = ft.Icons.ERROR_OUTLINE
                    icon_color = ft.Colors.RED_600
                else:
                    color = ft.Colors.ON_SURFACE
                    icon = ft.Icons.INFO_OUTLINE
                    icon_color = ft.Colors.BLUE_600
                
                log_text = ft.Row([
                    ft.Icon(icon, size=14, color=icon_color),
                    ft.Text(
                        f"[{timestamp}] [{process_name}] {message}",
                        size=13,
                        color=color,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True
                    )
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)
                
                self.log_list.controls.append(log_text)


class HomePage:
    """首页组件"""
    
    def __init__(self, process_manager: ProcessManager,
                 on_navigate_logs: Optional[Callable] = None):
        """初始化首页
        
        Args:
            process_manager: 进程管理器实例
            on_navigate_logs: 导航到日志页面的回调
        """
        self.process_manager = process_manager
        self.on_navigate_logs = on_navigate_logs
        self.control = None
        
    def build(self):
        """构建UI组件"""
        # 创建进程状态卡片
        self.pmhq_card = ProcessStatusCard(
            "pmhq",
            "PMHQ",
            on_start=self._on_start_process,
            on_stop=self._on_stop_process
        )
        self.pmhq_card.build()
        
        self.llonebot_card = ProcessStatusCard(
            "llonebot",
            "LLOneBot",
            on_start=self._on_start_process,
            on_stop=self._on_stop_process
        )
        self.llonebot_card.build()
        
        # 创建资源监控卡片
        self.resource_card = ResourceMonitorCard()
        self.resource_card.build()
        
        # 创建日志预览卡片
        self.log_card = LogPreviewCard(
            on_view_all=self._on_view_all_logs
        )
        self.log_card.build()
        
        self.control = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        name=ft.Icons.DASHBOARD,
                        size=36,
                        color=ft.Colors.PRIMARY
                    ),
                    ft.Text(
                        "控制面板",
                        size=32,
                        weight=ft.FontWeight.BOLD
                    ),
                ], spacing=12),
                ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                
                # 进程状态区域
                ft.Row([
                    ft.Icon(ft.Icons.SETTINGS_APPLICATIONS, size=24, color=ft.Colors.PRIMARY),
                    ft.Text(
                        "进程状态",
                        size=22,
                        weight=ft.FontWeight.W_600
                    ),
                ], spacing=10),
                ft.Row([
                    ft.Container(
                        content=self.pmhq_card.control,
                        expand=1
                    ),
                    ft.Container(
                        content=self.llonebot_card.control,
                        expand=1
                    ),
                ], spacing=20),
                
                # 系统资源和日志预览
                ft.Row([
                    ft.Container(
                        content=self.resource_card.control,
                        expand=1
                    ),
                    ft.Container(
                        content=self.log_card.control,
                        expand=2
                    ),
                ], spacing=20),
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=28,
        )
        return self.control
    
    def _on_start_process(self, process_name: str):
        """启动进程处理
        
        Args:
            process_name: 进程名称
        """
        # TODO: 从配置中获取路径
        if process_name == "pmhq":
            success = self.process_manager.start_pmhq(
                "pmhq.exe",
                "pmhq_config.json"
            )
        elif process_name == "llonebot":
            success = self.process_manager.start_llonebot(
                "node.exe",
                "llonebot.js"
            )
        
        # 更新状态显示
        self.refresh_status()
    
    def _on_stop_process(self, process_name: str):
        """停止进程处理
        
        Args:
            process_name: 进程名称
        """
        self.process_manager.stop_process(process_name)
        
        # 更新状态显示
        self.refresh_status()
    
    def _on_view_all_logs(self):
        """查看全部日志处理"""
        if self.on_navigate_logs:
            self.on_navigate_logs()
    
    def refresh_status(self):
        """刷新进程状态显示"""
        pmhq_status = self.process_manager.get_process_status("pmhq")
        llonebot_status = self.process_manager.get_process_status("llonebot")
        
        self.pmhq_card.update_status(pmhq_status)
        self.llonebot_card.update_status(llonebot_status)
    
    def refresh_resources(self):
        """刷新系统资源显示"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            self.resource_card.update_resources(cpu_percent, memory_percent)
        except Exception as e:
            # 如果获取资源信息失败，使用默认值
            pass
    
    def refresh_logs(self, log_entries: List[dict]):
        """刷新日志预览
        
        Args:
            log_entries: 日志条目列表
        """
        self.log_card.update_logs(log_entries)
