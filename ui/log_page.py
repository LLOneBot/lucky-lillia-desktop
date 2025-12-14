"""日志页面UI模块 - 显示进程日志输出"""

import flet as ft
import threading
from typing import Optional, List, Tuple
from core.log_collector import LogCollector, LogEntry
from utils.constants import MAX_LOG_LINES


class LogPage:
    """日志页面组件 - 使用固定控件池避免内存泄漏"""

    MAX_DISPLAY = 100  # 显示行数
    AUTO_REFRESH_INTERVAL = 0.5  # 刷新频率

    def __init__(self, log_collector: LogCollector):
        """初始化日志页面"""
        self.log_collector = log_collector
        self.control: Optional[ft.Container] = None
        self._is_page_visible = False
        self._auto_refresh_enabled = True
        self._auto_refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_lock = threading.Lock()
        self._last_log_hash = None
        # 固定控件池
        self._log_rows: List[Tuple[ft.Container, ft.Text]] = []
        # 选中的行索引集合
        self._selected_rows: set = set()

    def build(self):
        """构建UI组件"""
        self.auto_refresh_switch = ft.Switch(
            label="自动刷新",
            value=True,
            on_change=self._on_auto_refresh_change,
        )

        self.copy_btn = ft.ElevatedButton(
            "复制选中",
            icon=ft.Icons.COPY,
            on_click=self._on_copy_logs,
            visible=False,  # 初始隐藏，有选中时显示
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        self.clear_selection_btn = ft.TextButton(
            "取消选择",
            on_click=self._on_clear_selection,
            visible=False,
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

        # 预创建固定数量的日志行控件
        self._log_rows = []
        for i in range(self.MAX_DISPLAY):
            text = ft.Text(
                value="",
                size=13,
                font_family="Cascadia Code, Consolas, monospace",
                color=ft.Colors.ON_SURFACE,
                expand=True,
            )
            row = ft.Row(
                controls=[text],
            )
            container = ft.Container(
                content=row,
                padding=ft.padding.symmetric(vertical=2, horizontal=4),
                border_radius=4,
                on_click=lambda e, idx=i: self._on_row_click(idx),
                ink=True,  # 点击效果
                visible=False,
            )
            self._log_rows.append((container, row, text))

        # 空状态提示
        self._empty_text = ft.Text(
            "暂无日志",
            size=14,
            color=ft.Colors.GREY_600,
            italic=True,
        )
        self._empty_container = ft.Container(
            content=self._empty_text,
            alignment=ft.alignment.center,
            expand=True,
            visible=True,
        )

        # 日志列表
        self.log_column = ft.Column(
            controls=[self._empty_container] + [container for container, _, _ in self._log_rows],
            spacing=2,
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
                                    self.clear_selection_btn,
                                    self.copy_btn,
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
        prefix = "ERR" if entry.level == "stderr" else "   "
        # LLOneBot 日志已包含时间戳，只显示前缀和原始消息
        if entry.process_name == "LLOneBot":
            return f"{prefix} {entry.message}"
        
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        return f"{prefix} {timestamp} [{entry.process_name}] {entry.message}"

    def _on_auto_refresh_change(self, e):
        """自动刷新开关变化"""
        self._auto_refresh_enabled = e.control.value

    def _on_row_click(self, idx: int):
        """点击行选中/取消选中"""
        if idx >= len(self._log_rows):
            return
        
        container, _, _ = self._log_rows[idx]
        
        if idx in self._selected_rows:
            self._selected_rows.remove(idx)
            container.bgcolor = None
        else:
            self._selected_rows.add(idx)
            container.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY)
        
        # 只更新被点击的行
        try:
            if self.control and self.control.page:
                container.update()
        except Exception:
            pass
        
        # 更新按钮可见性
        has_selection = len(self._selected_rows) > 0
        self.copy_btn.visible = has_selection
        self.clear_selection_btn.visible = has_selection
        
        try:
            if self.control and self.control.page:
                self.copy_btn.update()
                self.clear_selection_btn.update()
        except Exception:
            pass

    def _update_row_selection(self):
        """更新所有行的选中状态显示（用于清除选择）"""
        for i in list(self._selected_rows):
            if i < len(self._log_rows):
                container, _, _ = self._log_rows[i]
                container.bgcolor = None
                try:
                    if self.control and self.control.page:
                        container.update()
                except Exception:
                    pass
        self._selected_rows.clear()

    def _on_clear_selection(self, e):
        """取消所有选择"""
        self._update_row_selection()  # 这会清除选中并更新UI
        self.copy_btn.visible = False
        self.clear_selection_btn.visible = False
        try:
            if self.control and self.control.page:
                self.copy_btn.update()
                self.clear_selection_btn.update()
        except Exception:
            pass

    def _on_copy_logs(self, e):
        """复制选中的日志到剪贴板"""
        if not self._selected_rows:
            return
        
        # 获取选中行的文本
        lines = []
        sorted_indices = sorted(self._selected_rows)
        for idx in sorted_indices:
            if idx < len(self._log_rows):
                _, _, text = self._log_rows[idx]
                if text.value:
                    lines.append(text.value)
        
        if lines and self.control and self.control.page:
            self.control.page.set_clipboard("\n".join(lines))
            self.control.page.open(
                ft.SnackBar(content=ft.Text(f"已复制 {len(lines)} 行日志"), duration=2000)
            )
            # 复制后清除选择
            self._on_clear_selection(None)

    def _on_clear_logs(self, e):
        """清空日志"""
        self.log_collector.clear_logs()
        self._last_log_hash = None
        # 隐藏所有行，显示空状态
        self._empty_container.visible = True
        for container, row, text in self._log_rows:
            container.visible = False
            text.value = ""
        try:
            if self.control and self.control.page:
                self.log_column.update()
        except Exception:
            pass

    def _load_logs(self, force: bool = False):
        """加载日志"""
        if not self._update_lock.acquire(blocking=False):
            return

        try:
            if not self._is_page_visible:
                return

            log_count = self.log_collector.get_log_count()

            if log_count == 0:
                if self._last_log_hash is not None or force:
                    self._last_log_hash = None
                    self._empty_container.visible = True
                    for container, row, text in self._log_rows:
                        container.visible = False
                    try:
                        if self.control and self.control.page and self._is_page_visible:
                            self.log_column.update()
                    except Exception:
                        pass
                return

            # 获取最新日志
            logs = self.log_collector.get_recent_logs(self.MAX_DISPLAY)
            if not logs:
                return

            # 检测变化
            last_log = logs[-1]
            current_hash = (log_count, id(last_log), last_log.timestamp)
            if not force and current_hash == self._last_log_hash:
                return

            self._last_log_hash = current_hash
            self._empty_container.visible = False

            # 更新预创建的控件
            for i, (container, row, text) in enumerate(self._log_rows):
                if i < len(logs):
                    entry = logs[i]
                    formatted = self._format_log_entry(entry)
                    if text.value != formatted:
                        text.value = formatted
                        text.color = ft.Colors.RED_700 if entry.level == "stderr" else ft.Colors.ON_SURFACE
                    if not container.visible:
                        container.visible = True
                else:
                    if container.visible:
                        container.visible = False

            try:
                if self.control and self.control.page and self._is_page_visible:
                    self.log_column.update()
                    if self._auto_refresh_enabled:
                        self.log_column.scroll_to(offset=-1, duration=0)
            except Exception:
                pass

        finally:
            self._update_lock.release()

    def _auto_refresh_loop(self):
        """自动刷新循环"""
        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=self.AUTO_REFRESH_INTERVAL):
                break
            # 有选中行时暂停自动刷新
            if self._is_page_visible and self._auto_refresh_enabled and not self._selected_rows:
                try:
                    self._load_logs()
                except Exception:
                    pass

    def _start_auto_refresh(self):
        """启动自动刷新线程"""
        if self._auto_refresh_thread is None or not self._auto_refresh_thread.is_alive():
            self._stop_event.clear()
            self._auto_refresh_thread = threading.Thread(
                target=self._auto_refresh_loop, daemon=True
            )
            self._auto_refresh_thread.start()

    def cleanup(self):
        """清理资源"""
        self._stop_event.set()
        if self._auto_refresh_thread and self._auto_refresh_thread.is_alive():
            self._auto_refresh_thread.join(timeout=1.0)

    def refresh(self):
        """刷新页面"""
        self._load_logs(force=True)

    def on_page_enter(self):
        """进入页面"""
        self._is_page_visible = True
        self._last_log_hash = None
        self._start_auto_refresh()
        # 延迟加载日志，让页面先渲染完
        def delayed_load():
            import time
            time.sleep(0.1)
            self._load_logs(force=True)
        threading.Thread(target=delayed_load, daemon=True).start()

    def on_page_leave(self):
        """离开页面"""
        self._is_page_visible = False
        self._last_log_hash = None
        # 清除选中状态
        self._selected_rows.clear()
