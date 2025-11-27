"""更新检查模块 - 检查各组件的NPM更新"""

from dataclasses import dataclass
from typing import Optional, Dict
from packaging import version
from utils.npm_api import get_package_info, extract_version_from_tag, NpmAPIError
from utils.constants import NPM_PACKAGES, GITHUB_REPOS, UPDATE_CHECK_TIMEOUT


@dataclass
class UpdateInfo:
    """更新信息"""
    has_update: bool
    current_version: str
    latest_version: str
    release_url: str
    error: Optional[str] = None


class UpdateChecker:
    """检查NPM包的更新"""
    
    def __init__(self, timeout: int = UPDATE_CHECK_TIMEOUT):
        """初始化更新检查器
        
        Args:
            timeout: API请求超时时间（秒），默认为10秒
        """
        self.timeout = timeout
    
    def check_update(self, package_name: str, current_version: str, 
                     github_repo: Optional[str] = None) -> UpdateInfo:
        """检查指定npm包的更新
        
        Args:
            package_name: npm包名称
            current_version: 当前版本号
            github_repo: GitHub仓库地址（用于生成release URL）
            
        Returns:
            UpdateInfo对象，包含是否有更新、最新版本等信息
        """
        try:
            # 获取最新包信息
            package_info = get_package_info(package_name, timeout=self.timeout)
            
            if package_info is None:
                return UpdateInfo(
                    has_update=False,
                    current_version=current_version,
                    latest_version="未知",
                    release_url="",
                    error="未找到npm包信息"
                )
            
            # 提取版本号
            latest_version_str = package_info.get("version", "")
            
            # 生成release URL（使用GitHub仓库）
            release_url = ""
            if github_repo:
                release_url = f"https://github.com/{github_repo}/releases"
            
            # 比较版本号
            try:
                # 清理版本号
                current_clean = extract_version_from_tag(current_version)
                latest_clean = extract_version_from_tag(latest_version_str)
                
                current_ver = version.parse(current_clean)
                latest_ver = version.parse(latest_clean)
                
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
                
        except NpmAPIError as e:
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
    
    def check_all_updates(self, versions: Dict[str, str], 
                          packages: Optional[Dict[str, str]] = None,
                          repos: Optional[Dict[str, str]] = None) -> Dict[str, UpdateInfo]:
        """检查所有组件的更新
        
        Args:
            versions: 组件名到当前版本号的映射
                     例如: {"pmhq": "1.0.0", "llonebot": "2.1.0", "app": "1.0.0"}
            packages: 组件名到npm包名的映射（可选），如果不提供则使用默认值
                   例如: {"pmhq": "pmhq", "llonebot": "llonebot", "app": "lucky-lillia-desktop"}
            repos: 组件名到GitHub仓库的映射（可选），用于生成release URL
        
        Returns:
            组件名到UpdateInfo的映射
        """
        # 如果没有提供packages，使用默认值
        if packages is None:
            packages = NPM_PACKAGES
        
        # 如果没有提供repos，使用默认值
        if repos is None:
            repos = GITHUB_REPOS
        
        results = {}
        
        for component, current_version in versions.items():
            # 获取对应的npm包名
            package_name = packages.get(component)
            github_repo = repos.get(component)
            
            if package_name is None:
                results[component] = UpdateInfo(
                    has_update=False,
                    current_version=current_version,
                    latest_version="未知",
                    release_url="",
                    error=f"未配置{component}的npm包名"
                )
                continue
            
            # 检查更新
            results[component] = self.check_update(package_name, current_version, github_repo)
        
        return results
