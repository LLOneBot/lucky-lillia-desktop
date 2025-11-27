"""主窗口模块 - 实现应用主窗口和导航系统"""

import flet as ft
from typing import Optional, Callable
from core.process_manager import ProcessManager
from core.log_collector import LogCollector
from core.config_manager import ConfigManager
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from ui.home_page import HomePage
from ui.log_page import LogPage
from ui.config_page import ConfigPage
from ui.llonebot_config_page import LLOneBotConfigPage
from ui.about_page import AboutPage
from ui.theme import apply_theme, toggle_theme, get_current_theme_mode
from utils.storage import Storage
from utils.constants import (
    APP_NAME, 
    DEFAULT_WINDOW_WIDTH, 
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_THEME,
    RESOURCE_MONITOR_INTERVAL
)
import threading
import time


class MainWindow:
    """主窗口类，管理应用的整体布局和导航"""
    
    def __init__(self, 
                 process_manager: ProcessManager,
                 log_collector: LogCollector,
                 config_manager: ConfigManager,
                 version_detector: VersionDetector,
                 update_checker: UpdateChecker,
                 storage: Storage):
        """初始化主窗口
        
        Args:
            process_manager: 进程管理器实例
            log_collector: 日志收集器实例
            config_manager: 配置管理器实例
            version_detector: 版本检测器实例
            update_checker: 更新检查器实例
            storage: 本地存储实例
        """
        self.process_manager = process_manager
        self.log_collector = log_collector
        self.config_manager = config_manager
        self.version_detector = version_detector
        self.update_checker = update_checker
        self.storage = storage
        
        self.page: Optional[ft.Page] = None
        self.current_page_index = 0
        
        # 资源监控线程
        self.resource_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_resources = False
        
    def build(self, page: ft.Page):
        """构建主窗口UI
        
        Args:
            page: Flet页面对象
        """
        self.page = page
        
        # 设置窗口属性
        page.title = APP_NAME
        
        # 从本地存储恢复窗口尺寸
        window_width = self.storage.load_setting("window_width", DEFAULT_WINDOW_WIDTH)
        window_height = self.storage.load_setting("window_height", DEFAULT_WINDOW_HEIGHT)
        page.window.width = window_width
        page.window.height = window_height
        
        # 从本地存储恢复主题
        theme_mode = self.storage.load_setting("theme_mode", DEFAULT_THEME)
        apply_theme(page, theme_mode)
        
        # 注册窗口关闭事件
        page.on_window_event = self._on_window_event
        
        # 创建页面实例
        self.home_page = HomePage(
            self.process_manager,
            self.config_manager,
            log_collector=self.log_collector,
            on_navigate_logs=lambda: self._navigate_to(1),
            version_detector=self.version_detector,
            update_checker=self.update_checker
        )
        self.home_page.build()
        self.home_page.set_page(page)  # 设置页面引用以显示对话框
        
        # 进入控制面板时检查更新
        self.home_page.check_for_updates()
        
        self.log_page = LogPage(self.log_collector)
        self.log_page.build()
        
        self.config_page = ConfigPage(
            self.config_manager,
            on_config_saved=self._on_config_saved
        )
        self.config_page.build()
        
        self.llonebot_config_page = LLOneBotConfigPage(
            get_uin_func=self.process_manager.get_uin
        )
        self.llonebot_config_page.build()
        
        self.about_page = AboutPage(
            self.version_detector,
            self.update_checker,
            self.config_manager
        )
        self.about_page.build(page)
        
        # 创建导航栏
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=120,
            min_extended_width=220,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="控制面板",
                    padding=ft.padding.symmetric(vertical=8)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ARTICLE_OUTLINED,
                    selected_icon=ft.Icons.ARTICLE,
                    label="日志查看",
                    padding=ft.padding.symmetric(vertical=8)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="启动配置",
                    padding=ft.padding.symmetric(vertical=8)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.TUNE_OUTLINED,
                    selected_icon=ft.Icons.TUNE,
                    label="Bot配置",
                    padding=ft.padding.symmetric(vertical=8)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INFO_OUTLINED,
                    selected_icon=ft.Icons.INFO,
                    label="关于应用",
                    padding=ft.padding.symmetric(vertical=8)
                ),
            ],
            on_change=self._on_nav_change,
        )
        
        # 创建主题切换按钮
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE if theme_mode == "light" else ft.Icons.LIGHT_MODE,
            tooltip="切换主题",
            on_click=self._on_theme_toggle,
            icon_size=28,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        # 创建内容区域
        self.content_area = ft.Container(
            content=self.home_page.control,
            expand=True,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=300,
        )
        
        # 创建头像/图标容器
        self.avatar_icon = ft.Icon(
            name=ft.Icons.SMART_TOY,
            size=32,
            color=ft.Colors.PRIMARY
        )
        self.avatar_image = ft.Image(
            src="",
            width=48,
            height=48,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(24),
            visible=False
        )
        self.avatar_container = ft.Container(
            content=ft.Stack([
                self.avatar_icon,
                self.avatar_image
            ]),
            padding=ft.padding.symmetric(vertical=20),
            alignment=ft.alignment.center,
        )
        
        # 设置uin回调，当获取到uin时更新头像
        self.process_manager.set_uin_callback(self._on_uin_received)
        
        # 如果已经有uin，立即更新头像
        current_uin = self.process_manager.get_uin()
        if current_uin:
            self._update_avatar(current_uin)
        
        # 创建主布局
        main_layout = ft.Row([
            # 左侧导航栏
            ft.Container(
                content=ft.Column([
                    self.avatar_container,
                    ft.Container(
                        content=self.nav_rail,
                        expand=True,
                    ),
                    ft.Divider(height=1),
                    ft.Container(
                        content=self.theme_button,
                        padding=16,
                        alignment=ft.alignment.center,
                    ),
                ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
            ),
            # 右侧内容区域
            ft.VerticalDivider(width=2, thickness=2),
            self.content_area,
        ], spacing=0, expand=True)
        
        page.add(main_layout)
        
        # 启动资源监控
        self._start_resource_monitoring()
        
        # 刷新首页进程资源
        self.home_page.refresh_process_resources()
    
    def _on_nav_change(self, e):
        """导航栏选择变化处理
        
        Args:
            e: 导航栏变化事件
        """
        selected_index = e.control.selected_index
        self._navigate_to(selected_index)
    
    def _navigate_to(self, index: int):
        """导航到指定页面
        
        Args:
            index: 页面索引 (0=首页, 1=日志, 2=配置, 3=LLOneBot配置, 4=关于)
        """
        self.current_page_index = index
        self.nav_rail.selected_index = index
        
        # 淡出效果
        self.content_area.opacity = 0
        if self.page:
            self.page.update()
        
        # 切换内容区域
        if index == 0:
            self.content_area.content = self.home_page.control
        elif index == 1:
            self.content_area.content = self.log_page.control
            self.log_page.on_page_enter()
        elif index == 2:
            self.content_area.content = self.config_page.control
            self.config_page.refresh()
        elif index == 3:
            self.content_area.content = self.llonebot_config_page.control
            self.llonebot_config_page.refresh()
        elif index == 4:
            self.content_area.content = self.about_page.control
            self.about_page.refresh()
        
        # 淡入效果
        self.content_area.opacity = 1
        if self.page:
            self.page.update()
        
        # 首页资源刷新放在页面显示之后，避免阻塞
        if index == 0:
            self.home_page.refresh_process_resources()
            if self.page:
                self.page.update()
    
    def _on_theme_toggle(self, e):
        """主题切换按钮点击处理"""
        if self.page:
            # 切换主题
            new_theme = toggle_theme(self.page)
            
            # 更新按钮图标
            self.theme_button.icon = (
                ft.Icons.DARK_MODE if new_theme == "light" else ft.Icons.LIGHT_MODE
            )
            
            # 保存主题设置
            self.storage.save_setting("theme_mode", new_theme)
            
            self.page.update()
    
    def _on_config_saved(self, config: dict):
        """配置保存回调处理
        
        Args:
            config: 保存的配置字典
        """
        # 配置保存后可以执行一些操作，比如重启进程
        pass
    
    def _on_uin_received(self, uin: str, nickname: str):
        """uin获取成功的回调
        
        Args:
            uin: QQ号
            nickname: 昵称
        """
        # 有uin就更新头像
        if uin:
            self._update_avatar(uin)
        # 有nickname才更新标题
        if uin and nickname:
            self._update_home_title(uin, nickname)
    
    def _update_avatar(self, uin: str):
        """更新侧边栏头像
        
        Args:
            uin: QQ号
        """
        if not uin:
            return
        
        # 构建QQ头像URL
        avatar_url = f"https://thirdqq.qlogo.cn/g?b=qq&nk={uin}&s=640"
        
        # 更新头像图片
        self.avatar_image.src = avatar_url
        self.avatar_image.visible = True
        self.avatar_icon.visible = False
        
        if self.page:
            self.page.update()
    
    def _update_home_title(self, uin: str, nickname: str):
        """更新首页标题
        
        Args:
            uin: QQ号
            nickname: 昵称
        """
        if uin and nickname:
            self.home_page.update_title(f"{nickname}({uin})")
    
    def _on_window_event(self, e):
        """窗口事件处理
        
        Args:
            e: 窗口事件
        """
        if e.data == "close":
            # 检查是否有待执行的应用更新（首页或关于页面）
            if self.home_page.has_pending_app_update():
                self._execute_pending_update(self.home_page.get_pending_update_script())
            elif self.about_page.has_pending_app_update():
                self._execute_pending_update(self.about_page.get_pending_update_script())
            # 窗口关闭时的清理逻辑
            self._cleanup()
    
    def _execute_pending_update(self, script_path: str):
        """执行待处理的应用更新
        
        Args:
            script_path: 更新脚本路径
        """
        import subprocess
        import os
        
        if script_path and os.path.exists(script_path):
            batch_dir = os.path.dirname(script_path)
            subprocess.Popen(
                f'cmd /c start "更新" /D "{batch_dir}" "{script_path}"',
                shell=True
            )
    
    def _cleanup(self):
        """清理资源，停止所有进程和线程"""
        # 停止资源监控
        self.monitoring_resources = False
        if self.resource_monitor_thread and self.resource_monitor_thread.is_alive():
            self.resource_monitor_thread.join(timeout=1)
        
        # 保存窗口尺寸
        if self.page:
            self.storage.save_setting("window_width", self.page.window.width)
            self.storage.save_setting("window_height", self.page.window.height)
        
        # 停止所有进程
        self.process_manager.stop_all()
    
    def _start_resource_monitoring(self):
        """启动资源监控线程"""
        if not self.monitoring_resources:
            self.monitoring_resources = True
            self.resource_monitor_thread = threading.Thread(
                target=self._monitor_resources,
                daemon=True
            )
            self.resource_monitor_thread.start()
    
    def _monitor_resources(self):
        """监控系统资源使用情况"""
        while self.monitoring_resources:
            try:
                # 更新首页的资源显示
                if self.current_page_index == 0 and self.page:
                    self.home_page.refresh_process_resources()
                    
                    # 更新日志预览
                    logs = self.log_collector.get_logs()
                    log_entries = []
                    for log in logs[-10:]:  # 只取最新10条
                        log_entries.append({
                            "timestamp": log.timestamp.strftime("%H:%M:%S"),
                            "process_name": log.process_name,
                            "level": log.level,
                            "message": log.message
                        })
                    self.home_page.refresh_logs(log_entries)
                    
                    # 更新UI
                    if self.page:
                        self.page.update()
                
            except Exception as e:
                # 忽略监控过程中的错误
                pass
            
            # 等待指定间隔
            time.sleep(RESOURCE_MONITOR_INTERVAL)
