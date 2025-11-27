import errno
import socket


def is_local_port_available(port, host='localhost'):
    """
    检查本地端口是否可用（未被占用）

    使用双重检测机制：
    1. 尝试连接端口（检测是否有程序在监听）
    2. 尝试绑定端口（检测是否可以占用）

    :param port: 端口号
    :param host: 绑定的主机地址（默认 localhost）
    :return: True（可用） / False（被占用）
    """
    # 第一步：尝试连接端口，检查是否有服务在监听
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)  # 设置较短超时时间
            result = s.connect_ex((host, port))
            # 如果连接成功（result == 0），说明端口被占用
            if result == 0:
                return False
    except socket.error:
        pass  # 连接异常，继续下一步检测

    # 第二步：尝试绑定端口，检查是否可以占用该端口
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 明确不设置 SO_REUSEADDR，确保准确检测
            s.bind((host, port))
            s.listen(1)  # 尝试监听，进一步确认端口可用
            return True
    except socket.error as e:
        # 常见的端口被占用错误码
        if e.errno in [errno.EADDRINUSE, 10048]:  # Linux: EADDRINUSE, Windows: WSAEADDRINUSE
            return False
        # 权限不足或其他错误，也认为端口不可用
        return False

def get_available_port(init_port, host='localhost', max_attempts=1000):
    """
    获取可用的端口号

    :param init_port: 起始端口号
    :param host: 绑定的主机地址
    :param max_attempts: 最大尝试次数，防止无限循环
    :return: 可用的端口号
    :raises: RuntimeError 如果在最大尝试次数内找不到可用端口
    """
    port = init_port
    attempts = 0

    while attempts < max_attempts:
        if is_local_port_available(port, host):
            return port
        port += 1
        attempts += 1

    raise RuntimeError(f"Unable to find available port starting from {init_port} within {max_attempts} attempts")

