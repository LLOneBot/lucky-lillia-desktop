"""高频日志生成器 - 用于测试日志系统稳定性"""

import time
import sys
import random

MESSAGES = [
    "收到消息: 你好",
    "处理请求中...",
    "WebSocket 连接正常",
    "心跳包发送成功",
    "数据同步完成",
    "用户 12345 上线",
    "群消息推送: [图片]",
    "API 调用成功 200 OK",
    "缓存命中率: 95.2%",
    "内存使用: 128MB",
]

def main():
    count = 0
    interval = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
    
    print(f"开始生成日志，间隔 {interval} 秒", flush=True)
    
    while True:
        count += 1
        msg = random.choice(MESSAGES)
        print(f"[{count}] {msg}", flush=True)
        
        # 偶尔输出到 stderr
        if count % 20 == 0:
            print(f"[WARN] 警告信息 #{count}", file=sys.stderr, flush=True)
        
        time.sleep(interval)

if __name__ == "__main__":
    main()
