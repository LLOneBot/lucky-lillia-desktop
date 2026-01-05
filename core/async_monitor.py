"""异步资源监控器 - 统一管理所有后台异步任务"""

import asyncio
import logging
import os
import uuid
from typing import Optional, Dict, Callable, Any
import psutil

from utils.async_pmhq_client import AsyncPMHQClient, SelfInfo, DeviceInfo

logger = logging.getLogger(__name__)


class AsyncResourceMonitor:
    def __init__(self):
        self._pmhq_port: Optional[int] = None
        self._pmhq_client: Optional[AsyncPMHQClient] = None
        self._qq_pid: Optional[int] = None
        self._qq_resources: Dict[str, float] = {"cpu": 0.0, "memory": 0.0}
        self._qq_version: str = ""
        self._uin: Optional[str] = None
        self._nickname: Optional[str] = None
        self._running = False
        self._on_uin_callback: Optional[Callable[[str, str], None]] = None
    
    def set_pmhq_port(self, port: int):
        self._pmhq_port = port
        self._pmhq_client = AsyncPMHQClient(port, timeout=3)
    
    def set_uin_callback(self, callback: Callable[[str, str], None]):
        self._on_uin_callback = callback
    
    @property
    def qq_pid(self) -> Optional[int]:
        return self._qq_pid
    
    @property
    def qq_resources(self) -> Dict[str, float]:
        return self._qq_resources.copy()
    
    @property
    def qq_version(self) -> str:
        return self._qq_version
    
    @property
    def uin(self) -> Optional[str]:
        return self._uin
    
    async def start(self):
        self._running = True
    
    async def stop(self):
        self._running = False
        if self._pmhq_client:
            await self._pmhq_client.close()
    
    async def fetch_qq_process_info(self) -> Optional[int]:
        """异步获取 QQ 进程信息"""
        if self._qq_pid:
            is_running = await asyncio.to_thread(psutil.pid_exists, self._qq_pid)
            if is_running:
                await self._update_qq_resources(self._qq_pid)
                return self._qq_pid
            else:
                self._qq_pid = None
                self._qq_resources = {"cpu": 0.0, "memory": 0.0}
        
        if not self._pmhq_client:
            return None
        
        pid = await self._pmhq_client.fetch_qq_pid(echo=str(uuid.uuid4()))
        if pid:
            self._qq_pid = pid
            await self._update_qq_resources(pid)
            return pid
        
        self._qq_pid = None
        self._qq_resources = {"cpu": 0.0, "memory": 0.0}
        return None
    
    async def _update_qq_resources(self, pid: int):
        """异步更新 QQ 资源占用"""
        def get_resources():
            try:
                proc = psutil.Process(pid)
                if not proc.is_running():
                    return None
                cpu = proc.cpu_percent(interval=0.05)
                memory = proc.memory_info().rss / (1024 * 1024)
                return {"cpu": cpu, "memory": memory}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        
        result = await asyncio.to_thread(get_resources)
        if result:
            self._qq_resources = result
        else:
            self._qq_pid = None
            self._qq_resources = {"cpu": 0.0, "memory": 0.0}
    
    async def fetch_qq_version(self) -> str:
        """异步获取 QQ 版本"""
        if self._qq_version:
            return self._qq_version
        
        if not self._pmhq_client:
            return ""
        
        device_info = await self._pmhq_client.get_device_info()
        if device_info:
            self._qq_version = device_info.build_ver
        return self._qq_version
    
    async def fetch_uin_info(self) -> Optional[SelfInfo]:
        if not self._pmhq_client:
            return None
        
        info = await self._pmhq_client.fetch_self_info()
        if info and info.uin:
            uin_changed = self._uin != info.uin
            self._uin = info.uin
            self._nickname = info.nickname
            
            if uin_changed and self._on_uin_callback:
                self._on_uin_callback(info.uin, info.nickname)
            
            return info
        return None
    
    async def get_process_resources(self, pid: int) -> tuple:
        """异步获取进程资源占用"""
        def get_resources():
            try:
                proc = psutil.Process(pid)
                if not proc.is_running():
                    return 0.0, 0.0, False
                cpu = proc.cpu_percent(interval=0.05)
                mem = proc.memory_info().rss / 1024 / 1024
                return cpu, mem, True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return 0.0, 0.0, False
        
        return await asyncio.to_thread(get_resources)
