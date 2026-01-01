"""PMHQ HTTP API 客户端封装"""

import json
import logging
import threading
import time
import urllib.request
import urllib.error
import socket
from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict, List
from utils.http_client import HttpClient, HttpError

logger = logging.getLogger(__name__)


@dataclass
class PMHQResponse:
    success: bool
    result: Any = None
    error: str = ""


@dataclass
class SelfInfo:
    uin: str
    nickname: str


@dataclass
class ProcessInfo:
    pid: Optional[int] = None


@dataclass
class DeviceInfo:
    dev_type: str
    build_ver: str


class PMHQClient:
    """PMHQ HTTP API 客户端"""
    
    def __init__(self, port: int, timeout: int = 30):
        self._port = port
        self._base_url = f"http://127.0.0.1:{port}"
        self._client = HttpClient(timeout=timeout)
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    def _call(self, func: str, args: Optional[List] = None, 
              echo: Optional[str] = None, timeout: Optional[int] = None) -> PMHQResponse:
        payload: Dict[str, Any] = {
            "type": "call",
            "data": {
                "func": func,
                "args": args or []
            }
        }
        
        if echo:
            payload["data"]["echo"] = echo
        
        try:
            resp = self._client.post(self._base_url, json_data=payload, timeout=timeout)
            
            if resp.status != 200:
                return PMHQResponse(success=False, error=f"HTTP {resp.status}")
            
            data = resp.json()
            if data.get("type") != "call" or "data" not in data:
                return PMHQResponse(success=False, error="响应格式错误")
            
            inner_data = data["data"]
            if isinstance(inner_data, str):
                try:
                    inner_data = json.loads(inner_data)
                except json.JSONDecodeError:
                    return PMHQResponse(success=False, error="响应解析失败")
            
            if not isinstance(inner_data, dict):
                return PMHQResponse(success=False, error="响应格式异常")
            
            result = inner_data.get("result")
            
            if isinstance(result, str) and ("TypeError" in result or "Error" in result):
                return PMHQResponse(success=False, error=result)
            
            return PMHQResponse(success=True, result=result)
            
        except HttpError as e:
            return PMHQResponse(success=False, error=str(e))
        except Exception as e:
            logger.error(f"PMHQ API 调用异常: {e}")
            return PMHQResponse(success=False, error=str(e))
    
    def get_login_list(self, timeout: int = 10) -> PMHQResponse:
        return self._call("loginService.getLoginList", timeout=timeout)
    
    def quick_login(self, uin: str, timeout: int = 30) -> PMHQResponse:
        return self._call("loginService.quickLoginWithUin", args=[uin], timeout=timeout)
    
    def get_qrcode(self, timeout: int = 10) -> PMHQResponse:
        return self._call("loginService.getQRCodePicture", timeout=timeout)
    
    def get_self_info(self, timeout: int = 5) -> PMHQResponse:
        return self._call("getSelfInfo", timeout=timeout)
    
    def get_process_info(self, echo: Optional[str] = None, timeout: int = 5) -> PMHQResponse:
        return self._call("getProcessInfo", echo=echo, timeout=timeout)
    
    def get_device_info(self, timeout: int = 5) -> Optional[DeviceInfo]:
        resp = self._call("getDeviceInfo", timeout=timeout)
        if not resp.success or not isinstance(resp.result, dict):
            return None
        
        return DeviceInfo(
            dev_type=resp.result.get("devType", ""),
            build_ver=resp.result.get("buildVer", "")
        )
    
    def is_ready(self) -> bool:
        resp = self.get_login_list(timeout=5)
        return resp.success and isinstance(resp.result, dict)
    
    def fetch_self_info(self) -> Optional[SelfInfo]:
        resp = self.get_self_info()
        if not resp.success or not isinstance(resp.result, dict):
            return None
        
        uin = resp.result.get("uin")
        if not uin:
            return None
        
        nickname = resp.result.get("nickName") or resp.result.get("nickname") or resp.result.get("nick") or ""
        return SelfInfo(uin=str(uin), nickname=nickname)
    
    def fetch_qq_pid(self, echo: Optional[str] = None, timeout: int = 5) -> Optional[int]:
        resp = self.get_process_info(echo=echo, timeout=timeout)
        if not resp.success or not isinstance(resp.result, dict):
            return None
        return resp.result.get("pid")


class SSEListener:
    """PMHQ SSE 事件监听器"""
    
    def __init__(self, url: str):
        self._url = url
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._handlers: Dict[str, List[Callable[[dict], None]]] = {}
    
    def on(self, event_type: str, handler: Callable[[dict], None]):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Optional[Callable[[dict], None]] = None):
        if event_type not in self._handlers:
            return
        
        if handler is None:
            del self._handlers[event_type]
        else:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
    
    def start(self):
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def _listen_loop(self):
        logger.info(f"SSE 监听启动: {self._url}")
        
        while self._running:
            try:
                req = urllib.request.Request(self._url)
                
                with urllib.request.urlopen(req, timeout=120) as response:
                    logger.info(f"SSE 连接已建立, status={response.status}")
                    
                    buffer = ""
                    while self._running:
                        chunk = response.read(4096)
                        if not chunk:
                            break
                        
                        buffer += chunk.decode('utf-8')
                        
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            self._process_message(message)
                            
            except (urllib.error.URLError, socket.timeout) as e:
                if self._running:
                    logger.warning(f"SSE 连接断开: {e}")
                    time.sleep(1)
            except Exception as e:
                if self._running:
                    logger.error(f"SSE 监听异常: {e}", exc_info=True)
                    time.sleep(1)
    
    def _process_message(self, message: str):
        for line in message.split("\n"):
            line = line.strip()
            if line.startswith('data:'):
                data_str = line[5:].strip()
                try:
                    data = json.loads(data_str)
                    self._dispatch(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"SSE 数据解析失败: {e}")
    
    def _dispatch(self, data: dict):
        event_type = data.get("type")
        if not event_type:
            return
        
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"SSE 事件处理异常: {e}", exc_info=True)
