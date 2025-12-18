"""GitHub镜像管理"""

from typing import List, Optional
from utils.constants import GITHUB_MIRRORS
from utils.http_client import HttpClient, HttpError


class MirrorManager:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.mirrors = GITHUB_MIRRORS.copy()
        self._available_mirror: Optional[str] = None
        self._client = HttpClient(timeout=timeout)
    
    def get_available_mirror(self) -> str:
        # 如果已经有缓存的可用镜像，直接返回
        if self._available_mirror:
            return self._available_mirror
        
        # 测试每个镜像
        for mirror in self.mirrors:
            if self._test_mirror(mirror):
                self._available_mirror = mirror
                return mirror
        
        # 如果所有镜像都不可用，返回第一个（直连GitHub）
        return self.mirrors[0] if self.mirrors else "https://github.com/"
    
    def _test_mirror(self, mirror: str) -> bool:
        try:
            # 构造一个简单的测试URL（GitHub主页）
            test_url = mirror if mirror.endswith("/") else mirror + "/"
            
            # 发送HEAD请求测试连接
            resp = self._client.head(test_url, timeout=self.timeout)
            # 2xx或3xx状态码都认为是可用的
            return resp.status < 400
            
        except HttpError:
            return False
    
    def reset_cache(self):
        self._available_mirror = None
    
    def get_all_mirrors(self) -> List[str]:
        return self.mirrors.copy()
    
    def transform_url(self, github_url: str, mirror: Optional[str] = None) -> str:
        if mirror is None:
            mirror = self.get_available_mirror()
        
        # 如果是直连GitHub，直接返回原URL
        if mirror == "https://github.com/":
            return github_url
        
        # 替换URL前缀
        if github_url.startswith("https://github.com/"):
            return github_url.replace("https://github.com/", mirror)
        
        return github_url
