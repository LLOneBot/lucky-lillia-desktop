"""HTTP 客户端封装"""

import json
import urllib.request
import urllib.error
import socket
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


class HttpClient:
    DEFAULT_TIMEOUT = 30
    DEFAULT_USER_AGENT = "Lucky-Lillia-Desktop"
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, user_agent: str = DEFAULT_USER_AGENT):
        self.timeout = timeout
        self.user_agent = user_agent
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None, 
            timeout: Optional[int] = None) -> HttpResponse:
        return self._request('GET', url, headers=headers, timeout=timeout)
    
    def post(self, url: str, data: Optional[Union[Dict, bytes, str]] = None,
             json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None,
             timeout: Optional[int] = None) -> HttpResponse:
        return self._request('POST', url, data=data, json_data=json_data, 
                           headers=headers, timeout=timeout)
    
    def head(self, url: str, headers: Optional[Dict[str, str]] = None,
             timeout: Optional[int] = None) -> HttpResponse:
        return self._request('HEAD', url, headers=headers, timeout=timeout)
    
    def download(self, url: str, headers: Optional[Dict[str, str]] = None,
                 timeout: Optional[int] = None, 
                 chunk_callback: Optional[callable] = None) -> HttpResponse:
        req = self._build_request('GET', url, headers=headers)
        timeout = timeout or self.timeout
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunks = []
                
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    if chunk_callback:
                        chunk_callback(chunk, downloaded, total_size)
                
                return HttpResponse(
                    status=response.status,
                    data=b''.join(chunks),
                    headers=dict(response.headers),
                    url=response.url
                )
        except socket.timeout:
            raise TimeoutError(f"请求超时: {url}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"连接失败: {e.reason}")
    
    def _request(self, method: str, url: str, data: Optional[Union[Dict, bytes, str]] = None,
                 json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None,
                 timeout: Optional[int] = None) -> HttpResponse:
        req = self._build_request(method, url, data, json_data, headers)
        timeout = timeout or self.timeout
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return HttpResponse(
                    status=response.status,
                    data=response.read(),
                    headers=dict(response.headers),
                    url=response.url
                )
        except urllib.error.HTTPError as e:
            return HttpResponse(
                status=e.code,
                data=e.read() if e.fp else b'',
                headers=dict(e.headers) if e.headers else {},
                url=url
            )
        except socket.timeout:
            raise TimeoutError(f"请求超时: {url}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"连接失败: {e.reason}")
    
    def _build_request(self, method: str, url: str, 
                       data: Optional[Union[Dict, bytes, str]] = None,
                       json_data: Optional[Dict] = None,
                       headers: Optional[Dict[str, str]] = None) -> urllib.request.Request:
        req_headers = {'User-Agent': self.user_agent}
        if headers:
            req_headers.update(headers)
        
        req_data = None
        if json_data is not None:
            req_data = json.dumps(json_data).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                req_data = json.dumps(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/json'
            elif isinstance(data, str):
                req_data = data.encode('utf-8')
            else:
                req_data = data
        
        return urllib.request.Request(url, data=req_data, headers=req_headers, method=method)


_default_client: Optional[HttpClient] = None


def get_client() -> HttpClient:
    global _default_client
    if _default_client is None:
        _default_client = HttpClient()
    return _default_client


def get(url: str, **kwargs) -> HttpResponse:
    return get_client().get(url, **kwargs)


def post(url: str, **kwargs) -> HttpResponse:
    return get_client().post(url, **kwargs)


def head(url: str, **kwargs) -> HttpResponse:
    return get_client().head(url, **kwargs)
