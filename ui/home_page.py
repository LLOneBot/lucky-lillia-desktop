"""首页UI模块 - 显示进程状态、快速操作和系统监控"""
from pathlib import Path

import flet as ft
from typing import Optional, Callable, List
from datetime import datetime
import psutil
import os
from core.process_manager import ProcessManager, ProcessStatus
from core.config_manager import ConfigManager
from utils.downloader import Downloader, DownloadError
from utils.constants import DEFAULT_CONFIG


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


class HomePage:
    """首页组件"""
    
    def __init__(self, process_manager: ProcessManager,
                 config_manager: ConfigManager,
                 on_navigate_logs: Optional[Callable] = None):
        """初始化首页
        
        Args:
            process_manager: 进程管理器实例
            config_manager: 配置管理器实例
            on_navigate_logs: 导航到日志页面的回调
        """
        self.process_manager = process_manager
        self.config_manager = config_manager
        self.on_navigate_logs = on_navigate_logs
        self.downloader = Downloader()
        self.control = None
        self.page = None
        self.download_dialog = None
        self.is_downloading = False
        
    def build(self):
        """构建UI组件"""
        # 创建四个进程资源卡片
        self.manager_card = ProcessResourceCard(
            "manager",
            "本管理器",
            ft.Icons.DASHBOARD
        )
        self.manager_card.build()
        
        self.pmhq_card = ProcessResourceCard(
            "pmhq",
            "PMHQ",
            ft.Icons.TERMINAL,
            show_download_status=True  # PMHQ显示下载状态
        )
        self.pmhq_card.build()
        
        self.node_card = ProcessResourceCard(
            "llbot",
            "LLBot",
            ft.Icons.CODE
        )
        self.node_card.build()
        
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
        
        # 创建全局启动按钮
        self.global_start_button = ft.ElevatedButton(
            text="启动所有服务",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_global_start_click,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=20,
            ),
            height=50,
        )
        
        # 创建下载对话框
        self._build_download_dialog()
        
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
                
                # 全局启动按钮
                ft.Container(
                    content=self.global_start_button,
                    alignment=ft.alignment.center,
                ),
                
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
                        content=self.manager_card.control,
                        expand=1
                    ),
                    ft.Container(
                        content=self.pmhq_card.control,
                        expand=1
                    ),
                    ft.Container(
                        content=self.node_card.control,
                        expand=1
                    ),
                    ft.Container(
                        content=self.qq_card.control,
                        expand=1
                    ),
                ], spacing=16),
                
                # 日志预览
                ft.Row([
                    ft.Icon(ft.Icons.ARTICLE, size=24, color=ft.Colors.PRIMARY),
                    ft.Text(
                        "最近日志",
                        size=22,
                        weight=ft.FontWeight.W_600
                    ),
                ], spacing=10),
                ft.Container(
                    content=self.log_card.control,
                    height=340,
                ),
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=28,
        )
        return self.control
    
    def _build_download_dialog(self):
        """构建下载对话框"""
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
                        "PMHQ可执行文件不存在，需要从GitHub下载。",
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
    
    def _on_global_start_click(self, e):
        """全局启动按钮点击处理"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("全局启动按钮被点击")
        
        if self.is_downloading:
            logger.info("正在下载中，忽略点击")
            return
        
        # 获取配置
        try:
            config = self.config_manager.load_config()
            logger.info(f"配置加载成功: {config}")
        except Exception as ex:
            logger.error(f"配置加载失败: {ex}")
            self._show_error_dialog("配置加载失败", str(ex))
            return
        
        pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
        logger.info(f"PMHQ路径: {pmhq_path}")
        
        # 检查PMHQ文件是否存在
        file_exists = self.downloader.check_file_exists(pmhq_path)
        logger.info(f"PMHQ文件存在: {file_exists}")
        
        if not file_exists:
            # 显示下载对话框
            logger.info("PMHQ文件不存在，显示下载对话框")
            self._show_download_dialog()
        else:
            # 直接启动服务
            logger.info("PMHQ文件存在，直接启动服务")
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
                
                # 等待一秒后关闭对话框并启动服务
                import time
                time.sleep(1)
                
                if self.page:
                    self.download_dialog.open = False
                    self.page.update()
                
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
        """取消下载按钮点击处理"""
        self.is_downloading = False
        if self.page:
            self.download_dialog.open = False
            self.page.update()
    
    def _start_all_services(self):
        """启动所有服务"""
        try:
            config = self.config_manager.load_config()
            
            # 启动PMHQ
            pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
            if self.downloader.check_file_exists(pmhq_path):
                pmhq_success = self.process_manager.start_pmhq(pmhq_path)
                if not pmhq_success:
                    self._show_error_dialog("启动失败", "PMHQ启动失败")
                    return
            
            # 启动LLOneBot
            node_path = config.get("node_path", DEFAULT_CONFIG["node_path"])
            llonebot_path = config.get("llonebot_path", DEFAULT_CONFIG["llonebot_path"])
            
            if self.downloader.check_file_exists(node_path) and self.downloader.check_file_exists(llonebot_path):
                llbot_success = self.process_manager.start_llonebot(node_path, llonebot_path)
                if not llbot_success:
                    self._show_error_dialog("启动失败", "LLOneBot启动失败")
            
        except Exception as ex:
            self._show_error_dialog("启动失败", str(ex))
    
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
    
    def _on_view_all_logs(self):
        """查看全部日志处理"""
        if self.on_navigate_logs:
            self.on_navigate_logs()
    
    def refresh_process_resources(self):
        """刷新所有进程的资源使用情况"""
        try:
            # 重置所有卡片状态为未运行
            pmhq_found = False
            node_found = False
            qq_found = False
            
            # 检查PMHQ文件是否存在
            pmhq_file_exists = True
            try:
                config = self.config_manager.load_config()
                pmhq_path = config.get("pmhq_path", DEFAULT_CONFIG["pmhq_path"])
                pmhq_file_exists = self.downloader.check_file_exists(pmhq_path)
            except:
                pass
            
            # 获取当前进程（管理器自身）
            current_process = psutil.Process(os.getpid())
            manager_cpu = current_process.cpu_percent(interval=0)  # 非阻塞
            manager_mem = current_process.memory_info().rss / 1024 / 1024  # 转换为MB
            self.manager_card.update_resources(manager_cpu, manager_mem, True)
            
            # 查找并更新其他进程
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = proc.info['name'].lower()
                    
                    # PMHQ进程
                    if 'pmhq' in name and not pmhq_found:
                        cpu = proc.cpu_percent(interval=0)  # 非阻塞
                        mem = proc.info['memory_info'].rss / 1024 / 1024
                        self.pmhq_card.update_resources(cpu, mem, True, pmhq_file_exists)
                        pmhq_found = True
                    
                    # LLBot进程（Node.js运行的LLOneBot）
                    elif ('node' in name or 'llbot' in name or 'llonebot' in name) and not node_found:
                        cpu = proc.cpu_percent(interval=0)  # 非阻塞
                        mem = proc.info['memory_info'].rss / 1024 / 1024
                        self.node_card.update_resources(cpu, mem, True)
                        node_found = True
                    
                    # QQ进程
                    elif 'qq' in name and not qq_found:
                        cpu = proc.cpu_percent(interval=0)  # 非阻塞
                        mem = proc.info['memory_info'].rss / 1024 / 1024
                        self.qq_card.update_resources(cpu, mem, True)
                        qq_found = True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 更新未找到的进程为未运行状态
            if not pmhq_found:
                self.pmhq_card.update_resources(0, 0, False, pmhq_file_exists)
            if not node_found:
                self.node_card.update_resources(0, 0, False)
            if not qq_found:
                self.qq_card.update_resources(0, 0, False)
                    
        except Exception as e:
            # 如果获取资源信息失败，使用默认值
            pass
    
    def refresh_logs(self, log_entries: List[dict]):
        """刷新日志预览
        
        Args:
            log_entries: 日志条目列表
        """
        self.log_card.update_logs(log_entries)
