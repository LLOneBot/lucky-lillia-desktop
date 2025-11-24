# QQ机器人管理器

基于 Flet 框架的 QQ 机器人管理桌面应用程序。

## 环境设置

本项目使用 `uv` 进行 Python 环境管理。

### 安装依赖

```bash
# 创建虚拟环境（如果还没有）
uv venv

# 安装项目依赖
uv pip install -e .

# 安装测试依赖
uv pip install -e ".[test]"
```

### 使用 uv 运行代码

```bash
# 运行 Python 脚本
uv run python your_script.py

# 运行测试
uv run pytest

# 运行属性测试
uv run pytest -v tests/
```

### 激活虚拟环境（可选）

如果你想手动激活虚拟环境：

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

## 项目结构

```
.
├── core/              # 核心业务逻辑
│   ├── config_manager.py
│   └── process_manager.py
├── ui/                # 用户界面
├── utils/             # 工具模块
│   └── constants.py
├── pyproject.toml     # 项目配置和依赖
└── README.md
```

## 已实现的功能

- ✅ 配置管理模块 (ConfigManager)
- ✅ 进程管理模块 (ProcessManager)
  - 启动/停止 PMHQ 进程
  - 启动/停止 LLOneBot 进程
  - 进程状态监控
  - 异常退出检测

## 开发

查看 `.kiro/specs/qq-bot-manager/tasks.md` 了解完整的实施计划。
