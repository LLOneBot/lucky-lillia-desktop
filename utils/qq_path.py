from pathlib import Path


def get_win_reg_qq_path():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\QQ')
        qq_uninstall_path, _ = winreg.QueryValueEx(key, 'UninstallString')
        # print('获取到注册表 QQ 安装路径:', qq_uninstall_path)
        if qq_uninstall_path and qq_uninstall_path[0] == '"':
            qq_uninstall_path = qq_uninstall_path[1:-1]
        return Path(qq_uninstall_path).parent / 'QQ.exe'
    except Exception as e:
        print(f'获取QQ安装路径失败: {e}')
        return None