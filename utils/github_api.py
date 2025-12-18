"""GitHub API封装（已废弃，请使用 npm_api.py）"""

import re
import logging
from typing import Optional, Dict, Any
from utils.constants import UPDATE_CHECK_TIMEOUT
from utils.http_client import HttpClient, TimeoutError as HttpTimeoutError, ConnectionError as HttpConnectionError

# 从 npm_api 导入错误类以保持兼容性
from utils.npm_api import NpmAPIError, NetworkError as NpmNetworkError, TimeoutError as NpmTimeoutError, ParseError as NpmParseError


logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """GitHub API错误基类（已废弃，请使用 NpmAPIError）"""
    pass


class NetworkError(GitHubAPIError):
    """网络请求错误（已废弃，请使用 npm_api.NetworkError）"""
    pass


class TimeoutError(GitHubAPIError):
    """请求超时错误（已废弃，请使用 npm_api.TimeoutError）"""
    pass


class ParseError(GitHubAPIError):
    """响应解析错误（已废弃，请使用 npm_api.ParseError）"""
    pass


def get_latest_release(repo: str, timeout: int = UPDATE_CHECK_TIMEOUT, mirror_manager=None) -> Optional[Dict[str, Any]]:
    # 延迟导入避免循环依赖
    from utils.mirror_manager import MirrorManager
    
    # 如果没有提供mirror_manager，创建一个新的
    if mirror_manager is None:
        mirror_manager = MirrorManager(timeout=5)
    
    client = HttpClient(timeout=timeout)
    last_error = None
    mirrors = mirror_manager.get_all_mirrors()
    logger.info(f"获取 {repo} 的release信息，尝试镜像: {mirrors}")
    
    # 循环尝试所有镜像
    for mirror in mirrors:
        try:
            logger.info(f"尝试镜像: {mirror}")
            if mirror == "https://github.com/":
                # 直连GitHub，使用API
                result = _get_release_from_api(client, repo, timeout)
            else:
                # 使用镜像，通过解析release页面获取信息
                result = _get_release_from_mirror(client, repo, mirror, timeout)
            
            if result:
                logger.info(f"成功从 {mirror} 获取release信息: {result.get('tag_name')}")
                return result
            else:
                logger.warning(f"镜像 {mirror} 返回空结果")
                
        except HttpTimeoutError:
            last_error = TimeoutError(f"GitHub请求超时（{timeout}秒）: {mirror}")
            logger.warning(f"镜像 {mirror} 超时")
            continue
        except HttpConnectionError as e:
            last_error = NetworkError(f"网络连接失败: {e}")
            logger.warning(f"镜像 {mirror} 连接失败: {e}")
            continue
        except (ParseError, GitHubAPIError) as e:
            last_error = e
            logger.warning(f"镜像 {mirror} 解析失败: {e}")
            continue
    
    # 所有镜像都失败了，抛出最后一个错误
    logger.error(f"所有镜像都失败了，最后错误: {last_error}")
    if last_error:
        raise last_error
    else:
        raise NetworkError("所有镜像都无法访问")


def _get_release_from_api(client: HttpClient, repo: str, timeout: int) -> Optional[Dict[str, Any]]:
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    resp = client.get(api_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=timeout)
    
    if resp.status == 404:
        return None
    
    if resp.status >= 400:
        raise NetworkError(f"HTTP错误 {resp.status}")
    
    # 解析JSON响应
    try:
        data = resp.json()
    except (ValueError, Exception) as e:
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


def _get_release_from_mirror(client: HttpClient, repo: str, mirror: str, timeout: int) -> Optional[Dict[str, Any]]:
    release_url = f"{mirror}{repo}/releases/latest"
    
    resp = client.get(release_url, timeout=timeout)
    
    if resp.status == 404:
        return None
    
    if resp.status >= 400:
        raise NetworkError(f"HTTP错误 {resp.status}")
    
    # 从重定向URL或页面内容中提取tag
    final_url = resp.url
    
    # 尝试从URL中提取tag
    tag_match = re.search(r'/releases/tag/([^/\?]+)', final_url)
    if tag_match:
        tag_name = tag_match.group(1)
        return {
            "tag_name": tag_name,
            "name": tag_name,
            "html_url": f"https://github.com/{repo}/releases/tag/{tag_name}",
            "published_at": ""
        }
    
    # 如果URL中没有tag，尝试从页面内容中提取
    html_content = resp.text()
    
    # 尝试匹配 release tag 链接
    tag_pattern = re.search(r'/releases/tag/([^"\'>\s]+)', html_content)
    if tag_pattern:
        tag_name = tag_pattern.group(1)
        return {
            "tag_name": tag_name,
            "name": tag_name,
            "html_url": f"https://github.com/{repo}/releases/tag/{tag_name}",
            "published_at": ""
        }
    
    return None


def extract_version_from_tag(tag_name: str) -> str:
    if tag_name.startswith("v") or tag_name.startswith("V"):
        return tag_name[1:]
    return tag_name
