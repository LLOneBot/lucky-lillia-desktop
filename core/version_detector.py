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
        
        尝试通过运行 pmhq.exe --version 获取版本号。
        如果失败，返回None。
        
        Args:
            pmhq_path: pmhq.exe的路径
            
        Returns:
            版本号字符串，检测失败返回None
        """
        if not pmhq_path or not os.path.exists(pmhq_path):
            return None
            
        try:
            # 尝试运行 pmhq.exe --version
            result = subprocess.run(
                [pmhq_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # 从输出中提取版本号
                output = result.stdout.strip()
                # 尝试匹配常见的版本号格式 (如 "1.2.3", "v1.2.3", "version 1.2.3")
                version_match = re.search(r'v?(\d+\.\d+\.\d+)', output)
                if version_match:
                    return version_match.group(1)
                # 如果整个输出看起来像版本号，直接返回
                if re.match(r'^v?\d+\.\d+\.\d+$', output):
                    return output.lstrip('v')
                    
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            pass
            
        # 如果运行失败，尝试从文件元数据读取（Windows特定）
        if os.name == 'nt':
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
                # 只读取前20行，版本信息通常在文件头部
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    # 查找版本注释，如 "version: 1.2.3" 或 "@version 1.2.3"
                    version_match = re.search(r'(?:version|@version)[:\s]+v?(\d+\.\d+\.\d+)', line, re.IGNORECASE)
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
            # 尝试导入 __version__ 模块
            import __version__
            return __version__.__version__
        except (ImportError, AttributeError):
            pass
            
        # 如果导入失败，尝试直接读取文件
        try:
            version_file = Path(__file__).parent.parent / '__version__.py'
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 查找 __version__ = "x.x.x" 格式
                    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if version_match:
                        return version_match.group(1)
        except OSError:
            pass
            
        # 如果都失败，返回默认值
        return "unknown"
