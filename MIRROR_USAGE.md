# GitHub镜像使用说明

## 概述

本项目集成了GitHub镜像管理功能，可以自动选择最快的可用镜像进行下载和API访问，提高在中国大陆地区的访问速度。

## 镜像管理器 (MirrorManager)

### 功能特性

1. **自动镜像选择** - 自动测试所有配置的镜像，选择第一个可用的
2. **智能缓存** - 找到可用镜像后缓存结果，避免重复测试
3. **自动降级** - 如果所有镜像都不可用，使用直连GitHub
4. **URL转换** - 自动将GitHub URL转换为镜像URL

### 配置镜像

镜像列表在 `utils/constants.py` 中配置：

```python
GITHUB_MIRRORS = [
    "https://github.com/",  # 直连GitHub
    "https://gh-proxy.com/https://github.com/",  # 镜像1
    # 可以添加更多镜像...
]
```

### 使用示例

#### 1. 基本使用

```python
from utils.mirror_manager import MirrorManager

# 创建镜像管理器
mirror_manager = MirrorManager()

# 获取可用镜像
available_mirror = mirror_manager.get_available_mirror()
print(f"使用镜像: {available_mirror}")

# 转换GitHub URL
github_url = "https://github.com/owner/repo/releases/download/v1.0/file.exe"
mirror_url = mirror_manager.transform_url(github_url)
print(f"镜像URL: {mirror_url}")
```

#### 2. 在下载器中使用

下载器 (`Downloader`) 已经自动集成了镜像管理：

```python
from utils.downloader import Downloader

# 创建下载器（自动创建镜像管理器）
downloader = Downloader()

# 下载文件（自动使用镜像）
def progress_callback(downloaded, total):
    print(f"下载进度: {downloaded}/{total} bytes")

downloader.download_pmhq("path/to/save.exe", progress_callback)
```

#### 3. 在GitHub API中使用

GitHub API (`get_latest_release`) 也已经集成了镜像管理：

```python
from utils.github_api import get_latest_release
from utils.mirror_manager import MirrorManager

# 创建镜像管理器
mirror_manager = MirrorManager()

# 获取最新release（自动使用镜像）
release_info = get_latest_release(
    "owner/repo",
    mirror_manager=mirror_manager
)
```

## 工作流程

### 1. 镜像测试

当第一次调用 `get_available_mirror()` 时：

1. 按顺序测试每个镜像（发送HEAD请求）
2. 返回第一个响应成功的镜像（状态码 < 400）
3. 缓存结果供后续使用

### 2. URL转换

```python
# 原始GitHub URL
original = "https://github.com/owner/repo/releases/download/v1.0/file.exe"

# 使用镜像转换
mirror = "https://gh-proxy.com/https://github.com/"
transformed = mirror_manager.transform_url(original, mirror)
# 结果: "https://gh-proxy.com/https://github.com/owner/repo/releases/download/v1.0/file.exe"
```

### 3. 下载流程

下载PMHQ时的完整流程：

1. **获取下载URL**
   - 调用 `get_latest_release()` 获取最新版本信息（使用镜像）
   - 构建下载URL
   - 使用 `get_available_mirror()` 获取可用镜像
   - 转换URL为镜像URL

2. **下载文件**
   - 遍历所有镜像
   - 对每个镜像尝试下载
   - 如果失败，尝试下一个镜像
   - 报告下载进度

## API参考

### MirrorManager

#### `__init__(timeout: int = 5)`
创建镜像管理器实例。

- `timeout`: 测试镜像可用性的超时时间（秒）

#### `get_available_mirror() -> str`
获取可用的镜像URL。

- 返回: 可用的镜像URL
- 如果已有缓存，直接返回缓存的镜像
- 如果没有缓存，测试所有镜像并返回第一个可用的

#### `transform_url(github_url: str, mirror: Optional[str] = None) -> str`
将GitHub URL转换为镜像URL。

- `github_url`: 原始GitHub URL
- `mirror`: 要使用的镜像，如果为None则自动选择
- 返回: 转换后的URL

#### `get_all_mirrors() -> List[str]`
获取所有配置的镜像列表。

- 返回: 镜像URL列表

#### `reset_cache()`
重置缓存的可用镜像。

在网络环境变化时可以调用此方法重新测试镜像。

### Downloader

#### `get_pmhq_download_url(use_mirror: bool = True) -> str`
获取PMHQ最新版本的下载URL。

- `use_mirror`: 是否使用镜像转换URL，默认为True
- 返回: 下载URL（如果use_mirror=True则返回镜像URL）

#### `download_pmhq(save_path: str, progress_callback: Optional[Callable] = None) -> bool`
下载PMHQ可执行文件。

- `save_path`: 保存路径
- `progress_callback`: 进度回调函数，参数为(已下载字节数, 总字节数)
- 返回: 下载成功返回True，失败返回False

## 故障排除

### 所有镜像都不可用

如果所有镜像都不可用，系统会：
1. 返回第一个镜像（直连GitHub）
2. 尝试使用直连下载
3. 如果仍然失败，抛出 `NetworkError`

### 重置镜像缓存

如果网络环境变化（例如从公司网络切换到家庭网络），可以重置缓存：

```python
downloader = Downloader()
downloader.mirror_manager.reset_cache()
```

### 添加新镜像

在 `utils/constants.py` 中添加新镜像：

```python
GITHUB_MIRRORS = [
    "https://github.com/",
    "https://gh-proxy.com/https://github.com/",
    "https://your-new-mirror.com/https://github.com/",  # 新镜像
]
```

## 性能优化

1. **缓存机制** - 第一次测试后缓存可用镜像，后续调用直接使用缓存
2. **快速失败** - 每个镜像测试超时时间为5秒，快速切换到下一个
3. **并行下载** - 下载使用流式传输，支持大文件下载

## 测试

运行镜像管理器测试：

```bash
python -m pytest tests/test_mirror_manager.py -v
```

运行所有相关测试：

```bash
python -m pytest tests/test_mirror_manager.py tests/test_downloader.py tests/test_github_api.py -v
```
