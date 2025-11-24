"""日志页面UI模块 - 显示进程日志输出"""

import flet as ft
from typing import Optional, List
from core.log_collector import LogCollector, LogEntry


class LogPage:
    """日志页面组件"""
    
    def __init__(self, log_collector: LogCollector):
        """初始化日志页面
        
        Args:
            log_collector: 日志收集器实例
        """
        self.log_collector = log_collector
        self.current_filter = "all"  # "all", "pmhq", "llonebot"
        self.control = None
        self.auto_scroll = True
        
        # 注册日志回调
        self.log_collector.set_callback(self._on_new_log)
        
    def build(self):
        """构建UI组件"""
        # 进程过滤器
        self.filter_all_btn = ft.ElevatedButton(
            "所有",
            icon=ft.Icons.SELECT_ALL,
            on_click=lambda e: self._set_filter("all"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        self.filter_pmhq_btn = ft.OutlinedButton(
            "仅PMHQ",
            icon=ft.Icons.FILTER_1,
            on_click=lambda e: self._set_filter("pmhq"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        self.filter_llonebot_btn = ft.OutlinedButton(
            "仅LLOneBot",
            icon=ft.Icons.FILTER_2,
            on_click=lambda e: self._set_filter("llonebot"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        # 清空日志按钮
        self.clear_btn = ft.ElevatedButton(
            "清空日志",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._on_clear_logs,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ERROR,
                color=ft.Colors.ON_ERROR,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        )
        
        # 自动滚动开关
        self.auto_scroll_switch = ft.Switch(
            label="自动滚动",
            value=True,
            on_change=self._on_auto_scroll_change
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
            content=ft.Column([
                # 标题栏
                ft.Row([
                    ft.Icon(
                        name=ft.Icons.ARTICLE,
                        size=36,
                        color=ft.Colors.PRIMARY
                    ),
                    ft.Text(
                        "日志查看器",
                        size=32,
                        weight=ft.FontWeight.BOLD
                    ),
                ], spacing=12),
                ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
                
                # 控制栏
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FILTER_ALT, size=20, color=ft.Colors.PRIMARY),
                            ft.Text("过滤:", size=16, weight=ft.FontWeight.W_600),
                            self.filter_all_btn,
                            self.filter_pmhq_btn,
                            self.filter_llonebot_btn,
                            ft.Container(expand=True),  # 弹性空间
                            self.auto_scroll_switch,
                            self.clear_btn,
                        ], spacing=12, alignment=ft.MainAxisAlignment.START),
                        padding=16,
                    ),
                    elevation=2,
                ),
                
                # 日志显示区域
                self.log_container,
                
            ], spacing=20, expand=True),
            padding=28,
            expand=True,
        )
        
        # 初始加载日志
        self._refresh_logs()
        
        return self.control
    
    def _set_filter(self, filter_type: str):
        """设置日志过滤器
        
        Args:
            filter_type: 过滤类型 ("all", "pmhq", "llonebot")
        """
        self.current_filter = filter_type
        
        # 更新按钮样式
        if filter_type == "all":
            self.filter_all_btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            )
            self.filter_pmhq_btn.style = None
            self.filter_llonebot_btn.style = None
        elif filter_type == "pmhq":
            self.filter_all_btn.style = None
            self.filter_pmhq_btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            )
            self.filter_llonebot_btn.style = None
        elif filter_type == "llonebot":
            self.filter_all_btn.style = None
            self.filter_pmhq_btn.style = None
            self.filter_llonebot_btn.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            )
        
        # 刷新日志显示
        self._refresh_logs()
        
        # 更新UI
        if self.control and self.control.page:
            self.control.page.update()
    
    def _on_clear_logs(self, e):
        """清空日志按钮点击处理"""
        # 根据当前过滤器清空日志
        if self.current_filter == "all":
            self.log_collector.clear_logs()
        else:
            self.log_collector.clear_logs(self.current_filter)
        
        # 刷新显示
        self._refresh_logs()
        
        # 更新UI
        if self.control and self.control.page:
            self.control.page.update()
    
    def _on_auto_scroll_change(self, e):
        """自动滚动开关变化处理"""
        self.auto_scroll = e.control.value
    
    def _on_new_log(self, entry: LogEntry):
        """新日志回调处理
        
        Args:
            entry: 新的日志条目
        """
        # 检查是否应该显示这条日志
        if self.current_filter != "all" and entry.process_name != self.current_filter:
            return
        
        # 添加日志到显示
        log_widget = self._create_log_widget(entry)
        self.log_column.controls.append(log_widget)
        
        # 如果启用自动滚动，滚动到底部
        if self.auto_scroll and self.control and self.control.page:
            # 限制显示的日志数量以保持性能
            if len(self.log_column.controls) > 1000:
                self.log_column.controls = self.log_column.controls[-1000:]
            
            self.control.page.update()
            
            # 滚动到底部
            try:
                self.log_column.scroll_to(
                    offset=-1,
                    duration=100
                )
            except Exception:
                pass  # 忽略滚动错误
    
    def _refresh_logs(self):
        """刷新日志显示"""
        # 获取日志
        if self.current_filter == "all":
            logs = self.log_collector.get_logs()
        else:
            logs = self.log_collector.get_logs(self.current_filter)
        
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
                        italic=True
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
        log_content = ft.Row([
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
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(
            content=log_content,
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT if entry.level == "stdout" else ft.Colors.ERROR),
        )
    
    def refresh(self):
        """刷新页面（外部调用）"""
        self._refresh_logs()
        if self.control and self.control.page:
            self.control.page.update()
