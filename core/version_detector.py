"""版本检测模块 - 检测本地组件版本"""

import subprocess
import json
import re
import os
from pathlib import Path
from typing import Optional


class VersionDetector:
    """检测本地组件版本"""
    
    def detect_pmhq_version(self, pmhq_path: str) -> Optional[str]:
        """检测PMHQ版本
        
        尝试通过以下方式获取版本号：
        1. 读取同目录下的 package.json
        2. 运行 pmhq.exe --version
        3. 读取文件元数据（Windows）
        
        Args:
            pmhq_path: pmhq.exe的路径
            
        Returns:
            版本号字符串，检测失败返回None
        """
        if not pmhq_path:
            return None
        
        pmhq_dir = Path(pmhq_path).parent
        
        # 方法1: 尝试读取 package.json（优先）
        package_json_path = pmhq_dir / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    version = package_data.get('version')
                    if version:
                        return version
            except (json.JSONDecodeError, OSError):
                pass
        
        # 方法2: 尝试运行 pmhq.exe --version（备用）
        if os.path.exists(pmhq_path):
            try:
                result = subprocess.run(
                    [pmhq_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    version_match = re.search(r'v?(\d+\.\d+\.\d+)', output)
                    if version_match:
                        return version_match.group(1)
                    if re.match(r'^v?\d+\.\d+\.\d+$', output):
                        return output.lstrip('v')
                        
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
                pass
        
        # 方法3: 尝试从文件元数据读取（Windows特定）
        if os.name == 'nt' and os.path.exists(pmhq_path):
            try:
                import win32api
                info = win32api.GetFileVersionInfo(pmhq_path, '\\')
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}"
                return version
            except (ImportError, Exception):
                pass
                
        return None
    
    def detect_llonebot_version(self, script_path: str) -> Optional[str]:
        """检测LLOneBot版本
        
        尝试从以下位置检测版本：
        1. 同目录下的 package.json
        2. llonebot.js 文件头部的版本注释
        
        Args:
            script_path: llonebot.js的路径
            
        Returns:
            版本号字符串，检测失败返回None
        """
        if not script_path or not os.path.exists(script_path):
            return None
            
        script_dir = Path(script_path).parent
        
        # 方法1: 尝试读取 package.json
        package_json_path = script_dir / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    version = package_data.get('version')
                    if version:
                        return version
            except (json.JSONDecodeError, OSError):
                pass
        
        # 方法2: 尝试从 llonebot.js 文件头读取版本注释
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    version_match = re.search(
                        r'(?:version|@version)[:\s]+v?(\d+\.\d+\.\d+)', 
                        line, 
                        re.IGNORECASE
                    )
                    if version_match:
                        return version_match.group(1)
        except OSError:
            pass
            
        return None
    
    def get_app_version(self) -> str:
        """获取应用自身版本号
        
        从 __version__.py 文件读取版本号。
        
        Returns:
            版本号字符串
        """
        try:
            import __version__
            return __version__.__version__
        except (ImportError, AttributeError):
            pass
            
        try:
            version_file = Path(__file__).parent.parent / '__version__.py'
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    version_match = re.search(
                        r'__version__\s*=\s*["\']([^"\']+)["\']', 
                        content
                    )
                    if version_match:
                        return version_match.group(1)
        except OSError:
            pass
            
        return "unknown"
