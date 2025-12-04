"""GitHub镜像管理工具 - 管理和选择可用的GitHub镜像"""

import urllib.request
import urllib.error
import socket
from typing import List, Optional
from utils.constants import GITHUB_MIRRORS


class MirrorManager:
    """GitHub镜像管理器"""
    
    def __init__(self, timeout: int = 5):
        """初始化镜像管理器
        
        Args:
            timeout: 测试镜像可用性的超时时间（秒）
        """
        self.timeout = timeout
        self.mirrors = GITHUB_MIRRORS.copy()
        self._available_mirror: Optional[str] = None
    
    def get_available_mirror(self) -> str:
        """获取可用的镜像
        
        尝试按顺序测试每个镜像，返回第一个可用的镜像。
        如果之前已经找到可用镜像，直接返回缓存的结果。
        
        Returns:
            可用的镜像URL，如果所有镜像都不可用则返回第一个镜像
        """
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
        """测试镜像是否可用
        
        Args:
            mirror: 镜像URL
            
        Returns:
            镜像可用返回True，否则返回False
        """
        try:
            # 构造一个简单的测试URL（GitHub主页）
            if mirror.endswith("/"):
                test_url = mirror
            else:
                test_url = mirror + "/"
            
            # 发送HEAD请求测试连接
            req = urllib.request.Request(
                test_url,
                method='HEAD',
                headers={"User-Agent": "Lucky-Lillia"}
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                # 2xx或3xx状态码都认为是可用的
                return response.status < 400
            
        except (socket.timeout, urllib.error.URLError, urllib.error.HTTPError):
            return False
    
    def reset_cache(self):
        """重置缓存的可用镜像
        
        在网络环境变化时可以调用此方法重新测试镜像
        """
        self._available_mirror = None
    
    def get_all_mirrors(self) -> List[str]:
        """获取所有配置的镜像列表
        
        Returns:
            镜像URL列表
        """
        return self.mirrors.copy()
    
    def transform_url(self, github_url: str, mirror: Optional[str] = None) -> str:
        """将GitHub URL转换为镜像URL
        
        Args:
            github_url: 原始GitHub URL
            mirror: 要使用的镜像，如果为None则自动选择可用镜像
            
        Returns:
            转换后的URL
        """
        if mirror is None:
            mirror = self.get_available_mirror()
        
        # 如果是直连GitHub，直接返回原URL
        if mirror == "https://github.com/":
            return github_url
        
        # 替换URL前缀
        if github_url.startswith("https://github.com/"):
            return github_url.replace("https://github.com/", mirror)
        
        return github_url
