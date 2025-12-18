"""LLOneBot配置页面"""

import flet as ft
import json
import os
import copy
from typing import Optional, Callable, Dict, Any, List


class LLOneBotConfigPage:
    DEFAULT_CONFIG = {
        "webui": {"enable": True, "port": 3080},
        "satori": {"enable": False, "port": 5600, "token": ""},
        "ob11": {"enable": True, "connect": []},
        "milky": {
            "enable": False,
            "reportSelfMessage": False,
            "http": {"port": 3010, "prefix": "", "accessToken": ""},
            "webhook": {"urls": []}
        },
        "enableLocalFile2Url": False,
        "log": True,
        "autoDeleteFile": False,
        "autoDeleteFileSecond": 60,
        "musicSignUrl": "https://llob.linyuchen.net/sign/music",
        "msgCacheExpire": 120,
        "onlyLocalhost": True,
        "ffmpeg": ""
    }
    
    TYPE_NAMES = {
        "ws": "WebSocket",
        "ws-reverse": "反向WS", 
        "http": "HTTP",
        "http-post": "HTTP POST"
    }
    
    DEFAULT_CONNECT = {
        "ws": {"type": "ws", "enable": False, "port": 3001, "heartInterval": 60000,
               "token": "", "reportSelfMessage": False, "reportOfflineMessage": False,
               "messageFormat": "array", "debug": False},
        "ws-reverse": {"type": "ws-reverse", "enable": False, "url": "", "heartInterval": 60000,
                       "token": "", "reportSelfMessage": False, "reportOfflineMessage": False,
                       "messageFormat": "array", "debug": False},
        "http": {"type": "http", "enable": False, "port": 3000, "token": "",
                 "reportSelfMessage": False, "reportOfflineMessage": False,
                 "messageFormat": "array", "debug": False},
        "http-post": {"type": "http-post", "enable": False, "url": "", "enableHeart": False,
                      "heartInterval": 60000, "token": "", "reportSelfMessage": False,
                      "reportOfflineMessage": False, "messageFormat": "array", "debug": False}
    }
    
    def __init__(self, get_uin_func: Callable[[], Optional[str]],
                 on_config_saved: Optional[Callable] = None):
        self.get_uin_func = get_uin_func
        self.on_config_saved = on_config_saved
        self.control = None
        self.current_config: Dict[str, Any] = {}
        self.connect_controls: List[Dict] = []
        
    def _get_config_path(self) -> Optional[str]:
        uin = self.get_uin_func()
        if not uin:
            return None
        return os.path.join("bin", "llonebot", "data", f"config_{uin}.json")
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = self._get_config_path()
        if not config_path or not os.path.exists(config_path):
            return copy.deepcopy(self.DEFAULT_CONFIG)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return copy.deepcopy(self.DEFAULT_CONFIG)
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        config_path = self._get_config_path()
        if not config_path:
            return False
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def build(self):
        self.current_config = self._load_config()
        
        self.error_text = ft.Text("", color=ft.Colors.RED_400, size=14, visible=False)
        self.success_text = ft.Text("", color=ft.Colors.GREEN_400, size=14, visible=False)
        
        # WebUI
        self.webui_enable = ft.Checkbox(label="启用", 
            value=self.current_config.get("webui", {}).get("enable", True))
        self.webui_port = ft.TextField(label="端口", width=120,
            value=str(self.current_config.get("webui", {}).get("port", 3080)),
            keyboard_type=ft.KeyboardType.NUMBER)
        self.webui_open_btn = ft.IconButton(
            icon=ft.Icons.OPEN_IN_BROWSER,
            tooltip="在浏览器中打开WebUI",
            on_click=self._on_open_webui
        )
        
        # Satori
        self.satori_enable = ft.Checkbox(label="启用",
            value=self.current_config.get("satori", {}).get("enable", False))
        self.satori_port = ft.TextField(label="端口", width=120,
            value=str(self.current_config.get("satori", {}).get("port", 5600)),
            keyboard_type=ft.KeyboardType.NUMBER)
        self.satori_token = ft.TextField(label="Token", width=250,
            value=self.current_config.get("satori", {}).get("token", ""))
        
        # OB11
        self.ob11_enable = ft.Checkbox(label="启用 OneBot 11",
            value=self.current_config.get("ob11", {}).get("enable", True))
        
        # Milky
        milky_cfg = self.current_config.get("milky", {})
        self.milky_enable = ft.Checkbox(label="启用",
            value=milky_cfg.get("enable", False))
        self.milky_report_self = ft.Checkbox(label="上报自身消息",
            value=milky_cfg.get("reportSelfMessage", False))
        self.milky_http_port = ft.TextField(label="HTTP端口", width=120,
            value=str(milky_cfg.get("http", {}).get("port", 3010)),
            keyboard_type=ft.KeyboardType.NUMBER)
        self.milky_http_prefix = ft.TextField(label="前缀", width=150,
            value=milky_cfg.get("http", {}).get("prefix", ""))
        self.milky_http_token = ft.TextField(label="AccessToken", width=200,
            value=milky_cfg.get("http", {}).get("accessToken", ""))
        # Webhook URLs 动态列表
        self.milky_webhook_url_controls: List[ft.TextField] = []
        self.milky_webhook_container = ft.Column(spacing=8)
        self._rebuild_webhook_urls(milky_cfg.get("webhook", {}).get("urls", []))
        
        # 连接标签页
        self.connects_tabs = ft.Tabs(selected_index=0, tabs=[], height=320,
                                      on_change=self._on_tab_change)
        self._rebuild_tabs()
        
        # 其他配置
        self.enable_local_file2url = ft.Checkbox(label="本地文件转URL",
            value=self.current_config.get("enableLocalFile2Url", False))
        self.log_enable = ft.Checkbox(label="启用日志",
            value=self.current_config.get("log", True))
        self.auto_delete_file = ft.Checkbox(label="自动删除文件",
            value=self.current_config.get("autoDeleteFile", False))
        self.auto_delete_file_second = ft.TextField(label="删除时间(秒)", width=120,
            value=str(self.current_config.get("autoDeleteFileSecond", 60)),
            keyboard_type=ft.KeyboardType.NUMBER)
        self.music_sign_url = ft.TextField(label="音乐签名URL", width=400,
            value=self.current_config.get("musicSignUrl", ""))
        self.msg_cache_expire = ft.TextField(label="消息缓存(秒)", width=120,
            value=str(self.current_config.get("msgCacheExpire", 120)),
            keyboard_type=ft.KeyboardType.NUMBER)
        self.only_localhost = ft.Checkbox(label="仅本地访问",
            value=self.current_config.get("onlyLocalhost", True))
        self.ffmpeg_path = ft.TextField(label="FFmpeg路径", width=400,
            value=self.current_config.get("ffmpeg", ""))

        # 悬浮按钮
        self.floating_buttons = ft.Container(
            content=ft.Row([
                ft.FloatingActionButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="刷新",
                    on_click=lambda e: self.refresh(),
                    mini=True,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                ),
                ft.FloatingActionButton(
                    icon=ft.Icons.SAVE,
                    tooltip="保存配置",
                    on_click=self._on_save,
                ),
            ], spacing=12),
            right=20,
            bottom=20,
            visible=bool(self.get_uin_func()),
        )
        
        # 未登录提示界面
        self.no_uin_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=64, color=ft.Colors.ORANGE_400),
                ft.Text("请先启动并登录QQ", size=24, weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ORANGE_400),
                ft.Text("获取到QQ账号后才能编辑Bot配置", size=16, color=ft.Colors.GREY_600),
            ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=100),
            visible=not bool(self.get_uin_func()),
        )
        
        # 配置内容区域
        self.config_content = ft.Column([
            self._section("WebUI", ft.Icons.WEB, [
                ft.Row([self.webui_enable, self.webui_port, self.webui_open_btn], spacing=16)
            ]),
            self._section("OneBot 11", ft.Icons.SETTINGS_ETHERNET, [
                ft.Row([self.ob11_enable], spacing=16),
                self.connects_tabs
            ]),
            self._section("Satori", ft.Icons.CLOUD, [
                ft.Row([self.satori_enable, self.satori_port, self.satori_token], spacing=16)
            ]),
            self._section("Milky", ft.Icons.WATER_DROP, [
                ft.Row([self.milky_enable, self.milky_report_self], spacing=16),
                ft.Row([self.milky_http_port, self.milky_http_prefix, self.milky_http_token], spacing=16),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Webhook URLs", size=14, weight=ft.FontWeight.W_500),
                            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, tooltip="添加URL",
                                          on_click=self._on_add_webhook_url, icon_size=20),
                        ], spacing=8),
                        self.milky_webhook_container,
                    ], spacing=4),
                ),
            ]),
            self._section("其他配置", ft.Icons.MORE_HORIZ, [
                ft.Row([self.enable_local_file2url, self.log_enable,
                        self.auto_delete_file, self.only_localhost], spacing=16),
                ft.Row([self.auto_delete_file_second, self.msg_cache_expire], spacing=16),
                ft.Row([self.music_sign_url], spacing=16),
                ft.Row([self.ffmpeg_path], spacing=16)
            ]),
            self.error_text, self.success_text,
        ], spacing=16, visible=bool(self.get_uin_func()))
        
        # 主界面内容（所有内容放在一个Column里）
        main_content = ft.Column([
            ft.Row([ft.Icon(ft.Icons.TUNE, size=36, color=ft.Colors.PRIMARY),
                    ft.Text("LLBot 配置", size=32, weight=ft.FontWeight.BOLD)], spacing=12),
            ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
            self.no_uin_container,
            self.config_content,
        ], spacing=16)
        
        # 可滚动容器（和启动配置页一样的结构）
        scrollable_content = ft.Container(
            content=ft.ListView(
                controls=[main_content],
                spacing=0,
                padding=28,
                expand=True,
            ),
            expand=True,
        )
        
        # 使用Stack叠加内容和悬浮按钮
        self.control = ft.Stack([
            scrollable_content,
            self.floating_buttons,
        ], expand=True)
        
        return self.control
    
    def _section(self, title: str, icon, controls: List) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(icon, size=20, color=ft.Colors.PRIMARY),
                            ft.Text(title, size=18, weight=ft.FontWeight.W_600)], spacing=10),
                    *controls
                ], spacing=12),
                padding=16,
            ), elevation=2,
        )

    def _rebuild_tabs(self):
        self.connect_controls.clear()
        self.connects_tabs.tabs.clear()
        
        connects = self.current_config.get("ob11", {}).get("connect", [])
        
        # 添加每个连接的标签
        for i, conn in enumerate(connects):
            conn_type = conn.get("type", "ws")
            tab_name = self.TYPE_NAMES.get(conn_type, conn_type)
            controls = self._build_connect_controls(conn, i)
            self.connect_controls.append(controls)
            
            # 构建行，过滤掉None值
            row1 = [c for c in [controls["enable"], controls.get("port"), controls.get("url")] if c]
            row2 = [c for c in [controls.get("heart"), controls.get("enable_heart"), controls["token"]] if c]
            row3 = [controls["msg_format"], controls["report_self"], controls["report_offline"], controls["debug"]]
            
            # 删除按钮
            delete_btn = ft.TextButton(
                "删除此连接", icon=ft.Icons.DELETE,
                style=ft.ButtonStyle(color=ft.Colors.RED_400),
                on_click=lambda e, idx=i: self._on_delete_connect(idx)
            )
            
            self.connects_tabs.tabs.append(ft.Tab(
                text=tab_name,
                content=ft.Container(
                    content=ft.Column([
                        ft.Row(row1, spacing=16),
                        ft.Row(row2, spacing=16),
                        ft.Row(row3, spacing=16),
                        ft.Row([delete_btn], alignment=ft.MainAxisAlignment.END),
                    ], spacing=12),
                    padding=16
                )
            ))
        
        # 最后添加 "+" 标签用于添加新连接
        self.connects_tabs.tabs.append(ft.Tab(
            text="+",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("选择要添加的连接类型:", size=16),
                    ft.Row([
                        ft.ElevatedButton("WebSocket", on_click=lambda e: self._add_connect("ws")),
                        ft.ElevatedButton("反向WS", on_click=lambda e: self._add_connect("ws-reverse")),
                        ft.ElevatedButton("HTTP", on_click=lambda e: self._add_connect("http")),
                        ft.ElevatedButton("HTTP POST", on_click=lambda e: self._add_connect("http-post")),
                    ], spacing=12, wrap=True),
                ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, alignment=ft.alignment.center
            )
        ))
    
    def _build_connect_controls(self, conn: Dict, index: int) -> Dict:
        conn_type = conn.get("type", "ws")
        has_port = conn_type in ["ws", "http"]
        has_url = conn_type in ["ws-reverse", "http-post"]
        has_heart = conn_type != "http"
        has_enable_heart = conn_type == "http-post"
        
        controls = {
            "type": conn_type,
            "enable": ft.Checkbox(label="启用", value=conn.get("enable", False)),
            "token": ft.TextField(label="Token", width=180, value=conn.get("token", "")),
            "msg_format": ft.Dropdown(label="消息格式", width=120, value=conn.get("messageFormat", "array"),
                options=[ft.dropdown.Option("array"), ft.dropdown.Option("string")]),
            "report_self": ft.Checkbox(label="上报自身", value=conn.get("reportSelfMessage", False)),
            "report_offline": ft.Checkbox(label="上报离线", value=conn.get("reportOfflineMessage", False)),
            "debug": ft.Checkbox(label="调试", value=conn.get("debug", False)),
        }
        
        if has_port:
            default_port = 3001 if conn_type == "ws" else 3000
            controls["port"] = ft.TextField(label="端口", width=100, 
                value=str(conn.get("port", default_port)), keyboard_type=ft.KeyboardType.NUMBER)
        if has_url:
            controls["url"] = ft.TextField(label="URL", width=350, value=conn.get("url", ""))
        if has_heart:
            controls["heart"] = ft.TextField(label="心跳(ms)", width=120,
                value=str(conn.get("heartInterval", 60000)), keyboard_type=ft.KeyboardType.NUMBER)
        if has_enable_heart:
            controls["enable_heart"] = ft.Checkbox(label="启用心跳", value=conn.get("enableHeart", False))
        
        return controls

    def _on_tab_change(self, e):
        pass
    
    def _on_open_webui(self, e):
        import webbrowser
        port = self.webui_port.value or "3080"
        webbrowser.open(f"http://localhost:{port}")
    
    def _rebuild_webhook_urls(self, urls: List[str]):
        self.milky_webhook_url_controls.clear()
        self.milky_webhook_container.controls.clear()
        for i, url in enumerate(urls):
            self._add_webhook_url_row(url, i)
    
    def _add_webhook_url_row(self, url: str = "", index: int = -1):
        text_field = ft.TextField(value=url, width=350, hint_text="http://example.com/webhook")
        self.milky_webhook_url_controls.append(text_field)
        idx = len(self.milky_webhook_url_controls) - 1
        row = ft.Row([
            text_field,
            ft.IconButton(icon=ft.Icons.DELETE, tooltip="删除",
                          on_click=lambda e, i=idx: self._on_delete_webhook_url(i),
                          icon_size=18, icon_color=ft.Colors.RED_400),
        ], spacing=8)
        self.milky_webhook_container.controls.append(row)
    
    def _on_add_webhook_url(self, e):
        self._add_webhook_url_row("")
        self._try_update()
    
    def _on_delete_webhook_url(self, index: int):
        if 0 <= index < len(self.milky_webhook_url_controls):
            self.milky_webhook_url_controls.pop(index)
            self.milky_webhook_container.controls.pop(index)
            for i, row in enumerate(self.milky_webhook_container.controls):
                if isinstance(row, ft.Row) and len(row.controls) > 1:
                    btn = row.controls[1]
                    if isinstance(btn, ft.IconButton):
                        btn.on_click = lambda e, idx=i: self._on_delete_webhook_url(idx)
            self._try_update()
    
    def _collect_webhook_urls(self) -> List[str]:
        return [tf.value.strip() for tf in self.milky_webhook_url_controls if tf.value and tf.value.strip()]
    
    def _add_connect(self, conn_type: str):
        new_conn = copy.deepcopy(self.DEFAULT_CONNECT.get(conn_type, self.DEFAULT_CONNECT["ws"]))
        
        if "connect" not in self.current_config.get("ob11", {}):
            self.current_config["ob11"]["connect"] = []
        self.current_config["ob11"]["connect"].append(new_conn)
        
        self._rebuild_tabs()
        # 切换到新添加的标签（倒数第二个，因为最后一个是"+"）
        self.connects_tabs.selected_index = len(self.connects_tabs.tabs) - 2
        self._try_update()
    
    def _on_delete_connect(self, index: int):
        connects = self.current_config.get("ob11", {}).get("connect", [])
        if 0 <= index < len(connects):
            connects.pop(index)
            self._rebuild_tabs()
            # 调整选中索引
            if connects:
                self.connects_tabs.selected_index = min(index, len(connects) - 1)
            else:
                self.connects_tabs.selected_index = 0
            self._try_update()
    
    def _collect_connects(self) -> List[Dict]:
        result = []
        for ctrl in self.connect_controls:
            conn_type = ctrl["type"]
            conn = {
                "type": conn_type,
                "enable": ctrl["enable"].value,
                "token": ctrl["token"].value or "",
                "reportSelfMessage": ctrl["report_self"].value,
                "reportOfflineMessage": ctrl["report_offline"].value,
                "messageFormat": ctrl["msg_format"].value or "array",
                "debug": ctrl["debug"].value,
            }
            if "port" in ctrl:
                conn["port"] = int(ctrl["port"].value or 3001)
            if "url" in ctrl:
                conn["url"] = ctrl["url"].value or ""
            if "heart" in ctrl:
                conn["heartInterval"] = int(ctrl["heart"].value or 60000)
            if "enable_heart" in ctrl:
                conn["enableHeart"] = ctrl["enable_heart"].value
            result.append(conn)
        return result

    def _on_save(self, e):
        self.error_text.visible = False
        self.success_text.visible = False
        
        if not self.get_uin_func():
            self._show_error("请先启动PMHQ并登录QQ")
            return
        
        try:
            config = {
                "webui": {"enable": self.webui_enable.value, 
                          "port": int(self.webui_port.value or 3080)},
                "satori": {"enable": self.satori_enable.value,
                           "port": int(self.satori_port.value or 5600),
                           "token": self.satori_token.value or ""},
                "ob11": {"enable": self.ob11_enable.value, "connect": self._collect_connects()},
                "milky": {
                    "enable": self.milky_enable.value,
                    "reportSelfMessage": self.milky_report_self.value,
                    "http": {
                        "port": int(self.milky_http_port.value or 3010),
                        "prefix": self.milky_http_prefix.value or "",
                        "accessToken": self.milky_http_token.value or ""
                    },
                    "webhook": {
                        "urls": self._collect_webhook_urls()
                    }
                },
                "enableLocalFile2Url": self.enable_local_file2url.value,
                "log": self.log_enable.value,
                "autoDeleteFile": self.auto_delete_file.value,
                "autoDeleteFileSecond": int(self.auto_delete_file_second.value or 60),
                "musicSignUrl": self.music_sign_url.value or "",
                "msgCacheExpire": int(self.msg_cache_expire.value or 120),
                "onlyLocalhost": self.only_localhost.value,
                "ffmpeg": self.ffmpeg_path.value or ""
            }
            if self._save_config(config):
                self.current_config = config
                self._show_success("配置保存成功")
                if self.on_config_saved:
                    self.on_config_saved(config)
            else:
                self._show_error("配置保存失败")
        except ValueError as ex:
            self._show_error(f"配置值无效: {ex}")
    
    def _update_ui(self):
        cfg = self.current_config
        self.webui_enable.value = cfg.get("webui", {}).get("enable", True)
        self.webui_port.value = str(cfg.get("webui", {}).get("port", 3080))
        self.satori_enable.value = cfg.get("satori", {}).get("enable", False)
        self.satori_port.value = str(cfg.get("satori", {}).get("port", 5600))
        self.satori_token.value = cfg.get("satori", {}).get("token", "")
        self.ob11_enable.value = cfg.get("ob11", {}).get("enable", True)
        milky_cfg = cfg.get("milky", {})
        self.milky_enable.value = milky_cfg.get("enable", False)
        self.milky_report_self.value = milky_cfg.get("reportSelfMessage", False)
        self.milky_http_port.value = str(milky_cfg.get("http", {}).get("port", 3010))
        self.milky_http_prefix.value = milky_cfg.get("http", {}).get("prefix", "")
        self.milky_http_token.value = milky_cfg.get("http", {}).get("accessToken", "")
        self._rebuild_webhook_urls(milky_cfg.get("webhook", {}).get("urls", []))
        self.enable_local_file2url.value = cfg.get("enableLocalFile2Url", False)
        self.log_enable.value = cfg.get("log", True)
        self.auto_delete_file.value = cfg.get("autoDeleteFile", False)
        self.auto_delete_file_second.value = str(cfg.get("autoDeleteFileSecond", 60))
        self.music_sign_url.value = cfg.get("musicSignUrl", "")
        self.msg_cache_expire.value = str(cfg.get("msgCacheExpire", 120))
        self.only_localhost.value = cfg.get("onlyLocalhost", True)
        self.ffmpeg_path.value = cfg.get("ffmpeg", "")

    def _show_error(self, msg: str):
        self.error_text.value = msg
        self.error_text.visible = True
        self.success_text.visible = False
        self._try_update()
    
    def _show_success(self, msg: str):
        self.success_text.value = msg
        self.success_text.visible = True
        self.error_text.visible = False
        self._try_update()
    
    def _try_update(self):
        try:
            if self.control and self.control.page:
                self.control.page.update()
        except Exception:
            pass
    
    def refresh(self):
        has_uin = bool(self.get_uin_func())
        self.current_config = self._load_config()
        self._update_ui()
        self._rebuild_tabs()
        # 根据是否有UIN切换显示
        self.no_uin_container.visible = not has_uin
        self.config_content.visible = has_uin
        self.floating_buttons.visible = has_uin
        self.error_text.visible = False
        self.success_text.visible = False
        self._try_update()
