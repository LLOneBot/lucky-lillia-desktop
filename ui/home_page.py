"""首页/控制面板"""
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
        self.file_exists = True
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
        """更新资源使用情况"""
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.is_running = is_running
        self.file_exists = file_exists
        
        if self.show_download_status and not file_exists:
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
        
        # 除以核心数得到相对于整个系统的百分比
        cpu_count = psutil.cpu_count() or 1
        normalized_cpu = cpu_percent / cpu_count
        self.cpu_text.value = f"CPU: {normalized_cpu:.1f}%"
        self.cpu_progress.value = min(normalized_cpu / 100.0, 1.0)
        
        self.memory_text.value = f"内存: {memory_mb:.0f} MB"
        total_memory_mb = psutil.virtual_memory().total / 1024 / 1024
        self.memory_progress.value = min(memory_mb / total_memory_mb, 1.0)


class ResourceMonitorCard:
    """系统资源监控卡片组件"""
    
    def __init__(self):
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
        self._last_log_hash = None
        
    def build(self):
        """构建UI组件"""
        # 预创建10个日志行控件，避免频繁创建/销毁导致 Flutter 内存泄漏
        self._log_rows = []
        for _ in range(10):
            icon = ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.BLUE_600)
            text = ft.Text(
                "",
                size=13,
                color=ft.Colors.ON_SURFACE,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
                expand=True
            )
            row = ft.Row([icon, text], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START, visible=False)
            self._log_rows.append((row, icon, text))
        
        self._empty_text = ft.Text(
            "暂无日志",
            size=14,
            color=ft.Colors.GREY_600,
            italic=True
        )
        self._empty_container = ft.Container(
            content=self._empty_text,
            expand=True,
            alignment=ft.alignment.center,
        )
        
        self.log_list = ft.Column(
            controls=[self._empty_container] + [row for row, _, _ in self._log_rows],
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
        if self.on_view_all_callback:
            self.on_view_all_callback()
    
    def update_logs(self, log_entries: List[dict]):
        """更新日志显示
        
        Args:
            log_entries: 日志条目列表，每个条目包含timestamp, process_name, level, message
        """
        entries = log_entries[-10:]  # 只显示最新10条
        
        # 计算日志哈希，只在内容变化时才更新UI
        if entries:
            # 使用最后一条日志的时间戳和消息作为哈希
            last_entry = entries[-1]
            current_hash = (
                len(entries),
                last_entry.get("timestamp", ""),
                last_entry.get("message", "")[:50]  # 只取前50字符
            )
        else:
            current_hash = (0, "", "")
        
        # 如果内容没变化，跳过更新
        if current_hash == self._last_log_hash:
            return
        
        self._last_log_hash = current_hash
        self.log_entries = entries
        
        if not self.log_entries:
            # 显示空状态，隐藏所有日志行
            self._empty_container.visible = True
            for row, _, _ in self._log_rows:
                row.visible = False
        else:
            # 隐藏空状态
            self._empty_container.visible = False
            
            for i, (row, icon_ctrl, text_ctrl) in enumerate(self._log_rows):
                if i < len(self.log_entries):
                    entry = self.log_entries[i]
                    timestamp = entry.get("timestamp", "")
                    process_name = entry.get("process_name", "")
                    level = entry.get("level", "stdout")
                    message = entry.get("message", "")
                    
                    if level == "stderr":
                        text_ctrl.color = ft.Colors.RED_700
                        icon_ctrl.name = ft.Icons.ERROR_OUTLINE
                        icon_ctrl.color = ft.Colors.RED_600
                    else:
                        text_ctrl.color = ft.Colors.ON_SURFACE
                        icon_ctrl.name = ft.Icons.INFO_OUTLINE
                        icon_ctrl.color = ft.Colors.BLUE_600
                    if process_name == "LLBot":
                        text_ctrl.value = message
                    else:
                        text_ctrl.value = f"[{timestamp}] [{process_name}] {message}"
                    row.visible = True
                else:
                    row.visible = False
            
            self.log_list.scroll_to(offset=-1, duration=100)


class HomePage:
    """首页组件"""
    
    def __init__(self, process_manager: ProcessManager,
                 config_manager: ConfigManager,
                 log_collector=None,
                 on_navigate_logs: Optional[Callable] = None,
                 version_detector: Optional[VersionDetector] = None,
                 update_manager=None):
        """初始化首页
        
        Args:
            process_manager: 进程管理器实例
            config_manager: 配置管理器实例
            log_collector: 日志收集器实例（可选）
            on_navigate_logs: 导航到日志页面的回调
            version_detector: 版本检测器实例（可选）
            update_manager: 更新管理器实例（可选）
        """
        self.process_manager = process_manager
        self.config_manager = config_manager
        self.log_collector = log_collector
        self.on_navigate_logs = on_navigate_logs
        self.version_detector = version_detector or VersionDetector()
        self.update_manager = update_manager
        self.downloader = Downloader()
        self.control = None
        self.page = None
        self.download_dialog = None
        self.is_downloading = False
        self.download_llbot_dialog = None
        self.is_downloading_llbot = False
        self.download_node_dialog = None
        self.is_downloading_node = False
        self.download_ffmpeg_dialog = None
        self.is_downloading_ffmpeg = False
        self.download_ffprobe_dialog = None
        self.is_downloading_ffprobe = False
        self._is_downloading_update = False
        self._updates_found = []
        self._pending_app_update_script = None
        
        self._log_update_scheduled = False
        self._log_update_lock = __import__('threading').Lock()
        self._log_update_pending = False
    
    def _safe_update(self):
        """线程安全的 UI 更新，确保在主线程执行"""
        if self.page:
            try:
                self.page.run_thread(lambda: self.page.update() if self.page else None)
            except Exception:
                pass
        
    def build(self):
        """构建UI组件"""
        # 创建进程资源卡片（Bot占用整合了管理器、PMHQ、LLBot）
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
        self._build_llbot_download_dialog()
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
    
    def _build_llbot_download_dialog(self):
        self.llbot_download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=10,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
        )
        
        self.llbot_download_progress_text = ft.Text(
            "准备下载...",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.llbot_download_status_text = ft.Text(
            "0 MB / 0 MB (0%)",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.llbot_download_cancel_button = ft.TextButton(
            "取消",
            on_click=self._on_llbot_download_cancel_click,
        )
        
        self.download_llbot_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("下载LLBot"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "LLBot文件不存在，需要下载。",
                        size=14,
                    ),
                    ft.Container(height=20),
                    self.llbot_download_progress_text,
                    ft.Container(height=10),
                    self.llbot_download_progress_bar,
                    ft.Container(height=10),
                    self.llbot_download_status_text,
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=450,
            ),
            actions=[
                self.llbot_download_cancel_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _build_node_download_dialog(self):
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
        # 检查QQ是否在运行
        qq_pid = self.process_manager.get_qq_pid()
        if qq_pid:
            # QQ在运行，询问是否也停止QQ
            self._show_stop_confirm_dialog()
        else:
            # QQ不在运行，直接停止
            self._do_stop_services(stop_qq=False)
    
    def _show_stop_confirm_dialog(self):
        def on_confirm(e):
            if self.page:
                self.page.close(dialog)
            self._do_stop_services(stop_qq=True)
        
        def on_cancel(e):
            if self.page:
                self.page.close(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("停止服务"),
            content=ft.Text("确定要停止所有服务吗？"),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton(
                    "停止",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.open(dialog)
    
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
        import logging
        import shutil
        from datetime import datetime
        from core.log_collector import LogEntry
        logger = logging.getLogger(__name__)
        logger.info("全局启动按钮被点击")
        
        if self.is_downloading or self.is_downloading_llbot or self.is_downloading_node or self.is_downloading_ffmpeg or self.is_downloading_ffprobe:
            logger.info("正在下载中，忽略点击")
            return
        
        # 迁移旧版 llonebot 数据目录到 llbot
        old_data_dir = Path("bin/llonebot/data")
        new_data_dir = Path("bin/llbot/data")
        if old_data_dir.exists() and not new_data_dir.exists():
            try:
                new_data_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(old_data_dir, new_data_dir)
                logger.info(f"已迁移数据目录: {old_data_dir} -> {new_data_dir}")
            except Exception as ex:
                logger.warning(f"迁移数据目录失败: {ex}")
        
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
            # 立即刷新日志预览
            self._refresh_log_preview()
        
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
        llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
        node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
        ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
        ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
        logger.info(f"PMHQ路径: {pmhq_path}")
        logger.info(f"LLBot路径: {llbot_path}")
        logger.info(f"Node.exe路径: {node_path}")
        logger.info(f"FFmpeg.exe路径: {ffmpeg_path}")
        logger.info(f"FFprobe.exe路径: {ffprobe_path}")
        
        # 检查PMHQ文件是否存在
        pmhq_exists = self.downloader.check_file_exists(pmhq_path)
        logger.info(f"PMHQ文件存在: {pmhq_exists}")
        
        # 检查Node.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llbot/node.exe）
        # 同时检查版本是否 >= 22
        node_exists = self.downloader.check_file_exists(node_path)
        if node_exists:
            if not self.downloader.check_node_version_valid(node_path):
                logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
                node_exists = False
        
        if not node_exists:
            system_node = self.downloader.check_node_available()
            if system_node:
                if self.downloader.check_node_version_valid(system_node):
                    logger.info(f"在系统PATH中找到Node.js (版本>=22): {system_node}")
                    node_exists = True
                    config["node_path"] = system_node
                    self.config_manager.save_config(config)
                else:
                    logger.warning(f"系统PATH中的Node.js版本低于22: {system_node}")
            
            if not node_exists:
                local_node_path = "bin/llbot/node.exe"
                if self.downloader.check_file_exists(local_node_path):
                    logger.info(f"在本地目录找到Node.js: {local_node_path}")
                    node_exists = True
                    config["node_path"] = local_node_path
                    self.config_manager.save_config(config)
        logger.info(f"Node.exe可用: {node_exists}")
        
        # 检查FFmpeg.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llbot/ffmpeg.exe）
        ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
        if not ffmpeg_exists:
            system_ffmpeg = self.downloader.check_ffmpeg_available()
            if system_ffmpeg:
                logger.info(f"在系统PATH中找到FFmpeg: {system_ffmpeg}")
                ffmpeg_exists = True
                config["ffmpeg_path"] = system_ffmpeg
                self.config_manager.save_config(config)
            else:
                local_ffmpeg_path = "bin/llbot/ffmpeg.exe"
                if self.downloader.check_file_exists(local_ffmpeg_path):
                    logger.info(f"在本地目录找到FFmpeg: {local_ffmpeg_path}")
                    ffmpeg_exists = True
                    config["ffmpeg_path"] = local_ffmpeg_path
                    self.config_manager.save_config(config)
        logger.info(f"FFmpeg.exe可用: {ffmpeg_exists}")
        
        # 检查FFprobe.exe文件是否存在（先检查配置路径，再检查环境变量，最后检查bin/llbot/ffprobe.exe）
        ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
        if not ffprobe_exists:
            system_ffprobe = self.downloader.check_ffprobe_available()
            if system_ffprobe:
                logger.info(f"在系统PATH中找到FFprobe: {system_ffprobe}")
                ffprobe_exists = True
                config["ffprobe_path"] = system_ffprobe
                self.config_manager.save_config(config)
            else:
                local_ffprobe_path = "bin/llbot/ffprobe.exe"
                if self.downloader.check_file_exists(local_ffprobe_path):
                    logger.info(f"在本地目录找到FFprobe: {local_ffprobe_path}")
                    ffprobe_exists = True
                    config["ffprobe_path"] = local_ffprobe_path
                    self.config_manager.save_config(config)
        logger.info(f"FFprobe.exe可用: {ffprobe_exists}")
        
        # 检查LLBot文件是否存在
        llbot_exists = self.downloader.check_file_exists(llbot_path)
        logger.info(f"LLBot文件存在: {llbot_exists}")
        
        if not pmhq_exists:
            logger.info("PMHQ文件不存在，显示下载对话框")
            self._show_download_dialog()
        elif not node_exists:
            logger.info("Node.exe不可用，显示下载对话框")
            self._show_node_download_dialog()
        elif not ffmpeg_exists or not ffprobe_exists:
            logger.info("FFmpeg/FFprobe不可用，显示下载对话框")
            self._show_ffmpeg_download_dialog()
        elif not llbot_exists:
            logger.info("LLBot文件不存在，显示下载对话框")
            self._show_llbot_download_dialog()
        else:
            logger.info("所有文件存在，直接启动服务")
            self._start_all_services()
    
    def _show_download_dialog(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        self.download_progress_bar.value = 0
        self.download_progress_text.value = "准备下载..."
        self.download_status_text.value = "0 MB / 0 MB (0%)"
        self.download_cancel_button.disabled = False
        self.download_cancel_button.text = "取消"
        self.is_downloading = True
        
        if self.page:
            self.page.open(self.download_dialog)
        logger.info("下载对话框已显示")
        
        import threading
        download_thread = threading.Thread(target=self._download_pmhq)
        download_thread.daemon = True
        download_thread.start()
        logger.info("下载线程已启动")
    
    def _download_pmhq(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载PMHQ")
        
        try:
            config = self.config_manager.load_config()
            pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
            pmhq_path = pmhq_path.replace('.exe', '.zip')
            logger.info(f"下载目标路径: {pmhq_path}")
            
            pmhq_dir = os.path.dirname(pmhq_path)
            if pmhq_dir and not os.path.exists(pmhq_dir):
                logger.info(f"创建目录: {pmhq_dir}")
                os.makedirs(pmhq_dir, exist_ok=True)
            
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading:
                    raise DownloadError("下载已取消")
                
                if total > 0:
                    progress = downloaded / total
                    self.download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.download_progress_text.value = f"正在下载... {percentage}%"
                    self.download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    self._safe_update()
            
            success = self.downloader.download_pmhq(pmhq_path, progress_callback)
            
            if success and self.is_downloading:
                self.download_progress_text.value = "下载完成！"
                self.download_cancel_button.text = "关闭"
                self._safe_update()
                
                import time
                time.sleep(1)
                
                if self.page:
                    self.page.close(self.download_dialog)
                
                # 检查Node.exe是否需要下载（同时检查版本 >= 22）
                config = self.config_manager.load_config()
                node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
                node_exists = self.downloader.check_file_exists(node_path)
                if node_exists and not self.downloader.check_node_version_valid(node_path):
                    logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
                    node_exists = False
                
                if not node_exists:
                    self._show_node_download_dialog()
                else:
                    ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
                    ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
                    ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
                    ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
                    
                    if not ffmpeg_exists or not ffprobe_exists:
                        self._show_ffmpeg_download_dialog()
                    else:
                        llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
                        llbot_exists = self.downloader.check_file_exists(llbot_path)
                        
                        if not llbot_exists:
                            self._show_llbot_download_dialog()
                        else:
                            self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading:
                self.download_progress_text.value = "下载失败"
                self.download_status_text.value = str(ex)
                self.download_cancel_button.text = "关闭"
                self._safe_update()
        except Exception as ex:
            if self.is_downloading:
                self.download_progress_text.value = "下载失败"
                self.download_status_text.value = f"错误: {str(ex)}"
                self.download_cancel_button.text = "关闭"
                self._safe_update()
        finally:
            self.is_downloading = False
    
    def _on_download_cancel_click(self, e):
        self.is_downloading = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.page.close(self.download_dialog)
    
    def _show_llbot_download_dialog(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示LLBot下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        self.llbot_download_progress_bar.value = 0
        self.llbot_download_progress_text.value = "准备下载..."
        self.llbot_download_status_text.value = "0 MB / 0 MB (0%)"
        self.llbot_download_cancel_button.disabled = False
        self.llbot_download_cancel_button.text = "取消"
        self.is_downloading_llbot = True
        
        self.page.open(self.download_llbot_dialog)
        logger.info("LLBot下载对话框已显示")
        
        import threading
        download_thread = threading.Thread(target=self._download_llbot)
        download_thread.daemon = True
        download_thread.start()
        logger.info("LLBot下载线程已启动")
    
    def _download_llbot(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载LLBot")
        
        try:
            config = self.config_manager.load_config()
            llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
            llbot_zip_path = llbot_path.replace('.js', '.zip')
            if not llbot_zip_path.endswith('.zip'):
                llbot_zip_path = llbot_path + '.zip'
            logger.info(f"下载目标路径: {llbot_zip_path}")
            
            llbot_dir = os.path.dirname(llbot_zip_path)
            if llbot_dir and not os.path.exists(llbot_dir):
                logger.info(f"创建目录: {llbot_dir}")
                os.makedirs(llbot_dir, exist_ok=True)
            
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_llbot:
                    raise DownloadError("下载已取消")
                
                if total > 0:
                    progress = downloaded / total
                    self.llbot_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.llbot_download_progress_text.value = f"正在下载... {percentage}%"
                    self.llbot_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    self._safe_update()
            
            success = self.downloader.download_llbot(llbot_zip_path, progress_callback)
            
            if success and self.is_downloading_llbot:
                self.llbot_download_progress_text.value = "下载完成！"
                self.llbot_download_cancel_button.text = "关闭"
                self._safe_update()
                
                import time
                time.sleep(1)
                
                if self.page:
                    self.page.close(self.download_llbot_dialog)
                
                self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_llbot:
                self.llbot_download_progress_text.value = "下载失败"
                self.llbot_download_status_text.value = str(ex)
                self.llbot_download_cancel_button.text = "关闭"
                self._safe_update()
        except Exception as ex:
            if self.is_downloading_llbot:
                self.llbot_download_progress_text.value = "下载失败"
                self.llbot_download_status_text.value = f"错误: {str(ex)}"
                self.llbot_download_cancel_button.text = "关闭"
                self._safe_update()
        finally:
            self.is_downloading_llbot = False
    
    def _on_llbot_download_cancel_click(self, e):
        self.is_downloading_llbot = False
        self._update_button_state(False)
        if self.page:
            self.page.close(self.download_llbot_dialog)
    
    def _show_node_download_dialog(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示Node.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        self.node_download_progress_bar.value = 0
        self.node_download_progress_text.value = "准备下载..."
        self.node_download_status_text.value = "0 MB / 0 MB (0%)"
        self.node_download_cancel_button.disabled = False
        self.node_download_cancel_button.text = "取消"
        self.is_downloading_node = True
        
        self.page.open(self.download_node_dialog)
        logger.info("Node.exe下载对话框已显示")
        
        import threading
        download_thread = threading.Thread(target=self._download_node)
        download_thread.daemon = True
        download_thread.start()
        logger.info("Node.exe下载线程已启动")
    
    def _download_node(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载Node.exe")
        
        try:
            config = self.config_manager.load_config()
            node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
            logger.info(f"下载目标路径: {node_path}")
            
            node_dir = os.path.dirname(node_path)
            if node_dir and not os.path.exists(node_dir):
                logger.info(f"创建目录: {node_dir}")
                os.makedirs(node_dir, exist_ok=True)
            
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_node:
                    raise DownloadError("下载已取消")
                
                if total > 0:
                    progress = downloaded / total
                    self.node_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.node_download_progress_text.value = f"正在下载... {percentage}%"
                    self.node_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    self._safe_update()
            
            success = self.downloader.download_node(node_path, progress_callback)
            
            if success and self.is_downloading_node:
                self.node_download_progress_text.value = "下载完成！"
                self.node_download_cancel_button.text = "关闭"
                self._safe_update()
                
                import time
                time.sleep(1)
                
                if self.page:
                    self.page.close(self.download_node_dialog)
                
                config = self.config_manager.load_config()
                ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
                ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
                ffmpeg_exists = self.downloader.check_file_exists(ffmpeg_path)
                ffprobe_exists = self.downloader.check_file_exists(ffprobe_path)
                
                if not ffmpeg_exists or not ffprobe_exists:
                    self._show_ffmpeg_download_dialog()
                else:
                    llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
                    llbot_exists = self.downloader.check_file_exists(llbot_path)
                    
                    if not llbot_exists:
                        self._show_llbot_download_dialog()
                    else:
                        self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_node:
                self.node_download_progress_text.value = "下载失败"
                self.node_download_status_text.value = str(ex)
                self.node_download_cancel_button.text = "关闭"
                self._safe_update()
        except Exception as ex:
            if self.is_downloading_node:
                self.node_download_progress_text.value = "下载失败"
                self.node_download_status_text.value = f"错误: {str(ex)}"
                self.node_download_cancel_button.text = "关闭"
                self._safe_update()
        finally:
            self.is_downloading_node = False
    
    def _on_node_download_cancel_click(self, e):
        self.is_downloading_node = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.page.close(self.download_node_dialog)
    
    def _build_ffmpeg_download_dialog(self):
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示FFmpeg.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        self.ffmpeg_download_progress_bar.value = 0
        self.ffmpeg_download_progress_text.value = "准备下载..."
        self.ffmpeg_download_status_text.value = "0 MB / 0 MB (0%)"
        self.ffmpeg_download_cancel_button.disabled = False
        self.ffmpeg_download_cancel_button.text = "取消"
        self.is_downloading_ffmpeg = True
        
        self.page.open(self.download_ffmpeg_dialog)
        logger.info("FFmpeg.exe下载对话框已显示")
        
        import threading
        download_thread = threading.Thread(target=self._download_ffmpeg)
        download_thread.daemon = True
        download_thread.start()
        logger.info("FFmpeg.exe下载线程已启动")
    
    def _download_ffmpeg(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载FFmpeg.exe")
        
        try:
            config = self.config_manager.load_config()
            ffmpeg_path = config.get("ffmpeg_path", DEFAULT_CONFIG["ffmpeg_path"])
            logger.info(f"下载目标路径: {ffmpeg_path}")
            
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir and not os.path.exists(ffmpeg_dir):
                logger.info(f"创建目录: {ffmpeg_dir}")
                os.makedirs(ffmpeg_dir, exist_ok=True)
            
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_ffmpeg:
                    raise DownloadError("下载已取消")
                
                if total > 0:
                    progress = downloaded / total
                    self.ffmpeg_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.ffmpeg_download_progress_text.value = f"正在下载... {percentage}%"
                    self.ffmpeg_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    self._safe_update()
            
            success = self.downloader.download_ffmpeg(ffmpeg_path, progress_callback)
            
            if success and self.is_downloading_ffmpeg:
                self.ffmpeg_download_progress_text.value = "下载完成！"
                self.ffmpeg_download_cancel_button.text = "关闭"
                self._safe_update()
                
                import time
                time.sleep(1)
                
                if self.page:
                    self.page.close(self.download_ffmpeg_dialog)
                
                config = self.config_manager.load_config()
                llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
                llbot_exists = self.downloader.check_file_exists(llbot_path)
                
                if not llbot_exists:
                    self._show_llbot_download_dialog()
                else:
                    self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_ffmpeg:
                self.ffmpeg_download_progress_text.value = "下载失败"
                self.ffmpeg_download_status_text.value = str(ex)
                self.ffmpeg_download_cancel_button.text = "关闭"
                self._safe_update()
        except Exception as ex:
            if self.is_downloading_ffmpeg:
                self.ffmpeg_download_progress_text.value = "下载失败"
                self.ffmpeg_download_status_text.value = f"错误: {str(ex)}"
                self.ffmpeg_download_cancel_button.text = "关闭"
                self._safe_update()
        finally:
            self.is_downloading_ffmpeg = False
    
    def _on_ffmpeg_download_cancel_click(self, e):
        self.is_downloading_ffmpeg = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.page.close(self.download_ffmpeg_dialog)
    
    def _build_ffprobe_download_dialog(self):
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info("显示FFprobe.exe下载对话框")
        
        if not self.page:
            logger.error("页面引用为空，无法显示对话框")
            return
        
        self.ffprobe_download_progress_bar.value = 0
        self.ffprobe_download_progress_text.value = "准备下载..."
        self.ffprobe_download_status_text.value = "0 MB / 0 MB (0%)"
        self.ffprobe_download_cancel_button.disabled = False
        self.ffprobe_download_cancel_button.text = "取消"
        self.is_downloading_ffprobe = True
        
        self.page.open(self.download_ffprobe_dialog)
        logger.info("FFprobe.exe下载对话框已显示")
        
        import threading
        download_thread = threading.Thread(target=self._download_ffprobe)
        download_thread.daemon = True
        download_thread.start()
        logger.info("FFprobe.exe下载线程已启动")
    
    def _download_ffprobe(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始下载FFprobe.exe")
        
        try:
            config = self.config_manager.load_config()
            ffprobe_path = config.get("ffprobe_path", DEFAULT_CONFIG["ffprobe_path"])
            logger.info(f"下载目标路径: {ffprobe_path}")
            
            ffprobe_dir = os.path.dirname(ffprobe_path)
            if ffprobe_dir and not os.path.exists(ffprobe_dir):
                logger.info(f"创建目录: {ffprobe_dir}")
                os.makedirs(ffprobe_dir, exist_ok=True)
            
            def progress_callback(downloaded: int, total: int):
                if not self.is_downloading_ffprobe:
                    raise DownloadError("下载已取消")
                
                if total > 0:
                    progress = downloaded / total
                    self.ffprobe_download_progress_bar.value = progress
                    
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    percentage = int(progress * 100)
                    
                    self.ffprobe_download_progress_text.value = f"正在下载... {percentage}%"
                    self.ffprobe_download_status_text.value = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage}%)"
                    
                    self._safe_update()
            
            success = self.downloader.download_ffprobe(ffprobe_path, progress_callback)
            
            if success and self.is_downloading_ffprobe:
                self.ffprobe_download_progress_text.value = "下载完成！"
                self.ffprobe_download_cancel_button.text = "关闭"
                self._safe_update()
                
                import time
                time.sleep(1)
                
                if self.page:
                    self.page.close(self.download_ffprobe_dialog)
                
                config = self.config_manager.load_config()
                llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
                llbot_exists = self.downloader.check_file_exists(llbot_path)
                
                if not llbot_exists:
                    self._show_llbot_download_dialog()
                else:
                    self._start_all_services()
            
        except DownloadError as ex:
            if self.is_downloading_ffprobe:
                self.ffprobe_download_progress_text.value = "下载失败"
                self.ffprobe_download_status_text.value = str(ex)
                self.ffprobe_download_cancel_button.text = "关闭"
                self._safe_update()
        except Exception as ex:
            if self.is_downloading_ffprobe:
                self.ffprobe_download_progress_text.value = "下载失败"
                self.ffprobe_download_status_text.value = f"错误: {str(ex)}"
                self.ffprobe_download_cancel_button.text = "关闭"
                self._safe_update()
        finally:
            self.is_downloading_ffprobe = False
    
    def _on_ffprobe_download_cancel_click(self, e):
        self.is_downloading_ffprobe = False
        self._update_button_state(False)  # 恢复按钮状态
        if self.page:
            self.page.close(self.download_ffprobe_dialog)
    
    def _start_all_services(self):
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
                    config["qq_path"] = qq_path
                    self.config_manager.save_config(config)
                else:
                    logger.warning("未找到QQ路径")
                    self._update_button_state(False)
                    self._show_qq_install_dialog(config)
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
                        return  # 登录流程会继续启动LLBot
                else:
                    logger.error("PMHQ启动失败")
                    self._update_button_state(False)
                    self._show_error_dialog("启动失败", "PMHQ启动失败")
                    return
            
            self._start_llbot_service(config)
            
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
                    result = login_service.quick_login(auto_login_qq)
                    if result.success:
                        logger.info(f"快速登录成功: {auto_login_qq}")
                        self._wait_for_login_and_start_llbot(config)
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
    
    def _wait_for_login_and_start_llbot(self, config: dict):
        import logging
        import threading
        import time
        from utils.http_client import HttpClient
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
            
            client = HttpClient(timeout=5)
            max_attempts = 60
            for _ in range(max_attempts):
                try:
                    resp = client.post(url, json_data=payload, timeout=5)
                    if resp.status == 200:
                        data = resp.json()
                        if data.get("type") == "call" and "data" in data:
                            result = data["data"].get("result", {})
                            uin = result.get("uin")
                            if uin:
                                logger.info(f"登录完成，uin: {uin}")
                                async def start_llbot():
                                    self._start_llbot_service(config)
                                if self.page:
                                    self.page.run_task(start_llbot)
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
            self._start_llbot_service(config)
        
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
    
    def _start_llbot_service(self, config: dict):
        import logging
        logger = logging.getLogger(__name__)
        
        node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
        llbot_path = config.get("llbot_path", DEFAULT_CONFIG["llbot_path"])
        
        # 检查node是否可用（配置路径 -> 环境变量 -> bin/llbot/node.exe）
        node_available = self.downloader.check_file_exists(node_path)
        if node_available and not self.downloader.check_node_version_valid(node_path):
            logger.warning(f"配置路径的Node.js版本低于22: {node_path}")
            node_available = False
        
        if not node_available:
            system_node = self.downloader.check_node_available()
            if system_node and self.downloader.check_node_version_valid(system_node):
                node_path = system_node
                node_available = True
            else:
                local_node_path = "bin/llbot/node.exe"
                if self.downloader.check_file_exists(local_node_path):
                    node_path = local_node_path
                    node_available = True
        
        if node_available and self.downloader.check_file_exists(llbot_path):
            logger.info(f"正在启动LLBot: node={node_path}, script={llbot_path}")
            llbot_success = self.process_manager.start_llbot(node_path, llbot_path)
            if llbot_success:
                llbot_pid = self.process_manager.get_pid("llbot")
                logger.info(f"LLBot启动成功，PID: {llbot_pid}")
                if self.log_collector:
                    llbot_process = self.process_manager.get_process("llbot")
                    if llbot_process:
                        self.log_collector.attach_process("LLBot", llbot_process)
                        logger.info("LLBot进程已附加到日志收集器")
            else:
                logger.error("LLBot启动失败")
                self._show_error_dialog("启动失败", "LLBot启动失败")
        
        self._update_button_state(True)
        self.refresh_process_resources()
        if self.page:
            self.page.update()
    
    def _show_error_dialog(self, title: str, message: str):
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
        
        self.page.open(error_dialog)
    
    def _show_qq_install_dialog(self, config: dict):
        import logging
        import threading
        import subprocess
        import tempfile
        from utils.qq_path import get_win_reg_qq_path
        logger = logging.getLogger(__name__)
        
        if not self.page:
            return
        
        progress_bar = ft.ProgressBar(width=350, value=0, visible=False)
        progress_text = ft.Text("", size=12, visible=False)
        status_text = ft.Text("未检测到QQ安装，是否下载并安装QQ？", size=14)
        
        confirm_btn = ft.ElevatedButton("下载并安装")
        cancel_btn = ft.TextButton("取消")
        
        qq_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("未找到QQ", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    status_text,
                    ft.Container(height=10),
                    progress_bar,
                    progress_text,
                ], tight=True),
                width=400,
            ),
            actions=[cancel_btn, confirm_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        def do_download_and_install(e):
            confirm_btn.disabled = True
            cancel_btn.disabled = True
            progress_bar.visible = True
            progress_text.visible = True
            status_text.value = "正在下载QQ安装程序..."
            self.page.update()
            
            def download_task():
                try:
                    temp_dir = tempfile.gettempdir()
                    qq_installer_path = os.path.join(temp_dir, "QQ_installer.exe")
                    
                    def on_progress(downloaded, total):
                        if total > 0:
                            percent = downloaded / total
                            progress_bar.value = percent
                            progress_text.value = f"{downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({percent * 100:.1f}%)"
                        else:
                            progress_text.value = f"已下载: {downloaded / 1024 / 1024:.1f} MB"
                        try:
                            self.page.update()
                        except Exception:
                            pass
                    
                    self.downloader.download_qq(qq_installer_path, progress_callback=on_progress)
                    
                    status_text.value = "下载完成，正在静默安装QQ..."
                    progress_bar.value = None
                    self.page.update()
                    
                    subprocess.run([qq_installer_path, "/S"], capture_output=True, timeout=300)
                    
                    try:
                        os.unlink(qq_installer_path)
                    except Exception:
                        pass
                    
                    reg_qq_path = get_win_reg_qq_path()
                    if reg_qq_path and reg_qq_path.exists():
                        logger.info(f"QQ安装成功: {reg_qq_path}")
                        self._close_dialog(qq_dialog)
                        
                        config["qq_path"] = str(reg_qq_path)
                        self.config_manager.save_config(config)
                        
                        snackbar = ft.SnackBar(content=ft.Text("QQ安装成功！"), bgcolor=ft.Colors.GREEN_700)
                        self.page.overlay.append(snackbar)
                        snackbar.open = True
                        self.page.update()
                        
                        self._on_global_start_click(None)
                    else:
                        raise Exception("安装完成但未能检测到QQ路径")
                        
                except subprocess.TimeoutExpired:
                    logger.error("QQ安装超时")
                    status_text.value = "安装超时，请手动安装QQ后重试"
                    progress_bar.visible = False
                    progress_text.visible = False
                    confirm_btn.disabled = False
                    cancel_btn.disabled = False
                    self.page.update()
                except Exception as ex:
                    logger.error(f"QQ下载或安装失败: {ex}")
                    status_text.value = f"安装失败: {ex}"
                    progress_bar.visible = False
                    progress_text.visible = False
                    confirm_btn.disabled = False
                    cancel_btn.disabled = False
                    self.page.update()
            
            threading.Thread(target=download_task, daemon=True).start()
        
        def do_cancel(e):
            self._close_dialog(qq_dialog)
        
        confirm_btn.on_click = do_download_and_install
        cancel_btn.on_click = do_cancel
        
        self.page.open(qq_dialog)
    
    def _close_dialog(self, dialog):
        if self.page:
            self.page.close(dialog)
    
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
        if self.on_navigate_logs:
            self.on_navigate_logs()
    
    def _get_process_resources(self, pid: int) -> tuple:
        """获取进程的 CPU 和内存使用情况
        
        Returns:
            (cpu_percent, memory_mb, is_running) 或 (0.0, 0.0, False) 如果进程不存在
        """
        try:
            proc = psutil.Process(pid)
            if not proc.is_running():
                return 0.0, 0.0, False
            cpu = proc.cpu_percent(interval=0.05)
            mem = proc.memory_info().rss / 1024 / 1024
            return cpu, mem, True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0, 0.0, False
    
    def refresh_process_resources(self):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            total_cpu = 0.0
            total_mem = 0.0
            
            # 管理器自身
            manager_pid = os.getpid()
            cpu, mem, _ = self._get_process_resources(manager_pid)
            total_cpu += cpu
            total_mem += mem
            logger.debug(f"管理器 - PID: {manager_pid}, CPU: {cpu:.1f}%, 内存: {mem:.1f}MB")
            
            pids = self.process_manager.get_all_pids()
            
            # PMHQ
            pmhq_pid = pids.get("pmhq")
            pmhq_running = False
            if pmhq_pid:
                cpu, mem, pmhq_running = self._get_process_resources(pmhq_pid)
                if pmhq_running:
                    total_cpu += cpu
                    total_mem += mem
                    logger.debug(f"PMHQ - PID: {pmhq_pid}, CPU: {cpu:.1f}%, 内存: {mem:.1f}MB")
            
            # LLBot
            llbot_pid = pids.get("llbot")
            llbot_running = False
            if llbot_pid:
                cpu, mem, llbot_running = self._get_process_resources(llbot_pid)
                if llbot_running:
                    total_cpu += cpu
                    total_mem += mem
                    logger.debug(f"LLBot - PID: {llbot_pid}, CPU: {cpu:.1f}%, 内存: {mem:.1f}MB")
            
            # Bot运行状态：PMHQ和LLBot都启动才算运行中
            bot_running = pmhq_running and llbot_running
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
    
    def _refresh_log_preview(self):
        if self.log_collector:
            logs = self.log_collector.get_recent_logs(10)
            log_entries = [
                {
                    "timestamp": log.timestamp.strftime("%H:%M:%S"),
                    "process_name": log.process_name,
                    "level": log.level,
                    "message": log.message,
                }
                for log in logs
            ]
            self.log_card.update_logs(log_entries)
            if self.page:
                self.page.update()
    
    def _on_new_log(self, entry):
        """新日志回调 - 已废弃，日志更新由资源监控线程统一处理
        
        保留此方法是为了兼容性，但不再执行任何操作。
        
        Args:
            entry: LogEntry对象
        """
        # 不再使用回调方式更新日志，避免频繁创建线程导致的内存泄漏
        # 日志更新已由 main_window.py 中的资源监控线程统一处理
        pass
    
    def clear_update_banner(self, component: str = None):
        if component:
            component_map = {"app": "管理器", "pmhq": "PMHQ", "llbot": "LLBot"}
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
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.update_manager:
            logger.warning("UpdateManager未设置，跳过更新检查")
            return
        
        logger.info("开始检查组件更新...")
        
        def on_check_complete(all_check_results):
            updates_found = [(name, info) for name, info in all_check_results if info.has_update]
            if updates_found:
                update_names = [name for name, _ in updates_found]
                logger.info(f"发现更新: {', '.join(update_names)}")
                
                async def show_banner():
                    self.update_banner.content.controls[1].value = f"发现新版本: {', '.join(update_names)}"
                    self.update_banner.visible = True
                    if self.page:
                        self.page.update()
                
                if self.page:
                    self.page.run_task(show_banner)
            else:
                logger.info("所有组件已是最新版本")
        
        self.update_manager.set_callbacks(on_check_complete=on_check_complete)
        
        config = self.config_manager.load_config()
        pmhq_path = config.get("pmhq_path", "")
        llbot_path = config.get("llbot_path", "")
        
        versions = {
            "app": self.version_detector.get_app_version(),
            "pmhq": self.version_detector.detect_pmhq_version(pmhq_path),
            "llbot": self.version_detector.detect_llbot_version(llbot_path)
        }
        
        # 异步检查更新
        self.update_manager.check_updates_async(versions)
    
    def _on_update_click(self, e):
        if not self.update_manager or self.update_manager.is_downloading:
            return
        
        if not self.update_manager.has_updates:
            return
        
        # 弹出确认对话框
        self._show_update_confirm_dialog()
    
    def _show_update_confirm_dialog(self):
        running = self.update_manager.has_running_processes()
        
        def on_cancel(e):
            if self.page:
                self.page.close(confirm_dialog)
        
        def on_confirm(e):
            if self.page:
                self.page.close(confirm_dialog)
            self._start_component_updates()
        
        if running:
            content_text = (
                "进程正在运行中。\n\n"
                "更新需要先停止进程，更新完成后会自动重新启动服务。"
            )
        else:
            updates = self.update_manager.updates_found
            updates_str = "、".join([name for name, _ in updates])
            content_text = f"确定要更新 {updates_str} 吗？"
        
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("确认更新"),
            content=ft.Text(content_text),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton("确定更新" if not running else "停止并更新", on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.open(confirm_dialog)
    
    def _start_component_updates(self):
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.update_manager:
            return
        
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
            actions=[],  # 空的actions列表，避免渲染问题
        )
        
        if self.page:
            self.page.open(download_dialog)
        
        # 设置回调
        def on_download_status(status: str):
            async def update_status():
                component_text.value = status
                if self.page:
                    self.page.update()
            if self.page:
                self.page.run_task(update_status)
        
        def on_download_progress(name: str, downloaded: int, total: int):
            if total > 0:
                progress = downloaded / total
                async def update_progress():
                    progress_bar.value = progress
                    progress_text.value = f"下载中... {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({progress * 100:.0f}%)"
                    if self.page:
                        self.page.update()
                if self.page:
                    self.page.run_task(update_progress)
        
        def on_download_complete(success_list, error_list, had_running_processes):
            async def on_complete():
                # 先显示完成状态
                progress_bar.value = 1.0
                progress_text.value = "更新完成！"
                if self.page:
                    self.page.update()
                
                # 短暂延迟后关闭对话框
                import asyncio
                await asyncio.sleep(0.5)
                
                # 关闭下载对话框
                if self.page:
                    self.page.close(download_dialog)
                self.update_banner.visible = False
                if self.page:
                    self.page.update()
                
                # 如果有管理器更新，显示重启提示
                if "管理器" in success_list and self.update_manager.has_pending_app_update():
                    self._show_app_update_restart_dialog(success_list, error_list)
                elif had_running_processes:
                    # 只有之前有进程在运行，更新完成后才自动重新启动服务
                    self._auto_restart_after_update()
            
            if self.page:
                self.page.run_task(on_complete)
        
        self.update_manager.set_callbacks(
            on_download_status=on_download_status,
            on_download_progress=on_download_progress,
            on_download_complete=on_download_complete
        )
        
        # 异步下载所有更新
        self.update_manager.download_all_updates_async()

    def _auto_restart_after_update(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("更新完成，自动重新启动服务...")
        
        # 直接调用启动服务的方法
        self._on_global_start_click(None)

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
            script = self.update_manager.pending_app_update_script if self.update_manager else None
            if script:
                batch_dir = os.path.dirname(script)
                subprocess.Popen(
                    f'cmd /c start "更新" /D "{batch_dir}" "{script}"',
                    shell=True
                )
                # 清空待执行的更新脚本，避免主窗口退出时重复执行
                if self.update_manager:
                    self.update_manager.clear_pending_app_update()
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
            
            def close_info_dialog(ev):
                if self.page:
                    self.page.close(info_dialog)
            
            info_dialog = ft.AlertDialog(
                title=ft.Text("稍后更新"),
                content=ft.Text(
                    f"管理器更新已下载完成。\n\n"
                    f"退出程序时将自动完成更新。{other_msg}"
                ),
                actions=[
                    ft.TextButton("确定", on_click=close_info_dialog)
                ],
            )
            if self.page:
                self.page.open(info_dialog)
        
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
            self.page.open(restart_dialog)
    
    def get_pending_update_script(self) -> Optional[str]:
        """获取待执行的更新脚本路径
        
        Returns:
            更新脚本路径，如果没有待更新则返回None
        """
        return self.update_manager.pending_app_update_script if self.update_manager else None
    
    def has_pending_app_update(self) -> bool:
        """检查是否有待执行的应用更新
        
        Returns:
            如果有待更新返回True
        """
        return self.update_manager.has_pending_app_update() if self.update_manager else False
