"""日志收集模块 - 收集和管理进程日志输出"""

import subprocess
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Callable, Dict


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    process_name: str
    level: str  # "stdout" 或 "stderr"
    message: str


class LogCollector:
    """收集和管理进程日志输出"""
    
    def __init__(self, max_lines: int = 1000):
        """初始化日志收集器
        
        Args:
            max_lines: 最大保留日志行数
        """
        self.max_lines = max_lines
        self._logs: deque = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[LogEntry], None]] = []
        self._reader_threads: Dict[str, List[threading.Thread]] = {}
        
    def attach_process(self, process_name: str, process: subprocess.Popen) -> None:
        """附加到进程的输出流
        
        Args:
            process_name: 进程名称
            process: subprocess.Popen对象
        """
        # 创建线程读取stdout
        stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(process_name, process.stdout, "stdout"),
            daemon=True
        )
        stdout_thread.start()
        
        # 创建线程读取stderr
        stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(process_name, process.stderr, "stderr"),
            daemon=True
        )
        stderr_thread.start()
        
        # 保存线程引用
        self._reader_threads[process_name] = [stdout_thread, stderr_thread]
    
    def _read_stream(self, process_name: str, stream, level: str) -> None:
        """读取进程输出流
        
        Args:
            process_name: 进程名称
            stream: 输出流对象
            level: 日志级别 ("stdout" 或 "stderr")
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"开始读取 {process_name} 的 {level} 流")
        
        try:
            # 使用 readline() 而不是迭代器，避免缓冲延迟
            while True:
                line = stream.readline()
                if not line:  # 流结束
                    break
                line = line.rstrip('\n\r')
                if line:  # 确保不是空行
                    entry = LogEntry(
                        timestamp=datetime.now(),
                        process_name=process_name,
                        level=level,
                        message=line
                    )
                    
                    logger.debug(f"收到日志: [{process_name}][{level}] {line[:100]}")
                    
                    with self._lock:
                        self._logs.append(entry)
                    
                    # 调用回调函数
                    for callback in self._callbacks:
                        try:
                            callback(entry)
                        except Exception:
                            pass  # 忽略回调中的错误
        except Exception:
            pass  # 流关闭或其他错误
    
    def get_logs(self, process_name: Optional[str] = None) -> List[LogEntry]:
        """获取日志条目
        
        Args:
            process_name: 进程名称，None表示获取所有日志
            
        Returns:
            日志条目列表
        """
        with self._lock:
            if process_name is None:
                return list(self._logs)
            else:
                return [entry for entry in self._logs if entry.process_name == process_name]
    
    def clear_logs(self, process_name: Optional[str] = None) -> None:
        """清空日志
        
        Args:
            process_name: 进程名称，None表示清空所有日志
        """
        with self._lock:
            if process_name is None:
                self._logs.clear()
            else:
                # 只保留不匹配的日志
                self._logs = deque(
                    (entry for entry in self._logs if entry.process_name != process_name),
                    maxlen=self.max_lines
                )
    
    def set_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """设置新日志回调函数，用于实时更新UI
        
        Args:
            callback: 回调函数，接收LogEntry参数
        """
        self._callbacks.append(callback)
    
    def add_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """添加新日志回调函数（set_callback的别名）
        
        Args:
            callback: 回调函数，接收LogEntry参数
        """
        self._callbacks.append(callback)
