"""主窗口模块 - 实现应用主窗口和导航系统"""

import flet as ft
from typing import Optional, Callable
from core.process_manager import ProcessManager
from core.log_collector import LogCollector
from core.config_manager import ConfigManager
from core.version_detector import VersionDetector
from core.update_checker import UpdateChecker
from core.update_manager import UpdateManager
from ui.home_page import HomePage
from ui.log_page import LogPage
from ui.config_page import ConfigPage
from ui.llonebot_config_page import LLOneBotConfigPage
from ui.about_page import AboutPage
from ui.theme import apply_theme, toggle_theme, get_current_theme_mode
from utils.constants import (
    APP_NAME, 
    DEFAULT_WINDOW_WIDTH, 
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_THEME,
    RESOURCE_MONITOR_INTERVAL,
    TRAY_TOOLTIP,
    CLOSE_TO_TRAY_DEFAULT
)
from utils.downloader import Downloader
import threading
import time


class MainWindow:
    """主窗口类，管理应用的整体布局和导航"""
    
    def __init__(self, 
                 process_manager: ProcessManager,
                 log_collector: LogCollector,
                 config_manager: ConfigManager,
                 version_detector: VersionDetector,
                 update_checker: UpdateChecker):
        """初始化主窗口
        
        Args:
            process_manager: 进程管理器实例
            log_collector: 日志收集器实例
            config_manager: 配置管理器实例
            version_detector: 版本检测器实例
            update_checker: 更新检查器实例
        """
        self.process_manager = process_manager
        self.log_collector = log_collector
        self.config_manager = config_manager
        self.version_detector = version_detector
        self.update_checker = update_checker
        
        # 创建更新管理器
        self.update_manager = UpdateManager(
            update_checker=update_checker,
            config_manager=config_manager,
            process_manager=process_manager,
            downloader=Downloader()
        )
        
        # 用于快速中断资源监控线程的事件
        self._stop_monitoring_event = threading.Event()
        
        self.page: Optional[ft.Page] = None
        self.current_page_index = 0
        
        # 资源监控线程
        self.resource_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_resources = False
        
        # 托盘相关
        self.close_dialog: Optional[ft.AlertDialog] = None
        self.remember_choice = False  # 是否记住选择
        self.tray_icon = None  # pystray 图标
        self.tray_thread = None  # 托盘线程
        
    def build(self, page: ft.Page):
        """构建主窗口UI
        
        Args:
            page: Flet页面对象
        """
        self.page = page
        
        # 设置窗口属性
        page.title = APP_NAME
        page.padding = 0  # 移除页面默认padding
        
        # 从配置恢复窗口尺寸
        window_width = self.config_manager.load_setting("window_width", DEFAULT_WINDOW_WIDTH)
        window_height = self.config_manager.load_setting("window_height", DEFAULT_WINDOW_HEIGHT)
        page.window.width = window_width
        page.window.height = window_height
        
        # 从配置恢复主题
        theme_mode = self.config_manager.load_setting("theme_mode", DEFAULT_THEME)
        apply_theme(page, theme_mode)
        
        # 注册窗口关闭事件
        page.window.prevent_close = True  # 阻止默认关闭行为
        page.window.on_event = self._on_window_event
        
        # 创建页面实例
        self.home_page = HomePage(
            self.process_manager,
            self.config_manager,
            log_collector=self.log_collector,
            on_navigate_logs=lambda: self._navigate_to(1),
            version_detector=self.version_detector,
            update_manager=self.update_manager
        )
        self.home_page.build()
        self.home_page.set_page(page)  # 设置页面引用以显示对话框
        
        # 设置页面的主窗口引用，供子页面使用
        page.main_window = self
        
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
            update_manager=self.update_manager,
            on_restart_service=self._on_restart_service_after_update
        )
        self.about_page.config_manager = self.config_manager
        self.about_page.build(page)
        
        # 创建导航栏
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=160,
            group_alignment=-0.9,
            bgcolor=ft.Colors.TRANSPARENT,
            leading=None,
            trailing=None,
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
        
        # 创建内容区域（移除动画避免卡顿）
        self.content_area = ft.Container(
            content=self.home_page.control,
            expand=True,
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
        
        # 设置系统托盘（延迟一点启动，确保窗口已完全初始化）
        def delayed_tray_setup():
            import time
            time.sleep(2)  # 等待2秒，确保窗口完全加载
            print("延迟托盘初始化开始...")
            self._setup_system_tray()
        
        tray_setup_thread = threading.Thread(target=delayed_tray_setup, daemon=True)
        tray_setup_thread.start()
        
        # 启动资源监控
        self._start_resource_monitoring()
        
        # 刷新首页进程资源
        self.home_page.refresh_process_resources()
        
        # 检查是否需要自动启动bot
        self._check_auto_start_bot()
        
        # 检查是否需要启动后自动缩进托盘
        self._check_minimize_to_tray_on_start()
    
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
        # 离开当前页面时的处理
        if self.current_page_index == 1 and index != 1:
            self.log_page.on_page_leave()
        
        self.current_page_index = index
        self.nav_rail.selected_index = index
        
        # 直接切换内容区域（无动画）
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
        
        try:
            if self.page:
                self.page.update()
        except AssertionError:
            pass
        
        # 首页资源刷新放在页面显示之后
        if index == 0:
            self.home_page.refresh_process_resources()
    
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
            self.config_manager.save_setting("theme_mode", new_theme)
            
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
        # 有nickname才更新标题和窗口标题
        if uin and nickname:
            self._update_home_title(uin, nickname)
            self._update_window_title(uin, nickname)
    
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
    
    def _on_about_page_update_complete(self, component: str):
        """关于页面更新完成回调
        
        Args:
            component: 更新完成的组件名称 ("app"/"pmhq"/"llonebot")
        """
        # 清除控制面板的更新横幅
        self.home_page.clear_update_banner(component)
    
    def _on_restart_service_after_update(self):
        """更新完成后重启服务的回调"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("更新完成，自动重启服务...")
        # 先切换到首页
        self._navigate_to(0)
        # 然后调用首页的启动服务方法
        self.home_page._on_global_start_click(None)
    
    def _update_window_title(self, uin: str, nickname: str):
        """更新窗口标题
        
        Args:
            uin: QQ号
            nickname: 昵称
        """
        if self.page and uin and nickname:
            self.page.title = f"{APP_NAME} -- {nickname}({uin})"
            self.page.update()
            # 同步更新托盘提示
            self._update_tray_title()
    
    def _on_window_event(self, e):
        """窗口事件处理
        
        Args:
            e: 窗口事件
        """
        if e.data == "close":
            # 检查用户是否已经记住了选择
            close_to_tray = self.config_manager.load_setting("close_to_tray", None)
            
            if close_to_tray is True:
                # 用户选择了收进托盘
                self._minimize_to_tray()
            elif close_to_tray is False:
                # 用户选择了直接退出
                self._do_close()
            else:
                # 首次关闭，显示选择对话框
                self._show_close_dialog()
    
    def _show_close_dialog(self):
        """显示关闭确认对话框"""
        self.remember_choice = False
        
        self.close_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("关闭窗口", text_align=ft.TextAlign.CENTER, width=250),
            content=ft.Row(
                [
                    ft.Checkbox(
                        label="记住我的选择",
                        value=False,
                        on_change=lambda e: setattr(self, 'remember_choice', e.control.value)
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            actions=[
                ft.TextButton(
                    "收进托盘",
                    icon=ft.Icons.MINIMIZE,
                    on_click=lambda e: self._on_close_choice(True)
                ),
                ft.TextButton(
                    "直接退出",
                    icon=ft.Icons.CLOSE,
                    on_click=lambda e: self._on_close_choice(False)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.open(self.close_dialog)
    
    def _on_close_choice(self, to_tray: bool):
        """处理关闭选择
        
        Args:
            to_tray: True表示收进托盘，False表示直接退出
        """
        # 关闭对话框
        if self.close_dialog and self.page:
            self.page.close(self.close_dialog)
        
        # 如果用户选择记住，保存设置
        if self.remember_choice:
            self.config_manager.save_setting("close_to_tray", to_tray)
        
        if to_tray:
            self._minimize_to_tray()
        else:
            self._do_close()
    
    def _minimize_to_tray(self):
        """最小化到托盘"""
        if self.page:
            self.page.window.visible = False
            self.page.update()
    
    def _restore_from_tray(self, e=None):
        """从托盘恢复窗口"""
        if self.page:
            self.page.window.visible = True
            # 如果窗口被最小化，先恢复窗口
            if self.page.window.minimized:
                self.page.window.minimized = False
            self.page.window.focused = True
            self.page.update()
    
    def _do_close(self, force_exit: bool = False):
        """执行真正的关闭操作
        
        Args:
            force_exit: 是否强制快速退出（用于更新重启）
        """
        # 检查是否有待执行的应用更新
        if self.update_manager.has_pending_app_update():
            self._execute_pending_update(self.update_manager.pending_app_update_script)
        
        # 窗口关闭时的清理逻辑
        self._cleanup(force_cleanup=force_exit)
        
        # 关闭窗口 - 取消阻止关闭，让系统直接处理
        if self.page:
            self.page.window.prevent_close = False
            self.page.window.close()
    
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
    
    def _cleanup(self, force_cleanup: bool = False):
        """清理资源，停止所有进程和线程
        
        Args:
            force_cleanup: 是否强制清理（用于更新重启）
        """
        # 停止资源监控 - 设置事件立即中断等待
        self.monitoring_resources = False
        self._stop_monitoring_event.set()  # 立即中断 Event.wait()
        if self.resource_monitor_thread and self.resource_monitor_thread.is_alive():
            timeout = 0.1 if force_cleanup else 0.2  # 减少等待时间
            self.resource_monitor_thread.join(timeout=timeout)
        
        # 清理日志页面资源
        if hasattr(self, 'log_page') and self.log_page:
            self.log_page.cleanup()
        
        # 清理日志收集器回调
        if self.log_collector:
            self.log_collector.clear_callbacks()
        
        # 停止托盘图标
        if self.tray_icon:
            try:
                # 总是异步停止托盘，避免阻塞
                def stop_tray():
                    try:
                        self.tray_icon.stop()
                    except Exception:
                        pass
                threading.Thread(target=stop_tray, daemon=True).start()
            except Exception:
                pass
        
        # 保存窗口尺寸
        if self.page:
            try:
                self.config_manager.save_setting("window_width", self.page.window.width)
                self.config_manager.save_setting("window_height", self.page.window.height)
            except Exception:
                pass  # 忽略保存失败
        
        # 停止所有进程
        self.process_manager.stop_all()
    
    def _setup_system_tray(self):
        """设置系统托盘（使用 pystray）"""
        try:
            print("开始初始化系统托盘...")
            import pystray
            from PIL import Image, ImageDraw
            print("pystray 和 PIL 导入成功")
            
            # 保存 pystray 模块引用
            self._pystray = pystray
            
            # 创建托盘图标
            print("正在创建托盘图标图像...")
            icon_image = self._create_tray_icon_image()
            print(f"托盘图标创建成功，尺寸: {icon_image.size}, 模式: {icon_image.mode}")
            
            # 获取当前窗口标题
            current_title = self._get_current_window_title()
            print(f"窗口标题: {current_title}")
            
            # 创建托盘菜单
            print("创建托盘菜单...")
            menu = pystray.Menu(
                pystray.MenuItem(
                    "显示窗口",
                    self._on_tray_show,
                    default=True  # 设为默认项，单击时触发
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出程序", self._on_tray_exit)
            )
            print("托盘菜单创建成功")
            
            # 创建托盘图标
            print("创建托盘图标对象...")
            self.tray_icon = pystray.Icon(
                name="lucky_lillia",
                icon=icon_image,
                title=current_title,
                menu=menu
            )
            print("托盘图标对象创建成功")
            
            print("开始启动系统托盘...")
            # 使用 run_detached 方法，这样不会阻塞主线程
            try:
                self.tray_icon.run_detached()
                print("托盘图标已启动（detached 模式）")
            except AttributeError:
                # 如果没有 run_detached 方法，使用线程方式
                print("使用线程方式启动托盘...")
                self.tray_thread = threading.Thread(target=self._run_tray_icon, daemon=True)
                self.tray_thread.start()
                print("托盘线程已启动")
            
        except ImportError as e:
            print(f"系统托盘初始化失败（缺少依赖）: {e}")
            self.tray_icon = None
        except Exception as e:
            print(f"系统托盘初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.tray_icon = None
    
    def _run_tray_icon(self):
        """运行托盘图标的线程函数"""
        try:
            print("托盘图标开始运行...")
            self.tray_icon.run()
            print("托盘图标运行结束")
        except Exception as e:
            print(f"托盘图标运行失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_current_window_title(self) -> str:
        """获取当前窗口标题"""
        if self.page and self.page.title:
            return self.page.title
        return APP_NAME
    
    def _update_tray_title(self):
        """更新托盘图标的提示文字和菜单"""
        if self.tray_icon and hasattr(self, '_pystray'):
            try:
                current_title = self._get_current_window_title()
                # 更新提示文字
                self.tray_icon.title = current_title
                # 重新创建菜单以更新菜单项文本
                self.tray_icon.menu = self._pystray.Menu(
                    self._pystray.MenuItem(
                        current_title,
                        self._on_tray_show,
                        default=True
                    ),
                    self._pystray.Menu.SEPARATOR,
                    self._pystray.MenuItem("退出程序", self._on_tray_exit)
                )
                # 通知托盘更新
                self.tray_icon.update_menu()
            except Exception:
                pass
    
    def _create_tray_icon_image(self):
        """创建托盘图标图像
        
        Returns:
            PIL Image 对象
        """
        from PIL import Image, ImageDraw
        import os
        import sys
        
        # 获取资源文件路径（支持 PyInstaller 打包）
        def get_resource_path(relative_path):
            """获取资源文件的绝对路径"""
            try:
                # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
                base_path = sys._MEIPASS
            except AttributeError:
                # 开发环境中直接使用当前目录
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        # 首先尝试加载现有图标
        icon_paths = [
            "icon.ico", "icon.png", "icon.jpg", "icon.jpeg",
            "assets/icon.ico", "assets/icon.png", "assets/icon.jpg", "assets/icon.jpeg"
        ]
        print(f"尝试加载图标文件...")
        for path in icon_paths:
            full_path = get_resource_path(path)
            print(f"检查路径: {full_path}")
            if os.path.exists(full_path):
                try:
                    print(f"找到图标文件: {full_path}")
                    img = Image.open(full_path)
                    print(f"原始图标: 尺寸={img.size}, 模式={img.mode}")
                    # 确保图标是 RGBA 格式，并且尺寸合适
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                        print("已转换为 RGBA 格式")
                    # 调整到合适的托盘图标尺寸
                    if img.size != (32, 32):
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        print("已调整为 32x32 尺寸")
                    print(f"最终图标: 尺寸={img.size}, 模式={img.mode}")
                    return img
                except Exception as e:
                    print(f"加载图标失败 {full_path}: {e}")
                    pass
            else:
                print(f"图标文件不存在: {full_path}")
        
        print("未找到图标文件，使用默认图标")
        
        # 创建默认图标 (32x32 蓝色圆形机器人图标，适合托盘)
        size = 32
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景圆
        draw.ellipse([2, 2, size-2, size-2], fill=(100, 149, 237, 255))
        # 眼睛
        draw.ellipse([9, 11, 14, 16], fill=(255, 255, 255, 255))
        draw.ellipse([18, 11, 23, 16], fill=(255, 255, 255, 255))
        # 嘴巴
        draw.arc([10, 18, 22, 25], 0, 180, fill=(255, 255, 255, 255), width=2)
        
        return img
    
    def _on_tray_show(self, icon=None, item=None):
        """托盘菜单：显示主窗口"""
        if self.page:
            self.page.window.visible = True
            # 如果窗口被最小化，先恢复窗口
            if self.page.window.minimized:
                self.page.window.minimized = False
            self.page.window.focused = True
            self.page.update()
    
    def _on_tray_exit(self, icon=None, item=None):
        """托盘菜单：退出程序"""
        # 停止托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
        # 执行关闭
        self._do_close()
    
    def _start_resource_monitoring(self):
        """启动资源监控线程"""
        if not self.monitoring_resources:
            self.monitoring_resources = True
            self._stop_monitoring_event.clear()  # 重置停止事件
            self.resource_monitor_thread = threading.Thread(
                target=self._monitor_resources,
                daemon=True
            )
            self.resource_monitor_thread.start()
    
    def _check_auto_start_bot(self):
        """检查是否需要自动启动bot"""
        try:
            # 加载配置
            config = self.config_manager.load_config()
            auto_start_bot = config.get("auto_start_bot", False)
            
            if auto_start_bot:
                # 延迟一秒后自动启动，让界面完全加载完成
                import threading
                def delayed_start():
                    time.sleep(1)
                    if self.page:
                        # 触发首页的全局启动按钮
                        self.home_page._on_global_start_click(None)
                
                start_thread = threading.Thread(target=delayed_start, daemon=True)
                start_thread.start()
                
        except Exception as e:
            # 忽略自动启动过程中的错误
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"自动启动bot失败: {e}")
    
    def _check_minimize_to_tray_on_start(self):
        """检查是否需要启动后自动缩进托盘"""
        try:
            # 加载配置
            config = self.config_manager.load_config()
            minimize_to_tray_on_start = config.get("minimize_to_tray_on_start", False)
            
            if minimize_to_tray_on_start:
                # 延迟一点执行，确保托盘已初始化
                import threading
                def delayed_minimize():
                    time.sleep(2.5)  # 等待托盘初始化完成
                    if self.page:
                        self._minimize_to_tray()
                
                minimize_thread = threading.Thread(target=delayed_minimize, daemon=True)
                minimize_thread.start()
                
        except Exception as e:
            # 忽略自动缩进托盘过程中的错误
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"自动缩进托盘失败: {e}")
    
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
            
            # 使用 Event.wait 替代 time.sleep，可以被快速中断
            if self._stop_monitoring_event.wait(timeout=RESOURCE_MONITOR_INTERVAL):
                # 如果事件被设置，立即退出循环
                break
