"""异步应用管理器 - 统一管理所有异步任务"""

import asyncio
import logging
from typing import Optional, Callable, List, Dict, Any

from core.async_log_collector import AsyncLogCollector, LogEntry
from core.async_monitor import AsyncResourceMonitor

logger = logging.getLogger(__name__)


class AsyncApp:
    """异步应用管理器，负责调度所有后台异步任务"""
    
    def __init__(self, log_collector: AsyncLogCollector, resource_monitor: AsyncResourceMonitor):
        self.log_collector = log_collector
        self.resource_monitor = resource_monitor
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # 回调函数
        self._on_logs_updated: Optional[Callable[[List[LogEntry]], Any]] = None
        self._on_resources_updated: Optional[Callable[[Dict[str, Any]], Any]] = None
    
    def set_logs_callback(self, callback: Callable[[List[LogEntry]], Any]):
        self._on_logs_updated = callback
    
    def set_resources_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self._on_resources_updated = callback
    
    async def start(self):
        """启动所有异步任务"""
        self._running = True
        await self.resource_monitor.start()
        
        self._tasks = [
            asyncio.create_task(self._log_consumer_loop()),
            asyncio.create_task(self._resource_monitor_loop()),
            asyncio.create_task(self._uin_fetch_loop()),
        ]
    
    async def stop(self):
        """停止所有异步任务"""
        self._running = False
        await self.resource_monitor.stop()
        self.log_collector.stop()
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
    
    async def _log_consumer_loop(self):
        """日志消费循环 - 从队列获取日志并触发回调"""
        while self._running:
            try:
                new_logs = await self.log_collector.process_pending_logs()
                if new_logs and self._on_logs_updated:
                    await self._on_logs_updated(new_logs)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"日志消费异常: {e}")
            
            await asyncio.sleep(0.2)
    
    async def _resource_monitor_loop(self):
        """资源监控循环"""
        while self._running:
            try:
                if self._on_resources_updated:
                    qq_pid = await self.resource_monitor.fetch_qq_process_info()
                    qq_version = await self.resource_monitor.fetch_qq_version()
                    
                    data = {
                        "qq_pid": qq_pid,
                        "qq_resources": self.resource_monitor.qq_resources,
                        "qq_version": qq_version,
                    }
                    await self._on_resources_updated(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"资源监控异常: {e}")
            
            await asyncio.sleep(3.0)
    
    async def _uin_fetch_loop(self):
        """UIN 获取循环"""
        max_attempts = 120
        attempt = 0
        
        while self._running and attempt < max_attempts:
            try:
                info = await self.resource_monitor.fetch_uin_info()
                if info and info.uin and info.nickname:
                    logger.info(f"获取到 UIN: {info.uin}, 昵称: {info.nickname}")
                    return
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"获取 UIN 异常: {e}")
            
            attempt += 1
            await asyncio.sleep(1.0)
