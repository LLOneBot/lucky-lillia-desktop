"""首页UI模块 - 显示进程状态、快速操作和系统监控"""
from pathlib import Path

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
import psutil
import os
from core.process_manager import ProcessManager, ProcessStatus
from core.config_manager import ConfigManager
from core.update_checker import UpdateChecker, UpdateInfo
from core.version_detector import VersionDetector
from utils.downloader import Downloader, DownloadError
from utils.constants import DEFAULT_CONFIG, NPM_PACKAGES, GITHUB_REPOS


class ProcessResourceCard:
    """进程资源占用卡片组件"""
    
    def __init__(self, process_name: str, display_name: str, icon: str = ft.Icons.COMPUTER, 
                 show_download_status: bool = False):
        """初始化进程资源卡片
        
        Args:
            process_name: 进程名称
            display_name: 显示名称
            icon: 图标
            show_download_status: 是否显示下载状态（用于PMHQ）
        """
        self.process_name = process_name
        self.display_name = display_name
        self.icon = icon
        self.cpu_percent = 0.0
        self.memory_mb = 0.0
        self.is_running = False
        self.show_download_status = show_download_status
        self.file_exists = True  # 默认文件存在
        self.control = None
        
    def build(self):
        """构建UI组件"""
        self.status_icon = ft.Icon(
            name=ft.Icons.CIRCLE,
            color=ft.Colors.GREY_400,
            size=16
        )
        
        self.status_text = ft.Text(
            "未运行",
            size=13,
            color=ft.Colors.GREY_600,
        )
        
        self.cpu_text = ft.Text(
            "CPU: 0.0%",
            size=14,
            weight=ft.FontWeight.W_500
        )
        
        self.cpu_progress = ft.ProgressBar(
            value=0,
            height=6,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
            border_radius=3
        )
        
        self.memory_text = ft.Text(
            "内存: 0 MB",
            size=14,
            weight=ft.FontWeight.W_500
        )
        
        self.memory_progress = ft.ProgressBar(
            value=0,
            height=6,
            color=ft.Colors.GREEN_600,
            bgcolor=ft.Colors.GREEN_100,
            border_radius=3
        )
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            name=self.icon,
                            size=20,
                            color=ft.Colors.PRIMARY
                        ),
                        ft.Text(
                            self.display_name,
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                    ], spacing=10),
                    ft.Row([
                        self.status_icon,
                        self.status_text,
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(height=1, thickness=1),
                    ft.Column([
                        self.cpu_text,
                        self.cpu_progress,
                    ], spacing=6),
                    ft.Column([
                        self.memory_text,
                        self.memory_progress,
                    ], spacing=6),
                ], spacing=12),
                padding=16,
            ),
            elevation=2,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def update_resources(self, cpu_percent: float, memory_mb: float, is_running: bool, 
                        file_exists: bool = True):
        """更新资源使用情况
        
        Args:
            cpu_percent: CPU使用率百分比
            memory_mb: 内存使用量（MB）
            is_running: 是否运行中
            file_exists: 文件是否存在（仅用于PMHQ）
        """
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.is_running = is_running
        self.file_exists = file_exists
        
        # 更新状态
        if self.show_download_status and not file_exists:
            # PMHQ未下载
            self.status_icon.name = ft.Icons.DOWNLOAD
            self.status_icon.color = ft.Colors.ORANGE_600
            self.status_text.value = "未下载"
            self.status_text.color = ft.Colors.ORANGE_700
        elif is_running:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE
            self.status_icon.color = ft.Colors.GREEN_600
            self.status_text.value = "运行中"
            self.status_text.color = ft.Colors.GREEN_700
        else:
            self.status_icon.name = ft.Icons.CIRCLE
            self.status_icon.color = ft.Colors.GREY_400
            self.status_text.value = "未启动"
            self.status_text.color = ft.Colors.GREY_600
        
        # 更新CPU
        self.cpu_text.value = f"CPU: {cpu_percent:.1f}%"
        self.cpu_progress.value = min(cpu_percent / 100.0, 1.0)
        
        # 更新内存
        self.memory_text.value = f"内存: {memory_mb:.0f} MB"
        # 假设最大内存为1GB用于进度条显示
        self.memory_progress.value = min(memory_mb / 1024.0, 1.0)


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
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SPEED, size=18, color=ft.Colors.BLUE_600),
                            self.cpu_text,
                        ], spacing=8),
                        self.cpu_progress,
                    ], spacing=10),
                    ft.Container(height=20),
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.STORAGE, size=18, color=ft.Colors.GREEN_600),
                            self.memory_text,
                        ], spacing=8),
                        self.memory_progress,
                    ], spacing=10),
                    ft.Container(expand=True),
                ], spacing=16, expand=True),
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
            
            # 自动滚动到最新日志
            self.log_list.scroll_to(offset=-1, duration=100)


class HomePage:
    """首页组件"""
    
    def __init__(self, process_manager: ProcessManager,
                 config_manager: ConfigManager,
                 log_collector=None,
                 on_navigate_logs: Optional[Callable] = None,
                 version_detector: Optional[VersionDetector] = None,
                 update_checker: Optional[UpdateChecker] = None):
        """初始化首页
        
        Args:
            process_manager: 进程管理器实例
            config_manager: 配置管理器实例
            log_collector: 日志收集器实例（可选）
            on_navigate_logs: 导航到日志页面的回调
            version_detector: 版本检测器实例（可选）
            update_checker: 更新检查器实例（可选）
        """
        self.process_manager = process_manager
        self.config_manager = config_manager
        self.log_collector = log_collector
        self.on_navigate_logs = on_navigate_logs
        self.version_detector = version_detector or VersionDetector()
        self.update_checker = update_checker or UpdateChecker()
        self.downloader = Downloader()
        self.control = None
        self.page = None
        self.download_dialog = None
        self.is_downloading = False
        self.download_llonebot_dialog = None
        self.is_downloading_llonebot = False
        self.download_node_dialog = None
        self.is_downloading_node = False
        self.download_ffmpeg_dialog = None
        self.is_downloading_ffmpeg = False
        self.download_ffprobe_dialog = None
        self.is_downloading_ffprobe = False
        self._is_downloading_update = False
        self._updates_found = []  # 存储发现的更新列表 [(component_name, UpdateInfo), ...]
        self._pending_app_update_script = None  # 待执行的应用更新脚本路径
        
        # 日志实时更新相关
        self._log_update_scheduled = False
        self._log_update_lock = __import__('threading').Lock()
        
        # 进程对象缓存（用于正确计算CPU使用率）
        # cpu_percent(interval=0) 需要在同一个Process对象上多次调用才能返回正确值
        self._process_cache = {}  # {pid: psutil.Process}
        
        # 注册日志回调
        if self.log_collector:
            self.log_collector.add_callback(self._on_new_log)
        
    def build(self):
        """构建UI组件"""
        # 创建进程资源卡片（Bot占用整合了管理器、PMHQ、LLOneBot）
        self.bot_card = ProcessResourceCard(
            "bot",
            "Bot占用",
            ft.Icons.SMART_TOY
        )
        self.bot_card.build()
        
        self.qq_card = ProcessResourceCard(
            "qq",
            "QQ",
            ft.Icons.CHAT
        )
        self.qq_card.build()
        
        # 创建日志预览卡片
        self.log_card = LogPreviewCard(
            on_view_all=self._on_view_all_logs
        )
        self.log_card.build()
        
        # 服务运行状态
        self.services_running = False
        
        # 创建全局启动/停止按钮
        self.global_start_button = ft.ElevatedButton(
            text="启动",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_global_button_click,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=40, vertical=16),
            ),
            height=56,
        )
        
        # 更新提示横幅
        self.update_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.UPDATE, color=ft.Colors.WHITE, size=20),
                ft.Text("发现新版本！", color=ft.Colors.WHITE, size=14),
                ft.TextButton(
                    "更新",
                    on_click=self._on_update_click,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                    )
                ),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.ORANGE_600,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=8,
            visible=False,
        )
        
        # 创建下载对话框
        self._build_download_dialog()
        self._build_llonebot_download_dialog()
        self._build_node_download_dialog()
        self._build_ffmpeg_download_dialog()
        self._build_ffprobe_download_dialog()
        
        # 悬浮启动按钮
        floating_button = ft.Container(
            content=self.global_start_button,
            bottom=30,
            left=0,
            right=0,
            alignment=ft.alignment.center,
        )
        
        # 标题文本（可动态更新）
        self.title_text = ft.Text(
            "控制面板",
            size=32,
            weight=ft.FontWeight.BOLD
        )
        
        # 标题图标（显示昵称时隐藏）
        self.title_icon = ft.Icon(
            name=ft.Icons.DASHBOARD,
            size=36,
            color=ft.Colors.PRIMARY
        )
        
        # 主内容区域
        main_content = ft.Column([
            # 更新提示横幅
            self.update_banner,
            
            ft.Row([
                self.title_icon,
                self.title_text,
            ], spacing=12),
            ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
            
            # 进程资源监控区域
            ft.Row([
                ft.Icon(ft.Icons.MEMORY, size=24, color=ft.Colors.PRIMARY),
                ft.Text(
                    "进程资源监控",
                    size=22,
                    weight=ft.FontWeight.W_600
                ),
            ], spacing=10),
            ft.Row([
                ft.Container(
                    content=self.bot_card.control,
                    expand=1
                ),
                ft.Container(
                    content=self.qq_card.control,
                    expand=1
                ),
            ], spacing=16),
            
            # 日志预览（标题已包含在 LogPreviewCard 中）
            ft.Container(
                content=self.log_card.control,
                height=280,
            ),
            
            # 底部留白，给悬浮按钮腾出空间
            ft.Container(height=50),
        ], spacing=16, scroll=ft.ScrollMode.AUTO)
        
        self.control = ft.Stack([
            ft.Container(content=main_content, padding=24, expand=True),
            floating_button,
        ], expand=True)
        
        return self.control
    
    def _build_download_dialog(self):
        """构建PMHQ下载对话框"""
        self.download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_download_cancel_click,
        )
        
        self.download_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载PMHQ"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "PMHQ可执行文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.download_progress_text,
                    ft.Container(height=10),
                    self.download_progress_bar,
                    ft.Container(height=10),
                    self.download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_llonebot_download_dialog(self):
        """构建LLOneBot下载对话框"""
        self.llonebot_download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.llonebot_download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.llonebot_download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.llonebot_download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_llonebot_download_cancel_click,
        )
        
        self.download_llonebot_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载LLOneBot"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "LLOneBot文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.llonebot_download_progress_text,
                    ft.Container(height=10),
                    self.llonebot_download_progress_bar,
                    ft.Container(height=10),
                    self.llonebot_download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.llonebot_download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_node_download_dialog(self):
        """构建Node.exe下载对话框"""
        self.node_download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.node_download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.node_download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.node_download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_node_download_cancel_click,
        )
        
        self.download_node_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载Node.exe"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Node.exe文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.node_download_progress_text,
                    ft.Container(height=10),
                    self.node_download_progress_bar,
                    ft.Container(height=10),
                    self.node_download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.node_download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _on_global_button_click(self, e):
        """全局启动/停止按钮点击处理"""
        if self.services_running:
            self._stop_all_services()
        else:
            self._on_global_start_click(e)
    
    def _update_button_state(self, running: bool):
        """更新按钮状态
        
        Args:
            running: 服务是否正在运行
        """
        self.services_running = running
        if running:
            self.global_start_button.text = "停止"
            self.global_start_button.icon = ft.Icons.STOP
            self.global_start_button.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600,
                padding=ft.padding.symmetric(horizontal=40, vertical=16),
            )
        else:
            self.global_start_button.text = "启动"
            self.global_start_button.icon = ft.Icons.PLAY_ARROW
            self.global_start_button.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=40, vertical=16),
            )
        if self.page:
            self.global_start_button.update()
    
    def _stop_all_services(self):
        """停止所有服务 - 弹出询问对话框"""
        # 检查QQ是否在运行
        qq_pid = self.process_manager.get_qq_pid()
        if qq_pid:
            # QQ在运行，询问是否也停止QQ
            self._show_stop_confirm_dialog()
        else:
            # QQ不在运行，直接停止
            self._do_stop_services(stop_qq=False)
    
    def _show_stop_confirm_dialog(self):
        """显示停止确认对话框"""
        def on_stop_all(e):
            dialog.open = False
            if self.page:
                self.page.update()
            self._do_stop_services(stop_qq=True)
        
        def on_stop_keep_qq(e):
            dialog.open = False
            if self.page:
                self.page.update()
            self._do_stop_services(stop_qq=False)
        
        def on_cancel(e):
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("停止服务"),
            content=ft.Text("检测到QQ正在运行，是否同时关闭QQ？"),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.TextButton("保留QQ", on_click=on_stop_keep_qq),
                ft.ElevatedButton(
                    "全部停止",
                    on_click=on_stop_all,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
    
    def _do_stop_services(self, stop_qq: bool = False):
        """实际执行停止服务
        
        Args:
            stop_qq: 是否同时停止QQ进程
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"停止所有服务, stop_qq={stop_qq}")
        
        try:
            # 停止所有托管进程（包括QQ进程，如果stop_qq为True）
            self.process_manager.stop_all(stop_qq=stop_qq)
            logger.info("所有服务已停止")
            
            # 更新按钮状态
            self._update_button_state(False)
            
            # 刷新进程资源显示
            self.refresh_process_resources()
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"停止服务失败: {ex}")
            self._show_error_dialog("停止失败", str(ex))
    
    def _on_global_start_click(self, e):
        """全局启动按钮点击处理"""
        import logging
        from datetime import datetime
        from core.log_collector import LogEntry
        logger = logging.getLogger(__name__)
        logger.info("全局启动按钮被点击")
        
        if self.is_downloading or self.is_downloading_llonebot or self.is_downloading_node or self.is_downloading_ffmpeg or self.is_downloading_ffprobe:
            logger.info("正在下载中，忽略点击")
            return
        
        # 立即更新按钮状态为"已启动"，提供即时反馈
        self._update_button_state(True)
        
        # 添加"正在启动..."日志
        if self.log_collector:
            entry = LogEntry(
                timestamp=datetime.now(),
                process_name="系统",
                level="stdout",
                message="正在启动..."
            )
            self.log_collector._logs.append(entry)
            # 触发回调更新UI
            for callback in self.log_collector._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass
        
        # 获取配置
        try:
            config = self.config_manager.load_config()
            logger.info(f"配置加载成功: {config}")
        except Exception as ex:
            logger.error(f"配置加载失败: {ex}")
            self._update_button_state(False)  # 恢复按钮状态
            self._show_error_dialog("配置加载失败", str(ex))
            return
        
        pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
        llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
        node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
        ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
        ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
        logger.info(f"PMHQ路径: {pmhq_path}")
        logger.info(f"LLOneBot路径: {llonebot_path}")
        logger.info(f"Node.exe路径: {node_path}")
        logger.info(f"FFmpeg.exe路径: {ffmpeg_path}")
        logger.info(f"FFprobe.exe路径: {ffprobe_path}")
        
        # 检查PMHQ文件是否存在
        pmhq_exists = self.downloader.check_file_exists(pmhq_path)
        logger.info(f"PMHQ文件存在: {pmhq_exists}")
        
        # 检查Node.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llonebot/node.exe）
        # 同时检查版本是否 >= 22
        node_exists = self.downloader.check_file_exists(node_path)
        if node_exists:
            # 检查版本
            if not self.downloader.check_node_version_valid(node_path):
                logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
                node_exists = False
        
        if not node_exists:
            # 尝试从环境变量查找
            system_node = self.downloader.check_node_available()
            if system_node:
                # 检查版本是否 >= 22
                if self.downloader.check_node_version_valid(system_node):
                    logger.info(f"在系统PATH中找到Node.js (版本>=22): {system_node}")
                    node_exists = True
                    # 更新配置使用系统的node
                    config["node_path"] = system_node
                    self.config_manager.save_config(config)
                else:
                    logger.warning(f"系统PATH中的Node.js版本低于22: {system_node}")
            
            if not node_exists:
                # 检查 bin/llonebot/node.exe
                local_node_path = "bin/llonebot/node.exe"
                if self.downloader.check_file_exists(local_node_path):
                    # 本地下载的node不需要检查版本（我们下载的肯定是新版）
                    logger.info(f"在本地目录找到Node.js: {local_node_path}")
                    node_exists = True
                    # 更新配置使用本地的node
                    config["node_path"] = local_node_path
                    self.config_manager.save_config(config)
        logger.info(f"Node.exe可用: {node_exists}")
        
        # 检查FFmpeg.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llonebot/ffmpeg.exe）
        ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
        if not ffmpeg_exists:
            # 尝试从环境变量查找
            system_ffmpeg = self.downloader.check_ffmpeg_available()
            if system_ffmpeg:
                logger.info(f"在系统PATH中找到FFmpeg: {system_ffmpeg}")
                ffmpeg_exists = True
                # 更新配置使用系统的ffmpeg
                config["ffmpeg_path"] = system_ffmpeg
                self.config_manager.save_config(config)
            else:
                # 检查 bin/llonebot/ffmpeg.exe
                local_ffmpeg_path = "bin/llonebot/ffmpeg.exe"
                if self.downloader.check_file_exists(local_ffmpeg_path):
                    logger.info(f"在本地目录找到FFmpeg: {local_ffmpeg_path}")
                    ffmpeg_exists = True
                    # 更新配置使用本地的ffmpeg
                    config["ffmpeg_path"] = local_ffmpeg_path
                    self.config_manager.save_config(config)
        logger.info(f"FFmpeg.exe可用: {ffmpeg_exists}")
        
        # 检查FFprobe.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llonebot/ffprobe.exe）
        ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
        if not ffprobe_exists:
            # 尝试从环境变量查找
            system_ffprobe = self.downloader.check_ffprobe_available()
            if system_ffprobe:
                logger.info(f"在系统PATH中找到FFprobe: {system_ffprobe}")
                ffprobe_exists = True
                # 更新配置使用系统的ffprobe
                config["ffprobe_path"] = system_ffprobe
                self.config_manager.save_config(config)
            else:
                # 检查 bin/llonebot/ffprobe.exe
                local_ffprobe_path = "bin/llonebot/ffprobe.exe"
                if self.downloader.check_file_exists(local_ffprobe_path):
                    logger.info(f"在本地目录找到FFprobe: {local_ffprobe_path}")
                    ffprobe_exists = True
                    # 更新配置使用本地的ffprobe
                    config["ffprobe_path"] = local_ffprobe_path
                    self.config_manager.save_config(config)
        logger.info(f"FFprobe.exe可用: {ffprobe_exists}")
        
        # 检查LLOneBot文件是否存在
        llonebot_exists = self.downloader.check_file_exists(llonebot_path)
        logger.info(f"LLOneBot文件存在: {llonebot_exists}")
        
        if not pmhq_exists:
            # 显示PMHQ下载对话框
            logger.info("PMHQ文件不存在，显示下载对话框")
            self._show_download_dialog()
        elif not node_exists:
            # 显示Node.exe下载对话框
            logger.info("Node.exe不可用，显示下载对话框")
            self._show_node_download_dialog()
        elif not ffmpeg_exists or not ffprobe_exists:
            # ffmpeg和ffprobe在同一个npm包中，下载一次即可
            logger.info("FFmpeg/FFprobe不可用，显示下载对话框")
            self._show_ffmpeg_download_dialog()
        elif not llonebot_exists:
            # 显示LLOneBot下载对话框
            logger.info("LLOneBot文件不存在，显示下载对话框")
            self._show_llonebot_download_dialog()
        else:
            # 直接启动服务
            logger.info("所有文件存在，直接启动服务")
            self._start_all_services()
    
    def _show_download_dialog(self):
        """显示下载对话框并开始下载"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        # 重置对话框状态
        self.download_progress_bar.value = 0
        self.download_progress_text.value = "准备下载..."
        self.download_status_text.value = "0 MB / 0 MB (0%)"
        self.download_cancel_button.disabled = False
        self.is_downloading = True
        
        # 显示对话框
        self.page.overlay.append(self.download_dialog)
        self.download_dialog.open = True
        self.page.update()
        logger.info("下载对话框已显示")
        
        # 开始下载（在后台线程中）
        import threading
        download_thread = threading.Thread(target=self._download_pmhq)
        download_thread.daemon = True
        download_thread.start()
        logger.info("下载线程已启动")
    
    def _download_pmhq(self):
        """下载PMHQ（在后台线程中执行）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载PMHQ")
        
        try:
            config = self.config_manager.load_config()
            pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
            pmhq_path = pmhq_path.replace('.exe', '.zip')
            logger.info(f"下载目标路径: {pmhq_path}")
            
            # 确保目录存在
            pmhq_dir = os.path.dirname(pmhq_path)
            if pmhq_dir and not os.path.exists(pmhq_dir):
                logger.info(f"创建目录: {pmhq_dir}")
                os.makedirs(pmhq_dir, exist_ok=True)
            
            # 下载文件
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading:
                    # 用户取消了下载
                    raise DownloadError("下载已取消")
                
                # 更新进度
                if total > 0:
                    progress = downloaded / total
                    self.download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.download_progress_text.value = f"正在下载... {percentage}%"
                    self.download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    if self.page:
                        self.page.update()
            
            success = self.downloader.download_pmhq(pmhq_path, progress_callback)
            
            if success and self.is_downloading:
                # 下载成功
                self.download_progress_text.value = "下载完成！"
                self.download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
                
                # 等待一秒后关闭对话框
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_dialog.open = False
                    self.page.update()
                
                # 检查Node.exe是否需要下载（同时检查版本 >= 22）
                config = self.config_manager.load_config()
                node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
                node_exists = self.downloader.check_file_exists(node_path)
                if node_exists and not self.downloader.check_node_version_valid(node_path):
                    logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
                    node_exists = False
                
                if not node_exists:
                    # 显示Node.exe下载对话框
                    self._show_node_download_dialog()
                else:
                    # 检查FFmpeg/FFprobe是否需要下载
                    ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
                    ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
                    ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
                    ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
                    
                    if not ffmpeg_exists or not ffprobe_exists:
                        # ffmpeg和ffprobe在同一个npm包中，下载一次即可
                        self._show_ffmpeg_download_dialog()
                    else:
                        # 检查LLOneBot是否需要下载
                        llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
                        llonebot_exists = self.downloader.check_file_exists(llonebot_path)
                        
                        if not llonebot_exists:
                            # 显示LLOneBot下载对话框
                            self._show_llonebot_download_dialog()
                        else:
                            # 启动所有服务
                            self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading:  # 只在未取消时显示错误
                self.download_progress_text.value = "下载失败"
                self.download_status_text.value = str(ex)
                self.download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        except Exception as ex:
            if self.is_downloading:
                self.download_progress_text.value = "下载失败"
                self.download_status_text.value = f"错误: {str(ex)}"
                self.download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        finally:
            self.is_downloading = False
    
    def _on_download_cancel_click(self, e):
        """取消PMHQ下载按钮点击处理"""
        self.is_downloading = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.download_dialog.open = False
            self.page.update()
    
    def _show_llonebot_download_dialog(self):
        """显示LLOneBot下载对话框并开始下载"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示LLOneBot下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        # 重置对话框状态
        self.llonebot_download_progress_bar.value = 0
        self.llonebot_download_progress_text.value = "准备下载..."
        self.llonebot_download_status_text.value = "0 MB / 0 MB (0%)"
        self.llonebot_download_cancel_button.disabled = False
        self.is_downloading_llonebot = True
        
        # 显示对话框
        self.page.overlay.append(self.download_llonebot_dialog)
        self.download_llonebot_dialog.open = True
        self.page.update()
        logger.info("LLOneBot下载对话框已显示")
        
        # 开始下载（在后台线程中）
        import threading
        download_thread = threading.Thread(target=self._download_llonebot)
        download_thread.daemon = True
        download_thread.start()
        logger.info("LLOneBot下载线程已启动")
    
    def _download_llonebot(self):
        """下载LLOneBot（在后台线程中执行）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载LLOneBot")
        
        try:
            config = self.config_manager.load_config()
            llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
            # 下载zip文件
            llonebot_zip_path = llonebot_path.replace('.js', '.zip')
            # 如果路径中没有.js，则直接添加.zip
            if not llonebot_zip_path.endswith('.zip'):
                llonebot_zip_path = llonebot_path + '.zip'
            logger.info(f"下载目标路径: {llonebot_zip_path}")
            
            # 确保目录存在
            llonebot_dir = os.path.dirname(llonebot_zip_path)
            if llonebot_dir and not os.path.exists(llonebot_dir):
                logger.info(f"创建目录: {llonebot_dir}")
                os.makedirs(llonebot_dir, exist_ok=True)
            
            # 下载文件
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_llonebot:
                    # 用户取消了下载
                    raise DownloadError("下载已取消")
                
                # 更新进度
                if total > 0:
                    progress = downloaded / total
                    self.llonebot_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.llonebot_download_progress_text.value = f"正在下载... {percentage}%"
                    self.llonebot_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    if self.page:
                        self.page.update()
            
            success = self.downloader.download_llonebot(llonebot_zip_path, progress_callback)
            
            if success and self.is_downloading_llonebot:
                # 下载成功
                self.llonebot_download_progress_text.value = "下载完成！"
                self.llonebot_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
                
                # 等待一秒后关闭对话框并启动服务
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_llonebot_dialog.open = False
                    self.page.update()
                
                # 启动所有服务
                self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_llonebot:  # 只在未取消时显示错误
                self.llonebot_download_progress_text.value = "下载失败"
                self.llonebot_download_status_text.value = str(ex)
                self.llonebot_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        except Exception as ex:
            if self.is_downloading_llonebot:
                self.llonebot_download_progress_text.value = "下载失败"
                self.llonebot_download_status_text.value = f"错误: {str(ex)}"
                self.llonebot_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        finally:
            self.is_downloading_llonebot = False
    
    def _on_llonebot_download_cancel_click(self, e):
        """取消LLOneBot下载按钮点击处理"""
        self.is_downloading_llonebot = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.download_llonebot_dialog.open = False
            self.page.update()
    
    def _show_node_download_dialog(self):
        """显示Node.exe下载对话框并开始下载"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示Node.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        # 重置对话框状态
        self.node_download_progress_bar.value = 0
        self.node_download_progress_text.value = "准备下载..."
        self.node_download_status_text.value = "0 MB / 0 MB (0%)"
        self.node_download_cancel_button.disabled = False
        self.is_downloading_node = True
        
        # 显示对话框
        self.page.overlay.append(self.download_node_dialog)
        self.download_node_dialog.open = True
        self.page.update()
        logger.info("Node.exe下载对话框已显示")
        
        # 开始下载（在后台线程中）
        import threading
        download_thread = threading.Thread(target=self._download_node)
        download_thread.daemon = True
        download_thread.start()
        logger.info("Node.exe下载线程已启动")
    
    def _download_node(self):
        """下载Node.exe（在后台线程中执行）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载Node.exe")
        
        try:
            config = self.config_manager.load_config()
            node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
            logger.info(f"下载目标路径: {node_path}")
            
            # 确保目录存在
            node_dir = os.path.dirname(node_path)
            if node_dir and not os.path.exists(node_dir):
                logger.info(f"创建目录: {node_dir}")
                os.makedirs(node_dir, exist_ok=True)
            
            # 下载文件
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_node:
                    # 用户取消了下载
                    raise DownloadError("下载已取消")
                
                # 更新进度
                if total > 0:
                    progress = downloaded / total
                    self.node_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.node_download_progress_text.value = f"正在下载... {percentage}%"
                    self.node_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    if self.page:
                        self.page.update()
            
            success = self.downloader.download_node(node_path, progress_callback)
            
            if success and self.is_downloading_node:
                # 下载成功
                self.node_download_progress_text.value = "下载完成！"
                self.node_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
                
                # 等待一秒后关闭对话框
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_node_dialog.open = False
                    self.page.update()
                
                # 检查FFmpeg/FFprobe是否需要下载（它们在同一个npm包中）
                config = self.config_manager.load_config()
                ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
                ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
                ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
                ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
                
                if not ffmpeg_exists or not ffprobe_exists:
                    # ffmpeg和ffprobe在同一个npm包中，下载一次即可
                    self._show_ffmpeg_download_dialog()
                else:
                    # 检查LLOneBot是否需要下载
                    llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
                    llonebot_exists = self.downloader.check_file_exists(llonebot_path)
                    
                    if not llonebot_exists:
                        # 显示LLOneBot下载对话框
                        self._show_llonebot_download_dialog()
                    else:
                        # 启动所有服务
                        self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_node:  # 只在未取消时显示错误
                self.node_download_progress_text.value = "下载失败"
                self.node_download_status_text.value = str(ex)
                self.node_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        except Exception as ex:
            if self.is_downloading_node:
                self.node_download_progress_text.value = "下载失败"
                self.node_download_status_text.value = f"错误: {str(ex)}"
                self.node_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        finally:
            self.is_downloading_node = False
    
    def _on_node_download_cancel_click(self, e):
        """取消Node.exe下载按钮点击处理"""
        self.is_downloading_node = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.download_node_dialog.open = False
            self.page.update()
    
    def _build_ffmpeg_download_dialog(self):
        """构建FFmpeg.exe下载对话框"""
        self.ffmpeg_download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.ffmpeg_download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.ffmpeg_download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.ffmpeg_download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_ffmpeg_download_cancel_click,
        )
        
        self.download_ffmpeg_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载FFmpeg/FFprobe"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "FFmpeg/FFprobe文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.ffmpeg_download_progress_text,
                    ft.Container(height=10),
                    self.ffmpeg_download_progress_bar,
                    ft.Container(height=10),
                    self.ffmpeg_download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.ffmpeg_download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _show_ffmpeg_download_dialog(self):
        """显示FFmpeg.exe下载对话框并开始下载"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示FFmpeg.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        # 重置对话框状态
        self.ffmpeg_download_progress_bar.value = 0
        self.ffmpeg_download_progress_text.value = "准备下载..."
        self.ffmpeg_download_status_text.value = "0 MB / 0 MB (0%)"
        self.ffmpeg_download_cancel_button.disabled = False
        self.is_downloading_ffmpeg = True
        
        # 显示对话框
        self.page.overlay.append(self.download_ffmpeg_dialog)
        self.download_ffmpeg_dialog.open = True
        self.page.update()
        logger.info("FFmpeg.exe下载对话框已显示")
        
        # 开始下载（在后台线程中）
        import threading
        download_thread = threading.Thread(target=self._download_ffmpeg)
        download_thread.daemon = True
        download_thread.start()
        logger.info("FFmpeg.exe下载线程已启动")
    
    def _download_ffmpeg(self):
        """下载FFmpeg.exe（在后台线程中执行）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载FFmpeg.exe")
        
        try:
            config = self.config_manager.load_config()
            ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
            logger.info(f"下载目标路径: {ffmpeg_path}")
            
            # 确保目录存在
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir and not os.path.exists(ffmpeg_dir):
                logger.info(f"创建目录: {ffmpeg_dir}")
                os.makedirs(ffmpeg_dir, exist_ok=True)
            
            # 下载文件
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_ffmpeg:
                    # 用户取消了下载
                    raise DownloadError("下载已取消")
                
                # 更新进度
                if total > 0:
                    progress = downloaded / total
                    self.ffmpeg_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.ffmpeg_download_progress_text.value = f"正在下载... {percentage}%"
                    self.ffmpeg_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    if self.page:
                        self.page.update()
            
            success = self.downloader.download_ffmpeg(ffmpeg_path, progress_callback)
            
            if success and self.is_downloading_ffmpeg:
                # 下载成功
                self.ffmpeg_download_progress_text.value = "下载完成！"
                self.ffmpeg_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
                
                # 等待一秒后关闭对话框
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_ffmpeg_dialog.open = False
                    self.page.update()
                
                # ffmpeg和ffprobe在同一个npm包中，下载ffmpeg后ffprobe也会存在
                # 检查LLOneBot是否需要下载
                config = self.config_manager.load_config()
                llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
                llonebot_exists = self.downloader.check_file_exists(llonebot_path)
                
                if not llonebot_exists:
                    # 显示LLOneBot下载对话框
                    self._show_llonebot_download_dialog()
                else:
                    # 启动所有服务
                    self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_ffmpeg:  # 只在未取消时显示错误
                self.ffmpeg_download_progress_text.value = "下载失败"
                self.ffmpeg_download_status_text.value = str(ex)
                self.ffmpeg_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        except Exception as ex:
            if self.is_downloading_ffmpeg:
                self.ffmpeg_download_progress_text.value = "下载失败"
                self.ffmpeg_download_status_text.value = f"错误: {str(ex)}"
                self.ffmpeg_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        finally:
            self.is_downloading_ffmpeg = False
    
    def _on_ffmpeg_download_cancel_click(self, e):
        """取消FFmpeg.exe下载按钮点击处理"""
        self.is_downloading_ffmpeg = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.download_ffmpeg_dialog.open = False
            self.page.update()
    
    def _build_ffprobe_download_dialog(self):
        """构建FFprobe.exe下载对话框"""
        self.ffprobe_download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.ffprobe_download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.ffprobe_download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.ffprobe_download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_ffprobe_download_cancel_click,
        )
        
        self.download_ffprobe_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载FFprobe.exe"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "FFprobe.exe文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.ffprobe_download_progress_text,
                    ft.Container(height=10),
                    self.ffprobe_download_progress_bar,
                    ft.Container(height=10),
                    self.ffprobe_download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.ffprobe_download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _show_ffprobe_download_dialog(self):
        """显示FFprobe.exe下载对话框并开始下载"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示FFprobe.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        # 重置对话框状态
        self.ffprobe_download_progress_bar.value = 0
        self.ffprobe_download_progress_text.value = "准备下载..."
        self.ffprobe_download_status_text.value = "0 MB / 0 MB (0%)"
        self.ffprobe_download_cancel_button.disabled = False
        self.is_downloading_ffprobe = True
        
        # 显示对话框
        self.page.overlay.append(self.download_ffprobe_dialog)
        self.download_ffprobe_dialog.open = True
        self.page.update()
        logger.info("FFprobe.exe下载对话框已显示")
        
        # 开始下载（在后台线程中）
        import threading
        download_thread = threading.Thread(target=self._download_ffprobe)
        download_thread.daemon = True
        download_thread.start()
        logger.info("FFprobe.exe下载线程已启动")
    
    def _download_ffprobe(self):
        """下载FFprobe.exe（在后台线程中执行）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载FFprobe.exe")
        
        try:
            config = self.config_manager.load_config()
            ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
            logger.info(f"下载目标路径: {ffprobe_path}")
            
            # 确保目录存在
            ffprobe_dir = os.path.dirname(ffprobe_path)
            if ffprobe_dir and not os.path.exists(ffprobe_dir):
                logger.info(f"创建目录: {ffprobe_dir}")
                os.makedirs(ffprobe_dir, exist_ok=True)
            
            # 下载文件
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_ffprobe:
                    # 用户取消了下载
                    raise DownloadError("下载已取消")
                
                # 更新进度
                if total > 0:
                    progress = downloaded / total
                    self.ffprobe_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.ffprobe_download_progress_text.value = f"正在下载... {percentage}%"
                    self.ffprobe_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    if self.page:
                        self.page.update()
            
            success = self.downloader.download_ffprobe(ffprobe_path, progress_callback)
            
            if success and self.is_downloading_ffprobe:
                # 下载成功
                self.ffprobe_download_progress_text.value = "下载完成！"
                self.ffprobe_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
                
                # 等待一秒后关闭对话框
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_ffprobe_dialog.open = False
                    self.page.update()
                
                # 检查LLOneBot是否需要下载
                config = self.config_manager.load_config()
                llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
                llonebot_exists = self.downloader.check_file_exists(llonebot_path)
                
                if not llonebot_exists:
                    # 显示LLOneBot下载对话框
                    self._show_llonebot_download_dialog()
                else:
                    # 启动所有服务
                    self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_ffprobe:  # 只在未取消时显示错误
                self.ffprobe_download_progress_text.value = "下载失败"
                self.ffprobe_download_status_text.value = str(ex)
                self.ffprobe_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        except Exception as ex:
            if self.is_downloading_ffprobe:
                self.ffprobe_download_progress_text.value = "下载失败"
                self.ffprobe_download_status_text.value = f"错误: {str(ex)}"
                self.ffprobe_download_cancel_button.text = "关闭"
                if self.page:
                    self.page.update()
        finally:
            self.is_downloading_ffprobe = False
    
    def _on_ffprobe_download_cancel_click(self, e):
        """取消FFprobe.exe下载按钮点击处理"""
        self.is_downloading_ffprobe = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.download_ffprobe_dialog.open = False
            self.page.update()
    
    def _start_all_services(self):
        """启动所有服务"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            config = self.config_manager.load_config()
            
            # 启动PMHQ
            pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
            qq_path = config.get("qq_path", "")
            auto_login_qq = config.get("auto_login_qq", "")
            headless = config.get("headless", False)
            
            # 如果QQ路径为空，尝试从注册表获取
            if not qq_path:
                from utils.qq_path import get_win_reg_qq_path
                reg_qq_path = get_win_reg_qq_path()
                if reg_qq_path and reg_qq_path.exists():
                    qq_path = str(reg_qq_path)
                    logger.info(f"从注册表获取到QQ路径: {qq_path}")
                    # 保存到配置
                    config["qq_path"] = qq_path
                    self.config_manager.save_config(config)
                else:
                    logger.warning("未找到QQ路径")
                    self._update_button_state(False)  # 恢复按钮状态
                    self._show_error_dialog(
                        "未找到QQ路径", 
                        "未能自动检测到QQ安装路径，请在「启动配置」中手动指定QQ路径，或安装QQ后重试。"
                    )
                    return
            
            # 检查QQ路径是否真实存在
            if not Path(qq_path).exists():
                logger.warning(f"QQ路径不存在: {qq_path}")
                self._update_button_state(False)  # 恢复按钮状态
                self._show_error_dialog(
                    "QQ路径无效", 
                    f"指定的QQ路径不存在：{qq_path}\n\n请在「启动配置」中重新指定正确的QQ路径。"
                )
                return
            
            if self.downloader.check_file_exists(pmhq_path):
                # 无头模式下，不传递auto_login_qq给pmhq，改用HTTP API登录
                pmhq_auto_login = "" if headless else auto_login_qq
                logger.info(f"正在启动PMHQ: {pmhq_path}, qq_path={qq_path}, auto_login_qq={pmhq_auto_login}, headless={headless}")
                pmhq_success = self.process_manager.start_pmhq(pmhq_path, qq_path=qq_path, auto_login_qq=pmhq_auto_login, headless=headless)
                if pmhq_success:
                    pmhq_pid = self.process_manager.get_pid("pmhq")
                    logger.info(f"PMHQ启动成功，PID: {pmhq_pid}")
                    # 将PMHQ进程附加到日志收集器
                    if self.log_collector:
                        pmhq_process = self.process_manager.get_process("pmhq")
                        if pmhq_process:
                            self.log_collector.attach_process("PMHQ", pmhq_process)
                            logger.info("PMHQ进程已附加到日志收集器")
                        else:
                            logger.warning("PMHQ进程对象为空，无法收集日志（可能是以管理员权限单独启动的）")
                    
                    # 无头模式下，使用HTTP API进行登录
                    if headless:
                        self._handle_headless_login(auto_login_qq, config)
                        return  # 登录流程会继续启动LLOneBot
                else:
                    logger.error("PMHQ启动失败")
                    self._update_button_state(False)  # 恢复按钮状态
                    self._show_error_dialog("启动失败", "PMHQ启动失败")
                    return
            
            # 继续启动LLOneBot
            self._start_llonebot_service(config)
            
        except Exception as ex:
            logger.error(f"启动服务失败: {ex}")
            self._update_button_state(False)  # 恢复按钮状态
            self._show_error_dialog("启动失败", str(ex))
    
    def _handle_headless_login(self, auto_login_qq: str, config: dict):
        """处理无头模式登录
        
        Args:
            auto_login_qq: 自动登录的QQ号
            config: 配置字典
        """
        import logging
        import threading
        import time
        logger = logging.getLogger(__name__)
        
        pmhq_port = self.process_manager.get_pmhq_port()
        if not pmhq_port:
            logger.error("无法获取PMHQ端口")
            self._update_button_state(False)  # 恢复按钮状态
            self._show_error_dialog("登录失败", "无法获取PMHQ端口")
            return
        
        def login_thread():
            # 等待PMHQ完全启动
            time.sleep(2)
            
            from utils.login_service import LoginService
            login_service = LoginService(pmhq_port)
            
            # 如果指定了自动登录QQ号，尝试快速登录
            if auto_login_qq:
                logger.info(f"尝试快速登录: {auto_login_qq}")
                
                # 获取可快速登录的账号列表
                quick_accounts = login_service.get_quick_login_accounts()
                
                # 检查指定的QQ号是否在可快速登录列表中
                target_account = None
                for acc in quick_accounts:
                    if acc.uin == auto_login_qq:
                        target_account = acc
                        break
                
                if target_account:
                    # 尝试快速登录
                    result = login_service.quick_login(auto_login_qq)
                    if result.success:
                        logger.info(f"快速登录成功: {auto_login_qq}")
                        # 等待登录完成，然后启动LLOneBot
                        self._wait_for_login_and_start_llonebot(config)
                        return
                    else:
                        logger.warning(f"快速登录失败: {result.error_msg}")
                        # 显示登录对话框
                        async def show_login_dialog():
                            self._show_login_dialog_with_error(pmhq_port, config, result.error_msg)
                        if self.page:
                            self.page.run_task(show_login_dialog)
                        return
                else:
                    logger.warning(f"指定的QQ号 {auto_login_qq} 不在可快速登录列表中")
            
            # 没有指定自动登录QQ号，或者指定的QQ号不可用，显示登录对话框
            async def show_login_dialog():
                self._show_login_dialog(pmhq_port, config)
            if self.page:
                self.page.run_task(show_login_dialog)
        
        thread = threading.Thread(target=login_thread, daemon=True)
        thread.start()
    
    def _wait_for_login_and_start_llonebot(self, config: dict):
        """等待登录完成并启动LLOneBot
        
        Args:
            config: 配置字典
        """
        import logging
        import threading
        import time
        import requests
        logger = logging.getLogger(__name__)
        
        pmhq_port = self.process_manager.get_pmhq_port()
        if not pmhq_port:
            return
        
        def wait_thread():
            url = f"http://127.0.0.1:{pmhq_port}"
            payload = {
                "type": "call",
                "data": {
                    "func": "getSelfInfo",
                    "args": []
                }
            }
            
            max_attempts = 60  # 最多等待60秒
            for _ in range(max_attempts):
                try:
                    response = requests.post(url, json=payload, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("type") == "call" and "data" in data:
                            result = data["data"].get("result", {})
                            uin = result.get("uin")
                            if uin:
                                logger.info(f"登录完成，uin: {uin}")
                                # 在主线程中启动LLOneBot
                                async def start_llonebot():
                                    self._start_llonebot_service(config)
                                if self.page:
                                    self.page.run_task(start_llonebot)
                                return
                except Exception:
                    pass
                time.sleep(1)
            
            logger.warning("等待登录超时")
        
        thread = threading.Thread(target=wait_thread, daemon=True)
        thread.start()
    
    def _show_login_dialog(self, pmhq_port: int, config: dict):
        """显示登录对话框
        
        Args:
            pmhq_port: PMHQ端口号
            config: 配置字典
        """
        from ui.login_dialog import LoginDialog
        
        def on_login_success(uin: str):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"登录成功: {uin}")
            # 启动LLOneBot
            self._start_llonebot_service(config)
        
        def on_cancel():
            import logging
            logger = logging.getLogger(__name__)
            logger.info("用户取消登录")
            # 更新按钮状态
            self._update_button_state(True)
            self.refresh_process_resources()
            if self.page:
                self.page.update()
        
        login_dialog = LoginDialog(
            page=self.page,
            pmhq_port=pmhq_port,
            on_login_success=on_login_success,
            on_cancel=on_cancel
        )
        login_dialog.show()
    
    def _show_login_dialog_with_error(self, pmhq_port: int, config: dict, error_msg: str):
        """显示带错误信息的登录对话框
        
        Args:
            pmhq_port: PMHQ端口号
            config: 配置字典
            error_msg: 错误信息
        """
        # 先显示错误提示
        self._show_error_dialog("快速登录失败", error_msg)
        
        # 然后显示登录对话框
        self._show_login_dialog(pmhq_port, config)
    
    def _start_llonebot_service(self, config: dict):
        """启动LLOneBot服务
        
        Args:
            config: 配置字典
        """
        import logging
        logger = logging.getLogger(__name__)
        
        node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
        llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
        
        # 检查node是否可用（配置路径 -> 环境变量 -> bin/llonebot/node.exe）
        # 同时检查版本是否 >= 22
        node_available = self.downloader.check_file_exists(node_path)
        if node_available and not self.downloader.check_node_version_valid(node_path):
            logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
            node_available = False
        
        if not node_available:
            # 尝试从环境变量查找
            system_node = self.downloader.check_node_available()
            if system_node and self.downloader.check_node_version_valid(system_node):
                node_path = system_node
                node_available = True
            else:
                # 检查 bin/llonebot/node.exe
                local_node_path = "bin/llonebot/node.exe"
                if self.downloader.check_file_exists(local_node_path):
                    node_path = local_node_path
                    node_available = True
        
        if node_available and self.downloader.check_file_exists(llonebot_path):
            logger.info(f"正在启动LLOneBot: node={node_path}, script={llonebot_path}")
            llbot_success = self.process_manager.start_llonebot(node_path, llonebot_path)
            if llbot_success:
                llbot_pid = self.process_manager.get_pid("llonebot")
                logger.info(f"LLOneBot启动成功，PID: {llbot_pid}")
                # 将LLOneBot进程附加到日志收集器
                if self.log_collector:
                    llbot_process = self.process_manager.get_process("llonebot")
                    if llbot_process:
                        self.log_collector.attach_process("LLOneBot", llbot_process)
                        logger.info("LLOneBot进程已附加到日志收集器")
            else:
                logger.error("LLOneBot启动失败")
                self._show_error_dialog("启动失败", "LLOneBot启动失败")
        
        # 更新按钮状态为"停止"
        self._update_button_state(True)
        
        # 刷新进程资源显示
        self.refresh_process_resources()
        if self.page:
            self.page.update()
    
    def _show_error_dialog(self, title: str, message: str):
        """显示错误对话框"""
        if not self.page:
            return
        
        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("确定", on_click=lambda e: self._close_dialog(error_dialog)),
            ],
        )
        
        self.page.overlay.append(error_dialog)
        error_dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """关闭对话框"""
        if self.page:
            dialog.open = False
            self.page.update()
    
    def set_page(self, page):
        """设置页面引用（用于显示对话框）"""
        self.page = page
    
    def update_title(self, title: str):
        """更新控制面板标题
        
        Args:
            title: 新标题
        """
        if self.title_text:
            self.title_text.value = title
            # 显示昵称时隐藏图标
            if self.title_icon:
                self.title_icon.visible = (title == "控制面板")
            if self.page:
                self.page.update()
    
    def _on_view_all_logs(self):
        """查看全部日志处理"""
        if self.on_navigate_logs:
            self.on_navigate_logs()
    
    def _get_cached_process(self, pid: int) -> psutil.Process:
        """获取缓存的进程对象，如果不存在或已失效则创建新的
        
        Args:
            pid: 进程ID
            
        Returns:
            psutil.Process对象
            
        Raises:
            psutil.NoSuchProcess: 进程不存在
        """
        # 检查缓存中是否有该进程
        if pid in self._process_cache:
            proc = self._process_cache[pid]
            # 验证进程是否仍然存在
            if proc.is_running():
                return proc
            else:
                # 进程已结束，从缓存中移除
                del self._process_cache[pid]
        
        # 创建新的进程对象并缓存
        proc = psutil.Process(pid)
        self._process_cache[pid] = proc
        # 首次调用cpu_percent进行初始化（返回0，但会记录采样点）
        proc.cpu_percent(interval=0)
        return proc
    
    def _cleanup_process_cache(self, valid_pids: set):
        """清理不再需要的进程缓存
        
        Args:
            valid_pids: 当前有效的PID集合
        """
        # 移除不在有效PID列表中的缓存
        stale_pids = [pid for pid in self._process_cache if pid not in valid_pids]
        for pid in stale_pids:
            del self._process_cache[pid]
    
    def refresh_process_resources(self):
        """刷新所有进程的资源使用情况
        
        Bot占用整合了管理器、PMHQ、LLOneBot的资源
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 汇总Bot占用（管理器 + PMHQ + LLOneBot）
            total_cpu = 0.0
            total_mem = 0.0
            
            # 收集当前有效的PID
            valid_pids = set()
            
            # 获取当前进程（管理器自身）
            manager_pid = os.getpid()
            valid_pids.add(manager_pid)
            try:
                current_process = self._get_cached_process(manager_pid)
                manager_cpu = current_process.cpu_percent(interval=0)
                manager_mem = current_process.memory_info().rss / 1024 / 1024
                total_cpu += manager_cpu
                total_mem += manager_mem
                logger.debug(f"管理器 - PID: {manager_pid}, CPU: {manager_cpu:.1f}%, 内存: {manager_mem:.1f}MB")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # 使用ProcessManager中的PID来监控进程
            pids = self.process_manager.get_all_pids()
            
            # 监控PMHQ进程
            pmhq_pid = pids.get("pmhq")
            pmhq_running = False
            if pmhq_pid:
                valid_pids.add(pmhq_pid)
                try:
                    proc = self._get_cached_process(pmhq_pid)
                    pmhq_cpu = proc.cpu_percent(interval=0)
                    pmhq_mem = proc.memory_info().rss / 1024 / 1024
                    total_cpu += pmhq_cpu
                    total_mem += pmhq_mem
                    pmhq_running = True
                    logger.debug(f"PMHQ - PID: {pmhq_pid}, CPU: {pmhq_cpu:.1f}%, 内存: {pmhq_mem:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 监控LLOneBot进程（Node.js）
            llonebot_pid = pids.get("llonebot")
            llonebot_running = False
            if llonebot_pid:
                valid_pids.add(llonebot_pid)
                try:
                    proc = self._get_cached_process(llonebot_pid)
                    llonebot_cpu = proc.cpu_percent(interval=0)
                    llonebot_mem = proc.memory_info().rss / 1024 / 1024
                    total_cpu += llonebot_cpu
                    total_mem += llonebot_mem
                    llonebot_running = True
                    logger.debug(f"LLOneBot - PID: {llonebot_pid}, CPU: {llonebot_cpu:.1f}%, 内存: {llonebot_mem:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 清理不再需要的进程缓存
            self._cleanup_process_cache(valid_pids)
            
            # Bot运行状态：PMHQ和LLOneBot都启动才算运行中
            bot_running = pmhq_running and llonebot_running
            logger.debug(f"Bot总占用 - CPU: {total_cpu:.1f}%, 内存: {total_mem:.1f}MB, 运行中: {bot_running}")
            
            # 更新Bot占用卡片
            self.bot_card.update_resources(total_cpu, total_mem, bot_running)
            
            # 获取QQ进程资源占用（通过PMHQ的getProcessInfo接口）
            qq_cpu = 0.0
            qq_mem = 0.0
            qq_running = False
            
            # 尝试从PMHQ获取QQ进程信息
            qq_pid = self.process_manager.fetch_qq_process_info()
            if qq_pid:
                qq_running = True
                qq_resources = self.process_manager.get_qq_resources()
                qq_cpu = qq_resources.get("cpu", 0.0)
                qq_mem = qq_resources.get("memory", 0.0)
            
            self.qq_card.update_resources(qq_cpu, qq_mem, qq_running)
                    
        except Exception as e:
            # 如果获取资源信息失败，使用默认值
            pass
    
    def refresh_logs(self, log_entries: List[dict]):
        """刷新日志预览
        
        Args:
            log_entries: 日志条目列表
        """
        self.log_card.update_logs(log_entries)
    
    def _on_new_log(self, entry):
        """新日志回调 - 实时更新首页日志预览
        
        Args:
            entry: LogEntry对象
        """
        import threading
        
        with self._log_update_lock:
            if self._log_update_scheduled:
                return
            self._log_update_scheduled = True
        
        # 延迟100ms批量更新，避免频繁刷新
        def update_logs():
            import time
            time.sleep(0.1)
            
            with self._log_update_lock:
                self._log_update_scheduled = False
            
            # 只在首页时更新
            if self.page and self.log_collector:
                try:
                    logs = self.log_collector.get_logs()
                    log_entries = []
                    for log in logs[-10:]:  # 只取最新10条
                        log_entries.append({
                            "timestamp": log.timestamp.strftime("%H:%M:%S"),
                            "process_name": log.process_name,
                            "level": log.level,
                            "message": log.message
                        })
                    self.log_card.update_logs(log_entries)
                    self.page.update()
                except Exception:
                    pass
        
        threading.Thread(target=update_logs, daemon=True).start()
    
    def clear_update_banner(self, component: str = None):
        """清除更新横幅
        
        Args:
            component: 要清除的组件名称（"app"/"pmhq"/"llonebot"），如果为None则清除所有
        """
        if component:
            # 从更新列表中移除指定组件
            component_map = {"app": "管理器", "pmhq": "PMHQ", "llonebot": "LLOneBot"}
            display_name = component_map.get(component, component)
            self._updates_found = [(name, info) for name, info in self._updates_found if name != display_name]
            
            # 如果还有其他更新，更新横幅文字
            if self._updates_found:
                update_names = [name for name, _ in self._updates_found]
                self.update_banner.content.controls[1].value = f"发现新版本: {', '.join(update_names)}"
            else:
                self.update_banner.visible = False
        else:
            # 清除所有更新
            self._updates_found = []
            self.update_banner.visible = False
        
        if self.page:
            self.page.update()
    
    def check_for_updates(self):
        """检查管理器、PMHQ和LLOneBot更新（进入控制面板时调用）"""
        import threading
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始检查组件更新...")
        
        def check_thread():
            try:
                updates_found = []
                
                # 获取配置中的路径
                config = self.config_manager.load_config()
                pmhq_path = config.get("pmhq_path", "")
                llonebot_path = config.get("llonebot_path", "")
                
                # 检查管理器更新
                app_version = self.version_detector.get_app_version()
                logger.info(f"管理器当前版本: {app_version}")
                if app_version and app_version != "未知":
                    app_package = NPM_PACKAGES.get("app")
                    app_repo = GITHUB_REPOS.get("app")
                    if app_package:
                        app_update = self.update_checker.check_update(app_package, app_version, app_repo)
                        logger.info(f"管理器更新检查: has_update={app_update.has_update}, latest={app_update.latest_version}, error={app_update.error}")
                        if app_update.has_update:
                            updates_found.append(("管理器", app_update))
                
                # 检查PMHQ更新
                pmhq_version = self.version_detector.detect_pmhq_version(pmhq_path)
                logger.info(f"PMHQ当前版本: {pmhq_version}")
                if pmhq_version and pmhq_version != "未知":
                    pmhq_package = NPM_PACKAGES.get("pmhq")
                    pmhq_repo = GITHUB_REPOS.get("pmhq")
                    if pmhq_package:
                        pmhq_update = self.update_checker.check_update(pmhq_package, pmhq_version, pmhq_repo)
                        logger.info(f"PMHQ更新检查: has_update={pmhq_update.has_update}, latest={pmhq_update.latest_version}")
                        if pmhq_update.has_update:
                            updates_found.append(("PMHQ", pmhq_update))
                
                # 检查LLOneBot更新
                llonebot_version = self.version_detector.detect_llonebot_version(llonebot_path)
                logger.info(f"LLOneBot当前版本: {llonebot_version}")
                if llonebot_version and llonebot_version != "未知":
                    llonebot_package = NPM_PACKAGES.get("llonebot")
                    llonebot_repo = GITHUB_REPOS.get("llonebot")
                    if llonebot_package:
                        llonebot_update = self.update_checker.check_update(llonebot_package, llonebot_version, llonebot_repo)
                        logger.info(f"LLOneBot更新检查: has_update={llonebot_update.has_update}, latest={llonebot_update.latest_version}")
                        if llonebot_update.has_update:
                            updates_found.append(("LLOneBot", llonebot_update))
                
                # 如果有更新，显示横幅
                if updates_found:
                    self._updates_found = updates_found
                    update_names = [name for name, _ in updates_found]
                    logger.info(f"发现更新: {', '.join(update_names)}")
                    
                    async def show_banner():
                        # 更新横幅文字
                        self.update_banner.content.controls[1].value = f"发现新版本: {', '.join(update_names)}"
                        self.update_banner.visible = True
                        if self.page:
                            self.page.update()
                    
                    if self.page:
                        self.page.run_task(show_banner)
                else:
                    logger.info("所有组件已是最新版本")
                        
            except Exception as ex:
                logger.error(f"检查更新失败: {ex}", exc_info=True)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def _on_update_click(self, e):
        """点击更新按钮"""
        if self._is_downloading_update:
            return
        
        if not hasattr(self, '_updates_found') or not self._updates_found:
            return
        
        self._start_component_updates()
    
    def _start_component_updates(self):
        """开始下载组件更新（PMHQ和LLOneBot）"""
        import threading
        import logging
        logger = logging.getLogger(__name__)
        
        self._is_downloading_update = True
        
        # 创建下载进度对话框
        progress_bar = ft.ProgressBar(width=300, value=0)
        progress_text = ft.Text("准备下载...", size=14)
        component_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
        
        download_dialog = ft.AlertDialog(
            title=ft.Text("正在更新组件"),
            content=ft.Column([
                component_text,
                progress_text,
                progress_bar,
            ], spacing=12, tight=True),
            modal=True,
        )
        
        if self.page:
            self.page.overlay.append(download_dialog)
            download_dialog.open = True
            self.page.update()
        
        def download_thread():
            try:
                success_list = []
                error_list = []
                
                for component_name, update_info in self._updates_found:
                    # 更新当前组件名称
                    async def update_component_name(name=component_name):
                        component_text.value = f"正在更新: {name}"
                        progress_bar.value = 0
                        progress_text.value = "准备下载..."
                        if self.page:
                            self.page.update()
                    
                    if self.page:
                        self.page.run_task(update_component_name)
                    
                    # 进度回调
                    def progress_callback(downloaded: int, total: int):
                        if total > 0:
                            progress = downloaded / total
                            
                            async def update_progress():
                                progress_bar.value = progress
                                progress_text.value = f"下载中... {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({progress * 100:.0f}%)"
                                if self.page:
                                    self.page.update()
                            
                            if self.page:
                                self.page.run_task(update_progress)
                    
                    try:
                        # 根据组件类型下载
                        if component_name == "管理器":
                            # 使用新的自动更新逻辑
                            import sys
                            current_pid = os.getpid()
                            if getattr(sys, 'frozen', False):
                                current_exe = sys.executable
                            else:
                                current_exe = os.path.abspath("lucky-lillia-desktop.exe")
                            
                            new_exe_path = self.downloader.download_app_update(current_exe, progress_callback)
                            batch_script = self.downloader.apply_app_update(new_exe_path, current_exe, current_pid)
                            self._pending_app_update_script = batch_script
                            success_list.append(component_name)
                        elif component_name == "PMHQ":
                            config = self.config_manager.load_config()
                            pmhq_path = config.get("pmhq_path", "bin/pmhq/pmhq-win-x64.exe")
                            save_path = pmhq_path.replace('.exe', '.zip')
                            self.downloader.download_pmhq(save_path, progress_callback)
                            success_list.append(component_name)
                        elif component_name == "LLOneBot":
                            config = self.config_manager.load_config()
                            llonebot_path = config.get("llonebot_path", "bin/llonebot/llonebot.js")
                            save_path = llonebot_path.replace('.js', '.zip')
                            if not save_path.endswith('.zip'):
                                save_path = llonebot_path + '.zip'
                            self.downloader.download_llonebot(save_path, progress_callback)
                            success_list.append(component_name)
                    except Exception as ex:
                        logger.error(f"下载{component_name}失败: {ex}")
                        error_list.append((component_name, str(ex)))
                
                # 下载完成
                async def on_complete():
                    self._is_downloading_update = False
                    download_dialog.open = False
                    self.update_banner.visible = False
                    self._updates_found = []
                    if self.page:
                        self.page.update()
                    
                    # 如果有管理器更新，显示重启提示
                    if "管理器" in success_list and self._pending_app_update_script:
                        self._show_app_update_restart_dialog(success_list, error_list)
                    else:
                        # 显示普通结果
                        if success_list and not error_list:
                            msg = f"以下组件已更新成功:\n{', '.join(success_list)}\n\n请重新启动服务以使用新版本。"
                            title = "更新完成"
                        elif error_list and not success_list:
                            msg = "更新失败:\n" + "\n".join([f"{name}: {err}" for name, err in error_list])
                            title = "更新失败"
                        else:
                            msg = f"成功: {', '.join(success_list)}\n失败: " + ", ".join([name for name, _ in error_list])
                            title = "部分更新完成"
                        
                        result_dialog = ft.AlertDialog(
                            title=ft.Text(title),
                            content=ft.Text(msg),
                            actions=[
                                ft.TextButton("确定", on_click=lambda e: self._close_dialog(result_dialog))
                            ],
                        )
                        if self.page:
                            self.page.overlay.append(result_dialog)
                            result_dialog.open = True
                            self.page.update()
                
                if self.page:
                    self.page.run_task(on_complete)
                    
            except Exception as ex:
                logger.error(f"下载更新失败: {ex}")
                
                async def on_error():
                    self._is_downloading_update = False
                    download_dialog.open = False
                    if self.page:
                        self.page.update()
                    
                    # 显示错误提示
                    error_dialog = ft.AlertDialog(
                        title=ft.Text("更新失败"),
                        content=ft.Text(f"下载更新时发生错误:\n\n{str(ex)}"),
                        actions=[
                            ft.TextButton("确定", on_click=lambda e: self._close_dialog(error_dialog))
                        ],
                    )
                    if self.page:
                        self.page.overlay.append(error_dialog)
                        error_dialog.open = True
                        self.page.update()
                
                if self.page:
                    self.page.run_task(on_error)
        
        # 启动下载线程
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """关闭对话框"""
        dialog.open = False
        if self.page:
            self.page.update()

    def _show_app_update_restart_dialog(self, success_list: list, error_list: list):
        """显示应用更新重启对话框
        
        Args:
            success_list: 成功更新的组件列表
            error_list: 失败的组件列表
        """
        import subprocess
        
        other_updates = [s for s in success_list if s != "管理器"]
        
        def on_restart(e):
            import os  # 在函数开始时导入os模块
            self._close_dialog(restart_dialog)
            # 启动更新脚本并退出当前程序
            if self._pending_app_update_script:
                batch_dir = os.path.dirname(self._pending_app_update_script)
                subprocess.Popen(
                    f'cmd /c start "更新" /D "{batch_dir}" "{self._pending_app_update_script}"',
                    shell=True
                )
                # 清空待执行的更新脚本，避免主窗口退出时重复执行
                self._pending_app_update_script = None
            # 直接退出程序，不触发关闭确认对话框
            if self.page:
                # 通过主窗口实例直接调用关闭方法
                from ui.main_window import MainWindow
                # 获取主窗口实例（通过页面的用户数据）
                main_window = getattr(self.page, 'main_window', None)
                if main_window and hasattr(main_window, '_do_close'):
                    main_window._do_close(force_exit=True)  # 强制快速退出
                else:
                    # 备用方案：直接退出进程
                    os._exit(0)
        
        def on_later(e):
            self._close_dialog(restart_dialog)
            # 提示用户
            other_msg = ""
            if other_updates:
                other_msg = f"\n\n其他组件（{', '.join(other_updates)}）已更新，请重新启动服务以使用新版本。"
            
            info_dialog = ft.AlertDialog(
                title=ft.Text("稍后更新"),
                content=ft.Text(
                    f"管理器更新已下载完成。\n\n"
                    f"退出程序时将自动完成更新。{other_msg}"
                ),
                actions=[
                    ft.TextButton("确定", on_click=lambda e: self._close_dialog(info_dialog))
                ],
            )
            if self.page:
                self.page.overlay.append(info_dialog)
                info_dialog.open = True
                self.page.update()
        
        # 构建消息
        msg = "管理器新版本已下载完成！\n\n需要重启程序以完成更新。"
        if other_updates:
            msg += f"\n\n其他组件（{', '.join(other_updates)}）也已更新。"
        if error_list:
            msg += f"\n\n以下组件更新失败: {', '.join([name for name, _ in error_list])}"
        msg += "\n\n是否立即重启？"
        
        restart_dialog = ft.AlertDialog(
            title=ft.Text("更新已就绪"),
            content=ft.Text(msg),
            actions=[
                ft.TextButton("稍后", on_click=on_later),
                ft.ElevatedButton("立即重启", on_click=on_restart),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if self.page:
            self.page.overlay.append(restart_dialog)
            restart_dialog.open = True
            self.page.update()
    
    def get_pending_update_script(self) -> Optional[str]:
        """获取待执行的更新脚本路径
        
        Returns:
            更新脚本路径，如果没有待更新则返回None
        """
        return self._pending_app_update_script
    
    def has_pending_app_update(self) -> bool:
        """检查是否有待执行的应用更新
        
        Returns:
            如果有待更新返回True
        """
        return self._pending_app_update_script is not None
