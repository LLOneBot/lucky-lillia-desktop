"""登录服务模块"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Callable, List

from utils.pmhq_client import PMHQClient, SSEListener

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
    PMHQ_READY_TIMEOUT = 30
    PMHQ_CHECK_INTERVAL = 1
    
    def __init__(self, port: int):
        self._port = port
        self._client = PMHQClient(port, timeout=30)
        self._sse_listener: Optional[SSEListener] = None
        self._qrcode_callback: Optional[Callable[[QRCodeInfo], None]] = None
        self._login_success_callback: Optional[Callable[[str], None]] = None
        self._pmhq_ready = False
    
    def is_pmhq_ready(self) -> bool:
        return self._client.is_ready()
    
    def wait_for_pmhq_ready(self, timeout: Optional[float] = None, 
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        if self._pmhq_ready:
            return True
            
        timeout = timeout or self.PMHQ_READY_TIMEOUT
        elapsed = 0
        
        logger.info(f"等待PMHQ就绪，超时时间: {timeout}秒")
        
        while elapsed < timeout:
            if self._client.is_ready():
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
        if wait_ready and not self._pmhq_ready:
            if not self.wait_for_pmhq_ready():
                logger.warning("PMHQ未就绪，无法获取登录列表")
                return []
        
        resp = self._client.get_login_list(timeout=10)
        if not resp.success:
            logger.warning(f"获取登录列表失败: {resp.error}")
            return []
        
        result = resp.result
        if not isinstance(result, dict):
            return []
        
        if result.get("result") != 0:
            return []
        
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
    
    def get_quick_login_accounts(self) -> List[LoginAccount]:
        all_accounts = self.get_login_list()
        return [acc for acc in all_accounts if acc.is_quick_login and not acc.is_user_login]
    
    def quick_login(self, uin: str, wait_ready: bool = True) -> LoginResult:
        if wait_ready and not self._pmhq_ready:
            if not self.wait_for_pmhq_ready():
                return LoginResult(success=False, error_msg="PMHQ未就绪")
        
        resp = self._client.quick_login(uin, timeout=30)
        if not resp.success:
            return LoginResult(success=False, error_msg=resp.error or "登录请求失败")
        
        result = resp.result
        if not isinstance(result, dict):
            if result == 0 or result == "0":
                return LoginResult(success=True)
            return LoginResult(success=False, error_msg="登录失败")
        
        result_code = result.get("result")
        if result_code == 0 or result_code == "0":
            return LoginResult(success=True)
        
        error_info = result.get("loginErrorInfo", {})
        if isinstance(error_info, dict):
            error_msg = error_info.get("errMsg", "登录失败")
        else:
            error_msg = "登录失败"
        return LoginResult(success=False, error_msg=error_msg)
    
    def request_qrcode(self, wait_ready: bool = True) -> bool:
        logger.info(f"开始请求二维码, wait_ready={wait_ready}, _pmhq_ready={self._pmhq_ready}")
        
        if wait_ready and not self._pmhq_ready:
            logger.info("PMHQ未就绪，开始等待...")
            if not self.wait_for_pmhq_ready():
                logger.warning("PMHQ未就绪，无法请求二维码")
                return False
            logger.info("PMHQ已就绪")
        
        resp = self._client.get_qrcode(timeout=10)
        logger.info(f"二维码请求结果: success={resp.success}, error={resp.error}")
        return resp.success
    
    def start_sse_listener(self, 
                          qrcode_callback: Callable[[QRCodeInfo], None],
                          login_success_callback: Optional[Callable[[str], None]] = None):
        if self._sse_listener:
            return
        
        self._qrcode_callback = qrcode_callback
        self._login_success_callback = login_success_callback
        
        self._sse_listener = SSEListener(self._client.base_url)
        self._sse_listener.on("nodeIKernelLoginListener", self._handle_login_event)
        self._sse_listener.start()
    
    def stop_sse_listener(self):
        if self._sse_listener:
            self._sse_listener.stop()
            self._sse_listener = None
    
    def _handle_login_event(self, data: dict):
        inner_data = data.get("data", {})
        sub_type = inner_data.get("sub_type")
        logger.info(f"登录监听器事件, sub_type={sub_type}")
        
        if sub_type == "onQRCodeGetPicture":
            qr_data = inner_data.get("data", {})
            png_base64_raw = qr_data.get("pngBase64QrcodeData", "")
            
            if png_base64_raw and not png_base64_raw.startswith("data:"):
                png_base64 = f"data:image/png;base64,{png_base64_raw}"
            else:
                png_base64 = png_base64_raw
            
            logger.info(f"收到二维码数据, png_base64长度={len(png_base64)}")
            
            qrcode_info = QRCodeInfo(
                png_base64=png_base64,
                qrcode_url=qr_data.get("qrcodeUrl", ""),
                expire_time=qr_data.get("expireTime", 120),
                poll_interval=qr_data.get("pollTimeInterval", 2)
            )
            
            if self._qrcode_callback:
                self._qrcode_callback(qrcode_info)
