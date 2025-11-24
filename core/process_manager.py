"""进程管理模块 - 管理外部进程的生命周期"""

import subprocess
import os
from enum import Enum
from typing import Optional, Dict
import threading
import time


class ProcessStatus(Enum):
    """进程状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class ProcessManager:
    """管理外部进程的生命周期"""
    
    def __init__(self):
        """初始化进程管理器"""
        self._processes: Dict[str, subprocess.Popen] = {}
        self._status: Dict[str, ProcessStatus] = {
            "pmhq": ProcessStatus.STOPPED,
            "llonebot": ProcessStatus.STOPPED
        }
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        
    def start_pmhq(self, pmhq_path: str, config_path: str = "pmhq_config.json") -> bool:
        """启动PMHQ进程
        
        Args:
            pmhq_path: pmhq.exe的路径
            config_path: pmhq_config.json的路径
            
        Returns:
            启动成功返回True，失败返回False
        """
        with self._lock:
            # 检查是否已经在运行
            if self._status.get("pmhq") == ProcessStatus.RUNNING:
                return True
            
            # 验证可执行文件路径
            if not os.path.isfile(pmhq_path):
                self._status["pmhq"] = ProcessStatus.ERROR
                return False
            
            try:
                self._status["pmhq"] = ProcessStatus.STARTING
                
                # 启动进程
                process = subprocess.Popen(
                    [pmhq_path, "--config", config_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # 等待一小段时间确认进程启动成功
                time.sleep(0.5)
                if process.poll() is not None:
                    # 进程已经退出，启动失败
                    self._status["pmhq"] = ProcessStatus.ERROR
                    return False
                
                self._processes["pmhq"] = process
                self._status["pmhq"] = ProcessStatus.RUNNING
                
                # 启动监控线程
                self._start_monitoring()
                
                return True
                
            except (OSError, subprocess.SubprocessError) as e:
                self._status["pmhq"] = ProcessStatus.ERROR
                return False
    
    def start_llonebot(self, node_path: str, script_path: str) -> bool:
        """启动LLOneBot进程
        
        Args:
            node_path: node.exe的路径
            script_path: llonebot.js的路径
            
        Returns:
            启动成功返回True，失败返回False
        """
        with self._lock:
            # 检查是否已经在运行
            if self._status.get("llonebot") == ProcessStatus.RUNNING:
                return True
            
            # 验证可执行文件和脚本路径
            if not os.path.isfile(node_path):
                self._status["llonebot"] = ProcessStatus.ERROR
                return False
            
            if not os.path.isfile(script_path):
                self._status["llonebot"] = ProcessStatus.ERROR
                return False
            
            try:
                self._status["llonebot"] = ProcessStatus.STARTING
                
                # 启动进程
                process = subprocess.Popen(
                    [node_path, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # 等待一小段时间确认进程启动成功
                time.sleep(0.5)
                if process.poll() is not None:
                    # 进程已经退出，启动失败
                    self._status["llonebot"] = ProcessStatus.ERROR
                    return False
                
                self._processes["llonebot"] = process
                self._status["llonebot"] = ProcessStatus.RUNNING
                
                # 启动监控线程
                self._start_monitoring()
                
                return True
                
            except (OSError, subprocess.SubprocessError) as e:
                self._status["llonebot"] = ProcessStatus.ERROR
                return False
    
    def stop_process(self, process_name: str) -> bool:
        """停止指定进程
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
            
        Returns:
            停止成功返回True，失败返回False
        """
        with self._lock:
            if process_name not in self._processes:
                return True  # 进程不存在，视为已停止
            
            process = self._processes[process_name]
            
            # 检查进程是否已经停止
            if process.poll() is not None:
                del self._processes[process_name]
                self._status[process_name] = ProcessStatus.STOPPED
                return True
            
            try:
                self._status[process_name] = ProcessStatus.STOPPING
                
                # 尝试优雅地终止进程
                process.terminate()
                
                # 等待进程结束（最多3秒）
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # 如果进程没有响应，强制杀死
                    process.kill()
                    process.wait()
                
                del self._processes[process_name]
                self._status[process_name] = ProcessStatus.STOPPED
                return True
                
            except Exception as e:
                self._status[process_name] = ProcessStatus.ERROR
                return False
    
    def get_process_status(self, process_name: str) -> ProcessStatus:
        """获取进程状态
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
        
        Returns:
            ProcessStatus枚举值 (RUNNING, STOPPED, ERROR)
        """
        with self._lock:
            return self._status.get(process_name, ProcessStatus.STOPPED)
    
    def stop_all(self) -> None:
        """停止所有托管进程"""
        # 停止监控线程
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)
        
        # 停止所有进程
        process_names = list(self._processes.keys())
        for process_name in process_names:
            self.stop_process(process_name)
    
    def get_process(self, process_name: str) -> Optional[subprocess.Popen]:
        """获取进程对象（用于日志收集器附加）
        
        Args:
            process_name: 进程名称
            
        Returns:
            subprocess.Popen对象，如果进程不存在返回None
        """
        with self._lock:
            return self._processes.get(process_name)
    
    def _start_monitoring(self) -> None:
        """启动进程监控线程"""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
            self._monitor_thread.start()
    
    def _monitor_processes(self) -> None:
        """监控进程状态，检测异常退出"""
        while self._monitoring:
            time.sleep(1)  # 每秒检查一次
            
            with self._lock:
                for process_name, process in list(self._processes.items()):
                    # 检查进程是否已退出
                    if process.poll() is not None:
                        # 进程已退出
                        if self._status[process_name] == ProcessStatus.RUNNING:
                            # 这是异常退出
                            self._status[process_name] = ProcessStatus.ERROR
                        del self._processes[process_name]
