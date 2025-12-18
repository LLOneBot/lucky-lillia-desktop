# Code Style

## 注释规范
- 仅在逻辑复杂或难以理解的地方添加注释
- 不要写与变量名/函数名重复的注释（如 `self._uin = None  # 存储QQ号`）
- 不要为显而易见的代码添加注释
- 函数名就已经体现了功能的函数 docstring 不需要保留

## 示例

```python
# 不好的注释
self._port = None  # 存储端口号
def get_status(self):
    """获取状态"""  # 与函数名重复
    
# 好的注释
# ShellExecuteW 返回值 > 32 表示成功
if result > 32:
    ...

# 使用位运算合并多个标志位
flags = FLAG_A | FLAG_B | FLAG_C
```
