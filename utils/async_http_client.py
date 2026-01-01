"""异步 HTTP 客户端"""

import asyncio
import json
import aiohttp
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class HttpResponse:
    status: int
    data: bytes
    headers: Dict[str, str]
    url: str
    
    def json(self) -> Any:
        return json.loads(self.data.decode('utf-8'))
    
    def text(self) -> str:
        return self.data.decode('utf-8')


class HttpError(Exception):
    pass


class TimeoutError(HttpError):
    pass


class ConnectionError(HttpError):
    pass


class AsyncHttpClient:
    DEFAULT_TIMEOUT = 10
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": self.DEFAULT_USER_AGENT}
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get(self, url: str, timeout: Optional[int] = None) -> HttpResponse:
        return await self._request('GET', url, timeout=timeout)
    
    async def post(self, url: str, json_data: Optional[Dict] = None,
                   timeout: Optional[int] = None) -> HttpResponse:
        return await self._request('POST', url, json_data=json_data, timeout=timeout)
    
    async def _request(self, method: str, url: str, 
                       json_data: Optional[Dict] = None,
                       timeout: Optional[int] = None) -> HttpResponse:
        session = await self._get_session()
        req_timeout = aiohttp.ClientTimeout(total=timeout or self.timeout)
        
        try:
            async with session.request(method, url, json=json_data, timeout=req_timeout) as resp:
                data = await resp.read()
                return HttpResponse(
                    status=resp.status,
                    data=data,
                    headers=dict(resp.headers),
                    url=str(resp.url)
                )
        except asyncio.TimeoutError:
            raise TimeoutError(f"请求超时: {url}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"连接失败: {e}")
