"""更新检查模块 - 检查各组件的GitHub更新"""

from dataclasses import dataclass
from typing import Optional, Dict
from packaging import version
from utils.github_api import get_latest_release, extract_version_from_tag, GitHubAPIError
from utils.constants import GITHUB_REPOS, UPDATE_CHECK_TIMEOUT


@dataclass
class UpdateInfo:
    """更新信息"""
    has_update: bool
    current_version: str
    latest_version: str
    release_url: str
    error: Optional[str] = None


class UpdateChecker:
    """检查GitHub仓库的更新"""
    
    def __init__(self, timeout: int = UPDATE_CHECK_TIMEOUT):
        """初始化更新检查器
        
        Args:
            timeout: API请求超时时间（秒），默认为10秒
        """
        self.timeout = timeout
    
    def check_update(self, repo: str, current_version: str) -> UpdateInfo:
        """检查指定仓库的更新
        
        Args:
            repo: GitHub仓库 (格式: "owner/repo")
            current_version: 当前版本号
            
        Returns:
            UpdateInfo对象，包含是否有更新、最新版本等信息
        """
        try:
            # 获取最新release信息
            release_data = get_latest_release(repo, timeout=self.timeout)
            
            if release_data is None:
                return UpdateInfo(
                    has_update=False,
                    current_version=current_version,
                    latest_version="未知",
                    release_url="",
                    error="未找到release信息"
                )
            
            # 提取版本号
            latest_tag = release_data["tag_name"]
            latest_version_str = extract_version_from_tag(latest_tag)
            release_url = release_data["html_url"]
            
            # 比较版本号
            try:
                current_ver = version.parse(current_version)
                latest_ver = version.parse(latest_version_str)
                
                has_update = latest_ver > current_ver
                
                return UpdateInfo(
                    has_update=has_update,
                    current_version=current_version,
                    latest_version=latest_version_str,
                    release_url=release_url,
                    error=None
                )
            except version.InvalidVersion as e:
                return UpdateInfo(
                    has_update=False,
                    current_version=current_version,
                    latest_version=latest_version_str,
                    release_url=release_url,
                    error=f"版本号格式无效: {e}"
                )
                
        except GitHubAPIError as e:
            return UpdateInfo(
                has_update=False,
                current_version=current_version,
                latest_version="未知",
                release_url="",
                error=str(e)
            )
        except Exception as e:
            return UpdateInfo(
                has_update=False,
                current_version=current_version,
                latest_version="未知",
                release_url="",
                error=f"检查更新失败: {e}"
            )
    
    def check_all_updates(self, versions: Dict[str, str]) -> Dict[str, UpdateInfo]:
        """检查所有组件的更新
        
        Args:
            versions: 组件名到当前版本号的映射
                     例如: {"pmhq": "1.0.0", "llonebot": "2.1.0", "app": "1.0.0"}
        
        Returns:
            组件名到UpdateInfo的映射
        """
        results = {}
        
        for component, current_version in versions.items():
            # 获取对应的GitHub仓库
            repo = GITHUB_REPOS.get(component)
            
            if repo is None:
                results[component] = UpdateInfo(
                    has_update=False,
                    current_version=current_version,
                    latest_version="未知",
                    release_url="",
                    error=f"未配置{component}的GitHub仓库"
                )
                continue
            
            # 检查更新
            results[component] = self.check_update(repo, current_version)
        
        return results
