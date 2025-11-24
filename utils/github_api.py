"""GitHub API封装 - 用于查询仓库的最新release信息"""

import requests
from typing import Optional, Dict, Any
from utils.constants import UPDATE_CHECK_TIMEOUT


class GitHubAPIError(Exception):
    """GitHub API错误基类"""
    pass


class NetworkError(GitHubAPIError):
    """网络请求错误"""
    pass


class TimeoutError(GitHubAPIError):
    """请求超时错误"""
    pass


class ParseError(GitHubAPIError):
    """响应解析错误"""
    pass


def get_latest_release(repo: str, timeout: int = UPDATE_CHECK_TIMEOUT) -> Optional[Dict[str, Any]]:
    """获取GitHub仓库的最新release信息
    
    Args:
        repo: GitHub仓库，格式为 "owner/repo"
        timeout: 请求超时时间（秒），默认为10秒
        
    Returns:
        包含release信息的字典，包含以下字段：
        - tag_name: 版本标签
        - name: release名称
        - html_url: release页面URL
        - published_at: 发布时间
        如果请求失败返回None
        
    Raises:
        NetworkError: 网络请求失败
        TimeoutError: 请求超时
        ParseError: 响应格式错误
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    try:
        response = requests.get(
            api_url,
            timeout=timeout,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "QQ-Bot-Manager"
            }
        )
        
        # 检查HTTP状态码
        if response.status_code == 404:
            # 仓库不存在或没有release
            return None
        
        response.raise_for_status()
        
        # 解析JSON响应
        try:
            data = response.json()
        except ValueError as e:
            raise ParseError(f"无法解析GitHub API响应: {e}")
        
        # 验证必需字段
        if "tag_name" not in data:
            raise ParseError("GitHub API响应缺少tag_name字段")
        
        return {
            "tag_name": data.get("tag_name", ""),
            "name": data.get("name", ""),
            "html_url": data.get("html_url", ""),
            "published_at": data.get("published_at", "")
        }
        
    except requests.exceptions.Timeout:
        raise TimeoutError(f"GitHub API请求超时（{timeout}秒）")
    except requests.exceptions.ConnectionError as e:
        raise NetworkError(f"网络连接失败: {e}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"请求失败: {e}")


def extract_version_from_tag(tag_name: str) -> str:
    """从tag名称中提取版本号
    
    GitHub的tag通常格式为 "v1.0.0" 或 "1.0.0"
    此函数移除前导的 'v' 字符
    
    Args:
        tag_name: tag名称
        
    Returns:
        版本号字符串
    """
    if tag_name.startswith("v") or tag_name.startswith("V"):
        return tag_name[1:]
    return tag_name
