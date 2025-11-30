"""日志页面UI模块 - 显示进程日志输出"""

import flet as ft
import threading
import time
from typing import List
from core.log_collector import LogCollector, LogEntry


class LogPage:
    """日志页面组件"""

    def __init__(self, log_collector: LogCollector):
        """初始化日志页面

        Args:
            log_collector: 日志收集器实例
        """
        self.log_collector = log_collector
        self.control = None
        self.auto_scroll = True

        # 批量更新相关
        self._pending_logs: List[LogEntry] = []
        self._pending_lock = threading.Lock()
        self._update_scheduled = False

        # 注册日志回调
        self.log_collector.set_callback(self._on_new_log)

    def build(self):
        """构建UI组件"""
        # 清空日志按钮
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

        # 自动滚动开关
        self.auto_scroll_switch = ft.Switch(
            label="自动滚动", value=True, on_change=self._on_auto_scroll_change
        )

        # 日志显示区域
        self.log_column = ft.Column(
            controls=[],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
        )

        # 使用ListView包装以支持自动滚动
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
                    # 标题栏
                    ft.Row(
                        [
                            ft.Icon(
                                name=ft.Icons.ARTICLE, size=36, color=ft.Colors.PRIMARY
                            ),
                            ft.Text(
                                "日志查看器", size=32, weight=ft.FontWeight.BOLD
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                    # 控制栏
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(expand=True),  # 弹性空间
                                    self.auto_scroll_switch,
                                    self.clear_btn,
                                ],
                                spacing=12,
                                alignment=ft.MainAxisAlignment.END,
                            ),
                            padding=16,
                        ),
                        elevation=2,
                    ),
                    # 日志显示区域
                    self.log_container,
                ],
                spacing=20,
                expand=True,
            ),
            padding=28,
            expand=True,
        )

        # 初始加载日志
        self._refresh_logs()

        return self.control

    def _on_clear_logs(self, e):
        """清空日志按钮点击处理"""
        # 先清空待处理队列，防止线程竞争
        with self._pending_lock:
            self._pending_logs.clear()
            self._update_scheduled = False
        
        self.log_collector.clear_logs()
        self._refresh_logs()
        if self.control and self.control.page:
            self.control.page.update()

    def _on_auto_scroll_change(self, e):
        """自动滚动开关变化处理"""
        self.auto_scroll = e.control.value

    def _on_new_log(self, entry: LogEntry):
        """新日志回调处理 - 使用批量更新减少UI刷新频率

        Args:
            entry: 新的日志条目
        """
        # 将日志添加到待处理队列
        with self._pending_lock:
            self._pending_logs.append(entry)

            # 如果还没有安排更新，则安排一个
            if not self._update_scheduled and self.control and self.control.page:
                self._update_scheduled = True
                # 使用50ms的延迟批量更新，减少UI刷新频率
                threading.Timer(0.05, self._flush_pending_logs).start()

    def _flush_pending_logs(self):
        """批量刷新待处理的日志到UI"""
        with self._pending_lock:
            if not self._pending_logs:
                self._update_scheduled = False
                return

            # 取出所有待处理日志
            logs_to_add = self._pending_logs.copy()
            self._pending_logs.clear()
            self._update_scheduled = False

        # 检查控件是否仍然有效
        if not self.control or not self.control.page or not self.log_column:
            return

        try:
            # 批量添加日志到显示
            for entry in logs_to_add:
                log_widget = self._create_log_widget(entry)
                self.log_column.controls.append(log_widget)

            # 限制显示的日志数量以保持性能
            if len(self.log_column.controls) > 1000:
                self.log_column.controls = self.log_column.controls[-1000:]

            # 更新UI
            if self.control and self.control.page:
                self.control.page.update()
                # 如果启用自动滚动，滚动到底部
                if self.auto_scroll:
                    self.log_column.scroll_to(offset=-1, duration=0)
        except (AssertionError, Exception):
            pass  # 忽略更新错误，包括控件状态不一致的情况

    def _refresh_logs(self):
        """刷新日志显示"""
        logs = self.log_collector.get_logs()

        # 清空当前显示
        self.log_column.controls.clear()

        # 添加日志
        if not logs:
            self.log_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        "暂无日志",
                        size=14,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    padding=10,
                    expand=True,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for entry in logs:
                log_widget = self._create_log_widget(entry)
                self.log_column.controls.append(log_widget)

    def _create_log_widget(self, entry: LogEntry) -> ft.Container:
        """创建日志显示组件

        Args:
            entry: 日志条目

        Returns:
            日志显示组件
        """
        # 根据日志级别设置颜色和图标
        if entry.level == "stderr":
            text_color = ft.Colors.RED_700
            bg_color = ft.Colors.RED_50
            icon = ft.Icons.ERROR_OUTLINE
            icon_color = ft.Colors.RED_600
        else:
            text_color = ft.Colors.ON_SURFACE
            bg_color = ft.Colors.SURFACE
            icon = ft.Icons.INFO_OUTLINE
            icon_color = ft.Colors.BLUE_600

        # 格式化时间戳
        timestamp_str = entry.timestamp.strftime("%H:%M:%S")

        # 创建日志文本
        log_content = ft.Row(
            [
                ft.Icon(icon, size=16, color=icon_color),
                ft.Text(
                    timestamp_str,
                    size=12,
                    color=ft.Colors.GREY_600,
                    weight=ft.FontWeight.W_500,
                    font_family="Courier New",
                ),
                ft.Container(
                    content=ft.Text(
                        entry.process_name,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    ),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=4,
                ),
                ft.Text(
                    entry.message,
                    size=13,
                    color=text_color,
                    font_family="Courier New",
                    selectable=True,
                    expand=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=log_content,
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
            border=ft.border.all(
                1,
                ft.Colors.OUTLINE_VARIANT
                if entry.level == "stdout"
                else ft.Colors.ERROR,
            ),
        )

    def refresh(self):
        """刷新页面（外部调用）"""
        self._refresh_logs()
        if self.control and self.control.page:
            self.control.page.update()
            self._scroll_to_bottom()

    def on_page_enter(self):
        """进入页面时调用 - 刷新并滚动到底部"""
        self._refresh_logs()
        if self.control and self.control.page:
            self.control.page.update()
            # 延迟滚动到底部，确保UI已渲染
            threading.Thread(target=self._delayed_scroll_to_bottom, daemon=True).start()

    def _delayed_scroll_to_bottom(self):
        """延迟滚动到底部"""
        time.sleep(0.2)  # 等待UI渲染完成
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        if (
            self.auto_scroll
            and self.log_column.controls
            and self.control
            and self.control.page
        ):
            try:
                self.log_column.scroll_to(offset=-1, duration=0)
                self.control.page.update()
            except Exception:
                pass
