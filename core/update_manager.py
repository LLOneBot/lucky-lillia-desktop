"""更新管理器 - 统一管理更新检查和下载"""

import logging
import threading
import time
import os
from typing import Optional, Callable, List, Tuple, Dict
from dataclasses import dataclass, field

from core.update_checker import UpdateChecker, UpdateInfo
from core.process_manager import ProcessManager, ProcessStatus
from core.config_manager import ConfigManager
from utils.downloader import Downloader
from utils.constants import NPM_PACKAGES, GITHUB_REPOS

logger = logging.getLogger(__name__)


class UpdateManager:
    """统一管理更新检查和下载"""
    
    def __init__(self, 
                 update_checker: UpdateChecker,
                 config_manager: ConfigManager,
                 process_manager: ProcessManager,
                 downloader: Downloader):
        self.update_checker = update_checker
        self.config_manager = config_manager
        self.process_manager = process_manager
        self.downloader = downloader
        
        self._lock = threading.Lock()
        self._updates_found: List[Tuple[str, UpdateInfo]] = []
        self._is_checking = False
        self._is_downloading = False
        self._pending_app_update_script: Optional[str] = None
        self._last_check_time: Optional[float] = None
        
        # UI 回调
        self._on_check_start: Optional[Callable[[], None]] = None
        self._on_check_complete: Optional[Callable[[List[Tuple[str, UpdateInfo]]], None]] = None
        self._on_download_start: Optional[Callable[[], None]] = None
        self._on_download_progress: Optional[Callable[[str, int, int], None]] = None
        self._on_download_status: Optional[Callable[[str], None]] = None
        self._on_download_complete: Optional[Callable[[List[str], List[Tuple[str, str]], bool], None]] = None
    
    def set_callbacks(self,
                      on_check_start: Optional[Callable[[], None]] = None,
                      on_check_complete: Optional[Callable[[List[Tuple[str, UpdateInfo]]], None]] = None,
                      on_download_start: Optional[Callable[[], None]] = None,
                      on_download_progress: Optional[Callable[[str, int, int], None]] = None,
                      on_download_status: Optional[Callable[[str], None]] = None,
                      on_download_complete: Optional[Callable[[List[str], List[Tuple[str, str]], bool], None]] = None):
        """设置UI回调函数"""
        self._on_check_start = on_check_start
        self._on_check_complete = on_check_complete
        self._on_download_start = on_download_start
        self._on_download_progress = on_download_progress
        self._on_download_status = on_download_status
        self._on_download_complete = on_download_complete
    
    @property
    def has_updates(self) -> bool:
        """是否有可用更新"""
        with self._lock:
            return len(self._updates_found) > 0
    
    @property
    def updates_found(self) -> List[Tuple[str, UpdateInfo]]:
        """获取发现的更新列表"""
        with self._lock:
            return self._updates_found.copy()
    
    @property
    def is_checking(self) -> bool:
        """是否正在检查更新"""
        with self._lock:
            return self._is_checking
    
    @property
    def is_downloading(self) -> bool:
        """是否正在下载更新"""
        with self._lock:
            return self._is_downloading
    
    @property
    def pending_app_update_script(self) -> Optional[str]:
        """获取待执行的应用更新脚本"""
        return self._pending_app_update_script
    
    def clear_pending_app_update(self):
        """清除待执行的应用更新脚本"""
        self._pending_app_update_script = None
    
    def has_pending_app_update(self) -> bool:
        """检查是否有待执行的应用更新"""
        return self._pending_app_update_script is not None
    
    def get_update_info(self, component: str) -> Optional[UpdateInfo]:
        """获取指定组件的更新信息"""
        with self._lock:
            for name, info in self._updates_found:
                if name == component:
                    return info
            return None
    
    def clear_update(self, component: str):
        """清除指定组件的更新状态"""
        with self._lock:
            self._updates_found = [(name, info) for name, info in self._updates_found if name != component]
    
    def clear_all_updates(self):
        """清除所有更新状态"""
        with self._lock:
            self._updates_found = []
    
    def check_updates_async(self, versions: Dict[str, str]):
        """异步检查更新
        
        Args:
            versions: 组件名到当前版本号的映射
        """
        if self.is_checking:
            return
        
        def check_thread():
            self._check_updates(versions)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def _check_updates(self, versions: Dict[str, str]):
        """检查更新（同步）"""
        with self._lock:
            self._is_checking = True
        
        if self._on_check_start:
            self._on_check_start()
        
        try:
            updates_found = []  # 有更新的组件
            all_check_results = []  # 所有检查结果（用于UI显示）
            
            # 检查管理器更新
            if "app" in versions and versions["app"] and versions["app"] != "未知":
                app_package = NPM_PACKAGES.get("app")
                app_repo = GITHUB_REPOS.get("app")
                if app_package:
                    app_update = self.update_checker.check_update(app_package, versions["app"], app_repo)
                    logger.info(f"管理器更新检查: has_update={app_update.has_update}, latest={app_update.latest_version}")
                    all_check_results.append(("管理器", app_update))
                    if app_update.has_update:
                        updates_found.append(("管理器", app_update))
            
            # 检查PMHQ更新
            if "pmhq" in versions and versions["pmhq"] and versions["pmhq"] != "未知":
                pmhq_package = NPM_PACKAGES.get("pmhq")
                pmhq_repo = GITHUB_REPOS.get("pmhq")
                if pmhq_package:
                    pmhq_update = self.update_checker.check_update(pmhq_package, versions["pmhq"], pmhq_repo)
                    logger.info(f"PMHQ更新检查: has_update={pmhq_update.has_update}, latest={pmhq_update.latest_version}")
                    all_check_results.append(("PMHQ", pmhq_update))
                    if pmhq_update.has_update:
                        updates_found.append(("PMHQ", pmhq_update))
            
            # 检查LLOneBot更新
            if "llonebot" in versions and versions["llonebot"] and versions["llonebot"] != "未知":
                llonebot_package = NPM_PACKAGES.get("llonebot")
                llonebot_repo = GITHUB_REPOS.get("llonebot")
                if llonebot_package:
                    llonebot_update = self.update_checker.check_update(llonebot_package, versions["llonebot"], llonebot_repo)
                    logger.info(f"LLOneBot更新检查: has_update={llonebot_update.has_update}, latest={llonebot_update.latest_version}")
                    all_check_results.append(("LLOneBot", llonebot_update))
                    if llonebot_update.has_update:
                        updates_found.append(("LLOneBot", llonebot_update))
            
            with self._lock:
                self._updates_found = updates_found
                self._last_check_time = time.time()
            
            if updates_found:
                logger.info(f"发现 {len(updates_found)} 个更新: {[name for name, _ in updates_found]}")
            else:
                logger.info("所有组件已是最新版本")
            
            # 回调传递所有检查结果，让UI可以显示"已是最新版本"
            if self._on_check_complete:
                self._on_check_complete(all_check_results)
                
        except Exception as e:
            logger.error(f"检查更新失败: {e}", exc_info=True)
            if self._on_check_complete:
                self._on_check_complete([])
        finally:
            with self._lock:
                self._is_checking = False
    
    def has_running_processes(self) -> bool:
        """检查是否有进程在运行"""
        return (
            self.process_manager.get_process_status("pmhq") == ProcessStatus.RUNNING or
            self.process_manager.get_process_status("llonebot") == ProcessStatus.RUNNING or
            self.process_manager.get_qq_pid() is not None
        )
    
    def download_all_updates_async(self):
        """异步下载所有更新"""
        if self.is_downloading or not self.has_updates:
            return
        
        def download_thread():
            self._download_all_updates()
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _download_all_updates(self):
        """下载所有更新（同步）"""
        with self._lock:
            if self._is_downloading:
                return
            self._is_downloading = True
            updates_to_download = self._updates_found.copy()
        
        if self._on_download_start:
            self._on_download_start()
        
        success_list = []
        error_list = []
        
        try:
            # 检查更新前是否有进程在运行
            had_running_processes = self.has_running_processes()
            
            # 停止所有进程
            if had_running_processes:
                if self._on_download_status:
                    self._on_download_status("正在停止所有进程...")
                logger.info("更新前停止所有进程...")
                self.process_manager.stop_all(stop_qq=True)
                
                if not self.process_manager.wait_all_stopped(timeout=10.0):
                    logger.warning("部分进程可能未完全退出，继续更新...")
                else:
                    logger.info("所有进程已完全退出")
            
            # 下载所有更新
            for component_name, update_info in updates_to_download:
                if self._on_download_status:
                    self._on_download_status(f"正在更新: {component_name}")
                
                def make_progress_callback(name):
                    def callback(downloaded, total):
                        if self._on_download_progress:
                            self._on_download_progress(name, downloaded, total)
                    return callback
                
                try:
                    if component_name == "管理器":
                        import sys
                        current_pid = os.getpid()
                        if getattr(sys, 'frozen', False):
                            current_exe = sys.executable
                        else:
                            current_exe = os.path.abspath("lucky-lillia-desktop.exe")
                        
                        new_exe_path = self.downloader.download_app_update(
                            current_exe, make_progress_callback(component_name))
                        batch_script = self.downloader.apply_app_update(
                            new_exe_path, current_exe, current_pid)
                        self._pending_app_update_script = batch_script
                        success_list.append(component_name)
                        
                    elif component_name == "PMHQ":
                        config = self.config_manager.load_config()
                        pmhq_path = config.get("pmhq_path", "bin/pmhq/pmhq-win-x64.exe")
                        save_path = pmhq_path.replace('.exe', '.zip')
                        self.downloader.download_pmhq(save_path, make_progress_callback(component_name))
                        success_list.append(component_name)
                        
                    elif component_name == "LLOneBot":
                        config = self.config_manager.load_config()
                        llonebot_path = config.get("llonebot_path", "bin/llonebot/llonebot.js")
                        save_path = llonebot_path.replace('.js', '.zip')
                        if not save_path.endswith('.zip'):
                            save_path = llonebot_path + '.zip'
                        self.downloader.download_llonebot(save_path, make_progress_callback(component_name))
                        success_list.append(component_name)
                        
                except Exception as ex:
                    logger.error(f"下载{component_name}失败: {ex}")
                    error_list.append((component_name, str(ex)))
            
            # 清除已更新的组件
            with self._lock:
                self._updates_found = [(name, info) for name, info in self._updates_found 
                                       if name not in success_list]
            
            if self._on_download_complete:
                self._on_download_complete(success_list, error_list, had_running_processes)
            
        except Exception as e:
            logger.error(f"下载更新失败: {e}", exc_info=True)
            if self._on_download_complete:
                self._on_download_complete([], [(str(e), "")], False)
        finally:
            with self._lock:
                self._is_downloading = False
