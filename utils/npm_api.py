"""NPM Registry API封装"""

import re
import logging
import concurrent.futures
from typing import Optional, Dict, Any, List, Tuple
from utils.constants import UPDATE_CHECK_TIMEOUT, NPM_OFFICIAL_REGISTRY, NPM_REGISTRY_MIRRORS
from utils.http_client import HttpClient, TimeoutError as HttpTimeoutError, ConnectionError as HttpConnectionError


class NpmAPIError(Exception):
    pass


class NetworkError(NpmAPIError):
    pass


class TimeoutError(NpmAPIError):
    pass


class ParseError(NpmAPIError):
    pass


logger = logging.getLogger(__name__)


def _fetch_from_registry(client: HttpClient, package_name: str, registry: str, 
                         timeout: int) -> Tuple[str, Optional[Dict[str, Any]], Optional[Exception]]:
    """从单个registry获取包信息，返回 (registry, result, error)"""
    try:
        result = _get_package_from_registry(client, package_name, registry, timeout)
        return (registry, result, None)
    except Exception as e:
        return (registry, None, e)


def get_package_info(package_name: str, timeout: int = UPDATE_CHECK_TIMEOUT,
                     registry_mirrors: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    获取npm包信息
    策略：先从官方源获取，失败则并发从所有镜像源获取
    """
    if registry_mirrors is None:
        registry_mirrors = NPM_REGISTRY_MIRRORS.copy()
    
    client = HttpClient(timeout=timeout)
    
    # 1. 先尝试官方源
    logger.info(f"获取 {package_name} 的npm包信息，先尝试官方源")
    try:
        result = _get_package_from_registry(client, package_name, NPM_OFFICIAL_REGISTRY, timeout)
        if result:
            logger.info(f"成功从官方源获取包信息: {result.get('version')}")
            result['_source_registry'] = NPM_OFFICIAL_REGISTRY
            return result
    except Exception as e:
        logger.warning(f"官方源获取失败: {e}")
    
    # 2. 官方源失败，并发从所有镜像源获取
    logger.info(f"官方源失败，并发尝试镜像源: {registry_mirrors}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(registry_mirrors)) as executor:
        futures = {
            executor.submit(_fetch_from_registry, client, package_name, mirror, timeout): mirror
            for mirror in registry_mirrors
        }
        
        for future in concurrent.futures.as_completed(futures):
            registry, result, error = future.result()
            if result:
                logger.info(f"成功从镜像 {registry} 获取包信息: {result.get('version')}")
                result['_source_registry'] = registry
                return result
            elif error:
                logger.warning(f"镜像 {registry} 失败: {error}")
    
    raise NetworkError("所有npm源都无法获取包信息")


def _get_package_from_registry(client: HttpClient, package_name: str, registry: str, 
                               timeout: int) -> Optional[Dict[str, Any]]:
    encoded_name = package_name.replace("/", "%2F")
    api_url = f"{registry.rstrip('/')}/{encoded_name}/latest"
    
    resp = client.get(api_url, headers={"Accept": "application/json"}, timeout=timeout)
    
    if resp.status == 404:
        return None
    
    if resp.status >= 400:
        raise NetworkError(f"HTTP错误 {resp.status}")
    
    try:
        data = resp.json()
    except (ValueError, Exception) as e:
        raise ParseError(f"无法解析NPM API响应: {e}")
    
    if "version" not in data:
        raise ParseError("NPM API响应缺少version字段")
    
    return {
        "name": data.get("name", package_name),
        "version": data.get("version", ""),
        "description": data.get("description", ""),
        "dist": data.get("dist", {}),
        "repository": data.get("repository", {}),
    }


def _check_version_exists(client: HttpClient, package_name: str, version: str, 
                          registry: str, timeout: int) -> Tuple[str, bool]:
    """检查指定版本是否存在于registry，返回 (registry, exists)"""
    try:
        encoded_name = package_name.replace("/", "%2F")
        api_url = f"{registry.rstrip('/')}/{encoded_name}/{version}"
        resp = client.get(api_url, headers={"Accept": "application/json"}, timeout=timeout)
        return (registry, resp.status == 200)
    except Exception:
        return (registry, False)


def get_best_download_registry(package_name: str, version: str, 
                               timeout: int = UPDATE_CHECK_TIMEOUT,
                               registry_mirrors: Optional[List[str]] = None) -> str:
    """
    获取最佳下载源
    策略：并发检查所有镜像源是否存在该版本，返回第一个存在的；都不存在则返回官方源
    """
    if registry_mirrors is None:
        registry_mirrors = NPM_REGISTRY_MIRRORS.copy()
    
    client = HttpClient(timeout=timeout)
    logger.info(f"查找 {package_name}@{version} 的最佳下载源")
    
    # 并发检查所有镜像源
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(registry_mirrors)) as executor:
        futures = {
            executor.submit(_check_version_exists, client, package_name, version, mirror, timeout): mirror
            for mirror in registry_mirrors
        }
        
        for future in concurrent.futures.as_completed(futures):
            registry, exists = future.result()
            if exists:
                logger.info(f"镜像 {registry} 存在版本 {version}")
                return registry
            else:
                logger.debug(f"镜像 {registry} 不存在版本 {version}")
    
    # 所有镜像都没有，返回官方源
    logger.info(f"所有镜像都不存在版本 {version}，使用官方源")
    return NPM_OFFICIAL_REGISTRY


def get_package_tarball_url(package_name: str, version: Optional[str] = None,
                            timeout: int = UPDATE_CHECK_TIMEOUT,
                            registry_mirrors: Optional[List[str]] = None) -> str:
    """
    获取包的下载URL
    策略：
    1. 先获取最新版本信息
    2. 查找存在该版本的镜像源
    3. 返回该镜像源的tarball URL
    """
    # 获取包信息（会返回最新版本）
    package_info = get_package_info(package_name, timeout, registry_mirrors)
    
    if not package_info:
        raise NetworkError(f"无法获取 {package_name} 的包信息")
    
    target_version = version or package_info.get("version", "")
    if not target_version:
        raise NetworkError(f"无法确定 {package_name} 的版本")
    
    # 查找最佳下载源
    best_registry = get_best_download_registry(package_name, target_version, timeout, registry_mirrors)
    
    # 构造tarball URL
    dist = package_info.get("dist", {})
    original_tarball = dist.get("tarball", "")
    
    if not original_tarball:
        # 手动构造URL
        encoded_name = package_name.replace("/", "%2F")
        tarball_url = f"{best_registry.rstrip('/')}/{encoded_name}/-/{package_name.split('/')[-1]}-{target_version}.tgz"
    else:
        # 替换registry
        tarball_url = original_tarball
        for registry in [NPM_OFFICIAL_REGISTRY] + (registry_mirrors or NPM_REGISTRY_MIRRORS):
            if registry in original_tarball:
                tarball_url = original_tarball.replace(registry, best_registry)
                break
    
    logger.info(f"最终下载URL: {tarball_url}")
    return tarball_url


def extract_version_from_tag(tag_name: str) -> str:
    if tag_name.startswith("v") or tag_name.startswith("V"):
        return tag_name[1:]
    return tag_name
