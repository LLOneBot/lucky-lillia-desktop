# 需求文档

## 简介

QQ机器人管理器是一个基于Flet框架开发的桌面应用程序，用于管理和监控QQ机器人相关的后端服务。该系统负责启动、停止和监控两个核心CLI程序（pmhq.exe和LLOneBot），提供实时日志查看、配置管理、版本更新检查等功能，为用户提供统一的可视化管理界面。

## 术语表

- **QQ机器人管理器**：本桌面应用程序系统
- **PMHQ进程**：pmhq.exe可执行程序进程
- **LLOneBot进程**：通过node.exe运行llonebot.js的进程
- **托管进程**：PMHQ进程和LLOneBot进程的统称
- **日志流**：托管进程的标准输出和标准错误输出
- **配置文件**：pmhq_config.json配置文件
- **GitHub发布版本**：GitHub仓库中的release tag版本
- **本地版本**：当前安装的程序版本号
- **Flet框架**：用于构建本应用的Python UI框架

## 需求

### 需求 1：进程生命周期管理

**用户故事：** 作为QQ机器人管理员，我希望能够启动和停止机器人服务进程，以便控制机器人的运行状态。

#### 验收标准

1. WHEN 用户点击启动PMHQ按钮 THEN QQ机器人管理器 SHALL 启动PMHQ进程并显示运行状态
2. WHEN 用户点击启动LLOneBot按钮 THEN QQ机器人管理器 SHALL 使用node.exe启动llonebot.js进程并显示运行状态
3. WHEN 用户点击停止按钮 THEN QQ机器人管理器 SHALL 终止对应的托管进程并更新状态显示
4. WHEN 托管进程异常退出 THEN QQ机器人管理器 SHALL 检测到退出事件并更新进程状态为已停止
5. WHEN QQ机器人管理器关闭 THEN QQ机器人管理器 SHALL 终止所有正在运行的托管进程

### 需求 2：实时日志监控

**用户故事：** 作为QQ机器人管理员，我希望能够实时查看机器人服务的日志输出，以便监控运行状态和排查问题。

#### 验收标准

1. WHEN 托管进程产生标准输出 THEN QQ机器人管理器 SHALL 在日志页面实时显示该输出内容
2. WHEN 托管进程产生标准错误输出 THEN QQ机器人管理器 SHALL 在日志页面实时显示该错误内容
3. WHEN 用户切换到日志页面 THEN QQ机器人管理器 SHALL 显示所有托管进程的日志流
4. WHEN 日志内容超过1000行 THEN QQ机器人管理器 SHALL 自动删除最旧的日志行以保持性能
5. WHEN 用户点击清空日志按钮 THEN QQ机器人管理器 SHALL 清除当前显示的所有日志内容

### 需求 3：配置文件管理

**用户故事：** 作为QQ机器人管理员，我希望能够通过图形界面编辑PMHQ配置，以便无需手动编辑JSON文件。

#### 验收标准

1. WHEN 用户打开配置页面 THEN QQ机器人管理器 SHALL 读取并显示pmhq_config.json的所有配置项
2. WHEN 用户修改配置项并保存 THEN QQ机器人管理器 SHALL 将更改写入pmhq_config.json文件
3. WHEN pmhq_config.json文件不存在 THEN QQ机器人管理器 SHALL 创建包含默认值的新配置文件
4. WHEN 配置文件格式无效 THEN QQ机器人管理器 SHALL 显示错误消息并阻止保存操作
5. WHEN 用户修改qq_path配置 THEN QQ机器人管理器 SHALL 验证路径指向有效的可执行文件

### 需求 4：版本更新检查

**用户故事：** 作为QQ机器人管理员，我希望系统能够检查各组件的更新，以便及时获取新功能和修复。

#### 验收标准

1. WHEN 用户点击检查更新按钮 THEN QQ机器人管理器 SHALL 查询PMHQ的GitHub仓库获取最新发布版本
2. WHEN 用户点击检查更新按钮 THEN QQ机器人管理器 SHALL 查询LLOneBot的GitHub仓库获取最新发布版本
3. WHEN 用户点击检查更新按钮 THEN QQ机器人管理器 SHALL 查询自身的GitHub仓库获取最新发布版本
4. WHEN GitHub发布版本高于本地版本 THEN QQ机器人管理器 SHALL 显示更新可用提示和版本号差异
5. WHEN GitHub发布版本等于或低于本地版本 THEN QQ机器人管理器 SHALL 显示当前版本为最新
6. WHEN 网络请求失败 THEN QQ机器人管理器 SHALL 显示检查更新失败的错误消息

### 需求 5：版本信息显示

**用户故事：** 作为QQ机器人管理员，我希望能够查看各组件的当前版本号，以便了解系统状态。

#### 验收标准

1. WHEN 用户打开关于页面 THEN QQ机器人管理器 SHALL 显示PMHQ的本地版本号
2. WHEN 用户打开关于页面 THEN QQ机器人管理器 SHALL 显示LLOneBot的本地版本号
3. WHEN 用户打开关于页面 THEN QQ机器人管理器 SHALL 显示QQ机器人管理器自身的版本号
4. WHEN 无法检测到组件版本 THEN QQ机器人管理器 SHALL 显示版本未知标识

### 需求 6：用户界面设计

**用户故事：** 作为QQ机器人管理员，我希望应用界面美观现代，以便获得良好的使用体验。

#### 验收标准

1. THE QQ机器人管理器 SHALL 使用现代化的Material Design设计语言
2. THE QQ机器人管理器 SHALL 提供深色和浅色主题切换功能
3. THE QQ机器人管理器 SHALL 在首页显示所有托管进程的运行状态概览
4. THE QQ机器人管理器 SHALL 在首页显示快速启动和停止按钮
5. THE QQ机器人管理器 SHALL 使用侧边导航栏组织不同功能页面
6. THE QQ机器人管理器 SHALL 在首页显示最近的关键日志条目预览
7. THE QQ机器人管理器 SHALL 在首页显示系统资源使用情况（CPU和内存）

### 需求 7：错误处理

**用户故事：** 作为QQ机器人管理员，我希望系统能够妥善处理错误情况，以便了解问题并采取措施。

#### 验收标准

1. WHEN 托管进程启动失败 THEN QQ机器人管理器 SHALL 显示包含失败原因的错误对话框
2. WHEN 配置文件读取失败 THEN QQ机器人管理器 SHALL 显示错误消息并使用默认配置
3. WHEN 配置文件写入失败 THEN QQ机器人管理器 SHALL 显示错误消息并保留原有配置
4. WHEN GitHub API请求超时 THEN QQ机器人管理器 SHALL 在10秒后终止请求并显示超时消息
5. WHEN 可执行文件路径无效 THEN QQ机器人管理器 SHALL 阻止启动操作并提示用户检查配置

### 需求 8：应用程序持久化

**用户故事：** 作为QQ机器人管理员，我希望应用能够记住我的设置，以便下次启动时保持一致的体验。

#### 验收标准

1. WHEN 用户切换主题 THEN QQ机器人管理器 SHALL 保存主题选择到本地存储
2. WHEN 用户调整窗口大小 THEN QQ机器人管理器 SHALL 保存窗口尺寸到本地存储
3. WHEN QQ机器人管理器启动 THEN QQ机器人管理器 SHALL 恢复上次保存的主题设置
4. WHEN QQ机器人管理器启动 THEN QQ机器人管理器 SHALL 恢复上次保存的窗口尺寸
