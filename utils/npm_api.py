"""NPM Registry API封装 - 用于查询npm包的最新版本信息"""

import re
import logging
from typing import Optional, Dict, Any, List
from utils.constants import UPDATE_CHECK_TIMEOUT, NPM_REGISTRY_MIRRORS
from utils.http_client import HttpClient, TimeoutError as HttpTimeoutError, ConnectionError as HttpConnectionError


class NpmAPIError(Exception):
    """NPM API错误基类"""
    pass


class NetworkError(NpmAPIError):
    """网络请求错误"""
    pass


class TimeoutError(NpmAPIError):
    """请求超时错误"""
    pass


class ParseError(NpmAPIError):
    """响应解析错误"""
    pass


logger = logging.getLogger(__name__)


def get_package_info(package_name: str, timeout: int = UPDATE_CHECK_TIMEOUT, 
                     registry_mirrors: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """获取npm包的信息
    
    Args:
        package_name: npm包名称
        timeout: 请求超时时间（秒），默认为10秒
        registry_mirrors: npm镜像列表，如果为None则使用默认镜像
        
    Returns:
        包含包信息的字典，包含以下字段：
        - name: 包名
        - version: 最新版本
        - dist: 分发信息（包含tarball下载地址）
        如果请求失败返回None
        
    Raises:
        NetworkError: 网络请求失败
        TimeoutError: 请求超时
        ParseError: 响应格式错误
    """
    if registry_mirrors is None:
        registry_mirrors = NPM_REGISTRY_MIRRORS.copy()
    
    last_error = None
    logger.info(f"获取 {package_name} 的npm包信息，尝试镜像: {registry_mirrors}")
    client = HttpClient(timeout=timeout)
    
    # 循环尝试所有镜像
    for registry in registry_mirrors:
        try:
            logger.info(f"尝试npm镜像: {registry}")
            result = _get_package_from_registry(client, package_name, registry, timeout)
            
            if result:
                logger.info(f"成功从 {registry} 获取包信息: {result.get('version')}")
                return result
            else:
                logger.warning(f"镜像 {registry} 返回空结果")
                
        except HttpTimeoutError:
            last_error = TimeoutError(f"NPM请求超时（{timeout}秒）: {registry}")
            logger.warning(f"镜像 {registry} 超时")
            continue
        except HttpConnectionError as e:
            last_error = NetworkError(f"网络连接失败: {e}")
            logger.warning(f"镜像 {registry} 连接失败: {e}")
            continue
        except (ParseError, NpmAPIError) as e:
            last_error = e
            logger.warning(f"镜像 {registry} 解析失败: {e}")
            continue
    
    # 所有镜像都失败了，抛出最后一个错误
    logger.error(f"所有npm镜像都失败了，最后错误: {last_error}")
    if last_error:
        raise last_error
    else:
        raise NetworkError("所有npm镜像都无法访问")


def _get_package_from_registry(client: HttpClient, package_name: str, registry: str, timeout: int) -> Optional[Dict[str, Any]]:
    """从npm registry获取包信息"""
    # 构建API URL - 获取最新版本
    # 处理scoped包名（如 @anthropic/sdk）
    encoded_name = package_name.replace("/", "%2F")
    api_url = f"{registry.rstrip('/')}/{encoded_name}/latest"
    
    resp = client.get(api_url, headers={"Accept": "application/json"}, timeout=timeout)
    
    if resp.status == 404:
        return None
    
    if resp.status >= 400:
        raise NetworkError(f"HTTP错误 {resp.status}")
    
    # 解析JSON响应
    try:
        data = resp.json()
    except (ValueError, Exception) as e:
        raise ParseError(f"无法解析NPM API响应: {e}")
    
    # 验证必需字段
    if "version" not in data:
        raise ParseError("NPM API响应缺少version字段")
    
    return {
        "name": data.get("name", package_name),
        "version": data.get("version", ""),
        "description": data.get("description", ""),
        "dist": data.get("dist", {}),
        "repository": data.get("repository", {}),
    }


def get_package_tarball_url(package_name: str, version: Optional[str] = None,
                            timeout: int = UPDATE_CHECK_TIMEOUT,
                            registry_mirrors: Optional[List[str]] = None) -> str:
    """获取npm包的tarball下载URL
    
    Args:
        package_name: npm包名称
        version: 版本号，如果为None则获取最新版本
        timeout: 请求超时时间（秒）
        registry_mirrors: npm镜像列表
        
    Returns:
        tarball下载URL
        
    Raises:
        NetworkError: 无法获取下载链接
    """
    package_info = get_package_info(package_name, timeout, registry_mirrors)
    
    if not package_info:
        raise NetworkError(f"无法获取 {package_name} 的包信息")
    
    dist = package_info.get("dist", {})
    tarball_url = dist.get("tarball", "")
    
    if not tarball_url:
        raise NetworkError(f"无法获取 {package_name} 的下载链接")
    
    return tarball_url


def extract_version_from_tag(tag_name: str) -> str:
    """从tag名称中提取版本号
    
    npm的版本通常格式为 "v1.0.0" 或 "1.0.0"
    此函数移除前导的 'v' 字符
    
    Args:
        tag_name: tag名称
        
    Returns:
        版本号字符串
    """
    if tag_name.startswith("v") or tag_name.startswith("V"):
        return tag_name[1:]
    return tag_name
