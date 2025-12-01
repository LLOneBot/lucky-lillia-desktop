"""关于/版本页面UI模块 - 显示版本信息和更新检查"""

import flet as ft
from typing import Optional, Callable, Dict
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker, UpdateInfo
from core.config_manager import ConfigManager
from utils.constants import APP_NAME, NPM_PACKAGES, GITHUB_REPOS
from utils.downloader import Downloader, DownloadError
import threading
import os
import sys


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径（支持 PyInstaller 打包）
    
    Args:
        relative_path: 相对路径
        
    Returns:
        资源文件的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，资源文件在 _MEIPASS 临时目录中
        base_path = sys._MEIPASS
    else:
        # 开发模式，使用当前目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class VersionInfoCard:
    """版本信息卡片组件"""
    
    def __init__(self, component_name: str, display_name: str, 
                 on_update_click: Optional[Callable[[str], None]] = None):
        """初始化版本信息卡片
        
        Args:
            component_name: 组件名称 ("app", "pmhq", "llonebot")
            display_name: 显示名称
            on_update_click: 点击更新按钮的回调函数
        """
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
        
        self.update_status = ft.Container(
            visible=False
        )
        
        self.control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(
                            name=ft.Icons.APPS,
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
                    self.version_text,
                    self.update_status,
                ], spacing=16),
                padding=24,
            ),
            elevation=3,
            surface_tint_color=ft.Colors.PRIMARY,
        )
        return self.control
    
    def update_version(self, version: str):
        """更新当前版本显示
        
        Args:
            version: 版本号字符串
        """
        self.current_version = version if version else "未知"
        self.version_text.value = f"当前版本: {self.current_version}"
    
    def update_check_result(self, update_info: UpdateInfo):
        """更新检查结果显示
        
        Args:
            update_info: 更新信息对象
        """
        self.latest_version = update_info.latest_version
        self.has_update = update_info.has_update
        self.release_url = update_info.release_url
        
        if update_info.error:
            # 显示错误信息
            self.update_status.content = ft.Row([
                ft.Icon(
                    name=ft.Icons.ERROR_OUTLINE,
                    color=ft.Colors.RED_400,
                    size=20
                ),
                ft.Text(
                    f"检查失败: {update_info.error}",
                    size=12,
                    color=ft.Colors.RED_600
                )
            ], spacing=8)
            self.update_status.visible = True
        elif update_info.has_update:
            # 有更新可用
            buttons = []
            # pmhq、llonebot和app都支持自动更新
            if self.component_name in ["pmhq", "llonebot", "app"] and self.on_update_click:
                buttons.append(ft.ElevatedButton(
                    "立即更新",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: self.on_update_click(self.component_name),
                    style=ft.ButtonStyle(
                        color=ft.Colors.ON_PRIMARY,
                        bgcolor=ft.Colors.PRIMARY,
                    )
                ))
            if self.release_url:
                buttons.append(ft.TextButton(
                    "查看详情",
                    on_click=lambda e: self._open_release_url(),
                    style=ft.ButtonStyle(
                        color=ft.Colors.BLUE_600
                    )
                ))
            
            self.update_status.content = ft.Column([
                ft.Row([
                    ft.Icon(
                        name=ft.Icons.UPDATE,
                        color=ft.Colors.ORANGE_400,
                        size=20
                    ),
                    ft.Text(
                        f"有新版本: {update_info.latest_version}",
                        size=12,
                        color=ft.Colors.ORANGE_600,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=8),
                ft.Row(buttons, spacing=8) if buttons else None
            ], spacing=8)
            self.update_status.visible = True
        else:
            # 已是最新版本
            self.update_status.content = ft.Row([
                ft.Icon(
                    name=ft.Icons.CHECK_CIRCLE_OUTLINE,
                    color=ft.Colors.GREEN_400,
                    size=20
                ),
                ft.Text(
                    "已是最新版本",
                    size=12,
                    color=ft.Colors.GREEN_600
                )
            ], spacing=8)
            self.update_status.visible = True
    
    def _open_release_url(self):
        """打开release页面"""
        if self.release_url:
            import webbrowser
            webbrowser.open(self.release_url)
    
    def clear_update_status(self):
        """清除更新状态显示"""
        self.update_status.visible = False
        self.latest_version = None
        self.has_update = False
        self.release_url = ""


class AboutPage:
    """关于/版本页面组件"""
    
    def __init__(self, 
                 version_detector: VersionDetector,
                 update_checker: UpdateChecker,
                 config_manager: Optional[ConfigManager] = None,
                 downloader: Optional[Downloader] = None,
                 on_update_complete: Optional[Callable[[str], None]] = None):
        """初始化关于页面
        
        Args:
            version_detector: 版本检测器实例
            update_checker: 更新检查器实例
            config_manager: 配置管理器实例（可选，用于获取路径）
            downloader: 下载器实例（可选，用于下载更新）
            on_update_complete: 更新完成回调（参数为组件名称）
        """
        self.version_detector = version_detector
        self.update_checker = update_checker
        self.on_update_complete = on_update_complete
        self.config_manager = config_manager
        self.downloader = downloader or Downloader()
        self.control = None
        self.page = None
        self._is_downloading = False
        self._pending_app_update_script = None  # 待执行的应用更新脚本路径
        
    def build(self, page: ft.Page):
        """构建UI组件
        
        Args:
            page: Flet页面对象
        """
        self.page = page
        
        # 创建版本信息卡片
        self.app_card = VersionInfoCard("app", APP_NAME, on_update_click=self._on_update_click)
        self.app_card.build()
        
        self.pmhq_card = VersionInfoCard("pmhq", "PMHQ", on_update_click=self._on_update_click)
        self.pmhq_card.build()
        
        self.llonebot_card = VersionInfoCard("llonebot", "LLOneBot", on_update_click=self._on_update_click)
        self.llonebot_card.build()
        
        # 检查更新按钮
        self.check_update_button = ft.ElevatedButton(
            "检查更新",
            icon=ft.Icons.CLOUD_DOWNLOAD,
            on_click=self._on_check_update,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY,
                bgcolor=ft.Colors.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        )
        
        # 加载中指示器
        self.loading_indicator = ft.ProgressRing(
            width=24,
            height=24,
            stroke_width=3,
            visible=False
        )
        
        # GitHub仓库链接
        github_links = [
            ft.TextButton(
                'QQ群：545402644',
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=lambda e, url=f"https://qm.qq.com/q/4XrMj9iReU": self._open_url(url),
                style=ft.ButtonStyle(
                    color=ft.Colors.BLUE_600
                )
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
                        style=ft.ButtonStyle(
                            color=ft.Colors.BLUE_600
                        )
                    )
                )
        
        self.control = ft.Container(
            content=ft.Column([
                # 标题
                ft.Row([
                    ft.Icon(
                        name=ft.Icons.INFO,
                        size=36,
                        color=ft.Colors.PRIMARY
                    ),
                    ft.Text(
                        "关于",
                        size=32,
                        weight=ft.FontWeight.BOLD
                    ),
                ], spacing=12),
                ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                
                # 应用信息
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Image(
                                    src=get_resource_path("icon.png"),
                                    width=80,
                                    height=80,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                ft.Column([
                                    ft.Text(
                                        APP_NAME,
                                        size=28,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "QQ机器人管理工具 - 统一管理PMHQ和LLOneBot",
                                        size=15,
                                        color=ft.Colors.GREY_600,
                                        weight=ft.FontWeight.W_500
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
                    ft.Text(
                        "版本信息",
                        size=22,
                        weight=ft.FontWeight.W_600
                    ),
                ], spacing=10),
                
                ft.Container(
                    content=self.app_card.control,
                ),
                
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
                
                # 检查更新按钮
                ft.Row([
                    self.check_update_button,
                    self.loading_indicator,
                ], spacing=20),
                
                # GitHub链接
                # ft.Row([
                #     ft.Icon(ft.Icons.LINK, size=24, color=ft.Colors.PRIMARY),
                #     ft.Text(
                #         "相关链接",
                #         size=22,
                #         weight=ft.FontWeight.W_600
                #     ),
                # ], spacing=10),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CODE, size=20, color=ft.Colors.PRIMARY),
                                ft.Text(
                                    "相关链接",
                                    size=18,
                                    weight=ft.FontWeight.BOLD
                                ),
                            ], spacing=10),
                            # ft.Divider(height=1, thickness=2),
                            ft.Column(
                                github_links,
                                spacing=12
                            ) if github_links else ft.Text(
                                "暂无可用链接",
                                size=14,
                                color=ft.Colors.GREY_600,
                                italic=True
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
        # 加载应用版本（同步，很快）
        app_version = self.version_detector.get_app_version()
        self.app_card.update_version(app_version)
        
        # 先显示"检测中..."，然后异步加载PMHQ和LLOneBot版本
        self.pmhq_card.update_version("检测中...")
        self.llonebot_card.update_version("检测中...")
        
        if self.page:
            self.page.update()
        
        # 异步加载版本信息
        def load_versions_async():
            # 加载PMHQ版本
            pmhq_path = ""
            if self.config_manager:
                try:
                    config = self.config_manager.load_config()
                    pmhq_path = config.get("pmhq_path", "")
                except Exception:
                    pass
            
            pmhq_version = self.version_detector.detect_pmhq_version(pmhq_path)
            
            # 加载LLOneBot版本
            llonebot_path = ""
            if self.config_manager:
                try:
                    config = self.config_manager.load_config()
                    llonebot_path = config.get("llonebot_path", "")
                except Exception:
                    pass
            
            llonebot_version = self.version_detector.detect_llonebot_version(llonebot_path)
            
            # 更新UI（需要在主线程中执行）
            async def update_ui():
                self.pmhq_card.update_version(pmhq_version if pmhq_version else "未知")
                self.llonebot_card.update_version(llonebot_version if llonebot_version else "未知")
                if self.page:
                    self.page.update()
            
            if self.page:
                self.page.run_task(update_ui)
        
        # 启动后台线程
        thread = threading.Thread(target=load_versions_async, daemon=True)
        thread.start()
    
    def _on_check_update(self, e):
        """检查更新按钮点击处理"""
        # 禁用按钮并显示加载指示器
        self.check_update_button.disabled = True
        self.loading_indicator.visible = True
        
        # 清除之前的更新状态
        self.app_card.clear_update_status()
        self.pmhq_card.clear_update_status()
        self.llonebot_card.clear_update_status()
        
        if self.page:
            self.page.update()
        
        # 在后台线程中执行更新检查
        def check_updates_thread():
            try:
                # 准备版本信息
                versions = {
                    "app": self.app_card.current_version,
                    "pmhq": self.pmhq_card.current_version,
                    "llonebot": self.llonebot_card.current_version,
                }
                
                # 检查所有更新
                results = self.update_checker.check_all_updates(versions)
                
                # 更新UI（需要在主线程中执行）
                async def update_ui():
                    if "app" in results:
                        self.app_card.update_check_result(results["app"])
                    if "pmhq" in results:
                        self.pmhq_card.update_check_result(results["pmhq"])
                    if "llonebot" in results:
                        self.llonebot_card.update_check_result(results["llonebot"])
                    
                    # 恢复按钮状态
                    self.check_update_button.disabled = False
                    self.loading_indicator.visible = False
                    
                    if self.page:
                        self.page.update()
                
                if self.page:
                    self.page.run_task(update_ui)
                    
            except Exception as ex:
                # 处理异常
                async def show_error():
                    # 显示错误对话框
                    error_dialog = ft.AlertDialog(
                        title=ft.Text("检查更新失败"),
                        content=ft.Text(f"发生错误: {str(ex)}"),
                        actions=[
                            ft.TextButton("确定", on_click=lambda e: self._close_dialog(error_dialog))
                        ],
                    )
                    if self.page:
                        self.page.overlay.append(error_dialog)
                        error_dialog.open = True
                    
                    # 恢复按钮状态
                    self.check_update_button.disabled = False
                    self.loading_indicator.visible = False
                    
                    if self.page:
                        self.page.update()
                
                if self.page:
                    self.page.run_task(show_error)
        
        # 启动后台线程
        thread = threading.Thread(target=check_updates_thread, daemon=True)
        thread.start()
    
    def _open_url(self, url: str):
        """打开URL
        
        Args:
            url: 要打开的URL
        """
        import webbrowser
        webbrowser.open(url)
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """关闭对话框
        
        Args:
            dialog: 要关闭的对话框
        """
        dialog.open = False
        if self.page:
            self.page.update()
    
    def refresh(self):
        """刷新页面（重新加载版本信息）"""
        self._load_versions()
    
    def _on_update_click(self, component: str):
        """点击更新按钮处理
        
        Args:
            component: 组件名称 ("pmhq", "llonebot" 或 "app")
        """
        if self._is_downloading:
            return
        
        if component == "pmhq":
            card = self.pmhq_card
            display_name = "PMHQ"
        elif component == "llonebot":
            card = self.llonebot_card
            display_name = "LLOneBot"
        else:
            card = self.app_card
            display_name = APP_NAME
        
        # 显示确认对话框
        def on_confirm(e):
            self._close_dialog(confirm_dialog)
            self._start_download(component)
        
        def on_cancel(e):
            self._close_dialog(confirm_dialog)
        
        confirm_dialog = ft.AlertDialog(
            title=ft.Text(f"更新 {display_name}"),
            content=ft.Text(
                f"确定要将 {display_name} 从 {card.current_version} 更新到 {card.latest_version} 吗？\n\n"
                "更新过程中请勿关闭程序。"
            ),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton("确定更新", on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            self.page.update()
    
    def _start_download(self, component: str):
        """开始下载更新
        
        Args:
            component: 组件名称 ("pmhq", "llonebot" 或 "app")
        """
        self._is_downloading = True
        
        if component == "pmhq":
            display_name = "PMHQ"
        elif component == "llonebot":
            display_name = "LLOneBot"
        else:
            display_name = APP_NAME
        
        # 创建下载进度对话框
        progress_bar = ft.ProgressBar(width=300, value=0)
        progress_text = ft.Text("准备下载...", size=14)
        
        download_dialog = ft.AlertDialog(
            title=ft.Text(f"正在更新 {display_name}"),
            content=ft.Column([
                progress_text,
                progress_bar,
            ], spacing=16, tight=True),
            modal=True,
        )
        
        if self.page:
            self.page.overlay.append(download_dialog)
            download_dialog.open = True
            self.page.update()
        
        def download_thread():
            try:
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
                
                if component == "app":
                    # 应用自身更新
                    self._download_app_update(progress_callback, progress_text, download_dialog, display_name)
                else:
                    # PMHQ或LLOneBot更新
                    self._download_component_update(component, progress_callback, download_dialog, display_name)
                    
            except (DownloadError, Exception) as ex:
                # 捕获异常信息，避免闭包问题
                error_msg = str(ex)
                
                async def on_error(err_msg=error_msg):
                    self._is_downloading = False
                    download_dialog.open = False
                    if self.page:
                        self.page.update()
                    
                    # 显示错误提示
                    error_dialog = ft.AlertDialog(
                        title=ft.Text("更新失败"),
                        content=ft.Text(f"下载 {display_name} 时发生错误:\n\n{err_msg}"),
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
    
    def _download_component_update(self, component: str, progress_callback, download_dialog, display_name: str):
        """下载PMHQ或LLOneBot更新
        
        Args:
            component: 组件名称
            progress_callback: 进度回调
            download_dialog: 下载对话框
            display_name: 显示名称
        """
        # 获取保存路径
        save_dir = os.path.join("bin", component)
        os.makedirs(save_dir, exist_ok=True)
        
        if component == "pmhq":
            save_path = os.path.join(save_dir, "pmhq-win-x64.zip")
        else:
            save_path = os.path.join(save_dir, "LLOneBot.zip")
        
        # 执行下载
        if component == "pmhq":
            self.downloader.download_pmhq(save_path, progress_callback)
        else:
            self.downloader.download_llonebot(save_path, progress_callback)
        
        # 下载成功
        async def on_success():
            self._is_downloading = False
            download_dialog.open = False
            if self.page:
                self.page.update()
            
            # 清除更新状态（因为已经更新完成）
            if component == "pmhq":
                self.pmhq_card.clear_update_status()
            else:
                self.llonebot_card.clear_update_status()
            
            # 通知外部更新完成（清除控制面板的更新横幅）
            if self.on_update_complete:
                self.on_update_complete(component)
            
            # 刷新版本信息
            self._load_versions()
        
        if self.page:
            self.page.run_task(on_success)
    
    def _download_app_update(self, progress_callback, progress_text, download_dialog, display_name: str):
        """下载应用自身更新
        
        Args:
            progress_callback: 进度回调
            progress_text: 进度文本控件
            download_dialog: 下载对话框
            display_name: 显示名称
        """
        import sys
        import subprocess
        
        # 获取当前进程PID
        current_pid = os.getpid()
        
        # 获取当前exe路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe
            current_exe = sys.executable
        else:
            # 开发模式，使用固定的exe名字
            current_exe = os.path.abspath("lucky-lillia-desktop.exe")
        
        # 下载新版本
        new_exe_path = self.downloader.download_app_update(current_exe, progress_callback)
        
        # 创建更新脚本
        async def update_progress_text():
            progress_text.value = "正在准备更新..."
            if self.page:
                self.page.update()
        
        if self.page:
            self.page.run_task(update_progress_text)
        
        batch_script = self.downloader.apply_app_update(new_exe_path, current_exe, current_pid)
        self._pending_app_update_script = batch_script  # 保存脚本路径
        
        # 下载成功，提示用户重启
        async def on_success():
            self._is_downloading = False
            download_dialog.open = False
            if self.page:
                self.page.update()
            
            def on_restart(e):
                import os  # 在函数开始时导入os模块
                self._close_dialog(success_dialog)
                # 启动更新脚本并退出当前程序
                # 使用 cmd /c start 启动批处理，确保在新窗口中运行
                batch_dir = os.path.dirname(batch_script)
                subprocess.Popen(
                    f'cmd /c start "更新" /D "{batch_dir}" "{batch_script}"',
                    shell=True
                )
                # 清空待执行的更新脚本，避免主窗口退出时重复执行
                self._pending_app_update_script = None
                # 直接退出程序，不触发关闭确认对话框
                if self.page:
                    # 通过主窗口实例直接调用关闭方法
                    main_window = getattr(self.page, 'main_window', None)
                    if main_window and hasattr(main_window, '_do_close'):
                        main_window._do_close(force_exit=True)  # 强制快速退出
                    else:
                        # 备用方案：直接退出进程
                        os._exit(0)
            
            def on_later(e):
                self._close_dialog(success_dialog)
                # 清除更新状态（更新已下载，不再显示更新按钮）
                self.app_card.clear_update_status()
                # 通知外部更新完成（清除控制面板的更新横幅）
                if self.on_update_complete:
                    self.on_update_complete("app")
                if self.page:
                    self.page.update()
            
            # 显示成功提示，询问是否立即重启
            success_dialog = ft.AlertDialog(
                title=ft.Text("更新已就绪"),
                content=ft.Text(
                    f"{display_name} 新版本已下载完成！\n\n"
                    "需要重启程序以完成更新。\n"
                    "是否立即重启？"
                ),
                actions=[
                    ft.TextButton("稍后", on_click=on_later),
                    ft.ElevatedButton("立即重启", on_click=on_restart),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            if self.page:
                self.page.overlay.append(success_dialog)
                success_dialog.open = True
                self.page.update()
        
        if self.page:
            self.page.run_task(on_success)

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
