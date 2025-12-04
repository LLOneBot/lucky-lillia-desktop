"""文件下载管理 - 从NPM下载文件并报告进度"""

import os
import shutil
import zipfile
import tarfile
import urllib.request
import urllib.error
import socket
from typing import Optional, Callable
from utils.constants import UPDATE_CHECK_TIMEOUT, NPM_PACKAGES, NPM_REGISTRY_MIRRORS
from utils.npm_api import get_package_info, get_package_tarball_url, NpmAPIError, NetworkError, TimeoutError


class DownloadError(Exception):
    """下载错误基类"""
    pass


class Downloader:
    """管理文件下载"""
    
    def __init__(self, timeout: int = 30):
        """初始化下载管理器
        
        Args:
            timeout: 下载超时时间（秒）
        """
        self.timeout = timeout
        self.registry_mirrors = NPM_REGISTRY_MIRRORS.copy()
    
    def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件存在返回True，否则返回False
        """
        return os.path.isfile(file_path)
    
    def find_in_path(self, executable: str) -> Optional[str]:
        """在系统PATH环境变量中查找可执行文件
        
        Args:
            executable: 可执行文件名（如 node.exe, ffmpeg.exe）
            
        Returns:
            找到返回完整路径，否则返回None
        """
        return shutil.which(executable)
    
    def check_node_available(self) -> Optional[str]:
        """检查系统是否已安装Node.js
        
        Returns:
            如果找到返回node.exe的完整路径，否则返回None
        """
        return self.find_in_path("node.exe") or self.find_in_path("node")
    
    def get_node_version(self, node_path: str) -> Optional[int]:
        """获取Node.js的主版本号
        
        Args:
            node_path: node可执行文件的路径
            
        Returns:
            主版本号（如22），获取失败返回None
        """
        import subprocess
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            result = subprocess.run(
                [node_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 版本格式: v22.0.0 或 v18.17.1
                version_str = result.stdout.strip()
                match = re.match(r'v(\d+)', version_str)
                if match:
                    major_version = int(match.group(1))
                    logger.info(f"Node.js版本: {version_str} (主版本: {major_version})")
                    return major_version
        except Exception as e:
            logger.warning(f"获取Node.js版本失败: {e}")
        return None
    
    def check_node_version_valid(self, node_path: str, min_version: int = 22) -> bool:
        """检查Node.js版本是否满足最低要求
        
        Args:
            node_path: node可执行文件的路径
            min_version: 最低版本要求，默认22
            
        Returns:
            版本满足要求返回True，否则返回False
        """
        version = self.get_node_version(node_path)
        if version is None:
            return False
        return version >= min_version
    
    def check_ffmpeg_available(self) -> Optional[str]:
        """检查系统是否已安装FFmpeg
        
        Returns:
            如果找到返回ffmpeg.exe的完整路径，否则返回None
        """
        return self.find_in_path("ffmpeg.exe") or self.find_in_path("ffmpeg")
    
    def check_ffprobe_available(self) -> Optional[str]:
        """检查系统是否已安装FFprobe
        
        Returns:
            如果找到返回ffprobe.exe的完整路径，否则返回None
        """
        return self.find_in_path("ffprobe.exe") or self.find_in_path("ffprobe")

    def _get_npm_tarball_url(self, package_name: str) -> str:
        """获取npm包的tarball下载URL
        
        Args:
            package_name: npm包名
            
        Returns:
            tarball下载URL
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        return get_package_tarball_url(
            package_name, 
            timeout=UPDATE_CHECK_TIMEOUT,
            registry_mirrors=self.registry_mirrors
        )

    def _download_and_extract_tarball(self, tarball_url: str, extract_dir: str,
                                       progress_callback: Optional[Callable[[int, int], None]] = None,
                                       skip_files: Optional[list] = None) -> bool:
        """下载并解压npm tarball
        
        Args:
            tarball_url: tarball下载URL
            extract_dir: 解压目标目录
            progress_callback: 进度回调函数
            skip_files: 要跳过的文件名列表（如 ["package.json"]）
            
        Returns:
            成功返回True
            
        Raises:
            NetworkError: 下载失败
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if skip_files is None:
            skip_files = []
        
        last_error = None
        
        # 尝试从不同镜像下载
        urls_to_try = [tarball_url]
        
        # 如果URL是官方源，添加镜像URL
        if "registry.npmjs.org" in tarball_url:
            for mirror in self.registry_mirrors:
                if mirror != "https://registry.npmjs.org":
                    mirror_url = tarball_url.replace("https://registry.npmjs.org", mirror)
                    urls_to_try.insert(0, mirror_url)
        
        for url in urls_to_try:
            try:
                logger.info(f"尝试下载: {url}")
                
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "QQ-Bot-Manager"}
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # 确保目录存在
                    os.makedirs(extract_dir, exist_ok=True)
                    
                    # 临时文件路径
                    temp_file = os.path.join(extract_dir, "temp_download.tgz")
                    
                    # 下载文件
                    downloaded_size = 0
                    chunk_size = 8192
                    
                    with open(temp_file, 'wb') as f:
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded_size, total_size)
                
                # 解压tarball
                try:
                    with tarfile.open(temp_file, 'r:gz') as tar:
                        # npm tarball通常包含一个package目录
                        tar.extractall(extract_dir, filter='data')
                    
                    # 移动package目录内容到目标目录
                    package_dir = os.path.join(extract_dir, "package")
                    if os.path.exists(package_dir):
                        for item in os.listdir(package_dir):
                            # 跳过指定的文件
                            if item in skip_files:
                                logger.info(f"跳过文件: {item}")
                                continue
                            
                            src = os.path.join(package_dir, item)
                            dst = os.path.join(extract_dir, item)
                            if os.path.exists(dst):
                                if os.path.isdir(dst):
                                    shutil.rmtree(dst)
                                else:
                                    os.remove(dst)
                            shutil.move(src, dst)
                        shutil.rmtree(package_dir)
                    
                    # 删除临时文件
                    os.remove(temp_file)
                    
                    logger.info(f"成功下载并解压到: {extract_dir}")
                    return True
                    
                except tarfile.TarError as e:
                    raise NetworkError(f"解压失败，文件可能已损坏: {e}")
                    
            except socket.timeout:
                last_error = TimeoutError(f"下载超时（{self.timeout}秒）: {url}")
                logger.warning(f"下载超时: {url}")
                continue
            except urllib.error.URLError as e:
                last_error = NetworkError(f"网络连接失败: {e.reason}")
                logger.warning(f"连接失败: {url}")
                continue
            except urllib.error.HTTPError as e:
                last_error = NetworkError(f"HTTP错误 {e.code}: {e.reason}")
                logger.warning(f"请求失败: {url}")
                continue
            except OSError as e:
                raise NetworkError(f"文件保存失败: {e}")
        
        if last_error:
            raise last_error
        else:
            raise NetworkError("所有下载源都无法访问")

    def get_pmhq_download_url(self) -> str:
        """获取PMHQ最新版本的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        package_name = NPM_PACKAGES.get("pmhq", "pmhq")
        return self._get_npm_tarball_url(package_name)

    def get_llonebot_download_url(self) -> str:
        """获取LLOneBot最新版本的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        package_name = NPM_PACKAGES.get("llonebot", "llonebot")
        return self._get_npm_tarball_url(package_name)

    def get_node_download_url(self) -> str:
        """获取Node.exe最新版本的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        package_name = NPM_PACKAGES.get("node", "llonebot-exe")
        return self._get_npm_tarball_url(package_name)

    def download_pmhq(self, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载PMHQ
        
        Args:
            save_path: 保存路径（目录或zip文件路径）
            progress_callback: 进度回调函数，参数为(已下载字节数, 总字节数)
            
        Returns:
            下载成功返回True
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        try:
            tarball_url = self.get_pmhq_download_url()
            
            # 确定解压目录
            if save_path.endswith('.zip'):
                extract_dir = os.path.dirname(save_path)
            else:
                extract_dir = os.path.dirname(save_path) if os.path.isfile(save_path) else save_path
            
            if not extract_dir:
                extract_dir = "bin/pmhq"
            
            return self._download_and_extract_tarball(tarball_url, extract_dir, progress_callback)
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def download_llonebot(self, save_path: str, 
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载LLOneBot
        
        Args:
            save_path: 保存路径
            progress_callback: 进度回调函数
            
        Returns:
            下载成功返回True
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        try:
            tarball_url = self.get_llonebot_download_url()
            
            if save_path.endswith('.zip'):
                extract_dir = os.path.dirname(save_path)
            else:
                extract_dir = os.path.dirname(save_path) if os.path.isfile(save_path) else save_path
            
            if not extract_dir:
                extract_dir = "bin/llonebot"
            
            return self._download_and_extract_tarball(tarball_url, extract_dir, progress_callback)
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def download_node(self, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载Node.exe
        
        Args:
            save_path: 保存路径（忽略，强制下载到 bin/llonebot）
            progress_callback: 进度回调函数
            
        Returns:
            下载成功返回True
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        try:
            tarball_url = self.get_node_download_url()
            
            # 强制下载到 bin/llonebot 目录，跳过 package.json 避免覆盖 llonebot 的配置
            extract_dir = "bin/llonebot"
            
            return self._download_and_extract_tarball(
                tarball_url, extract_dir, progress_callback, 
                skip_files=["package.json"]
            )
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def get_ffmpeg_download_url(self) -> str:
        """获取FFmpeg最新版本的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        package_name = NPM_PACKAGES.get("ffmpeg", "llonebot-ffmpeg-exe")
        return self._get_npm_tarball_url(package_name)

    def download_ffmpeg(self, save_path: str, 
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载FFmpeg.exe
        
        Args:
            save_path: 保存路径（忽略，强制下载到 bin/llonebot）
            progress_callback: 进度回调函数
            
        Returns:
            下载成功返回True
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        try:
            tarball_url = self.get_ffmpeg_download_url()
            
            # 强制下载到 bin/llonebot 目录，跳过 package.json 避免覆盖 llonebot 的配置
            extract_dir = "bin/llonebot"
            
            return self._download_and_extract_tarball(
                tarball_url, extract_dir, progress_callback,
                skip_files=["package.json"]
            )
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def download_ffprobe(self, save_path: str, 
                        progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载FFprobe.exe（与ffmpeg在同一个包中）
        
        Args:
            save_path: 保存路径
            progress_callback: 进度回调函数
            
        Returns:
            下载成功返回True
        """
        # ffprobe和ffmpeg在同一个npm包中
        return self.download_ffmpeg(save_path, progress_callback)

    def get_app_update_download_url(self) -> str:
        """获取应用更新的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        package_name = NPM_PACKAGES.get("app", "lucky-lillia-desktop")
        return self._get_npm_tarball_url(package_name)

    def download_app_update(self, save_path: str, 
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """下载应用更新
        
        下载新版本的exe文件到临时目录，返回新exe的路径。
        由于运行中的exe无法直接覆盖，需要使用批处理脚本来完成替换。
        
        Args:
            save_path: 当前exe的路径（用于确定更新目标）
            progress_callback: 进度回调函数
            
        Returns:
            新版本exe文件的路径
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            tarball_url = self.get_app_update_download_url()
            
            # 下载到临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="app_update_")
            logger.info(f"下载更新到临时目录: {temp_dir}")
            
            self._download_and_extract_tarball(tarball_url, temp_dir, progress_callback)
            
            # 查找下载的exe文件
            new_exe_path = None
            for item in os.listdir(temp_dir):
                if item.endswith('.exe'):
                    new_exe_path = os.path.join(temp_dir, item)
                    break
            
            if not new_exe_path:
                raise NetworkError("下载的更新包中未找到exe文件")
            
            logger.info(f"找到新版本exe: {new_exe_path}")
            return new_exe_path
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")
    
    def apply_app_update(self, new_exe_path: str, current_exe_path: str, current_pid: int) -> str:
        """应用应用更新
        
        创建批处理脚本来替换当前运行的exe文件。
        脚本会等待当前程序退出后执行替换，然后重新启动新版本。
        
        Args:
            new_exe_path: 新版本exe文件的路径（绝对路径）
            current_exe_path: 当前exe文件的路径（绝对路径）
            current_pid: 当前进程的PID
            
        Returns:
            批处理脚本的路径（绝对路径）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 确保使用绝对路径
        new_exe_path = os.path.abspath(new_exe_path)
        current_exe_path = os.path.abspath(current_exe_path)
        
        # 获取当前exe所在目录和文件名
        current_dir = os.path.dirname(current_exe_path)
        current_exe_name = os.path.basename(current_exe_path)
        temp_dir = os.path.dirname(new_exe_path)
        
        # 创建批处理脚本（放在临时目录，避免权限问题）
        batch_script = os.path.join(temp_dir, "_update.bat")
        
        # 批处理脚本内容
        # 1. 等待当前程序退出（通过PID检查）
        # 2. 备份旧版本
        # 3. 复制新版本
        # 4. 启动新版本
        # 5. 清理临时文件
        script_content = f'''@echo off
chcp 65001 >nul

:: 清除PyInstaller环境变量，避免新exe继承旧的临时目录
set _MEIPASS=
set _MEIPASS2=
set _PYI_ARCHIVE_FILE=
set _PYI_SPLASH_IPC=

cd /d "{current_dir}"
echo 正在更新应用程序，请稍候...
echo.

:: 等待原程序退出（通过PID检查，最多等待10秒）
set count=0
:wait_loop
tasklist /FI "PID eq {current_pid}" 2>NUL | find /I "{current_pid}" >NUL
if errorlevel 1 goto do_update
set /a count=%count%+1
if %count% geq 20 (
    echo 等待超时，尝试强制终止进程...
    taskkill /F /PID {current_pid} 2>NUL
    timeout /t 1 /nobreak >nul
    tasklist /FI "PID eq {current_pid}" 2>NUL | find /I "{current_pid}" >NUL
    if errorlevel 1 (
        echo 进程已强制终止
        goto do_update
    ) else (
        echo 无法终止进程，请手动关闭程序后重试
        pause
        exit /b 1
    )
)
echo 等待程序退出... %count%/20
timeout /t 0.5 /nobreak >nul
goto wait_loop

:do_update
echo 程序已退出，开始更新...

echo 正在备份旧版本...
if exist "{current_exe_path}.bak" del /f /q "{current_exe_path}.bak"
if exist "{current_exe_path}" move /y "{current_exe_path}" "{current_exe_path}.bak"

echo 正在安装新版本...
copy /y "{new_exe_path}" "{current_exe_path}"

if errorlevel 1 (
    echo 更新失败，正在恢复旧版本...
    if exist "{current_exe_path}.bak" move /y "{current_exe_path}.bak" "{current_exe_path}"
    pause
    exit /b 1
)

echo.
echo 更新完成！正在启动新版本...
timeout /t 2 /nobreak >nul

:: 切换到exe所在目录并启动
cd /d "{current_dir}"
start "" "{current_exe_name}"

:: 清理临时文件（使用cmd /c在新进程中延迟删除，避免路径问题）
start /b "" cmd /c "timeout /t 5 /nobreak >nul & rmdir /s /q "{temp_dir}" 2>nul"
exit
'''
        
        with open(batch_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"创建更新脚本: {batch_script}")
        return batch_script
