# 实施计划

- [x] 1. 设置项目结构和核心接口





  - 创建目录结构：ui/, core/, utils/
  - 设置requirements.txt和依赖项
  - 创建__version__.py定义应用版本
  - 创建constants.py定义常量（GitHub仓库URL、默认配置等）
  - _需求：所有需求的基础_

- [x] 2. 实现配置管理模块





  - 编写ConfigManager类，实现加载、保存、验证配置
  - 实现默认配置生成逻辑
  - 实现配置验证函数（检查必需字段、类型、路径有效性）
  - _需求：3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 编写配置管理的属性测试
  - **属性 7: 配置往返一致性**
  - **验证需求：3.2**

- [ ]* 2.2 编写配置管理的属性测试
  - **属性 8: 无效配置拒绝**
  - **验证需求：3.4**

- [ ]* 2.3 编写配置管理的属性测试
  - **属性 9: 路径验证正确性**
  - **验证需求：3.5, 7.5**

- [ ]* 2.4 编写配置管理的单元测试
  - 测试默认配置生成
  - 测试配置文件不存在的情况
  - 测试无效JSON格式处理
  - _需求：3.3, 7.2_

- [x] 3. 实现进程管理模块





  - 编写ProcessManager类
  - 实现start_pmhq方法，使用subprocess启动pmhq.exe
  - 实现start_llonebot方法，使用subprocess启动node.exe llonebot.js
  - 实现stop_process方法，终止指定进程
  - 实现get_process_status方法，查询进程状态
  - 实现stop_all方法，清理所有进程
  - 处理进程启动失败和异常退出
  - _需求：1.1, 1.2, 1.3, 1.4, 1.5, 7.1_

- [ ]* 3.1 编写进程管理的属性测试
  - **属性 1: 进程启动后状态为运行中**
  - **验证需求：1.1, 1.2**

- [ ]* 3.2 编写进程管理的属性测试
  - **属性 2: 进程停止后状态为已停止**
  - **验证需求：1.3**

- [ ]* 3.3 编写进程管理的属性测试
  - **属性 3: 应用关闭时清理所有进程**
  - **验证需求：1.5**

- [ ]* 3.4 编写进程管理的属性测试
  - **属性 15: 启动失败错误报告**
  - **验证需求：7.1**

- [ ]* 3.5 编写进程管理的单元测试
  - 测试进程异常退出检测
  - 测试无效可执行文件路径处理
  - 测试进程启动失败场景
  - _需求：1.4, 7.1, 7.5_

- [x] 4. 实现日志收集模块

  - 编写LogCollector类
  - 实现attach_process方法，附加到进程的stdout和stderr
  - 使用线程异步读取进程输出
  - 实现固定大小的环形缓冲区（使用deque，最大1000行）
  - 实现get_logs方法，支持按进程名过滤
  - 实现clear_logs方法
  - 实现回调机制用于实时UI更新
  - _需求：2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 4.1 编写日志收集的属性测试
  - **属性 4: 日志捕获完整性**
  - **验证需求：2.1, 2.2**

- [ ]* 4.2 编写日志收集的属性测试
  - **属性 5: 日志缓冲区大小限制**
  - **验证需求：2.4**

- [ ]* 4.3 编写日志收集的属性测试
  - **属性 6: 清空日志操作的完整性**
  - **验证需求：2.5**

- [ ]* 4.4 编写日志收集的单元测试
  - 测试多进程日志混合
  - 测试stdout和stderr区分
  - 测试日志时间戳
  - _需求：2.1, 2.2, 2.3_

- [x] 5. 实现版本检测模块





  - 编写VersionDetector类
  - 实现detect_pmhq_version方法（通过运行pmhq.exe --version或解析文件元数据）
  - 实现detect_llonebot_version方法（解析package.json或llonebot.js文件头）
  - 实现get_app_version方法（从__version__.py读取）
  - 处理版本检测失败的情况
  - _需求：5.1, 5.2, 5.3, 5.4_

- [ ]* 5.1 编写版本检测的单元测试
  - 测试版本检测失败返回None
  - 测试不同版本格式的解析
  - _需求：5.4_

- [x] 6. 实现GitHub API和更新检查模块






  - 编写github_api.py封装GitHub API调用
  - 实现获取最新release的函数
  - 实现10秒超时机制
  - 编写UpdateChecker类
  - 实现check_update方法，比较版本号
  - 使用packaging库进行版本比较
  - 实现check_all_updates方法，检查所有组件
  - 处理网络错误和超时
  - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 7.4_

- [ ]* 6.1 编写更新检查的属性测试
  - **属性 10: 版本比较正确性**
  - **验证需求：4.4, 4.5**

- [ ]* 6.2 编写更新检查的单元测试
  - 测试网络请求失败处理
  - 测试超时处理
  - 测试无效响应格式处理
  - _需求：4.6, 7.4_

- [x] 7. 实现本地存储模块





  - 编写storage.py实现持久化存储
  - 使用json文件存储应用设置（主题、窗口尺寸等）
  - 实现save_setting和load_setting方法
  - 处理文件读写错误
  - _需求：8.1, 8.2, 8.3, 8.4, 7.3_

- [ ]* 7.1 编写本地存储的属性测试
  - **属性 11: 主题切换往返一致性**
  - **验证需求：8.1, 8.3**

- [ ]* 7.2 编写本地存储的属性测试
  - **属性 12: 窗口尺寸往返一致性**
  - **验证需求：8.2, 8.4**

- [ ]* 7.3 编写本地存储的单元测试
  - 测试文件写入失败处理
  - 测试文件不存在时的默认值
  - _需求：7.3_
-

- [x] 8. 实现主题配置




  - 创建theme.py定义Material Design主题
  - 定义浅色主题配色方案
  - 定义深色主题配色方案
  - 创建主题切换函数
  - _需求：6.1, 6.2_

- [x] 9. 实现首页UI





  - 创建home_page.py
  - 实现进程状态卡片组件，显示PMHQ和LLOneBot的运行状态
  - 实现快速启动/停止按钮
  - 实现最近日志预览区域（显示最新5-10条日志）
  - 使用psutil实现系统资源监控（CPU和内存使用率）
  - 实现资源使用情况显示组件
  - 连接ProcessManager和LogCollector获取实时数据
  - _需求：6.3, 6.4, 6.6, 6.7_

- [ ]* 9.1 编写首页UI的属性测试
  - **属性 13: 进程状态显示一致性**
  - **验证需求：6.3**

- [ ]* 9.2 编写首页UI的属性测试
  - **属性 14: 日志预览最新性**
  - **验证需求：6.6**

- [x] 10. 实现日志页面UI





  - 创建log_page.py
  - 实现日志显示组件（使用ListView或Column）
  - 实现进程过滤器（显示所有/仅PMHQ/仅LLOneBot）
  - 实现清空日志按钮
  - 实现自动滚动到底部功能
  - 使用不同颜色区分stdout和stderr
  - 连接LogCollector的回调实现实时更新
  - _需求：2.1, 2.2, 2.3, 2.5_

- [x] 11. 实现配置页面UI





  - 创建config_page.py
  - 为每个配置项创建输入组件（TextField、Checkbox、NumberField）
  - 实现qq_path的文件选择器
  - 实现保存按钮和重置按钮
  - 实现配置验证和错误提示
  - 连接ConfigManager加载和保存配置
  - _需求：3.1, 3.2, 3.4, 3.5_

- [x] 12. 实现关于/版本页面UI





  - 创建about_page.py
  - 显示应用名称、版本号、描述
  - 显示PMHQ版本号
  - 显示LLOneBot版本号
  - 实现检查更新按钮
  - 显示更新检查结果（有更新/已是最新/检查失败）
  - 显示GitHub仓库链接
  - 连接VersionDetector和UpdateChecker
  - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4_

- [x] 13. 实现主窗口和导航





  - 创建main_window.py
  - 实现侧边导航栏（NavigationRail或Drawer）
  - 添加导航项：首页、日志、配置、关于
  - 实现页面切换逻辑
  - 实现主题切换按钮
  - 从本地存储恢复窗口尺寸和主题
  - 实现窗口关闭时的清理逻辑（停止所有进程、保存设置）
  - _需求：6.2, 6.5, 8.1, 8.2, 8.3, 8.4, 1.5_

- [x] 14. 实现主入口和应用初始化





  - 创建main.py
  - 初始化所有管理器（ProcessManager、LogCollector、ConfigManager等）
  - 创建Flet应用实例
  - 设置应用标题、图标、窗口大小
  - 启动主窗口
  - 实现优雅的错误处理和日志记录
  - _需求：所有需求的集成_

- [x] 15. 检查点 - 确保所有测试通过





  - 确保所有测试通过，如有问题请询问用户

- [x] 16. UI优化和打磨





  - 调整间距、对齐、字体大小
  - 添加图标和视觉元素
  - 实现加载动画和过渡效果
  - 优化颜色对比度和可读性
  - 测试响应式布局
  - _需求：6.1_




- [x] 17. 创建打包配置
  - 创建PyInstaller配置文件（.spec文件）
  - 准备应用图标（icon.ico）
  - 配置打包选项（单文件/文件夹、控制台隐藏等）

  - 测试打包后的可执行文件
  - _需求：部署需求_

- [x] 18. 最终检查点 - 确保所有测试通过





  - 确保所有测试通过，如有问题请询问用户

- [x] 19. 实现文件下载管理模块





  - 创建utils/downloader.py
  - 实现Downloader类
  - 实现get_pmhq_download_url方法，从GitHub API获取最新release的下载链接
  - 实现download_pmhq方法，使用requests库下载文件
  - 实现进度回调机制，报告已下载字节数和总字节数
  - 实现check_file_exists方法，检查文件是否存在
  - 处理下载超时和网络错误
  - _需求：9.1, 9.3, 9.4, 9.5, 9.6_

- [x] 19.1 编写下载管理的属性测试






  - **属性 16: 文件存在性检查正确性**
  - **验证需求：9.1**

- [x] 19.2 编写下载管理的属性测试






  - **属性 17: 下载进度报告完整性**
  - **验证需求：9.4**

- [ ]* 19.3 编写下载管理的属性测试
  - **属性 18: 下载文件完整性**
  - **验证需求：9.5**

- [ ]* 19.4 编写下载管理的单元测试
  - 测试下载URL获取失败处理
  - 测试下载超时处理
  - 测试网络错误处理
  - _需求：9.6_

- [x] 20. 在首页添加一个总体启动按钮





  - 点击总体启动按钮会启动pmhq和llonebot(nodejs llonebot.js)
  - 在home_page.py的PMHQ卡片中添加pmhq的状态，运行中、未启动、未下载
  - 实现启动按钮点击处理，检查pmhq.exe是否存在
  - 创建下载提示对话框组件
  - 实现下载进度显示（进度条和百分比）
  - 连接Downloader实现下载功能
  - 实现下载成功和失败的提示
  - 实现取消下载功能
  - _需求：9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ]* 20.1 编写首页启动按钮的单元测试
  - 测试文件存在时直接启动
  - 测试文件不存在时显示下载对话框
  - 测试下载成功后的状态更新
  - _需求：9.1, 9.2, 9.5_

- [ ] 21. 检查点 - 确保下载功能测试通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 22. 无头模式的登录功能


当使用无头模式登录时，弹出一个登录框，登录框有快速登录和扫码登录模式

HTTP POST http://127.0.0.1:<pmhq-port>

post json
```json
{
  "type" : "call",
  "data" : {
    "func" : "loginService.getLoginList",
    "args": []
  }
}
```

response json
```json
{
    "type": "call",
    "data": {
        "echo": "5a67aadd-e261-411f-97a5-c8ea55f85c39",
        "result": {
            "result": 0,
            "LocalLoginInfoList": [
                {
                    "uin": "379450326",
                    "uid": "u_snYxnEfja-Po_cdFcyccRQ",
                    "nickName": "林雨辰的猫找到了",
                    "faceUrl": "https://thirdqq.qlogo.cn/g?b=sdk&k=gRFDbALSu8ZtUpLdCpBYIw&kti=aRPyvhHya-I&s=640&t=1729758283",
                    "facePath": "C:\\Users\\linyu\\Documents\\Tencent Files\\379450326\\nt_qq\\nt_data\\avatar\\user\\92\\b_92974107e59d46994777b6dda07c4469",
                    "loginType": 1,
                    "isQuickLogin": true,
                    "isAutoLogin": false,
                    "isUserLogin": true
                },
                {
                    "uin": "721011692",
                    "uid": "u_qjD9LXs5B-OSCDKBAXTd-w",
                    "nickName": "测试昵称",
                    "faceUrl": "https://thirdqq.qlogo.cn/g?b=sdk&k=6t11HsgLWPjqRJyPXt2iaLA&kti=aRgYwBHya-E&s=640&t=1748765988",
                    "facePath": "C:\\Users\\linyu\\Documents\\Tencent Files\\721011692\\nt_qq\\nt_data\\avatar\\user\\fd\\b_fd8a14c2e331ab022b6d77735fc4f195",
                    "loginType": 1,
                    "isQuickLogin": true,
                    "isAutoLogin": false,
                    "isUserLogin": false
                }
            ]
        }
    }
}
```

再过滤出 isQuickLogin  && !isUserLogin 的账号，就是可以用于快速登录的账号

点击登录就提交 json
```json
quickLoginWithUin
{
  "type" : "call",
  "data" : {
    "func" : "loginService.quickLoginWithUin",
    "args": ["快速登录的uin"]
  }
}
```
登录response
```json
{
    "type": "call",
    "data": {
        "echo": "5a7a9a50-9343-482f-b23a-7210cdd7a323",
        "result": {
            "result": "3",  // 0为成功
            "loginErrorInfo": {
                "step": 0,
                "errMsg": "登录态已失效，请重新登录。",
                "proofWaterUrl": "",
                "newDevicePullQrCodeSig": {},
                "jumpUrl": "",
                "jumpWord": "",
                "tipsTitle": "",
                "tipsContent": "",
                "unusualDeviceQrSig": "",
                "uinToken": ""
            }
        }
    }
}
```

同时修改自动登录QQ号那里的逻辑，现在是把自动登录的QQ号传给了pmhq，现在改成使用HTTP接口登录，需要把登录结果show出来，如果登录失败就弹出失败原因和登录框

如果没有可用于快速登录的账号，就调用获取二维码接口
```json
getQrCode
{
  "type" : "call",
  "data" : {
    "func" : "loginService.getQrCode",
    "args": []
  }
}
```
调用这个接口之前要建立一个 SSE 通信，GET http://127.0.0.1:<pmhq-port>，用于获取二维码的

SSE 会返回 data
```json
{"type":"nodeIKernelLoginListener","data":{"sub_type":"onQRCodeGetPicture","data":{"pngBase64QrcodeData":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJMAAACTAQAAAACinha4AAAACXBIWXMAAAsTAAALEwEAmpwYAAACC0lEQVRIid2WP86lIBTFr6Gg0w2QsA06tqQbUNnAc0t0bIOEDUhHYbxz/N6b+SaZhptMMRligT8Tcu6/g8R/Lvqv2Uk0e5qi2VKeIg0SVvlavQ2JpnYtCa8SFs3SrpmuIV5TokXK0rU1e7q8ydlKilPZvZmkjCG/vMjuZIbv2LoY8rck83m+c9rFsGoyRPaI6viuZRe7XSZnD86j553yImEVQWjL0QY2sxaymElf5GlIZmq0iRiX8CTe7g66rkHEGuJQt6fVq5BUkLDT25PU6coR+dZ8yBiN2t5IYbScbJCwyvbWavf8+k1fL0OPM1SU06nQ3jXvZbe3tZUQy8GoXqkipq9REzp09Tj4HUcv46ZOr3adV59HV1jCTv2cNEJRzEPMk4TVhsNoxYQxZssMEsbYJns/k4FTzSRhSF7lvEUzftV/kLBbY6BRcCJf4A2bhNVoj6QQDQxpSuWQME55SNfsYCS2fvq0m0VsaXVPELNjETs9LKS8nNodmu7nbPUxjhwSnF6dlMm/fbeXQcgWkTne9bW0ImKM5LHaqdSooIglDClHmywxLwlfzCZhWCfGiwoMKfDbD3rZc8/E8viBfryEJQxaZnpChwVW/qWvj+Fe1RhrVAAmag8hm3FXwE4S+t2ykK1Q0crLQ4itIoY4vMUVtz8d95mZTob8wYemxqHlrykRsL/9r/dvsx8fETcdisW2KgAAAABJRU5ErkJggg==","qrcodeUrl":"https://txz.qq.com/p?k=J1CzHoZaqKpMjk2jraUdPJknhAnwDSLk&f=1600001604","expireTime":120,"pollTimeInterval":2}}}
```
同时修改不停获取uin的那个逻辑，如果获取到了uin就表示登录成功，登录弹框就消失

登录框上的切换账号就是list出所有可用于快速登录的账号，如果有可用快速登录的账号，就显示第一个为默认的

点击扫码登录就是走扫码登录的流程

登录框样式参考![快速登录](./img/快速登录.png),![切换账号](./img/切换账号.png),![扫码登录](./img/扫码登录.png)