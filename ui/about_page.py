"""关于/版本页面UI模块 - 显示版本信息和更新检查"""

import flet as ft
import time
import logging
from typing import Optional, Callable, Dict
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker, UpdateInfo
from core.config_manager import ConfigManager
from core.process_manager import ProcessManager, ProcessStatus
from utils.constants import APP_NAME, NPM_PACKAGES, GITHUB_REPOS
import threading
import os
import sys


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径（支持 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class VersionInfoCard:
    """版本信息卡片组件"""
    
    def __init__(self, component_name: str, display_name: str, 
                 on_update_click: Optional[Callable[[str], None]] = None):
        """初始化版本信息卡片"""
        self.component_name = component_name
        self.display_name = display_name
        self.current_version = "未知"
        self.latest_version = None
        self.has_update = False
        self.release_url = ""
        self.control = None
        self.on_update_click = on_update_click
        
    def build(self):
        """构建UI组件"""
        self.version_text = ft.Text(
            f"当前版本: {self.current_version}",
            size=15,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.W_500
        )
        
        # 更新图标
        self.update_icon = ft.Icon(name=ft.Icons.UPDATE, color=ft.Colors.ORANGE_400, size=20, visible=False)
        
        # 新版本文字
        self.update_text = ft.Text("", size=12, color=ft.Colors.ORANGE_600, weight=ft.FontWeight.BOLD, visible=False)
        
        # 查看详情按钮
        self.detail_button = ft.TextButton(
            "查看详情",
            on_click=lambda e: self._open_release_url(),
            style=ft.ButtonStyle(color=ft.Colors.BLUE_600),
            visible=False
        )
        
        # 已是最新版本图标和文字
        self.latest_icon = ft.Icon(name=ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN_400, size=20, visible=False)
        self.latest_text = ft.Text("已是最新版本", size=12, color=ft.Colors.GREEN_600, visible=False)
        
        # 错误图标和文字
        self.error_icon = ft.Icon(name=ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_400, size=20, visible=False)
        self.error_text = ft.Text("", size=12, color=ft.Colors.RED_600, visible=False)
        
        # 版本信息行：当前版本 + 更新状态
        self.version_row = ft.Row([
            self.version_text,
            self.update_icon,
            self.update_text,
            self.detail_button,
            self.latest_icon,
            self.latest_text,
            self.error_icon,
            self.error_text,
        ], spacing=8, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, height=36)
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(name=ft.Icons.APPS, size=24, color=ft.Colors.PRIMARY),
                        ft.Text(self.display_name, size=20, weight=ft.FontWeight.BOLD),
                    ], spacing=12),
                    ft.Divider(height=1, thickness=2),
                    self.version_row,
                ], spacing=16),
                padding=24,
            ),
            elevation=3,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def update_version(self, version: str):
        """更新当前版本显示"""
        self.current_version = version if version else "未知"
        self.version_text.value = f"当前版本: {self.current_version}"
    
    def update_check_result(self, update_info: UpdateInfo):
        """更新检查结果显示"""
        self.latest_version = update_info.latest_version
        self.has_update = update_info.has_update
        self.release_url = update_info.release_url
        
        # 先隐藏所有状态元素
        self._hide_all_status()
        
        if update_info.error:
            self.error_icon.visible = True
            self.error_text.value = f"检查失败: {update_info.error}"
            self.error_text.visible = True
        elif update_info.has_update:
            self.update_icon.visible = True
            self.update_text.value = f"有新版本: {update_info.latest_version}"
            self.update_text.visible = True
            if self.release_url:
                self.detail_button.visible = True
        else:
            self.latest_icon.visible = True
            self.latest_text.visible = True
    
    def _hide_all_status(self):
        """隐藏所有状态元素"""
        self.update_icon.visible = False
        self.update_text.visible = False
        self.detail_button.visible = False
        self.latest_icon.visible = False
        self.latest_text.visible = False
        self.error_icon.visible = False
        self.error_text.visible = False
    
    def _open_release_url(self):
        """打开release页面"""
        if self.release_url:
            import webbrowser
            webbrowser.open(self.release_url)
    
    def clear_update_status(self):
        """清除更新状态显示"""
        self._hide_all_status()
        self.latest_version = None
        self.has_update = False
        self.release_url = ""


class AboutPage:
    """关于/版本页面组件"""
    
    def __init__(self, 
                 version_detector: VersionDetector,
                 update_manager=None,
                 on_restart_service: Optional[Callable[[], None]] = None):
        """初始化关于页面"""
        self.version_detector = version_detector
        self.update_manager = update_manager
        self.on_restart_service = on_restart_service
        self.config_manager = None
        self.control = None
        self.page = None

    def build(self, page: ft.Page):
        """构建UI组件"""
        self.page = page
        
        # 创建版本信息卡片
        self.app_card = VersionInfoCard("app", APP_NAME)
        self.app_card.build()
        
        self.pmhq_card = VersionInfoCard("pmhq", "PMHQ")
        self.pmhq_card.build()
        
        self.llonebot_card = VersionInfoCard("llonebot", "LLOneBot")
        self.llonebot_card.build()
        
        # 检查更新/立即更新按钮
        self.check_update_button = ft.ElevatedButton(
            "检查更新",
            icon=ft.Icons.CLOUD_DOWNLOAD,
            on_click=self._on_check_or_update_click,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY,
                bgcolor=ft.Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        )
        
        # 加载中指示器
        self.loading_indicator = ft.ProgressRing(
            width=24, height=24, stroke_width=3, visible=False
        )
        
        # GitHub仓库链接
        github_links = [
            ft.TextButton(
                'QQ群：545402644',
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=lambda e, url=f"https://qm.qq.com/q/4XrMj9iReU": self._open_url(url),
                style=ft.ButtonStyle(color=ft.Colors.BLUE_600)
            )
        ]
        for component, repo in GITHUB_REPOS.items():
            if repo and repo != "owner/pmhq" and repo != "owner/qq-bot-manager":
                display_name = {
                    "app": 'Lucky Lillia Desktop',
                    "pmhq": "PMHQ",
                    "llonebot": "LLOneBot"
                }.get(component, component)
                
                github_links.append(
                    ft.TextButton(
                        f"{display_name} GitHub",
                        icon=ft.Icons.OPEN_IN_NEW,
                        on_click=lambda e, url=f"https://github.com/{repo}": self._open_url(url),
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_600)
                    )
                )
        
        self.control = ft.Container(
            content=ft.Column([
                # 标题
                ft.Row([
                    ft.Icon(name=ft.Icons.INFO, size=36, color=ft.Colors.PRIMARY),
                    ft.Text("关于", size=32, weight=ft.FontWeight.BOLD),
                ], spacing=12),
                ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                
                # 应用信息
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Image(
                                    src=get_resource_path("icon.png"),
                                    width=80, height=80,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                ft.Column([
                                    ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        "QQ机器人管理工具 - 统一管理PMHQ和LLOneBot",
                                        size=15, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500
                                    ),
                                ], spacing=8),
                            ], spacing=20),
                        ], spacing=16),
                        padding=28,
                    ),
                    elevation=3,
                    surface_tint_color=ft.Colors.PRIMARY,
                ),
                
                # 版本信息区域
                ft.Row([
                    ft.Icon(ft.Icons.NEW_RELEASES, size=24, color=ft.Colors.PRIMARY),
                    ft.Text("版本信息", size=22, weight=ft.FontWeight.W_600),
                ], spacing=10),
                
                ft.Container(content=self.app_card.control),
                
                ft.Row([
                    ft.Container(content=self.pmhq_card.control, expand=1),
                    ft.Container(content=self.llonebot_card.control, expand=1),
                ], spacing=20),
                
                # 检查更新按钮（居中对齐）
                ft.Row(
                    [self.check_update_button, self.loading_indicator], 
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # GitHub链接
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CODE, size=20, color=ft.Colors.PRIMARY),
                                ft.Text("相关链接", size=18, weight=ft.FontWeight.BOLD),
                            ], spacing=10),
                            ft.Column(github_links, spacing=12) if github_links else ft.Text(
                                "暂无可用链接", size=14, color=ft.Colors.GREY_600, italic=True
                            ),
                        ], spacing=16),
                        padding=24,
                    ),
                    elevation=3,
                    surface_tint_color=ft.Colors.PRIMARY,
                ),
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=28,
        )
        
        # 初始加载版本信息
        self._load_versions()
        
        return self.control
    
    def _load_versions(self):
        """加载当前版本信息"""
        app_version = self.version_detector.get_app_version()
        self.app_card.update_version(app_version)
        
        self.pmhq_card.update_version("检测中...")
        self.llonebot_card.update_version("检测中...")
        
        if self.page:
            self.page.update()
        
        def load_versions_async():
            pmhq_path = ""
            llonebot_path = ""
            if self.config_manager:
                try:
                    config = self.config_manager.load_config()
                    pmhq_path = config.get("pmhq_path", "")
                    llonebot_path = config.get("llonebot_path", "")
                except Exception:
                    pass
            
            pmhq_version = self.version_detector.detect_pmhq_version(pmhq_path)
            llonebot_version = self.version_detector.detect_llonebot_version(llonebot_path)
            
            async def update_ui():
                self.pmhq_card.update_version(pmhq_version if pmhq_version else "未知")
                self.llonebot_card.update_version(llonebot_version if llonebot_version else "未知")
                if self.page:
                    self.page.update()
            
            if self.page:
                self.page.run_task(update_ui)
        
        thread = threading.Thread(target=load_versions_async, daemon=True)
        thread.start()
    
    def _on_check_or_update_click(self, e):
        """检查更新/立即更新按钮点击处理"""
        if not self.update_manager:
            return
        
        if self.update_manager.is_downloading:
            return
        
        if self.update_manager.has_updates:
            self._start_all_updates()
        else:
            self._do_check_update()
    
    def _do_check_update(self):
        """执行检查更新"""
        if not self.update_manager:
            return
        
        self.check_update_button.disabled = True
        self.loading_indicator.visible = True
        
        self.app_card.clear_update_status()
        self.pmhq_card.clear_update_status()
        self.llonebot_card.clear_update_status()
        self.update_manager.clear_all_updates()
        
        if self.page:
            self.page.update()
        
        def on_check_complete(all_check_results):
            async def update_ui():
                # 更新所有卡片的检查结果（包括没有更新的）
                for name, info in all_check_results:
                    if name == "管理器":
                        self.app_card.update_check_result(info)
                    elif name == "PMHQ":
                        self.pmhq_card.update_check_result(info)
                    elif name == "LLOneBot":
                        self.llonebot_card.update_check_result(info)
                
                self.check_update_button.disabled = False
                self.loading_indicator.visible = False
                
                # 检查是否有任何组件需要更新
                has_any_update = any(info.has_update for _, info in all_check_results)
                if has_any_update:
                    self.check_update_button.text = "立即更新"
                    self.check_update_button.icon = ft.Icons.DOWNLOAD
                else:
                    self.check_update_button.text = "检查更新"
                    self.check_update_button.icon = ft.Icons.CLOUD_DOWNLOAD
                
                if self.page:
                    self.page.update()
            
            if self.page:
                self.page.run_task(update_ui)
        
        self.update_manager.set_callbacks(on_check_complete=on_check_complete)
        
        versions = {
            "app": self.app_card.current_version,
            "pmhq": self.pmhq_card.current_version,
            "llonebot": self.llonebot_card.current_version,
        }
        
        self.update_manager.check_updates_async(versions)

    def set_updates_found(self, updates_found: list):
        """设置发现的更新列表（从首页同步）"""
        if updates_found:
            self.check_update_button.text = "立即更新"
            self.check_update_button.icon = ft.Icons.DOWNLOAD
        else:
            self.check_update_button.text = "检查更新"
            self.check_update_button.icon = ft.Icons.CLOUD_DOWNLOAD
        
        for component_name, update_info in updates_found:
            if component_name == "管理器":
                self.app_card.update_check_result(update_info)
            elif component_name == "PMHQ":
                self.pmhq_card.update_check_result(update_info)
            elif component_name == "LLOneBot":
                self.llonebot_card.update_check_result(update_info)
        
        if self.page:
            try:
                self.page.update()
            except:
                pass
    
    def _start_all_updates(self):
        """开始更新所有组件"""
        if not self.update_manager or not self.update_manager.has_updates:
            return
        
        running = self.update_manager.has_running_processes()
        
        def on_confirm(e):
            if self.page:
                self.page.close(confirm_dialog)
            self._do_download_all_updates()
        
        def on_cancel(e):
            if self.page:
                self.page.close(confirm_dialog)
        
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
    
    def _do_download_all_updates(self):
        """执行下载所有更新"""
        if not self.update_manager:
            return
        
        progress_bar = ft.ProgressBar(width=300, value=0)
        progress_text = ft.Text("准备下载...", size=14)
        component_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
        
        download_dialog = ft.AlertDialog(
            title=ft.Text("正在更新"),
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
                
                self.check_update_button.text = "检查更新"
                self.check_update_button.icon = ft.Icons.CLOUD_DOWNLOAD
                
                self.app_card.clear_update_status()
                self.pmhq_card.clear_update_status()
                self.llonebot_card.clear_update_status()
                
                if self.page:
                    self.page.update()
                
                self._load_versions()
                
                if "管理器" in success_list and self.update_manager.has_pending_app_update():
                    self._show_app_restart_dialog()
                elif had_running_processes and self.on_restart_service:
                    logger = logging.getLogger(__name__)
                    logger.info("更新完成，自动重启服务...")
                    self.on_restart_service()
            
            if self.page:
                self.page.run_task(on_complete)
        
        self.update_manager.set_callbacks(
            on_download_status=on_download_status,
            on_download_progress=on_download_progress,
            on_download_complete=on_download_complete
        )
        
        self.update_manager.download_all_updates_async()
    
    def _show_app_restart_dialog(self):
        """显示应用重启对话框"""
        import subprocess
        
        def on_restart(e):
            self._close_dialog(restart_dialog)
            script = self.update_manager.pending_app_update_script if self.update_manager else None
            if script:
                batch_dir = os.path.dirname(script)
                subprocess.Popen(
                    f'cmd /c start "更新" /D "{batch_dir}" "{script}"',
                    shell=True
                )
                if self.update_manager:
                    self.update_manager.clear_pending_app_update()
            if self.page:
                main_window = getattr(self.page, 'main_window', None)
                if main_window and hasattr(main_window, '_do_close'):
                    main_window._do_close(force_exit=True)
                else:
                    os._exit(0)
        
        def on_later(e):
            self._close_dialog(restart_dialog)
        
        restart_dialog = ft.AlertDialog(
            title=ft.Text("更新已就绪"),
            content=ft.Text("管理器新版本已下载完成！\n\n需要重启程序以完成更新。"),
            actions=[
                ft.TextButton("稍后", on_click=on_later),
                ft.ElevatedButton("立即重启", on_click=on_restart),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.open(restart_dialog)
    
    def _open_url(self, url: str):
        """打开URL"""
        import webbrowser
        webbrowser.open(url)
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """关闭对话框"""
        if self.page:
            self.page.close(dialog)
    
    def refresh(self):
        """刷新页面（重新加载版本信息）"""
        self._load_versions()
        
        # 同步更新管理器的状态到卡片
        if self.update_manager and self.update_manager.has_updates:
            self.check_update_button.text = "立即更新"
            self.check_update_button.icon = ft.Icons.DOWNLOAD
            
            # 同步更新状态到卡片显示
            for name, info in self.update_manager.updates_found:
                if name == "管理器":
                    self.app_card.update_check_result(info)
                elif name == "PMHQ":
                    self.pmhq_card.update_check_result(info)
                elif name == "LLOneBot":
                    self.llonebot_card.update_check_result(info)
        else:
            self.check_update_button.text = "检查更新"
            self.check_update_button.icon = ft.Icons.CLOUD_DOWNLOAD
        
        if self.page:
            try:
                self.page.update()
            except:
                pass
