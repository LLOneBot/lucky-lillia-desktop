"""关于/版本页面UI模块 - 显示版本信息和更新检查"""

import flet as ft
from typing import Optional, Callable, Dict
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker, UpdateInfo
from core.config_manager import ConfigManager
from utils.constants import APP_NAME, GITHUB_REPOS
import threading


class VersionInfoCard:
    """版本信息卡片组件"""
    
    def __init__(self, component_name: str, display_name: str):
        """初始化版本信息卡片
        
        Args:
            component_name: 组件名称 ("app", "pmhq", "llonebot")
            display_name: 显示名称
        """
        self.component_name = component_name
        self.display_name = display_name
        self.current_version = "未知"
        self.latest_version = None
        self.has_update = False
        self.release_url = ""
        self.control = None
        
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
                ft.TextButton(
                    "查看更新",
                    on_click=lambda e: self._open_release_url(),
                    style=ft.ButtonStyle(
                        color=ft.Colors.BLUE_600
                    )
                ) if self.release_url else None
            ], spacing=4)
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
                 config_manager: Optional[ConfigManager] = None):
        """初始化关于页面
        
        Args:
            version_detector: 版本检测器实例
            update_checker: 更新检查器实例
            config_manager: 配置管理器实例（可选，用于获取路径）
        """
        self.version_detector = version_detector
        self.update_checker = update_checker
        self.config_manager = config_manager
        self.control = None
        self.page = None
        
    def build(self, page: ft.Page):
        """构建UI组件
        
        Args:
            page: Flet页面对象
        """
        self.page = page
        
        # 创建版本信息卡片
        self.app_card = VersionInfoCard("app", APP_NAME)
        self.app_card.build()
        
        self.pmhq_card = VersionInfoCard("pmhq", "PMHQ")
        self.pmhq_card.build()
        
        self.llonebot_card = VersionInfoCard("llonebot", "LLOneBot")
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
        github_links = []
        for component, repo in GITHUB_REPOS.items():
            if repo and repo != "owner/pmhq" and repo != "owner/qq-bot-manager":
                display_name = {
                    "app": APP_NAME,
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
                                ft.Icon(
                                    name=ft.Icons.ROCKET_LAUNCH,
                                    size=56,
                                    color=ft.Colors.PRIMARY
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
                ft.Row([
                    ft.Icon(ft.Icons.LINK, size=24, color=ft.Colors.PRIMARY),
                    ft.Text(
                        "相关链接",
                        size=22,
                        weight=ft.FontWeight.W_600
                    ),
                ], spacing=10),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CODE, size=20, color=ft.Colors.PRIMARY),
                                ft.Text(
                                    "GitHub仓库",
                                    size=18,
                                    weight=ft.FontWeight.BOLD
                                ),
                            ], spacing=10),
                            ft.Divider(height=1, thickness=2),
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
        # 加载应用版本
        app_version = self.version_detector.get_app_version()
        self.app_card.update_version(app_version)
        
        # 加载PMHQ版本
        pmhq_path = ""
        if self.config_manager:
            try:
                config = self.config_manager.load_config()
                pmhq_path = config.get("pmhq_path", "")
            except Exception:
                pass
        
        pmhq_version = self.version_detector.detect_pmhq_version(pmhq_path)
        self.pmhq_card.update_version(pmhq_version if pmhq_version else "未知")
        
        # 加载LLOneBot版本
        llonebot_path = ""
        if self.config_manager:
            try:
                config = self.config_manager.load_config()
                llonebot_path = config.get("llonebot_path", "")
            except Exception:
                pass
        
        llonebot_version = self.version_detector.detect_llonebot_version(llonebot_path)
        self.llonebot_card.update_version(llonebot_version if llonebot_version else "未知")
        
        if self.page:
            self.page.update()
    
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
                def update_ui():
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
                def show_error():
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
