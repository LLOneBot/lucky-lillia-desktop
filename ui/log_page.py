"""日志页面"""

import flet as ft
import threading
from typing import Optional, List, Tuple
from core.log_collector import LogCollector, LogEntry
from utils.constants import MAX_LOG_LINES


class LogPage:
    """日志页面组件 - 使用固定控件池避免内存泄漏"""

    MAX_DISPLAY = 100
    AUTO_REFRESH_INTERVAL = 0.5

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
            visible=False,
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
            alignment=ft.Alignment(0, 0),
            padding=20,
            visible=True,
        )

        # 日志列表
        self.log_list = ft.Column(
            controls=[self._empty_container] + [container for container, _, _ in self._log_rows],
            spacing=2,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.log_container = ft.Container(
            content=self.log_list,
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
                                ft.Icons.ARTICLE, size=36, color=ft.Colors.PRIMARY
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
        # LLBot 日志已包含时间戳，只显示前缀和原始消息
        if entry.process_name == "LLBot":
            return f"{prefix} {entry.message}"
        
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        return f"{prefix} {timestamp} [{entry.process_name}] {entry.message}"

    def _on_auto_refresh_change(self, e):
        """自动刷新开关变化"""
        self._auto_refresh_enabled = e.control.value

    def _on_row_click(self, idx: int):
        if idx >= len(self._log_rows):
            return
        
        container, _, _ = self._log_rows[idx]
        
        if idx in self._selected_rows:
            self._selected_rows.remove(idx)
            container.bgcolor = None
        else:
            self._selected_rows.add(idx)
            container.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.PRIMARY)
        
        has_selection = len(self._selected_rows) > 0
        self.copy_btn.visible = has_selection
        self.clear_selection_btn.visible = has_selection
        
        try:
            page = self.control.page if self.control else None
            if page:
                def safe_update():
                    try:
                        container.update()
                        self.copy_btn.update()
                        self.clear_selection_btn.update()
                    except Exception:
                        pass
                page.run_thread(safe_update)
        except Exception:
            pass

    def _update_row_selection(self):
        containers_to_update = []
        for i in list(self._selected_rows):
            if i < len(self._log_rows):
                container, _, _ = self._log_rows[i]
                container.bgcolor = None
                containers_to_update.append(container)
        self._selected_rows.clear()
        
        try:
            page = self.control.page if self.control else None
            if page and containers_to_update:
                def safe_update():
                    try:
                        for c in containers_to_update:
                            c.update()
                    except Exception:
                        pass
                page.run_thread(safe_update)
        except Exception:
            pass

    def _on_clear_selection(self, e):
        self._update_row_selection()
        self.copy_btn.visible = False
        self.clear_selection_btn.visible = False
        try:
            page = self.control.page if self.control else None
            if page:
                def safe_update():
                    try:
                        self.copy_btn.update()
                        self.clear_selection_btn.update()
                    except Exception:
                        pass
                page.run_thread(safe_update)
        except Exception:
            pass

    def _on_copy_logs(self, e):
        if not self._selected_rows:
            return
        
        lines = []
        sorted_indices = sorted(self._selected_rows)
        for idx in sorted_indices:
            if idx < len(self._log_rows):
                _, _, text = self._log_rows[idx]
                if text.value:
                    lines.append(text.value)
        
        if lines and self.control and self.control.page:
            async def do_copy():
                await self.control.page.clipboard.set("\n".join(lines))
            self.control.page.run_task(do_copy)
            self._on_clear_selection(None)

    def _on_clear_logs(self, e):
        self.log_collector.clear_logs()
        self._last_log_hash = None
        self._empty_container.visible = True
        for container, row, text in self._log_rows:
            container.visible = False
            text.value = ""
        try:
            page = self.control.page if self.control else None
            if page:
                def safe_update():
                    try:
                        self.log_list.update()
                    except Exception:
                        pass
                page.run_thread(safe_update)
        except Exception:
            pass

    def _load_logs(self, force: bool = False):
        """加载日志"""
        need_update = False
        need_scroll = False
        
        with self._update_lock:
            if not self._is_page_visible:
                return

            log_count = self.log_collector.get_log_count()

            if log_count == 0:
                if self._last_log_hash is not None or force:
                    self._last_log_hash = None
                    self._empty_container.visible = True
                    for container, row, text in self._log_rows:
                        container.visible = False
                    need_update = True
                # 不return，让后面的update在锁外执行
            else:
                # 获取最新日志
                logs = self.log_collector.get_recent_logs(self.MAX_DISPLAY)
                if logs:
                    last_log = logs[-1]
                    current_hash = (log_count, id(last_log), last_log.timestamp)
                    if force or current_hash != self._last_log_hash:
                        self._last_log_hash = current_hash
                        self._empty_container.visible = False

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
                        
                        need_update = True
                        need_scroll = self._auto_refresh_enabled
        
        if need_update:
            try:
                page = self.control.page if self.control else None
                if page and self._is_page_visible:
                    async def safe_update():
                        try:
                            if self.control and self.control.page and self._is_page_visible:
                                self.log_list.update()
                                if need_scroll:
                                    await self.log_list.scroll_to(offset=-1, duration=0)
                        except Exception:
                            pass
                    page.run_task(safe_update)
            except Exception:
                pass

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
