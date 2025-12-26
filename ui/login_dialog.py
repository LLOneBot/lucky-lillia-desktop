"""登录对话框"""

import base64
import logging
import threading
from typing import Optional, Callable, List

import flet as ft

from utils.login_service import LoginService, LoginAccount, QRCodeInfo, LoginResult

logger = logging.getLogger(__name__)


class LoginDialog:
    def __init__(self, 
                 page: ft.Page,
                 pmhq_port: int,
                 on_login_success: Optional[Callable[[str], None]] = None,
                 on_cancel: Optional[Callable[[], None]] = None):
        self.page = page
        self.pmhq_port = pmhq_port
        self.on_login_success = on_login_success
        self.on_cancel = on_cancel
        
        self.login_service = LoginService(pmhq_port)
        self.dialog: Optional[ft.AlertDialog] = None
        self.quick_login_accounts: List[LoginAccount] = []
        self.selected_account: Optional[LoginAccount] = None
        self.is_qrcode_mode = False
        self._uin_check_running = False
        self._uin_check_thread: Optional[threading.Thread] = None
        
        # UI组件
        self.content_container: Optional[ft.Container] = None
        self.avatar_image: Optional[ft.Image] = None
        self.nickname_text: Optional[ft.Text] = None
        self.uin_text: Optional[ft.Text] = None
        self.login_button: Optional[ft.ElevatedButton] = None
        self.switch_account_button: Optional[ft.TextButton] = None
        self.qrcode_button: Optional[ft.TextButton] = None
        self.qrcode_image: Optional[ft.Image] = None
        self.qrcode_tip_text: Optional[ft.Text] = None
        self.error_text: Optional[ft.Text] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        
    def show(self, auto_login_uin: str = ""):
        # 获取可快速登录的账号列表
        self._fetch_accounts_and_show(auto_login_uin)
    
    def _fetch_accounts_and_show(self, auto_login_uin: str = ""):
        def fetch_thread():
            self.quick_login_accounts = self.login_service.get_quick_login_accounts()
            logger.info(f"获取到 {len(self.quick_login_accounts)} 个可快速登录的账号")
            
            # 在主线程中显示对话框
            async def show_dialog():
                if self.quick_login_accounts:
                    # 有可快速登录的账号
                    if auto_login_uin:
                        # 查找指定的账号
                        for acc in self.quick_login_accounts:
                            if acc.uin == auto_login_uin:
                                self.selected_account = acc
                                break
                    
                    if not self.selected_account:
                        # 使用第一个账号作为默认
                        self.selected_account = self.quick_login_accounts[0]
                    
                    self._build_quick_login_dialog()
                    
                    # 如果指定了自动登录，直接尝试登录
                    if auto_login_uin and self.selected_account and self.selected_account.uin == auto_login_uin:
                        self._do_quick_login()
                else:
                    # 没有可快速登录的账号，显示扫码登录
                    self.is_qrcode_mode = True
                    self._build_qrcode_login_dialog()
                
                if self.dialog:
                    self.page.show_dialog(self.dialog)
            
            if self.page:
                self.page.run_task(show_dialog)
        
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()
    
    def _build_quick_login_dialog(self):
        # 头像
        avatar_url = self.selected_account.face_url if self.selected_account else ""
        self.avatar_image = ft.Container(
            content=ft.Image(
                src=avatar_url,
                width=80,
                height=80,
                fit="cover",
                border_radius=ft.border_radius.all(40),
                error_content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.GREY_400)
            ),
            width=80,
            height=80,
            border_radius=ft.border_radius.all(40),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
        
        # 昵称
        nickname = self.selected_account.nick_name if self.selected_account else ""
        self.nickname_text = ft.Text(
            nickname,
            size=18,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        
        # QQ号
        uin = self.selected_account.uin if self.selected_account else ""
        self.uin_text = ft.Text(
            f"QQ: {uin}",
            size=14,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )
        
        # 错误提示
        self.error_text = ft.Text(
            "",
            size=13,
            color=ft.Colors.RED_600,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )
        
        # 加载指示器
        self.loading_indicator = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            visible=False,
        )
        
        # 登录按钮
        self.login_button = ft.ElevatedButton(
            "登录",
            icon=ft.Icons.LOGIN,
            on_click=self._on_login_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=40, vertical=12),
            ),
            width=200,
        )
        
        # 切换账号按钮
        self.switch_account_button = ft.TextButton(
            "切换账号",
            icon=ft.Icons.SWAP_HORIZ,
            on_click=self._on_switch_account_click,
            visible=len(self.quick_login_accounts) > 1,
        )
        
        # 扫码登录按钮
        self.qrcode_button = ft.TextButton(
            "扫码登录",
            icon=ft.Icons.QR_CODE,
            on_click=self._on_qrcode_click,
        )
        
        # 内容容器
        self.content_container = ft.Container(
            content=ft.Column([
                self.avatar_image,
                ft.Container(height=8),
                self.nickname_text,
                self.uin_text,
                self.error_text,
                ft.Container(height=8),
                ft.Row([
                    self.loading_indicator,
                    self.login_button,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Row([
                    self.switch_account_button,
                    self.qrcode_button,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, tight=True),
            width=280,
            padding=12,
        )
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("快速登录"),
            content=self.content_container,
        )
    
    def _build_qrcode_login_dialog(self):
        # 二维码图片
        self.qrcode_image = ft.Image(
            src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            width=180,
            height=180,
            fit="contain",
            visible=False,
        )
        
        # 加载指示器
        self.loading_indicator = ft.ProgressRing(
            width=40,
            height=40,
            stroke_width=3,
        )
        
        # 提示文字
        self.qrcode_tip_text = ft.Text(
            "正在获取二维码...",
            size=14,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )
        
        # 错误提示
        self.error_text = ft.Text(
            "",
            size=13,
            color=ft.Colors.RED_600,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )
        
        # 快速登录按钮（如果有可用账号）
        quick_login_btn_visible = len(self.quick_login_accounts) > 0
        self.switch_account_button = ft.TextButton(
            "快速登录",
            icon=ft.Icons.FLASH_ON,
            on_click=self._on_quick_login_mode_click,
            visible=quick_login_btn_visible,
        )
        
        # 内容容器
        self.content_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            content=self.loading_indicator,
                            alignment=ft.Alignment(0, 0),
                        ),
                        self.qrcode_image,
                    ]),
                    width=180,
                    height=180,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=6),
                self.qrcode_tip_text,
                self.error_text,
                self.switch_account_button,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, tight=True),
            width=260,
            padding=12,
        )
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("扫码登录"),
            content=self.content_container,
        )
        
        # 启动SSE监听并请求二维码
        self._start_qrcode_login()
    
    def _start_qrcode_login(self):
        logger.info("启动扫码登录流程")
        
        # 启动SSE监听
        logger.info("启动SSE监听器")
        self.login_service.start_sse_listener(
            qrcode_callback=self._on_qrcode_received,
            login_success_callback=self._on_sse_login_success
        )
        
        # 启动uin检查线程
        self._start_uin_check()
        
        # 请求二维码
        def request_qrcode():
            import time
            logger.info("等待SSE连接建立...")
            time.sleep(0.5)  # 等待SSE连接建立
            logger.info("开始请求二维码")
            success = self.login_service.request_qrcode()
            logger.info(f"请求二维码结果: success={success}")
            if not success:
                async def show_error():
                    logger.warning("获取二维码失败，显示错误提示")
                    if self.qrcode_tip_text:
                        self.qrcode_tip_text.value = "获取二维码失败，请重试"
                    if self.loading_indicator:
                        self.loading_indicator.visible = False
                    if self.page:
                        self.page.update()
                
                if self.page:
                    self.page.run_task(show_error)
        
        thread = threading.Thread(target=request_qrcode, daemon=True)
        thread.start()
    
    def _on_qrcode_received(self, qrcode_info: QRCodeInfo):
        logger.info(f"收到二维码回调, png_base64长度={len(qrcode_info.png_base64) if qrcode_info.png_base64 else 0}")
        
        async def update_qrcode():
            logger.info("更新二维码UI")
            if self.qrcode_image and qrcode_info.png_base64:
                png_base64 = qrcode_info.png_base64
                # 确保是 data URI 格式
                if not png_base64.startswith("data:"):
                    png_base64 = f"data:image/png;base64,{png_base64}"
                self.qrcode_image.src = png_base64
                self.qrcode_image.visible = True
                logger.info("二维码图片已设置")
            else:
                logger.warning(f"无法设置二维码: qrcode_image={self.qrcode_image is not None}, png_base64={bool(qrcode_info.png_base64)}")
            if self.loading_indicator:
                self.loading_indicator.visible = False
            if self.qrcode_tip_text:
                self.qrcode_tip_text.value = "请使用手机QQ扫描二维码登录"
            if self.page:
                self.page.update()
                logger.info("页面已更新")
        
        if self.page:
            self.page.run_task(update_qrcode)
        else:
            logger.warning("page为None，无法更新UI")
    
    def _on_sse_login_success(self, uin: str):
        self._handle_login_success(uin)
    
    def _start_uin_check(self):
        if self._uin_check_running:
            return
        
        self._uin_check_running = True
        self._uin_check_thread = threading.Thread(
            target=self._uin_check_loop,
            daemon=True
        )
        self._uin_check_thread.start()
    
    def _stop_uin_check(self):
        self._uin_check_running = False
        if self._uin_check_thread:
            self._uin_check_thread.join(timeout=2)
            self._uin_check_thread = None
    
    def _uin_check_loop(self):
        import time
        from utils.pmhq_client import PMHQClient
        
        client = PMHQClient(self.pmhq_port, timeout=5)
        while self._uin_check_running:
            info = client.fetch_self_info()
            if info and info.uin:
                self._handle_login_success(info.uin)
                return
            time.sleep(1)
    
    def _handle_login_success(self, uin: str):
        logger.info(f"登录成功: {uin}")
        
        # 标记停止检查（不要在这里join，因为可能是从uin_check_loop中调用的）
        self._uin_check_running = False
        self.login_service.stop_sse_listener()
        
        async def close_and_callback():
            if self.dialog and self.page:
                self.page.pop_dialog()
            
            if self.on_login_success:
                self.on_login_success(uin)
        
        if self.page:
            self.page.run_task(close_and_callback)
    
    def _on_login_click(self, e):
        self._do_quick_login()
    
    def _do_quick_login(self):
        if not self.selected_account:
            return
        
        # 显示加载状态
        if self.loading_indicator:
            self.loading_indicator.visible = True
        if self.login_button:
            self.login_button.disabled = True
        if self.error_text:
            self.error_text.value = "登录中，请稍候..."
            self.error_text.color = ft.Colors.BLUE_600
            self.error_text.visible = True
        if self.page:
            self.page.update()
        
        def login_thread():
            result = self.login_service.quick_login(self.selected_account.uin)
            logger.info(f"快速登录结果: success={result.success}, error_msg={result.error_msg}")
            
            async def handle_result():
                if result.success:
                    # 登录请求成功，启动uin检查等待实际登录完成
                    self._start_uin_check()
                    # 保持加载状态，等待uin检查确认登录成功
                else:
                    # 登录失败，显示错误
                    if self.loading_indicator:
                        self.loading_indicator.visible = False
                    if self.login_button:
                        self.login_button.disabled = False
                    if self.error_text:
                        self.error_text.value = result.error_msg or "登录失败"
                        self.error_text.color = ft.Colors.RED_600
                        self.error_text.visible = True
                    logger.warning(f"快速登录失败: {result.error_msg}")
                
                if self.page:
                    self.page.update()
            
            if self.page:
                self.page.run_task(handle_result)
        
        thread = threading.Thread(target=login_thread, daemon=True)
        thread.start()
    
    def _on_switch_account_click(self, e):
        self._show_account_list()
    
    def _show_account_list(self):
        # 先关闭主登录对话框
        if self.dialog and self.page:
            self.page.pop_dialog()
        
        # 构建账号列表
        account_items = []
        for acc in self.quick_login_accounts:
            is_selected = self.selected_account and acc.uin == self.selected_account.uin
            
            item = ft.ListTile(
                leading=ft.Container(
                    content=ft.Image(
                        src=acc.face_url,
                        width=40,
                        height=40,
                        fit="cover",
                        border_radius=ft.border_radius.all(20),
                        error_content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=40)
                    ),
                    width=40,
                    height=40,
                    border_radius=ft.border_radius.all(20),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                title=ft.Text(acc.nick_name, size=14),
                subtitle=ft.Text(f"QQ: {acc.uin}", size=12),
                trailing=ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_600) if is_selected else None,
                on_click=lambda e, account=acc: self._on_account_selected(account),
            )
            account_items.append(item)
        
        # 保存账号选择对话框的引用
        self._account_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("选择账号"),
            content=ft.Container(
                content=ft.Column(
                    controls=account_items,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                ),
                width=300,
                height=min(len(account_items) * 72, 360),
            ),
            actions=[
                ft.TextButton("取消", on_click=self._on_account_cancel_click),
            ],
        )
        
        if self.page:
            self.page.show_dialog(self._account_dialog)
    
    def _on_account_cancel_click(self, e):
        # 关闭账号选择对话框
        if hasattr(self, '_account_dialog') and self._account_dialog and self.page:
            self.page.pop_dialog()
        
        # 重新显示主登录对话框
        self._build_quick_login_dialog()
        if self.dialog and self.page:
            self.page.show_dialog(self.dialog)
    
    def _on_account_selected(self, account: LoginAccount):
        self.selected_account = account
        
        # 关闭账号选择对话框
        if hasattr(self, '_account_dialog') and self._account_dialog and self.page:
            self.page.pop_dialog()
        
        # 重新构建并显示快速登录对话框（显示选中的账号）
        self._build_quick_login_dialog()
        if self.dialog and self.page:
            self.page.show_dialog(self.dialog)
    
    def _on_qrcode_click(self, e):
        self.is_qrcode_mode = True
        self._switch_to_qrcode_mode()
    
    def _switch_to_qrcode_mode(self):
        # 关闭当前对话框
        if self.dialog and self.page:
            self.page.pop_dialog()
        
        # 构建并显示扫码登录对话框
        self._build_qrcode_login_dialog()
        if self.dialog and self.page:
            self.page.show_dialog(self.dialog)
    
    def _on_quick_login_mode_click(self, e):
        if not self.quick_login_accounts:
            return
        
        self.is_qrcode_mode = False
        
        # 在后台停止SSE和uin检查，不阻塞UI
        self._uin_check_running = False
        def stop_background():
            self.login_service.stop_sse_listener()
            if self._uin_check_thread:
                self._uin_check_thread.join(timeout=2)
                self._uin_check_thread = None
        threading.Thread(target=stop_background, daemon=True).start()
        
        # 关闭当前对话框
        if self.dialog and self.page:
            self.page.pop_dialog()
        
        # 设置默认账号
        if not self.selected_account:
            self.selected_account = self.quick_login_accounts[0]
        
        # 构建并显示快速登录对话框
        self._build_quick_login_dialog()
        if self.dialog and self.page:
            self.page.show_dialog(self.dialog)
    
    def _on_cancel_click(self, e):
        self.close()
        if self.on_cancel:
            self.on_cancel()
    
    def close(self):
        # 停止SSE和uin检查
        self._stop_uin_check()
        self.login_service.stop_sse_listener()
        
        if self.dialog and self.page:
            self.page.pop_dialog()
