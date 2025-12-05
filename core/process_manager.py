"""进程管理模块 - 管理外部进程的生命周期"""

import subprocess
import os
import sys
import logging
import ctypes
import json
import uuid
from enum import Enum
from typing import Optional, Dict, Callable
import threading
import time

from utils.port import get_available_port
from utils.http_client import HttpClient, HttpError

logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """检查当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


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
        self._admin_pids: Dict[str, int] = {}  # 存储以管理员权限启动的进程PID
        self._status: Dict[str, ProcessStatus] = {
            "pmhq": ProcessStatus.STOPPED,
            "llonebot": ProcessStatus.STOPPED
        }
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._pmhq_port: Optional[int] = None  # 存储PMHQ使用的端口
        self._uin: Optional[str] = None  # 存储获取到的QQ号
        self._nickname: Optional[str] = None  # 存储获取到的昵称
        self._uin_callback: Optional[Callable[[str, str], None]] = None  # uin获取成功的回调(uin, nickname)
        self._uin_fetch_thread: Optional[threading.Thread] = None
        self._qq_pid: Optional[int] = None  # 存储QQ进程的PID
        self._qq_resources: Dict[str, float] = {"cpu": 0.0, "memory": 0.0}  # QQ进程资源占用
        self._qq_process: Optional["psutil.Process"] = None  # 缓存QQ进程对象（用于正确计算CPU）
        self._http_client: Optional[HttpClient] = None  # 共享的HTTP客户端实例
        
    def start_pmhq(self, pmhq_path: str, config_path: str = "pmhq_config.json", 
                   qq_path: str = "", auto_login_qq: str = "", headless: bool = False) -> bool:
        """启动PMHQ进程
        
        Args:
            pmhq_path: pmhq.exe的路径
            config_path: pmhq_config.json的路径
            qq_path: QQ可执行文件的路径（可选）
            auto_login_qq: 自动登录的QQ号（可选）
            headless: 是否启用无头模式（可选）
            
        Returns:
            启动成功返回True，失败返回False
        """
        logger.info(f"尝试启动PMHQ: path={pmhq_path}, config={config_path}, qq_path={qq_path}, auto_login_qq={auto_login_qq}, headless={headless}")
        
        with self._lock:
            # 检查是否已经在运行
            if self._status.get("pmhq") == ProcessStatus.RUNNING:
                logger.info("PMHQ已经在运行中")
                return True
            
            # 验证可执行文件路径
            if not os.path.isfile(pmhq_path):
                logger.error(f"PMHQ可执行文件不存在: {pmhq_path}")
                self._status["pmhq"] = ProcessStatus.ERROR
                return False
            
            # 获取绝对路径
            abs_pmhq_path = os.path.abspath(pmhq_path)
            abs_config_path = os.path.abspath(config_path)
            working_dir = os.path.dirname(abs_pmhq_path)
            
            logger.info(f"PMHQ绝对路径: {abs_pmhq_path}")
            logger.info(f"配置文件绝对路径: {abs_config_path}")
            logger.info(f"工作目录: {working_dir}")
            
            try:
                self._status["pmhq"] = ProcessStatus.STARTING
                
                # 获取可用端口
                self._pmhq_port = get_available_port(init_port=13000)
                logger.info(f"PMHQ使用端口: {self._pmhq_port}")
                
                # 启动进程，添加 --port 参数
                cmd = [abs_pmhq_path, f"--port={self._pmhq_port}"]
                # 如果指定了QQ路径，添加 --qq-path 参数
                if qq_path and os.path.isfile(qq_path):
                    cmd.append(f"--qq-path={qq_path}")
                # 如果指定了自动登录QQ号，添加 --qq 参数
                if auto_login_qq:
                    cmd.append(f"--qq={auto_login_qq}")
                # 如果启用无头模式，添加 --headless 参数
                if headless:
                    cmd.append("--headless")
                logger.info(f"启动命令: {cmd}")
                
                # 设置 CREATE_NO_WINDOW 标志，避免弹出控制台窗口
                creation_flags = 0
                if sys.platform == 'win32':
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                # 设置环境变量，禁用 Python 子进程的输出缓冲
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
                
                # Windows 中文系统使用 GBK 编码
                import locale
                system_encoding = locale.getpreferredencoding(False)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    cwd=working_dir,
                    creationflags=creation_flags,
                    env=env,
                    encoding=system_encoding,
                    errors='replace'
                )
                
                logger.info(f"进程已创建，PID: {process.pid}")
                
                # 等待一小段时间确认进程启动成功
                time.sleep(0.5)
                return_code = process.poll()
                if return_code is not None:
                    # 进程已经退出，启动失败
                    stdout, stderr = process.communicate(timeout=1)
                    logger.error(f"PMHQ进程立即退出，返回码: {return_code}")
                    logger.error(f"PMHQ stdout: {stdout}")
                    logger.error(f"PMHQ stderr: {stderr}")
                    self._status["pmhq"] = ProcessStatus.ERROR
                    return False
                
                self._processes["pmhq"] = process
                self._status["pmhq"] = ProcessStatus.RUNNING
                logger.info(f"PMHQ启动成功，PID: {process.pid}")
                
                # 启动监控线程
                self._start_monitoring()
                
                # 启动获取uin的线程
                self._start_uin_fetch()
                
                return True
                
            except OSError as e:
                # 检查是否是需要管理员权限的错误 (WinError 740)
                if hasattr(e, 'winerror') and e.winerror == 740:
                    if is_admin():
                        # 当前已经是管理员权限，但仍然失败，可能是其他原因
                        logger.error("当前已是管理员权限，但PMHQ仍然启动失败")
                        self._status["pmhq"] = ProcessStatus.ERROR
                        return False
                    else:
                        logger.warning("PMHQ需要管理员权限，尝试以管理员身份启动...")
                        logger.info("提示：如果以管理员身份运行本管理器，可以获取PMHQ的日志输出")
                        return self._start_pmhq_as_admin(abs_pmhq_path, working_dir, qq_path, auto_login_qq, headless)
                else:
                    logger.error(f"启动PMHQ时发生OSError: {e}", exc_info=True)
                    self._status["pmhq"] = ProcessStatus.ERROR
                    return False
            except subprocess.SubprocessError as e:
                logger.error(f"启动PMHQ时发生异常: {e}", exc_info=True)
                self._status["pmhq"] = ProcessStatus.ERROR
                return False
    
    def _start_pmhq_with_pty(self, pmhq_path: str, cmd_args: list, working_dir: str) -> bool:
        """使用伪终端启动PMHQ（可以实时获取输出）
        
        Args:
            pmhq_path: PMHQ可执行文件的绝对路径
            cmd_args: 命令行参数列表
            working_dir: 工作目录
            
        Returns:
            启动成功返回True，失败返回False
        """
        import winpty
        
        # 构建命令行
        cmd_line = f'"{pmhq_path}" ' + ' '.join(cmd_args)
        logger.info(f"使用 winpty 启动: {cmd_line}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 创建伪终端进程
        pty_process = winpty.PtyProcess.spawn(
            cmd_line,
            cwd=working_dir,
            env=env
        )
        
        logger.info(f"PTY进程已创建，PID: {pty_process.pid}")
        
        # 等待一小段时间确认进程启动成功
        time.sleep(0.5)
        if not pty_process.isalive():
            logger.error("PMHQ PTY进程立即退出")
            self._status["pmhq"] = ProcessStatus.ERROR
            return False
        
        # 保存 PTY 进程
        self._pty_processes = getattr(self, '_pty_processes', {})
        self._pty_processes["pmhq"] = pty_process
        self._status["pmhq"] = ProcessStatus.RUNNING
        logger.info(f"PMHQ (PTY) 启动成功，PID: {pty_process.pid}")
        
        # 启动监控线程
        self._start_monitoring()
        
        # 启动获取uin的线程
        self._start_uin_fetch()
        
        return True
    
    def _start_pmhq_as_admin(self, pmhq_path: str, working_dir: str, 
                              qq_path: str = "", auto_login_qq: str = "", headless: bool = False) -> bool:
        """以管理员权限启动PMHQ（使用ShellExecute）
        
        注意：使用ShellExecute启动的进程无法获取PID和stdout/stderr
        
        Args:
            pmhq_path: PMHQ可执行文件的绝对路径
            working_dir: 工作目录
            qq_path: QQ可执行文件的路径（可选）
            auto_login_qq: 自动登录的QQ号（可选）
            headless: 是否启用无头模式（可选）
            
        Returns:
            启动成功返回True，失败返回False
        """
        try:
            import ctypes
            
            # 获取可用端口（如果还没有获取）
            if self._pmhq_port is None:
                self._pmhq_port = get_available_port(init_port=13000)
                logger.info(f"PMHQ使用端口: {self._pmhq_port}")
            
            # 构建参数字符串
            params = f"--port={self._pmhq_port}"
            if qq_path and os.path.isfile(qq_path):
                params += f' --qq-path="{qq_path}"'
            if auto_login_qq:
                params += f' --qq={auto_login_qq}'
            if headless:
                params += ' --headless'
            
            # 使用ShellExecuteW以管理员权限启动
            # 参数: hwnd, operation, file, parameters, directory, show
            result = ctypes.windll.shell32.ShellExecuteW(
                None,           # hwnd
                "runas",        # operation - 请求管理员权限
                pmhq_path,      # file
                params,         # parameters - 添加端口参数和QQ路径
                working_dir,    # directory
                1               # SW_SHOWNORMAL
            )
            
            # ShellExecuteW 返回值 > 32 表示成功
            if result > 32:
                logger.info(f"PMHQ以管理员权限启动成功 (ShellExecute返回: {result})")
                # 注意：使用ShellExecute无法获取进程PID
                # 我们需要通过进程名查找PID
                time.sleep(1)  # 等待进程启动
                
                # 尝试通过进程名查找PID
                pid = self._find_process_pid_by_name("pmhq")
                if pid:
                    logger.info(f"找到PMHQ进程，PID: {pid}")
                    # 创建一个虚拟的进程对象来存储PID
                    self._admin_pids["pmhq"] = pid
                    self._status["pmhq"] = ProcessStatus.RUNNING
                    self._start_monitoring()
                    self._start_uin_fetch()
                    return True
                else:
                    logger.warning("PMHQ已启动但无法获取PID")
                    self._status["pmhq"] = ProcessStatus.RUNNING
                    self._start_uin_fetch()
                    return True
            else:
                logger.error(f"以管理员权限启动PMHQ失败，ShellExecute返回: {result}")
                self._status["pmhq"] = ProcessStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"以管理员权限启动PMHQ时发生异常: {e}", exc_info=True)
            self._status["pmhq"] = ProcessStatus.ERROR
            return False
    
    def _find_process_pid_by_name(self, name: str) -> Optional[int]:
        """通过进程名查找PID
        
        Args:
            name: 进程名（不区分大小写，不需要.exe后缀）
            
        Returns:
            找到返回PID，否则返回None
        """
        try:
            import psutil
            name_lower = name.lower()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if name_lower in proc_name:
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"查找进程PID时发生异常: {e}")
        return None
    
    def start_llonebot(self, node_path: str, script_path: str) -> bool:
        """启动LLOneBot进程
        
        Args:
            node_path: node.exe的路径
            script_path: llonebot.js的路径
            
        Returns:
            启动成功返回True，失败返回False
        """
        logger.info(f"尝试启动LLOneBot: node={node_path}, script={script_path}")
        
        with self._lock:
            # 检查是否已经在运行
            if self._status.get("llonebot") == ProcessStatus.RUNNING:
                logger.info("LLOneBot已经在运行中")
                return True
            
            # 验证可执行文件和脚本路径
            if not os.path.isfile(node_path):
                logger.error(f"Node.js可执行文件不存在: {node_path}")
                self._status["llonebot"] = ProcessStatus.ERROR
                return False
            
            if not os.path.isfile(script_path):
                logger.error(f"LLOneBot脚本文件不存在: {script_path}")
                self._status["llonebot"] = ProcessStatus.ERROR
                return False
            
            # 获取绝对路径
            abs_node_path = os.path.abspath(node_path)
            abs_script_path = os.path.abspath(script_path)
            working_dir = os.path.dirname(abs_script_path)
            
            logger.info(f"Node.js绝对路径: {abs_node_path}")
            logger.info(f"脚本绝对路径: {abs_script_path}")
            logger.info(f"工作目录: {working_dir}")
            
            try:
                self._status["llonebot"] = ProcessStatus.STARTING
                
                # 启动进程，添加 --pmhq-port 参数传递PMHQ端口
                cmd = [abs_node_path, abs_script_path]
                if self._pmhq_port is not None:
                    cmd.extend(["--", f"--pmhq-port={self._pmhq_port}"])
                logger.info(f"启动命令: {cmd}")
                
                # 设置 CREATE_NO_WINDOW 标志，避免弹出控制台窗口
                creation_flags = 0
                if sys.platform == 'win32':
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                # Node.js 输出使用 UTF-8 编码
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    cwd=working_dir,
                    creationflags=creation_flags,
                    encoding='utf-8',
                    errors='replace'
                )
                
                logger.info(f"进程已创建，PID: {process.pid}")
                
                # 等待一小段时间确认进程启动成功
                time.sleep(0.5)
                return_code = process.poll()
                if return_code is not None:
                    # 进程已经退出，启动失败
                    stdout, stderr = process.communicate(timeout=1)
                    logger.error(f"LLOneBot进程立即退出，返回码: {return_code}")
                    logger.error(f"LLOneBot stdout: {stdout}")
                    logger.error(f"LLOneBot stderr: {stderr}")
                    self._status["llonebot"] = ProcessStatus.ERROR
                    return False
                
                self._processes["llonebot"] = process
                self._status["llonebot"] = ProcessStatus.RUNNING
                logger.info(f"LLOneBot启动成功，PID: {process.pid}")
                
                # 启动监控线程
                self._start_monitoring()
                
                return True
                
            except (OSError, subprocess.SubprocessError) as e:
                logger.error(f"启动LLOneBot时发生异常: {e}", exc_info=True)
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
            # 先检查是否在 PTY 进程字典中
            pty_processes = getattr(self, '_pty_processes', {})
            if process_name in pty_processes:
                pty_process = pty_processes[process_name]
                try:
                    self._status[process_name] = ProcessStatus.STOPPING
                    logger.info(f"正在停止 PTY 进程 {process_name}...")
                    
                    if pty_process.isalive():
                        # 使用 psutil 终止进程
                        import psutil
                        try:
                            proc = psutil.Process(pty_process.pid)
                            proc.terminate()
                            proc.wait(timeout=1.5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        except psutil.NoSuchProcess:
                            pass
                    
                    del pty_processes[process_name]
                    self._status[process_name] = ProcessStatus.STOPPED
                    logger.info(f"PTY 进程 {process_name} 已停止")
                    return True
                except Exception as e:
                    logger.error(f"停止 PTY 进程 {process_name} 失败: {e}")
                    self._status[process_name] = ProcessStatus.ERROR
                    return False
            
            # 再检查是否在普通进程字典中
            if process_name in self._processes:
                process = self._processes[process_name]
                
                # 检查进程是否已经停止
                if process.poll() is not None:
                    del self._processes[process_name]
                    self._status[process_name] = ProcessStatus.STOPPED
                    return True
                
                try:
                    self._status[process_name] = ProcessStatus.STOPPING
                    logger.info(f"正在停止进程 {process_name}...")
                    
                    # 尝试优雅地终止进程
                    process.terminate()
                    
                    # 等待进程结束（最多1.5秒，更新时需要快速退出）
                    try:
                        process.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        # 如果进程没有响应，强制杀死
                        logger.warning(f"进程 {process_name} 没有响应，强制终止")
                        process.kill()
                        process.wait(timeout=1)  # 强制杀死后最多等待1秒
                    
                    del self._processes[process_name]
                    self._status[process_name] = ProcessStatus.STOPPED
                    logger.info(f"进程 {process_name} 已停止")
                    return True
                    
                except Exception as e:
                    logger.error(f"停止进程 {process_name} 失败: {e}")
                    self._status[process_name] = ProcessStatus.ERROR
                    return False
            
            # 检查是否在管理员进程字典中
            elif process_name in self._admin_pids:
                admin_pid = self._admin_pids[process_name]
                try:
                    import psutil
                    self._status[process_name] = ProcessStatus.STOPPING
                    logger.info(f"正在停止管理员进程 {process_name} (PID: {admin_pid})...")
                    
                    # 使用psutil终止进程
                    proc = psutil.Process(admin_pid)
                    proc.terminate()
                    
                    # 等待进程结束（最多1.5秒，更新时需要快速退出）
                    try:
                        proc.wait(timeout=1.5)
                    except psutil.TimeoutExpired:
                        logger.warning(f"管理员进程 {process_name} 没有响应，强制终止")
                        proc.kill()
                    
                    del self._admin_pids[process_name]
                    self._status[process_name] = ProcessStatus.STOPPED
                    logger.info(f"管理员进程 {process_name} 已停止")
                    return True
                    
                except psutil.NoSuchProcess:
                    # 进程已经不存在
                    del self._admin_pids[process_name]
                    self._status[process_name] = ProcessStatus.STOPPED
                    return True
                except Exception as e:
                    logger.error(f"停止管理员进程 {process_name} 失败: {e}")
                    self._status[process_name] = ProcessStatus.ERROR
                    return False
            
            # 进程不存在，视为已停止
            return True
    
    def get_process_status(self, process_name: str) -> ProcessStatus:
        """获取进程状态
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
        
        Returns:
            ProcessStatus枚举值 (RUNNING, STOPPED, ERROR)
        """
        with self._lock:
            return self._status.get(process_name, ProcessStatus.STOPPED)
    
    def stop_all(self, stop_qq: bool = True) -> None:
        """停止所有托管进程
        
        Args:
            stop_qq: 是否同时停止QQ进程，默认为True
        """
        # 检查是否有任何进程在运行
        pty_processes = getattr(self, '_pty_processes', {})
        has_processes = bool(self._processes or self._admin_pids or pty_processes)
        
        if not has_processes and not (stop_qq and self._qq_pid):
            # 没有运行的进程，快速退出
            logger.info("没有运行的进程，跳过清理")
            self._monitoring = False
            return
        
        logger.info(f"停止所有托管进程... (stop_qq={stop_qq})")
        
        # 停止监控线程
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)
        
        # 停止所有普通进程
        process_names = list(self._processes.keys())
        for process_name in process_names:
            self.stop_process(process_name)
        
        # 停止所有管理员进程
        admin_process_names = list(self._admin_pids.keys())
        for process_name in admin_process_names:
            self.stop_process(process_name)
        
        # 停止QQ进程
        if stop_qq and self._qq_pid:
            try:
                import psutil
                proc = psutil.Process(self._qq_pid)
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    logger.warning(f"QQ进程没有响应，强制终止")
                    proc.kill()
                logger.info(f"已终止QQ进程 (PID: {self._qq_pid})")
            except psutil.NoSuchProcess:
                logger.debug(f"QQ进程 {self._qq_pid} 已不存在")
            except Exception as e:
                logger.warning(f"终止QQ进程失败: {e}")
            finally:
                self._qq_pid = None
                self._qq_process = None
        
        logger.info("所有进程已停止")
    
    def wait_all_stopped(self, timeout: float = 10.0) -> bool:
        """等待所有进程完全退出
        
        Args:
            timeout: 最大等待时间（秒），默认10秒
            
        Returns:
            所有进程都已退出返回True，超时返回False
        """
        import psutil
        
        start_time = time.time()
        check_interval = 0.2  # 每200ms检查一次
        
        while time.time() - start_time < timeout:
            all_stopped = True
            
            # 检查PMHQ状态
            if self._status.get("pmhq") == ProcessStatus.RUNNING:
                all_stopped = False
            
            # 检查LLOneBot状态
            if self._status.get("llonebot") == ProcessStatus.RUNNING:
                all_stopped = False
            
            # 检查普通进程
            for name, proc in list(self._processes.items()):
                if proc.poll() is None:  # 进程仍在运行
                    all_stopped = False
                    break
            
            # 检查管理员进程
            for name, pid in list(self._admin_pids.items()):
                try:
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.is_running():
                            all_stopped = False
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 检查QQ进程
            if self._qq_pid:
                try:
                    if psutil.pid_exists(self._qq_pid):
                        all_stopped = False
                except:
                    pass
            
            if all_stopped:
                logger.info(f"所有进程已完全退出，耗时 {time.time() - start_time:.2f} 秒")
                return True
            
            time.sleep(check_interval)
        
        logger.warning(f"等待进程退出超时（{timeout}秒）")
        return False
    
    def get_process(self, process_name: str) -> Optional[subprocess.Popen]:
        """获取进程对象（用于日志收集器附加）
        
        Args:
            process_name: 进程名称
            
        Returns:
            subprocess.Popen对象，如果进程不存在返回None
        """
        with self._lock:
            return self._processes.get(process_name)
    
    def get_pty_process(self, process_name: str):
        """获取 PTY 进程对象（用于日志收集器附加）
        
        Args:
            process_name: 进程名称
            
        Returns:
            winpty.PtyProcess 对象，如果进程不存在返回None
        """
        with self._lock:
            pty_processes = getattr(self, '_pty_processes', {})
            return pty_processes.get(process_name)
    
    def get_pmhq_port(self) -> Optional[int]:
        """获取PMHQ使用的端口
        
        Returns:
            PMHQ端口号，如果PMHQ未启动返回None
        """
        return self._pmhq_port
    
    def get_uin(self) -> Optional[str]:
        """获取QQ号
        
        Returns:
            QQ号，如果未获取到返回None
        """
        return self._uin
    
    def get_nickname(self) -> Optional[str]:
        """获取昵称
        
        Returns:
            昵称，如果未获取到返回None
        """
        return self._nickname
    
    def set_uin_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置uin获取成功的回调函数
        
        Args:
            callback: 回调函数，接收uin和nickname字符串参数
        """
        self._uin_callback = callback
    
    def _start_uin_fetch(self) -> None:
        """启动获取uin的后台线程"""
        if self._uin_fetch_thread and self._uin_fetch_thread.is_alive():
            return
        
        self._uin_fetch_thread = threading.Thread(
            target=self._fetch_uin_loop,
            daemon=True
        )
        self._uin_fetch_thread.start()
    
    def _fetch_uin_loop(self) -> None:
        """循环请求PMHQ获取uin，直到成功"""
        if self._pmhq_port is None:
            logger.error("PMHQ端口未设置，无法获取uin")
            return
        
        url = f"http://localhost:{self._pmhq_port}"
        payload = {
            "type": "call",
            "data": {
                "func": "getSelfInfo",
                "args": []
            }
        }
        
        max_attempts = 1200  # 最多尝试次数，一秒一次
        attempt = 0
        client = self._get_http_client()
        
        while attempt < max_attempts:
            # 检查PMHQ是否还在运行
            if self._status.get("pmhq") != ProcessStatus.RUNNING:
                logger.info("PMHQ已停止，停止获取uin")
                return
            
            try:
                resp = client.post(url, json_data=payload, timeout=5)
                
                if resp.status == 200:
                    data = resp.json()
                    if data.get("type") == "call" and "data" in data:
                        result = data["data"].get("result", {})
                        uin = result.get("uin")
                        nickname = result.get("nickName") or result.get("nickname") or result.get("nick") or ""
                        
                        if uin:
                            # 先保存uin（即使nickname为空）
                            uin_changed = self._uin != uin
                            if uin_changed:
                                self._uin = uin
                                logger.info(f"成功获取uin: {uin}")
                                # uin变化时先触发一次回调（用于更新头像）
                                if self._uin_callback:
                                    try:
                                        self._uin_callback(uin, "")
                                    except Exception as e:
                                        logger.error(f"uin回调函数执行失败: {e}")
                            
                            if nickname:
                                self._nickname = nickname
                                logger.info(f"成功获取nickname: {nickname}")
                                
                                # uin和nickname都有了，调用回调函数（用于更新标题）
                                if self._uin_callback:
                                    try:
                                        self._uin_callback(uin, nickname)
                                    except Exception as e:
                                        logger.error(f"uin回调函数执行失败: {e}")
                                return
                            else:
                                # uin获取到了但nickname为空，继续尝试
                                logger.debug(f"获取到uin: {uin}，但nickname为空，继续尝试...")
                        
            except HttpError as e:
                logger.debug(f"获取uin请求失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
            except json.JSONDecodeError as e:
                logger.debug(f"解析uin响应失败: {e}")
            except Exception as e:
                logger.debug(f"获取uin时发生异常: {e}")
            
            attempt += 1
            time.sleep(1)  # 每秒尝试一次
        
        logger.warning(f"获取uin失败，已尝试 {max_attempts} 次")
    
    def get_qq_pid(self) -> Optional[int]:
        """获取QQ进程的PID
        
        Returns:
            QQ进程PID，如果未获取到返回None
        """
        return self._qq_pid
    
    def get_qq_resources(self) -> Dict[str, float]:
        """获取QQ进程的资源占用（仅指定pid的进程）
        
        Returns:
            字典，包含 cpu（百分比）和 memory（MB）
        """
        return self._qq_resources.copy()
    
    def _get_http_client(self) -> HttpClient:
        """获取共享的HTTP客户端实例（懒加载）
        
        Returns:
            HttpClient实例
        """
        if self._http_client is None:
            self._http_client = HttpClient(timeout=5)
        return self._http_client
    
    def fetch_qq_process_info(self) -> Optional[int]:
        """从PMHQ获取QQ进程信息
        
        如果已经获取到PID且进程仍在运行，直接复用已有PID，避免重复调用API。
        
        Returns:
            QQ进程PID，如果获取失败返回None
        """
        # 如果已有PID，先检查进程是否仍在运行
        if self._qq_pid is not None:
            try:
                import psutil
                if psutil.pid_exists(self._qq_pid):
                    # 进程仍存在，更新资源占用并返回
                    self._update_qq_resources(self._qq_pid)
                    return self._qq_pid
                else:
                    # 进程已退出，清空缓存
                    logger.info(f"QQ进程 {self._qq_pid} 已退出")
                    self._qq_pid = None
                    self._qq_process = None
                    self._qq_resources = {"cpu": 0.0, "memory": 0.0}
            except Exception as e:
                logger.debug(f"检查QQ进程状态时发生异常: {e}")
                self._qq_pid = None
                self._qq_process = None
        
        if self._pmhq_port is None:
            logger.debug("PMHQ端口未设置，无法获取QQ进程信息")
            return None
        
        url = f"http://localhost:{self._pmhq_port}"
        echo_id = str(uuid.uuid4())
        payload = {
            "type": "call",
            "data": {
                "func": "getProcessInfo",
                "args": [],
                "echo": echo_id
            }
        }
        
        try:
            client = self._get_http_client()
            resp = client.post(url, json_data=payload, timeout=5)
            
            logger.info(f"getProcessInfo响应状态码: {resp.status}")
            if resp.status == 200:
                data = resp.json()
                logger.info(f"getProcessInfo响应数据: {data}")
                if data.get("type") == "call" and "data" in data:
                    result = data["data"].get("result", {})
                    pid = result.get("pid")
                    if pid:
                        self._qq_pid = pid
                        logger.info(f"获取QQ进程PID: {pid}")
                        # 计算资源占用
                        self._update_qq_resources(pid)
                        return pid
                    else:
                        logger.info(f"getProcessInfo返回的result中没有pid: {result}")
                else:
                    logger.info(f"getProcessInfo响应格式不正确: type={data.get('type')}, data存在={('data' in data)}")
            else:
                logger.info(f"getProcessInfo请求失败，状态码: {resp.status}, 响应: {resp.text()}")
                        
        except HttpError as e:
            logger.info(f"获取QQ进程信息请求失败: {e}")
        except json.JSONDecodeError as e:
            logger.info(f"解析QQ进程信息响应失败: {e}")
        except Exception as e:
            logger.info(f"获取QQ进程信息时发生异常: {e}")
        
        # 获取失败时清空资源信息
        self._qq_process = None
        self._qq_pid = None
        self._qq_resources = {"cpu": 0.0, "memory": 0.0}
        return None
    
    def _update_qq_resources(self, pid: int) -> None:
        """更新QQ进程的资源占用（仅指定pid的进程）
        
        Args:
            pid: QQ进程的PID（由getProcessInfo接口返回）
        """
        try:
            import psutil
            
            # 检查是否需要创建新的进程对象
            # 如果PID变化或进程对象不存在，需要重新创建
            if self._qq_process is None or self._qq_process.pid != pid:
                self._qq_process = psutil.Process(pid)
                # 首次调用cpu_percent进行初始化（返回0，但会记录采样点）
                self._qq_process.cpu_percent(interval=0)
                logger.debug(f"创建QQ进程对象，PID: {pid}，首次采样已完成")
            
            # 验证进程是否仍在运行
            if not self._qq_process.is_running():
                self._qq_process = None
                self._qq_pid = None
                self._qq_resources = {"cpu": 0.0, "memory": 0.0}
                return
            
            # 获取CPU使用率（使用缓存的进程对象，可以正确计算）
            cpu = self._qq_process.cpu_percent(interval=0)
            
            # 获取内存使用量（使用RSS - 物理内存占用）
            mem_info = self._qq_process.memory_info()
            memory = mem_info.rss / (1024 * 1024)  # 转换为MB
            
            self._qq_resources = {
                "cpu": cpu,
                "memory": memory
            }
            logger.debug(f"QQ资源占用 - PID: {pid}, CPU: {cpu:.1f}%, 内存: {memory:.1f}MB")
            
        except psutil.NoSuchProcess:
            logger.debug(f"QQ进程 {pid} 不存在")
            self._qq_process = None
            self._qq_pid = None
            self._qq_resources = {"cpu": 0.0, "memory": 0.0}
        except psutil.AccessDenied:
            logger.debug(f"无权限访问QQ进程 {pid}")
        except Exception as e:
            logger.debug(f"更新QQ资源占用时发生异常: {e}")
    
    def get_pid(self, process_name: str) -> Optional[int]:
        """获取进程的PID
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
            
        Returns:
            进程PID，如果进程不存在或已停止返回None
        """
        with self._lock:
            # 先检查 PTY 进程
            pty_processes = getattr(self, '_pty_processes', {})
            pty_process = pty_processes.get(process_name)
            if pty_process and pty_process.isalive():
                return pty_process.pid
            # 再检查普通进程
            process = self._processes.get(process_name)
            if process and process.poll() is None:
                return process.pid
            # 再检查以管理员权限启动的进程
            admin_pid = self._admin_pids.get(process_name)
            if admin_pid:
                # 验证进程是否还在运行
                try:
                    import psutil
                    if psutil.pid_exists(admin_pid):
                        return admin_pid
                except:
                    pass
            return None
    
    def get_all_pids(self) -> Dict[str, Optional[int]]:
        """获取所有托管进程的PID
        
        Returns:
            字典，键为进程名称，值为PID（如果进程不存在则为None）
        """
        with self._lock:
            pids = {}
            for name in ["pmhq", "llonebot"]:
                # 先检查普通进程
                process = self._processes.get(name)
                if process and process.poll() is None:
                    pids[name] = process.pid
                else:
                    # 再检查以管理员权限启动的进程
                    admin_pid = self._admin_pids.get(name)
                    if admin_pid:
                        try:
                            import psutil
                            if psutil.pid_exists(admin_pid):
                                pids[name] = admin_pid
                            else:
                                pids[name] = None
                        except:
                            pids[name] = None
                    else:
                        pids[name] = None
            return pids
    
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
