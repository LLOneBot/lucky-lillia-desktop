# 设计文档

## 概述

QQ机器人管理器是一个基于Python Flet框架的跨平台桌面应用程序。该应用采用现代化的Material Design设计语言，提供进程管理、日志监控、配置编辑和版本更新等核心功能。

### 技术栈

- **UI框架**: Flet (基于Flutter的Python UI框架)
- **进程管理**: Python subprocess模块
- **配置管理**: Python json模块
- **HTTP客户端**: requests库（用于GitHub API调用）
- **版本比较**: packaging库
- **持久化存储**: Python shelve或json文件

### 设计原则

1. **关注点分离**: UI层、业务逻辑层、数据访问层清晰分离
2. **响应式设计**: 使用异步操作避免UI阻塞
3. **错误优先**: 所有外部操作都包含错误处理
4. **用户友好**: 提供清晰的状态反馈和错误提示

## 架构

### 整体架构

```
┌─────────────────────────────────────────┐
│           UI Layer (Flet)               │
│  ┌──────────┬──────────┬──────────┐    │
│  │ HomePage │ LogPage  │ ConfigPage│    │
│  └──────────┴──────────┴──────────┘    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│        Business Logic Layer             │
│  ┌──────────────┬──────────────────┐   │
│  │ProcessManager│ UpdateChecker    │   │
│  ├──────────────┼──────────────────┤   │
│  │ConfigManager │ VersionDetector  │   │
│  └──────────────┴──────────────────┘   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Data Access Layer               │
│  ┌──────────────┬──────────────────┐   │
│  │FileSystem    │ GitHub API       │   │
│  ├──────────────┼──────────────────┤   │
│  │Process I/O   │ Local Storage    │   │
│  └──────────────┴──────────────────┘   │
└─────────────────────────────────────────┘
```

### 模块划分

1. **UI模块** (`ui/`)
   - `main_window.py`: 主窗口和导航
   - `home_page.py`: 首页
   - `log_page.py`: 日志页面
   - `config_page.py`: 配置页面
   - `about_page.py`: 关于/版本页面
   - `theme.py`: 主题配置

2. **核心模块** (`core/`)
   - `process_manager.py`: 进程生命周期管理
   - `log_collector.py`: 日志收集和缓冲
   - `config_manager.py`: 配置文件读写
   - `update_checker.py`: 版本检查和比较
   - `version_detector.py`: 本地版本检测

3. **工具模块** (`utils/`)
   - `github_api.py`: GitHub API封装
   - `storage.py`: 本地持久化存储
   - `constants.py`: 常量定义
   - `downloader.py`: 文件下载管理

## 组件和接口

### ProcessManager

进程管理器负责启动、停止和监控托管进程。

```python
class ProcessManager:
    """管理外部进程的生命周期"""
    
    def start_pmhq(self, config_path: str) -> bool:
        """启动PMHQ进程
        
        Args:
            config_path: pmhq_config.json的路径
            
        Returns:
            启动成功返回True，失败返回False
        """
        
    def start_llonebot(self, node_path: str, script_path: str) -> bool:
        """启动LLOneBot进程
        
        Args:
            node_path: node.exe的路径
            script_path: llonebot.js的路径
            
        Returns:
            启动成功返回True，失败返回False
        """
        
    def stop_process(self, process_name: str) -> bool:
        """停止指定进程
        
        Args:
            process_name: 进程名称 ("pmhq" 或 "llonebot")
            
        Returns:
            停止成功返回True，失败返回False
        """
        
    def get_process_status(self, process_name: str) -> ProcessStatus:
        """获取进程状态
        
        Returns:
            ProcessStatus枚举值 (RUNNING, STOPPED, ERROR)
        """
        
    def stop_all(self) -> None:
        """停止所有托管进程"""
```

### LogCollector

日志收集器负责从进程输出流读取日志并缓冲。

```python
class LogCollector:
    """收集和管理进程日志输出"""
    
    def __init__(self, max_lines: int = 1000):
        """初始化日志收集器
        
        Args:
            max_lines: 最大保留日志行数
        """
        
    def attach_process(self, process_name: str, process: subprocess.Popen) -> None:
        """附加到进程的输出流
        
        Args:
            process_name: 进程名称
            process: subprocess.Popen对象
        """
        
    def get_logs(self, process_name: str = None) -> List[LogEntry]:
        """获取日志条目
        
        Args:
            process_name: 进程名称，None表示获取所有日志
            
        Returns:
            日志条目列表
        """
        
    def clear_logs(self, process_name: str = None) -> None:
        """清空日志
        
        Args:
            process_name: 进程名称，None表示清空所有日志
        """
        
    def set_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """设置新日志回调函数，用于实时更新UI"""
```

### ConfigManager

配置管理器负责读写pmhq_config.json文件。

```python
class ConfigManager:
    """管理PMHQ配置文件"""
    
    def __init__(self, config_path: str = "pmhq_config.json"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典，如果文件不存在则返回默认配置
            
        Raises:
            ConfigError: 配置文件格式无效
        """
        
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件
        
        Args:
            config: 配置字典
            
        Returns:
            保存成功返回True，失败返回False
        """
        
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证配置有效性
        
        Returns:
            (是否有效, 错误消息)
        """
        
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
```

### UpdateChecker

更新检查器负责查询GitHub API获取最新版本。

```python
class UpdateChecker:
    """检查GitHub仓库的更新"""
    
    def __init__(self, timeout: int = 10):
        """初始化更新检查器
        
        Args:
            timeout: API请求超时时间（秒）
        """
        
    def check_update(self, repo: str, current_version: str) -> UpdateInfo:
        """检查指定仓库的更新
        
        Args:
            repo: GitHub仓库 (格式: "owner/repo")
            current_version: 当前版本号
            
        Returns:
            UpdateInfo对象，包含是否有更新、最新版本等信息
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 请求超时
        """
        
    def check_all_updates(self) -> Dict[str, UpdateInfo]:
        """检查所有组件的更新
        
        Returns:
            组件名到UpdateInfo的映射
        """
```

### VersionDetector

版本检测器负责检测本地安装的组件版本。

```python
class VersionDetector:
    """检测本地组件版本"""
    
    def detect_pmhq_version(self, pmhq_path: str) -> Optional[str]:
        """检测PMHQ版本
        
        Args:
            pmhq_path: pmhq.exe的路径
            
        Returns:
            版本号字符串，检测失败返回None
        """
        
    def detect_llonebot_version(self, script_path: str) -> Optional[str]:
        """检测LLOneBot版本
        
        Args:
            script_path: llonebot.js的路径
            
        Returns:
            版本号字符串，检测失败返回None
        """
        
    def get_app_version(self) -> str:
        """获取应用自身版本号"""
```

### Downloader

下载管理器负责从GitHub下载文件并报告进度。

```python
class Downloader:
    """管理文件下载"""
    
    def __init__(self, timeout: int = 30):
        """初始化下载管理器
        
        Args:
            timeout: 下载超时时间（秒）
        """
        
    def download_pmhq(self, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """下载PMHQ可执行文件
        
        Args:
            save_path: 保存路径
            progress_callback: 进度回调函数，参数为(已下载字节数, 总字节数)
            
        Returns:
            下载成功返回True，失败返回False
            
        Raises:
            NetworkError: 网络请求失败
            TimeoutError: 下载超时
        """
        
    def get_pmhq_download_url(self) -> str:
        """获取PMHQ最新版本的下载URL
        
        Returns:
            下载URL字符串
            
        Raises:
            NetworkError: 无法获取下载链接
        """
        
    def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件存在返回True，否则返回False
        """
```

## 数据模型

### ProcessStatus

```python
from enum import Enum

class ProcessStatus(Enum):
    """进程状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
```

### LogEntry

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    process_name: str
    level: str  # "stdout" 或 "stderr"
    message: str
```

### UpdateInfo

```python
from dataclasses import dataclass

@dataclass
class UpdateInfo:
    """更新信息"""
    has_update: bool
    current_version: str
    latest_version: str
    release_url: str
    error: Optional[str] = None
```

### AppConfig

```python
from dataclasses import dataclass

@dataclass
class AppConfig:
    """应用配置"""
    theme_mode: str  # "light" 或 "dark"
    window_width: int
    window_height: int
    pmhq_path: str
    llonebot_path: str
    node_path: str
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 进程启动后状态为运行中
*对于任何*有效的进程配置，成功启动进程后，查询该进程状态应该返回RUNNING状态。
**验证需求：1.1, 1.2**

### 属性 2: 进程停止后状态为已停止
*对于任何*正在运行的进程，执行停止操作后，查询该进程状态应该返回STOPPED状态。
**验证需求：1.3**

### 属性 3: 应用关闭时清理所有进程
*对于任何*运行中的进程集合，当应用关闭时，所有进程都应该被终止。
**验证需求：1.5**

### 属性 4: 日志捕获完整性
*对于任何*进程输出（stdout或stderr），该输出都应该被捕获并出现在日志收集器中。
**验证需求：2.1, 2.2**

### 属性 5: 日志缓冲区大小限制
*对于任何*超过1000行的日志序列，日志收集器应该只保留最新的1000行。
**验证需求：2.4**

### 属性 6: 清空日志操作的完整性
*对于任何*日志状态，执行清空操作后，日志收集器应该返回空列表。
**验证需求：2.5**

### 属性 7: 配置往返一致性
*对于任何*有效的配置对象，保存到文件后再加载，应该得到等价的配置对象。
**验证需求：3.2**

### 属性 8: 无效配置拒绝
*对于任何*格式无效的配置数据，验证函数应该返回False并提供错误消息。
**验证需求：3.4**

### 属性 9: 路径验证正确性
*对于任何*不指向有效可执行文件的路径，验证函数应该拒绝该路径。
**验证需求：3.5, 7.5**

### 属性 10: 版本比较正确性
*对于任何*两个版本号，如果远程版本号大于本地版本号，更新检查器应该报告有更新可用。
**验证需求：4.4, 4.5**

### 属性 11: 主题切换往返一致性
*对于任何*主题设置（light或dark），保存到本地存储后再读取，应该得到相同的主题值。
**验证需求：8.1, 8.3**

### 属性 12: 窗口尺寸往返一致性
*对于任何*有效的窗口尺寸，保存到本地存储后再读取，应该得到相同的尺寸值。
**验证需求：8.2, 8.4**

### 属性 13: 进程状态显示一致性
*对于任何*进程状态集合，首页显示的状态概览应该包含所有进程的当前状态。
**验证需求：6.3**

### 属性 14: 日志预览最新性
*对于任何*日志集合，首页显示的日志预览应该包含时间戳最新的日志条目。
**验证需求：6.6**

### 属性 15: 启动失败错误报告
*对于任何*导致启动失败的情况，系统应该捕获错误并向用户显示包含失败原因的消息。
**验证需求：7.1**

### 属性 16: 文件存在性检查正确性
*对于任何*文件路径，如果该路径指向的文件存在于文件系统中，检查函数应该返回True。
**验证需求：9.1**

### 属性 17: 下载进度报告完整性
*对于任何*下载过程，进度回调应该至少被调用一次，且最后一次调用的已下载字节数应该等于总字节数。
**验证需求：9.4**

### 属性 18: 下载文件完整性
*对于任何*成功的下载操作，下载完成后指定路径应该存在一个文件。
**验证需求：9.5**

## 错误处理

### 错误类型

1. **进程错误**
   - 启动失败：可执行文件不存在、权限不足、端口占用
   - 运行时崩溃：进程异常退出
   - 停止失败：进程无响应

2. **配置错误**
   - 文件不存在：创建默认配置
   - 格式错误：显示错误并使用默认配置
   - 验证失败：阻止保存并提示用户

3. **网络错误**
   - API请求失败：显示错误消息
   - 超时：10秒后终止请求
   - 解析错误：显示格式错误消息

4. **文件系统错误**
   - 读取失败：使用默认值并提示
   - 写入失败：保留原值并提示
   - 权限错误：显示权限不足消息

### 错误处理策略

1. **用户友好的错误消息**
   - 使用简单语言描述问题
   - 提供可能的解决方案
   - 避免技术术语和堆栈跟踪

2. **优雅降级**
   - 配置加载失败时使用默认值
   - 版本检测失败时显示"未知"
   - 单个进程失败不影响其他进程

3. **错误日志**
   - 记录所有错误到日志文件
   - 包含时间戳和上下文信息
   - 便于问题排查

4. **用户反馈**
   - 使用对话框显示关键错误
   - 使用状态栏显示非关键提示
   - 使用颜色区分错误级别

## 测试策略

### 单元测试

使用pytest框架进行单元测试，覆盖以下方面：

1. **核心逻辑测试**
   - ProcessManager的启动/停止逻辑
   - ConfigManager的读写和验证
   - LogCollector的缓冲和过滤
   - UpdateChecker的版本比较

2. **边缘情况测试**
   - 空配置文件
   - 无效JSON格式
   - 不存在的可执行文件路径
   - 网络超时
   - 进程崩溃

3. **集成测试**
   - 进程启动到日志捕获的完整流程
   - 配置修改到进程重启的流程
   - 更新检查到版本显示的流程

### 属性测试

使用Hypothesis库进行属性测试，验证通用正确性属性：

**配置要求：**
- 每个属性测试应该运行至少100次迭代
- 使用合适的生成器生成测试数据
- 每个测试必须用注释标注对应的设计文档属性

**测试标注格式：**
```python
# Feature: qq-bot-manager, Property 7: 配置往返一致性
@given(config=valid_config_strategy())
def test_config_roundtrip(config):
    ...
```

**属性测试覆盖：**
1. 配置往返一致性（属性7）
2. 日志缓冲区大小限制（属性5）
3. 版本比较正确性（属性10）
4. 主题和窗口尺寸往返（属性11、12）
5. 路径验证（属性9）

### UI测试

由于Flet的特性，UI测试主要通过手动测试：

1. **视觉测试**
   - 主题切换效果
   - 响应式布局
   - 动画和过渡

2. **交互测试**
   - 按钮点击响应
   - 导航流畅性
   - 实时日志更新

3. **跨平台测试**
   - Windows、macOS、Linux上的表现
   - 不同分辨率下的显示

## 性能考虑

### 日志性能

1. **缓冲策略**
   - 使用deque实现固定大小的环形缓冲区
   - 批量更新UI而非逐行更新
   - 限制UI刷新频率（如每100ms）

2. **内存管理**
   - 限制日志行数为1000行
   - 及时释放已停止进程的日志
   - 避免在内存中保存完整历史

### UI响应性

1. **异步操作**
   - 所有I/O操作使用异步
   - 进程启动/停止不阻塞UI
   - GitHub API调用在后台线程

2. **延迟加载**
   - 日志页面按需加载历史日志
   - 配置页面延迟验证

### 资源监控

1. **轻量级监控**
   - 使用psutil库获取CPU和内存
   - 每5秒更新一次
   - 只监控托管进程

## 安全考虑

1. **路径验证**
   - 验证所有文件路径防止路径遍历
   - 检查可执行文件的有效性
   - 避免执行任意命令

2. **配置安全**
   - 验证配置值的合法性
   - 限制端口范围
   - 清理用户输入

3. **进程隔离**
   - 托管进程在独立的进程空间运行
   - 捕获并处理进程崩溃
   - 避免僵尸进程

## 部署和打包

### 打包工具

使用PyInstaller将应用打包为独立可执行文件：

```bash
pyinstaller --name="QQ Bot Manager" \
            --windowed \
            --icon=icon.ico \
            --add-data="assets:assets" \
            main.py
```

### 依赖管理

使用requirements.txt管理依赖：

```
flet>=0.21.0
requests>=2.31.0
psutil>=5.9.0
packaging>=23.0
hypothesis>=6.0.0  # 用于属性测试
pytest>=7.0.0      # 用于单元测试
```

### 版本管理

在`__version__.py`中定义版本号：

```python
__version__ = "1.0.0"
```

### 发布流程

1. 更新版本号
2. 运行所有测试
3. 构建可执行文件
4. 创建GitHub Release
5. 上传构建产物

