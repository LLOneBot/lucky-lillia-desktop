"""日志页面UI模块 - 显示进程日志输出"""

import flet as ft
import threading
import time
from typing import Optional
from core.log_collector import LogCollector, LogEntry
from utils.constants import MAX_LOG_LINES


class LogPage:
    """日志页面组件 - 自动刷新模式"""

    MAX_DISPLAY = 500
    AUTO_REFRESH_INTERVAL = 0.5  # 自动刷新间隔（秒）

    def __init__(self, log_collector: LogCollector):
        """初始化日志页面"""
        self.log_collector = log_collector
        self.control: Optional[ft.Container] = None
        self.log_text: Optional[ft.TextField] = None
        self._is_page_visible = False  # 页面是否可见
        self._auto_refresh_enabled = True  # 自动刷新开关状态
        self._auto_refresh_thread: Optional[threading.Thread] = None

    def build(self):
        """构建UI组件"""
        self.auto_refresh_switch = ft.Switch(
            label="自动刷新",
            value=True,
            on_change=self._on_auto_refresh_change,
        )

        self.clear_btn = ft.ElevatedButton(
            "清空日志",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._on_clear_logs,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ERROR,
                color=ft.Colors.ON_ERROR,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        # 使用单个 Text 控件显示所有日志，支持多行复制
        self.log_text = ft.Text(
            value="暂无日志",
            size=12,
            font_family="Consolas",
            selectable=True,
            width=float("inf"),  # 最大宽度
        )

        # 使用 Column 包裹，支持滚动
        self.log_column = ft.Column(
            controls=[self.log_text],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.log_container = ft.Container(
            content=self.log_column,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
            border_radius=12,
            padding=16,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.OUTLINE)),
        )

        self.control = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                name=ft.Icons.ARTICLE, size=36, color=ft.Colors.PRIMARY
                            ),
                            ft.Text("日志查看器", size=32, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(expand=True),
                                    self.auto_refresh_switch,
                                    self.clear_btn,
                                ],
                                spacing=12,
                                alignment=ft.MainAxisAlignment.END,
                            ),
                            padding=16,
                        ),
                        elevation=2,
                    ),
                    self.log_container,
                ],
                spacing=20,
                expand=True,
            ),
            padding=28,
            expand=True,
        )

        return self.control

    def _format_log_entry(self, entry: LogEntry) -> str:
        """格式化日志条目"""
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        prefix = "ERR" if entry.level == "stderr" else "   "
        return f"{prefix} {timestamp} [{entry.process_name}] {entry.message}"

    def _on_auto_refresh_change(self, e):
        """自动刷新开关变化"""
        self._auto_refresh_enabled = e.control.value

    def _on_clear_logs(self, e):
        """清空日志"""
        self.log_collector.clear_logs()
        if self.log_text:
            self.log_text.value = "暂无日志"
            self.log_text.color = ft.Colors.GREY_600
            try:
                if self.control and self.control.page:
                    self.control.page.update()
            except Exception:
                pass

    def _load_logs(self):
        """加载日志"""
        logs = self.log_collector.get_logs()

        if not logs:
            text = "暂无日志"
        else:
            # 正序显示（旧的在上，新的在下）
            recent_logs = list(logs)[-self.MAX_DISPLAY:]
            lines = [self._format_log_entry(entry) for entry in recent_logs]
            text = "\n".join(lines)

        if self.log_text:
            self.log_text.value = text
            self.log_text.color = ft.Colors.GREY_600 if not logs else ft.Colors.ON_SURFACE
            try:
                if self.control and self.control.page:
                    self.control.page.update()
                    # 开启自动刷新时，滚动到底部
                    if self._auto_refresh_enabled and self.log_column:
                        self.log_column.scroll_to(offset=-1, duration=0)
            except Exception as e:
                print(f"日志更新失败: {e}")

    def _auto_refresh_loop(self):
        """自动刷新循环"""
        while True:
            time.sleep(self.AUTO_REFRESH_INTERVAL)
            # 只有页面可见且开启自动刷新时才更新
            if self._is_page_visible and self._auto_refresh_enabled:
                self._load_logs()

    def _start_auto_refresh(self):
        """启动自动刷新线程"""
        if self._auto_refresh_thread is None or not self._auto_refresh_thread.is_alive():
            self._auto_refresh_thread = threading.Thread(
                target=self._auto_refresh_loop, daemon=True
            )
            self._auto_refresh_thread.start()

    def refresh(self):
        """刷新页面"""
        self._load_logs()

    def on_page_enter(self):
        """进入页面"""
        self._is_page_visible = True
        self._load_logs()
        self._start_auto_refresh()

    def on_page_leave(self):
        """离开页面"""
        self._is_page_visible = False
