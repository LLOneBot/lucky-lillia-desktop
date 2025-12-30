"""文件下载管理"""

import os
import shutil
import zipfile
import tarfile
import logging
from typing import Optional, Callable
from utils.constants import UPDATE_CHECK_TIMEOUT, NPM_PACKAGES, NPM_REGISTRY_MIRRORS, NPM_OFFICIAL_REGISTRY, QQ_DOWNLOAD_URL
from utils.npm_api import get_package_info, get_package_tarball_url, NpmAPIError, NetworkError, TimeoutError
from utils.http_client import HttpClient, TimeoutError as HttpTimeoutError, ConnectionError as HttpConnectionError


logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """下载错误基类"""
    pass


class Downloader:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.registry_mirrors = NPM_REGISTRY_MIRRORS.copy()
    
    def check_file_exists(self, file_path: str) -> bool:
        return os.path.isfile(file_path)
    
    def find_in_path(self, executable: str) -> Optional[str]:
        return shutil.which(executable)
    
    def check_node_available(self) -> Optional[str]:
        return self.find_in_path("node.exe") or self.find_in_path("node")
    
    def get_node_version(self, node_path: str) -> Optional[int]:
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
        version = self.get_node_version(node_path)
        if version is None:
            return False
        return version >= min_version
    
    def check_ffmpeg_available(self) -> Optional[str]:
        return self.find_in_path("ffmpeg.exe") or self.find_in_path("ffmpeg")
    
    def check_ffprobe_available(self) -> Optional[str]:
        return self.find_in_path("ffprobe.exe") or self.find_in_path("ffprobe")

    def check_ffmpeg_exists(self) -> bool:
        """先检查环境变量，再检查 bin/llbot/"""
        return bool(self.check_ffmpeg_available()) or self.check_file_exists("bin/llbot/ffmpeg.exe")
    
    def check_ffprobe_exists(self) -> bool:
        """先检查环境变量，再检查 bin/llbot/"""
        return bool(self.check_ffprobe_available()) or self.check_file_exists("bin/llbot/ffprobe.exe")

    def _get_npm_tarball_url(self, package_name: str) -> str:
        return get_package_tarball_url(
            package_name, 
            timeout=UPDATE_CHECK_TIMEOUT,
            registry_mirrors=self.registry_mirrors
        )

    def _download_and_extract_tarball(self, tarball_url: str, extract_dir: str,
                                       progress_callback: Optional[Callable[[int, int], None]] = None,
                                       skip_files: Optional[list] = None) -> bool:
        if skip_files is None:
            skip_files = []
        
        last_error = None
        client = HttpClient(timeout=self.timeout)
        
        # tarball_url 已经是最佳下载源的URL，直接下载
        # 如果失败，尝试替换为其他镜像源
        urls_to_try = [tarball_url]
        
        # 添加备用URL
        all_registries = [NPM_OFFICIAL_REGISTRY] + self.registry_mirrors
        for registry in all_registries:
            if registry in tarball_url:
                for other_registry in all_registries:
                    if other_registry != registry:
                        backup_url = tarball_url.replace(registry, other_registry)
                        if backup_url not in urls_to_try:
                            urls_to_try.append(backup_url)
                break
        
        for url in urls_to_try:
            try:
                logger.info(f"尝试下载: {url}")
                
                os.makedirs(extract_dir, exist_ok=True)
                
                temp_file = os.path.join(extract_dir, "temp_download.tgz")
                
                downloaded_size = [0]
                
                def on_chunk(chunk, downloaded, total):
                    downloaded_size[0] = downloaded
                    if progress_callback:
                        progress_callback(downloaded, total)
                
                resp = client.download(url, chunk_callback=on_chunk, timeout=self.timeout)
                
                if resp.status >= 400:
                    raise NetworkError(f"HTTP错误 {resp.status}")
                
                # 保存到临时文件
                with open(temp_file, 'wb') as f:
                    f.write(resp.data)
                
                # 解压tarball
                try:
                    with tarfile.open(temp_file, 'r:gz') as tar:
                        tar.extractall(extract_dir, filter='data')
                    
                    # 移动package目录内容到目标目录
                    package_dir = os.path.join(extract_dir, "package")
                    if os.path.exists(package_dir):
                        for item in os.listdir(package_dir):
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
                    
                    os.remove(temp_file)
                    
                    logger.info(f"成功下载并解压到: {extract_dir}")
                    return True
                    
                except tarfile.TarError as e:
                    raise NetworkError(f"解压失败，文件可能已损坏: {e}")
                    
            except HttpTimeoutError:
                last_error = TimeoutError(f"下载超时（{self.timeout}秒）: {url}")
                logger.warning(f"下载超时: {url}")
                continue
            except HttpConnectionError as e:
                last_error = NetworkError(f"网络连接失败: {e}")
                logger.warning(f"连接失败: {url}")
                continue
            except OSError as e:
                raise NetworkError(f"文件保存失败: {e}")
        
        if last_error:
            raise last_error
        else:
            raise NetworkError("所有下载源都无法访问")

    def get_pmhq_download_url(self) -> str:
        package_name = NPM_PACKAGES.get("pmhq", "pmhq")
        return self._get_npm_tarball_url(package_name)

    def get_llbot_download_url(self) -> str:
        package_name = NPM_PACKAGES.get("llbot", "llonebot")
        return self._get_npm_tarball_url(package_name)

    def get_node_download_url(self) -> str:
        package_name = NPM_PACKAGES.get("node", "llonebot-exe")
        return self._get_npm_tarball_url(package_name)

    def download_pmhq(self, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
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

    def download_llbot(self, save_path: str, 
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            tarball_url = self.get_llbot_download_url()
            
            if save_path.endswith('.zip'):
                extract_dir = os.path.dirname(save_path)
            else:
                extract_dir = os.path.dirname(save_path) if os.path.isfile(save_path) else save_path
            
            if not extract_dir:
                extract_dir = "bin/llbot"
            
            return self._download_and_extract_tarball(tarball_url, extract_dir, progress_callback)
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def download_node(self, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            tarball_url = self.get_node_download_url()
            
            # 强制下载到 bin/llbot 目录，跳过 package.json 避免覆盖 llbot 的配置
            extract_dir = "bin/llbot"
            
            return self._download_and_extract_tarball(
                tarball_url, extract_dir, progress_callback, 
                skip_files=["package.json"]
            )
            
        except (NetworkError, TimeoutError):
            raise
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def get_ffmpeg_download_url(self) -> str:
        package_name = NPM_PACKAGES.get("ffmpeg", "llonebot-ffmpeg-exe")
        return self._get_npm_tarball_url(package_name)

    def download_ffmpeg(self, save_path: str, 
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            tarball_url = self.get_ffmpeg_download_url()
            
            # 强制下载到 bin/llbot 目录，跳过 package.json 避免覆盖 llbot 的配置
            extract_dir = "bin/llbot"
            
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
        # ffprobe和ffmpeg在同一个npm包中
        return self.download_ffmpeg(save_path, progress_callback)

    def get_app_update_download_url(self) -> str:
        package_name = NPM_PACKAGES.get("app", "lucky-lillia-desktop")
        return self._get_npm_tarball_url(package_name)

    def download_qq(self, save_path: str,
                   progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            client = HttpClient(timeout=self.timeout)
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            def on_chunk(chunk, downloaded, total):
                if progress_callback:
                    progress_callback(downloaded, total)
            
            resp = client.download(QQ_DOWNLOAD_URL, chunk_callback=on_chunk, timeout=300)
            
            if resp.status >= 400:
                raise NetworkError(f"HTTP错误 {resp.status}")
            
            with open(save_path, 'wb') as f:
                f.write(resp.data)
            
            logger.info(f"QQ安装程序下载成功: {save_path}")
            return True
            
        except HttpTimeoutError:
            raise TimeoutError(f"下载超时: {QQ_DOWNLOAD_URL}")
        except HttpConnectionError as e:
            raise NetworkError(f"网络连接失败: {e}")
        except OSError as e:
            raise NetworkError(f"文件保存失败: {e}")
        except Exception as e:
            raise NetworkError(f"下载失败: {e}")

    def download_app_update(self, save_path: str, 
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
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
