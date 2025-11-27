# QQ机器人管理器 - 发布说明

## 版本 1.0.0

### 功能特性

#### 核心功能
- ✅ **进程管理**
  - 启动/停止 PMHQ 进程
  - 启动/停止 LLOneBot 进程
  - 实时进程状态监控
  - 异常退出检测和处理
  - 基于PID的精确进程跟踪

- ✅ **日志管理**
  - 实时日志收集和显示
  - 支持按进程过滤日志
  - 区分 stdout 和 stderr 输出
  - 固定大小环形缓冲区（最大1000行）
  - 日志清空功能

- ✅ **配置管理**
  - 可视化配置编辑界面
  - 配置验证和错误提示
  - 默认配置生成
  - 配置重置功能
  - 支持自动启动选项

- ✅ **版本管理**
  - 自动检测本地组件版本
  - GitHub Release 更新检查
  - 支持检查多个组件更新
  - 10秒超时保护

- ✅ **用户界面**
  - Material Design 风格
  - 浅色/深色主题切换
  - 响应式布局
  - 流畅的页面切换动画
  - 实时资源监控显示

#### 系统监控
- CPU 使用率监控
- 内存使用监控
- 进程状态实时更新
- 资源使用可视化

#### 组件下载
- PMHQ 自动下载功能
- 下载进度显示
- 下载失败处理

### 技术栈

- **UI框架**: Flet 0.21.0+
- **系统监控**: psutil 5.9.0+
- **HTTP客户端**: requests 2.31.0+
- **版本比较**: packaging 23.0+
- **打包工具**: PyInstaller 6.0.0+

### 测试覆盖

- ✅ 92个单元测试全部通过
- ✅ 配置管理测试
- ✅ 进程管理测试
- ✅ 日志收集测试
- ✅ UI组件测试
- ✅ 版本检测测试
- ✅ 更新检查测试
- ✅ 存储管理测试

### 打包说明

本应用支持打包为独立的Windows可执行文件：

1. **单文件模式**: 所有依赖打包到一个 .exe 文件
2. **无控制台**: 启动时不显示命令行窗口
3. **UPX压缩**: 减小文件大小
4. **自定义图标**: 支持自定义应用图标

详细打包说明请参考 [BUILD.md](BUILD.md)

### 使用方法

#### 开发环境运行

```bash
# 安装依赖
uv pip install -r requirements.txt

# 运行应用
uv run python main.py
```

#### 打包发布

```bash
# 方法1: 使用批处理脚本
build.bat

# 方法2: 手动打包
pyinstaller qq-bot-manager.spec
```

### 配置文件

应用首次运行时会自动创建默认配置文件 `config.json`。

配置示例请参考 [config.example.json](config.example.json)

### 目录结构

```
QQ机器人管理器/
├── core/              # 核心业务逻辑
│   ├── config_manager.py
│   ├── process_manager.py
│   ├── log_collector.py
│   ├── version_detector.py
│   └── update_checker.py
├── ui/                # 用户界面
│   ├── main_window.py
│   ├── home_page.py
│   ├── log_page.py
│   ├── config_page.py
│   ├── about_page.py
│   ├── theme.py
│   └── animations.py
├── utils/             # 工具模块
│   ├── constants.py
│   ├── storage.py
│   ├── github_api.py
│   └── downloader.py
├── tests/             # 测试文件
├── logs/              # 日志目录
├── bin/               # 外部组件目录
│   └── pmhq/
├── main.py            # 应用入口
└── config.json        # 配置文件
```

### 已知限制

1. 目前仅支持 Windows 平台
2. PMHQ 下载功能需要配置正确的下载URL
3. 进程监控依赖于 psutil 库的权限

### 未来计划

- [ ] 支持 Linux 和 macOS 平台
- [ ] 添加进程日志导出功能
- [ ] 支持多语言界面
- [ ] 添加插件系统
- [ ] 支持远程管理功能

### 贡献

欢迎提交 Issue 和 Pull Request！

### 许可证

待定

---

**发布日期**: 2025-11-25
**版本**: 1.0.0
