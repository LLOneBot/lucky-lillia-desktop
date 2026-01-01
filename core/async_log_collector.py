"""异步日志收集模块 - 使用 asyncio.Queue 实现生产者消费者模式"""

import asyncio
import logging
import subprocess
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Callable, Dict

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    timestamp: datetime
    process_name: str
    level: str
    message: str


class AsyncLogCollector:
    def __init__(self, max_lines: int = 1000):
        self.max_lines = max_lines
        self._logs: deque = deque(maxlen=max_lines)
        self._queue: Optional[asyncio.Queue] = None
        self._callbacks: List[Callable[[LogEntry], None]] = []
        self._reader_threads: Dict[str, List[threading.Thread]] = {}
        self._running = True
    
    def _ensure_queue(self):
        if self._queue is None:
            try:
                self._queue = asyncio.Queue()
            except RuntimeError:
                pass
    
    def _push_log(self, entry: LogEntry):
        """从任意线程安全地推送日志到队列"""
        # 同时写入 deque（线程安全）
        self._logs.append(entry)
        self._write_to_log_file(entry)
        
        # 尝试推送到队列（如果队列已初始化）
        if self._queue is not None:
            try:
                self._queue.put_nowait(entry)
            except (asyncio.QueueFull, RuntimeError):
                pass
    
    async def consume_logs(self) -> Optional[LogEntry]:
        """主线程异步消费日志，返回一条日志或 None（超时）"""
        self._ensure_queue()
        if self._queue is None:
            return None
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None
    
    async def process_pending_logs(self) -> List[LogEntry]:
        """处理所有待处理的日志，返回新增的日志列表"""
        self._ensure_queue()
        if self._queue is None:
            return []
        new_entries = []
        while True:
            try:
                entry = self._queue.get_nowait()
                new_entries.append(entry)
            except asyncio.QueueEmpty:
                break
        return new_entries
    
    def _write_to_log_file(self, entry: LogEntry) -> None:
        log_level = logging.INFO if entry.level == "stdout" else logging.WARNING
        logger.log(log_level, f"[{entry.process_name}] {entry.message}")
    
    def attach_process(self, process_name: str, process: subprocess.Popen) -> None:
        stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(process_name, process.stdout, "stdout"),
            daemon=True
        )
        stdout_thread.start()
        
        stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(process_name, process.stderr, "stderr"),
            daemon=True
        )
        stderr_thread.start()
        
        self._reader_threads[process_name] = [stdout_thread, stderr_thread]
    
    def _read_stream(self, process_name: str, stream, level: str) -> None:
        logger.info(f"开始读取 {process_name} 的 {level} 流")
        try:
            while self._running:
                line = stream.readline()
                if not line:
                    logger.info(f"{process_name} 的 {level} 流已结束")
                    break
                
                line = line.rstrip('\n\r')
                if line:
                    entry = LogEntry(
                        timestamp=datetime.now(),
                        process_name=process_name,
                        level=level,
                        message=line
                    )
                    self._push_log(entry)
        except Exception as e:
            logger.info(f"读取 {process_name} 的 {level} 流时发生异常: {e}")
    
    def get_logs(self, process_name: Optional[str] = None) -> List[LogEntry]:
        if process_name is None:
            return list(self._logs)
        return [e for e in self._logs if e.process_name == process_name]
    
    def get_log_count(self) -> int:
        return len(self._logs)
    
    def get_recent_logs(self, count: int) -> List[LogEntry]:
        if count >= len(self._logs):
            return list(self._logs)
        from itertools import islice
        start_idx = len(self._logs) - count
        return list(islice(self._logs, start_idx, None))
    
    def clear_logs(self, process_name: Optional[str] = None) -> None:
        if process_name is None:
            self._logs.clear()
        else:
            self._logs = deque(
                (e for e in self._logs if e.process_name != process_name),
                maxlen=self.max_lines
            )
    
    def stop(self):
        self._running = False
    
    def reset(self):
        self._running = True
