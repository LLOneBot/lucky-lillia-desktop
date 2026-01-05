"""LLBot配置页面"""

import flet as ft
import json
import os
import copy
from typing import Optional, Callable, Dict, Any, List


class LLBotConfigPage:
    DEFAULT_CONFIG = {
        "webui": {"enable": True, "port": 3080},
        "satori": {"enable": False, "port": 5600, "token": ""},
        "ob11": {"enable": True, "connect": []},
        "milky": {
            "enable": False,
            "reportSelfMessage": False,
            "http": {"port": 3010, "prefix": "", "accessToken": ""},
            "webhook": {"urls": [], "accessToken": ""}
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
        self._page = None
        self._initialized = False
        self._last_uin = None
        self._is_visible = False  # 标记页面是否可见
        
    def _get_config_path(self) -> Optional[str]:
        import logging
        logger = logging.getLogger(__name__)
        
        uin = self.get_uin_func()
        logger.info(f"获取配置路径: uin={uin}")
        
        if not uin:
            logger.warning("uin 为空，无法确定配置文件路径")
            return None
        
        config_path = os.path.join("bin", "llbot", "data", f"config_{uin}.json")
        logger.info(f"配置文件路径: {config_path}")
        return config_path
    
    def _load_config(self) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        config_path = self._get_config_path()
        logger.info(f"Bot配置加载: config_path={config_path}")
        
        if not config_path or not os.path.exists(config_path):
            logger.info(f"配置文件不存在，使用默认配置")
            return copy.deepcopy(self.DEFAULT_CONFIG)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"成功加载配置: {json.dumps(config, ensure_ascii=False, indent=2)}")
                return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
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
        # Webhook
        self.milky_webhook_token = ft.TextField(label="Webhook AccessToken", width=200,
            value=milky_cfg.get("webhook", {}).get("accessToken", ""))
        self.milky_webhook_url_controls: List[ft.TextField] = []
        self.milky_webhook_container = ft.Column(spacing=8)
        self._rebuild_webhook_urls(milky_cfg.get("webhook", {}).get("urls", []))
        
        # 连接标签页 - 使用自定义实现替代 ft.Tabs
        self._connect_tab_index = 0
        self._connect_tab_buttons = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO)
        self._connect_tab_content = ft.Container(height=280)
        self._connect_tab_contents: List[ft.Control] = []
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
            alignment=ft.Alignment(0, 0),
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
                ft.Column([
                    self._connect_tab_buttons,
                    ft.Divider(height=1),
                    self._connect_tab_content,
                ], spacing=0),
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
                            ft.Text("Webhook", size=14, weight=ft.FontWeight.W_500),
                            self.milky_webhook_token,
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Text("Webhook URLs", size=14, weight=ft.FontWeight.W_500),
                            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, tooltip="添加URL",
                                          on_click=self._on_add_webhook_url, icon_size=20),
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        self.milky_webhook_container,
                    ], spacing=8),
                ),
            ]),
            self._section("其他配置", ft.Icons.MORE_HORIZ, [
                ft.Row([self.enable_local_file2url, self.log_enable,
                        self.auto_delete_file, self.only_localhost], spacing=16),
                ft.Row([self.auto_delete_file_second, self.msg_cache_expire], spacing=16),
                ft.Row([self.music_sign_url], spacing=16),
                ft.Row([self.ffmpeg_path], spacing=16)
            ]),
            # 底部留白
            ft.Container(height=60),
        ], spacing=16, visible=bool(self.get_uin_func()))
        
        # 主界面内容
        main_content = ft.Column([
            ft.Row([ft.Icon(ft.Icons.TUNE, size=36, color=ft.Colors.PRIMARY),
                    ft.Text("LLBot 配置", size=32, weight=ft.FontWeight.BOLD)], spacing=12),
            ft.Divider(height=2, thickness=2, color=ft.Colors.PRIMARY),
            self.no_uin_container,
            self.config_content,
        ], spacing=16)
        
        scrollable_content = ft.Container(
            content=ft.ListView(
                controls=[main_content],
                spacing=0,
                padding=28,
                expand=True,
            ),
            expand=True,
        )
        
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
        self._connect_tab_contents.clear()
        self._connect_tab_buttons.controls.clear()
        
        connects = self.current_config.get("ob11", {}).get("connect", [])
        
        for i, conn in enumerate(connects):
            conn_type = conn.get("type", "ws")
            tab_name = self.TYPE_NAMES.get(conn_type, conn_type)
            controls = self._build_connect_controls(conn, i)
            self.connect_controls.append(controls)
            
            row1 = [c for c in [controls["enable"], controls.get("port"), controls.get("url")] if c]
            row2 = [c for c in [controls.get("heart"), controls.get("enable_heart"), controls["token"]] if c]
            row3 = [controls["msg_format"], controls["report_self"], controls["report_offline"], controls["debug"]]
            
            delete_btn = ft.TextButton(
                "删除此连接", icon=ft.Icons.DELETE,
                style=ft.ButtonStyle(color=ft.Colors.RED_400),
                on_click=lambda e, idx=i: self._on_delete_connect(idx)
            )
            
            content = ft.Container(
                content=ft.Column([
                    ft.Row(row1, spacing=16),
                    ft.Row(row2, spacing=16),
                    ft.Row(row3, spacing=16),
                    ft.Row([delete_btn], alignment=ft.MainAxisAlignment.END),
                ], spacing=12),
                padding=16
            )
            self._connect_tab_contents.append(content)
            
            tab_btn = ft.Container(
                content=ft.Text(tab_name, color=ft.Colors.PRIMARY if i == self._connect_tab_index else ft.Colors.ON_SURFACE),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.PRIMARY)) if i == self._connect_tab_index else None,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY) if i == self._connect_tab_index else None,
                border_radius=ft.border_radius.only(top_left=8, top_right=8),
                on_click=lambda e, idx=i: self._switch_tab(idx),
                ink=True,
            )
            self._connect_tab_buttons.controls.append(tab_btn)
        
        # 添加 "+" 按钮
        add_content = ft.Container(
            content=ft.Column([
                ft.Text("选择要添加的连接类型:", size=16),
                ft.Row([
                    ft.ElevatedButton("WebSocket", on_click=lambda e: self._add_connect("ws")),
                    ft.ElevatedButton("反向WS", on_click=lambda e: self._add_connect("ws-reverse")),
                    ft.ElevatedButton("HTTP", on_click=lambda e: self._add_connect("http")),
                    ft.ElevatedButton("HTTP POST", on_click=lambda e: self._add_connect("http-post")),
                ], spacing=12, wrap=True),
            ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
        )
        self._connect_tab_contents.append(add_content)
        
        add_btn = ft.Container(
            content=ft.Text("+", color=ft.Colors.PRIMARY if self._connect_tab_index == len(connects) else ft.Colors.ON_SURFACE),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.PRIMARY)) if self._connect_tab_index == len(connects) else None,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY) if self._connect_tab_index == len(connects) else None,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            on_click=lambda e: self._switch_tab(len(self._connect_tab_contents) - 1),
            ink=True,
        )
        self._connect_tab_buttons.controls.append(add_btn)
        
        # 更新当前显示的内容
        if self._connect_tab_contents:
            idx = min(self._connect_tab_index, len(self._connect_tab_contents) - 1)
            self._connect_tab_content.content = self._connect_tab_contents[idx]
    
    def _switch_tab(self, index: int):
        self._connect_tab_index = index
        for i, btn in enumerate(self._connect_tab_buttons.controls):
            if isinstance(btn, ft.Container):
                is_selected = i == index
                btn.border = ft.border.only(bottom=ft.BorderSide(2, ft.Colors.PRIMARY)) if is_selected else None
                btn.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY) if is_selected else None
                if btn.content and isinstance(btn.content, ft.Text):
                    btn.content.color = ft.Colors.PRIMARY if is_selected else ft.Colors.ON_SURFACE
        if 0 <= index < len(self._connect_tab_contents):
            self._connect_tab_content.content = self._connect_tab_contents[index]
        self._try_update()
    
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
        
        self._connect_tab_index = len(self.current_config["ob11"]["connect"]) - 1
        self._rebuild_tabs()
        self._try_update()
    
    def _on_delete_connect(self, index: int):
        connects = self.current_config.get("ob11", {}).get("connect", [])
        if 0 <= index < len(connects):
            connects.pop(index)
            if connects:
                self._connect_tab_index = min(index, len(connects) - 1)
            else:
                self._connect_tab_index = 0
            self._rebuild_tabs()
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
                        "urls": self._collect_webhook_urls(),
                        "accessToken": self.milky_webhook_token.value or ""
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
        self.milky_webhook_token.value = milky_cfg.get("webhook", {}).get("accessToken", "")
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
        page = self._page or (self.control.page if self.control else None)
        if page:
            snack = ft.SnackBar(
                content=ft.Text(msg, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600,
                duration=2000,
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    def _show_success(self, msg: str):
        page = self._page or (self.control.page if self.control else None)
        if page:
            snack = ft.SnackBar(
                content=ft.Text(msg, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_600,
                duration=2000,
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    def _try_update(self):
        try:
            page = self._page or (self.control.page if self.control else None)
            if page:
                page.update()
        except Exception:
            pass
    
    def refresh(self, skip_update: bool = False):
        """刷新配置页面 - 带可见性检查"""
        import logging
        logger = logging.getLogger(__name__)

        # 如果页面不可见，不执行刷新
        if not self._is_visible:
            logger.debug("Bot配置页面不可见，跳过刷新")
            return

        current_uin = self.get_uin_func()
        has_uin = bool(current_uin)
        uin_changed = current_uin != self._last_uin

        logger.info(f"Bot配置页面刷新: has_uin={has_uin}, current_uin={current_uin}, last_uin={self._last_uin}, uin_changed={uin_changed}, _initialized={self._initialized}")

        # 首次进入或 uin 发生变化时需要完整刷新
        if not self._initialized or uin_changed:
            if uin_changed:
                logger.info(f"UIN 发生变化: {self._last_uin} -> {current_uin}，重新加载配置")
            self._initialized = True
            self._last_uin = current_uin

            new_config = self._load_config()
            if new_config != self.current_config:
                logger.info("配置已更新，重新加载UI")
                self.current_config = new_config
                self._update_ui()
                self._rebuild_tabs()

        # 更新可见性
        self.no_uin_container.visible = not has_uin
        self.config_content.visible = has_uin
        self.floating_buttons.visible = has_uin
        logger.info(f"UI可见性更新: 未登录提示={not has_uin}, 配置内容={has_uin}")

        if not skip_update:
            self._try_update()

    def on_page_enter(self):
        """页面进入时调用"""
        self._is_visible = True

    def on_page_leave(self):
        """页面离开时调用"""
        self._is_visible = False
