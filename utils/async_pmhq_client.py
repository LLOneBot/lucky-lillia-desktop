"""异步 PMHQ HTTP API 客户端"""

import json
import logging
from dataclasses import dataclass
from typing import Optional, Any, Dict, List
from utils.async_http_client import AsyncHttpClient, HttpError

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
class DeviceInfo:
    dev_type: str
    build_ver: str


class AsyncPMHQClient:
    def __init__(self, port: int, timeout: int = 5):
        self._port = port
        self._base_url = f"http://127.0.0.1:{port}"
        self._client = AsyncHttpClient(timeout=timeout)
    
    @property
    def port(self) -> int:
        return self._port
    
    async def close(self):
        await self._client.close()
    
    async def _call(self, func: str, args: Optional[List] = None,
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
            resp = await self._client.post(self._base_url, json_data=payload, timeout=timeout)
            
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
            if isinstance(result, str) and "Error" in result:
                return PMHQResponse(success=False, error=result)
            
            return PMHQResponse(success=True, result=result)
            
        except HttpError as e:
            return PMHQResponse(success=False, error=str(e))
        except Exception as e:
            logger.debug(f"PMHQ API 调用异常: {e}")
            return PMHQResponse(success=False, error=str(e))
    
    async def get_self_info(self, timeout: int = 3) -> PMHQResponse:
        return await self._call("getSelfInfo", timeout=timeout)
    
    async def get_process_info(self, echo: Optional[str] = None, timeout: int = 2) -> PMHQResponse:
        return await self._call("getProcessInfo", echo=echo, timeout=timeout)
    
    async def get_device_info(self, timeout: int = 2) -> Optional[DeviceInfo]:
        resp = await self._call("getDeviceInfo", timeout=timeout)
        if not resp.success or not isinstance(resp.result, dict):
            return None
        return DeviceInfo(
            dev_type=resp.result.get("devType", ""),
            build_ver=resp.result.get("buildVer", "")
        )
    
    async def fetch_self_info(self) -> Optional[SelfInfo]:
        resp = await self.get_self_info()
        if not resp.success or not isinstance(resp.result, dict):
            return None
        uin = resp.result.get("uin")
        if not uin:
            return None
        nickname = resp.result.get("nickName") or resp.result.get("nickname") or ""
        return SelfInfo(uin=str(uin), nickname=nickname)
    
    async def fetch_qq_pid(self, echo: Optional[str] = None, timeout: int = 2) -> Optional[int]:
        resp = await self.get_process_info(echo=echo, timeout=timeout)
        if not resp.success or not isinstance(resp.result, dict):
            return None
        return resp.result.get("pid")
