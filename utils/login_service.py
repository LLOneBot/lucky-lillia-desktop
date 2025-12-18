"""登录服务模块 - 处理PMHQ的登录相关HTTP API调用"""

import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable, List
from utils.http_client import HttpClient, HttpError

logger = logging.getLogger(__name__)


@dataclass
class LoginAccount:
    uin: str
    uid: str
    nick_name: str
    face_url: str
    face_path: str
    login_type: int
    is_quick_login: bool
    is_auto_login: bool
    is_user_login: bool


@dataclass
class LoginResult:
    success: bool
    error_msg: str = ""


@dataclass
class QRCodeInfo:
    png_base64: str
    qrcode_url: str
    expire_time: int
    poll_interval: int


class LoginService:
    """登录服务 - 处理PMHQ的登录相关API"""
    
    # PMHQ就绪检查的最大等待时间（秒）
    PMHQ_READY_TIMEOUT = 30
    # 检查间隔（秒）
    PMHQ_CHECK_INTERVAL = 1
    
    def __init__(self, port: int):
        self._port = port
        self._base_url = f"http://127.0.0.1:{port}"
        self._client = HttpClient(timeout=30)
        self._sse_thread: Optional[threading.Thread] = None
        self._sse_running = False
        self._qrcode_callback: Optional[Callable[[QRCodeInfo], None]] = None
        self._login_success_callback: Optional[Callable[[str], None]] = None
        self._pmhq_ready = False
    
    def is_pmhq_ready(self) -> bool:
        try:
            # 尝试调用一个简单的API来检查PMHQ状态
            payload = {
                "type": "call",
                "data": {
                    "func": "loginService.getLoginList",
                    "args": []
                }
            }
            
            resp = self._client.post(self._base_url, json_data=payload, timeout=5)
            
            if resp.status == 200:
                data = resp.json()
                if data.get("type") == "call" and "data" in data:
                    inner_data = data["data"]
                    if isinstance(inner_data, dict):
                        result = inner_data.get("result", {})
                        # 如果result是错误字符串，说明PMHQ还没准备好
                        if isinstance(result, str) and ("TypeError" in result or "Error" in result):
                            return False
                        # 如果result是dict，说明PMHQ已就绪
                        if isinstance(result, dict):
                            return True
            return False
        except Exception:
            return False
    
    def wait_for_pmhq_ready(self, timeout: Optional[float] = None, 
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        if self._pmhq_ready:
            return True
            
        timeout = timeout or self.PMHQ_READY_TIMEOUT
        elapsed = 0
        
        logger.info(f"等待PMHQ就绪，超时时间: {timeout}秒")
        
        while elapsed < timeout:
            if self.is_pmhq_ready():
                self._pmhq_ready = True
                logger.info(f"PMHQ已就绪，等待了{elapsed}秒")
                return True
            
            if progress_callback:
                progress_callback(int(elapsed), int(timeout))
            
            time.sleep(self.PMHQ_CHECK_INTERVAL)
            elapsed += self.PMHQ_CHECK_INTERVAL
        
        logger.warning(f"等待PMHQ就绪超时（{timeout}秒）")
        return False
    
    def get_login_list(self, wait_ready: bool = True) -> List[LoginAccount]:
        try:
            # 等待PMHQ就绪
            if wait_ready and not self._pmhq_ready:
                if not self.wait_for_pmhq_ready():
                    logger.warning("PMHQ未就绪，无法获取登录列表")
                    return []
            
            payload = {
                "type": "call",
                "data": {
                    "func": "loginService.getLoginList",
                    "args": []
                }
            }
            
            resp = self._client.post(self._base_url, json_data=payload, timeout=10)
            
            if resp.status == 200:
                data = resp.json()
                if data.get("type") == "call" and "data" in data:
                    inner_data = data["data"]
                    # 如果inner_data是字符串，尝试解析为JSON
                    if isinstance(inner_data, str):
                        try:
                            inner_data = json.loads(inner_data)
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析data字段: {inner_data}")
                            return []
                    if not isinstance(inner_data, dict):
                        logger.warning(f"data字段类型异常: {type(inner_data)}")
                        return []
                    result = inner_data.get("result", {})
                    # 检查是否为错误信息字符串
                    if isinstance(result, str):
                        if "TypeError" in result or "Error" in result:
                            logger.warning(f"PMHQ返回错误: {result}")
                        return []
                    if not isinstance(result, dict):
                        logger.warning(f"result字段类型异常: {type(result)}, inner_data={inner_data}")
                        return []
                    if result.get("result") == 0:
                        login_list = result.get("LocalLoginInfoList", [])
                        accounts = []
                        for item in login_list:
                            account = LoginAccount(
                                uin=item.get("uin", ""),
                                uid=item.get("uid", ""),
                                nick_name=item.get("nickName", ""),
                                face_url=item.get("faceUrl", ""),
                                face_path=item.get("facePath", ""),
                                login_type=item.get("loginType", 0),
                                is_quick_login=item.get("isQuickLogin", False),
                                is_auto_login=item.get("isAutoLogin", False),
                                is_user_login=item.get("isUserLogin", False)
                            )
                            accounts.append(account)
                        return accounts
            
            logger.warning("获取登录列表失败")
            return []
            
        except HttpError as e:
            logger.error(f"获取登录列表请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取登录列表异常: {e}")
            return []
    
    def get_quick_login_accounts(self) -> List[LoginAccount]:
        all_accounts = self.get_login_list()
        return [acc for acc in all_accounts if acc.is_quick_login and not acc.is_user_login]
    
    def quick_login(self, uin: str, wait_ready: bool = True) -> LoginResult:
        try:
            # 等待PMHQ就绪
            if wait_ready and not self._pmhq_ready:
                if not self.wait_for_pmhq_ready():
                    return LoginResult(success=False, error_msg="PMHQ未就绪")
            
            payload = {
                "type": "call",
                "data": {
                    "func": "loginService.quickLoginWithUin",
                    "args": [uin]
                }
            }
            
            resp = self._client.post(self._base_url, json_data=payload, timeout=30)
            
            if resp.status == 200:
                data = resp.json()
                if data.get("type") == "call" and "data" in data:
                    inner_data = data["data"]
                    # 如果inner_data是字符串，尝试解析为JSON
                    if isinstance(inner_data, str):
                        try:
                            inner_data = json.loads(inner_data)
                        except json.JSONDecodeError:
                            return LoginResult(success=False, error_msg="响应解析失败")
                    if not isinstance(inner_data, dict):
                        return LoginResult(success=False, error_msg="响应格式异常")
                    result = inner_data.get("result", {})
                    if not isinstance(result, dict):
                        # result可能直接是结果码
                        if result == 0 or result == "0":
                            return LoginResult(success=True)
                        return LoginResult(success=False, error_msg="登录失败")
                    result_code = result.get("result")
                    
                    # result为0或"0"表示成功
                    if result_code == 0 or result_code == "0":
                        return LoginResult(success=True)
                    else:
                        error_info = result.get("loginErrorInfo", {})
                        if isinstance(error_info, dict):
                            error_msg = error_info.get("errMsg", "登录失败")
                        else:
                            error_msg = "登录失败"
                        return LoginResult(success=False, error_msg=error_msg)
            
            return LoginResult(success=False, error_msg="登录请求失败")
            
        except HttpError as e:
            logger.error(f"快速登录请求失败: {e}")
            return LoginResult(success=False, error_msg=f"网络错误: {e}")
        except Exception as e:
            logger.error(f"快速登录异常: {e}")
            return LoginResult(success=False, error_msg=f"登录异常: {e}")
    
    def request_qrcode(self, wait_ready: bool = True) -> bool:
        try:
            logger.info(f"开始请求二维码, wait_ready={wait_ready}, _pmhq_ready={self._pmhq_ready}")
            
            # 等待PMHQ就绪
            if wait_ready and not self._pmhq_ready:
                logger.info("PMHQ未就绪，开始等待...")
                if not self.wait_for_pmhq_ready():
                    logger.warning("PMHQ未就绪，无法请求二维码")
                    return False
                logger.info("PMHQ已就绪")
            
            payload = {
                "type": "call",
                "data": {
                    "func": "loginService.getQRCodePicture",
                    "args": []
                }
            }
            
            logger.info(f"发送二维码请求到 {self._base_url}")
            resp = self._client.post(self._base_url, json_data=payload, timeout=10)
            
            response_text = resp.text()
            logger.info(f"二维码请求响应: status={resp.status}, body={response_text[:500] if response_text else 'empty'}")
            return resp.status == 200
            
        except Exception as e:
            logger.error(f"请求二维码失败: {e}", exc_info=True)
            return False
    
    def start_sse_listener(self, 
                          qrcode_callback: Callable[[QRCodeInfo], None],
                          login_success_callback: Optional[Callable[[str], None]] = None):
        if self._sse_running:
            return
        
        self._qrcode_callback = qrcode_callback
        self._login_success_callback = login_success_callback
        self._sse_running = True
        
        self._sse_thread = threading.Thread(
            target=self._sse_listen_loop,
            daemon=True
        )
        self._sse_thread.start()
    
    def stop_sse_listener(self):
        self._sse_running = False
        if self._sse_thread:
            self._sse_thread.join(timeout=2)
            self._sse_thread = None
    
    def _sse_listen_loop(self):
        import urllib.request
        import urllib.error
        import socket
        
        logger.info(f"SSE监听循环启动, URL: {self._base_url}")
        while self._sse_running:
            try:
                logger.info("正在建立SSE连接...")
                req = urllib.request.Request(self._base_url)
                
                with urllib.request.urlopen(req, timeout=120) as response:
                    logger.info(f"SSE连接已建立, status={response.status}")
                    
                    # 使用缓冲区处理可能跨行的数据
                    buffer = ""
                    while self._sse_running:
                        chunk = response.read(4096)
                        if not chunk:
                            break
                        
                        buffer += chunk.decode('utf-8')
                        # SSE消息以双换行符分隔
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            for line in message.split("\n"):
                                line = line.strip()
                                if line.startswith('data:'):
                                    data_str = line[5:].strip()
                                    logger.debug(f"SSE收到数据长度: {len(data_str)}")
                                    try:
                                        data = json.loads(data_str)
                                        self._handle_sse_data(data)
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"SSE数据JSON解析失败: {e}, data={data_str[:100]}")
                                
            except (urllib.error.URLError, socket.timeout) as e:
                if self._sse_running:
                    logger.warning(f"SSE连接断开: {e}")
                    time.sleep(1)  # 重连延迟
            except Exception as e:
                if self._sse_running:
                    logger.error(f"SSE监听异常: {e}", exc_info=True)
                    time.sleep(1)
    
    def _handle_sse_data(self, data: dict):
        data_type = data.get("type")
        logger.info(f"处理SSE数据, type={data_type}")
        
        if data_type == "nodeIKernelLoginListener":
            inner_data = data.get("data", {})
            sub_type = inner_data.get("sub_type")
            logger.info(f"登录监听器事件, sub_type={sub_type}")
            
            if sub_type == "onQRCodeGetPicture":
                # 收到二维码
                qr_data = inner_data.get("data", {})
                logger.info(f"二维码原始数据字段: {list(qr_data.keys()) if isinstance(qr_data, dict) else type(qr_data)}")
                png_base64_raw = qr_data.get("pngBase64QrcodeData", "")
                logger.info(f"png_base64_raw内容(前200字符): {png_base64_raw[:200] if png_base64_raw else 'empty'}")
                logger.info(f"png_base64_raw总长度: {len(png_base64_raw)}")
                
                # 调试：将base64解码后写入文件
                # try:
                #     import base64
                #     import os
                #     # 去掉data:image/png;base64,前缀
                #     if png_base64_raw.startswith("data:"):
                #         b64_data = png_base64_raw.split(",", 1)[1] if "," in png_base64_raw else png_base64_raw
                #     else:
                #         b64_data = png_base64_raw
                #     decoded = base64.b64decode(b64_data)
                #     debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_qrcode.png")
                #     with open(debug_path, "wb") as f:
                #         f.write(decoded)
                #     logger.info(f"二维码已保存到: {debug_path}, 文件大小: {len(decoded)} bytes")
                # except Exception as e:
                #     logger.error(f"保存二维码调试文件失败: {e}")
                
                # 如果没有data:image前缀，添加它
                if png_base64_raw and not png_base64_raw.startswith("data:"):
                    png_base64 = f"data:image/png;base64,{png_base64_raw}"
                else:
                    png_base64 = png_base64_raw
                logger.info(f"收到二维码数据, png_base64长度={len(png_base64)}, qrcodeUrl={qr_data.get('qrcodeUrl', '')[:50]}")
                
                qrcode_info = QRCodeInfo(
                    png_base64=png_base64,
                    qrcode_url=qr_data.get("qrcodeUrl", ""),
                    expire_time=qr_data.get("expireTime", 120),
                    poll_interval=qr_data.get("pollTimeInterval", 2)
                )
                
                if self._qrcode_callback:
                    logger.info("调用二维码回调函数")
                    self._qrcode_callback(qrcode_info)
                else:
                    logger.warning("二维码回调函数未设置!")
        else:
            logger.debug(f"忽略SSE数据类型: {data_type}")
