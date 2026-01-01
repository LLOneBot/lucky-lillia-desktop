# PyInstaller hook for flet
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 排除不需要的模块
excludedimports = ['flet.testing']

datas, binaries, hiddenimports = collect_all('flet', exclude_datas=['testing'])

# flet_core 和 flet_runtime 在新版本中可能不是独立包，忽略警告
try:
    datas += collect_data_files('flet_core')
except Exception:
    pass
try:
    datas += collect_data_files('flet_runtime')
except Exception:
    pass

# 收集 flet_desktop 包（包含 flet.exe 桌面客户端）
datas += collect_data_files('flet_desktop', include_py_files=True)
hiddenimports += collect_submodules('flet_desktop')

# 过滤掉 flet.testing 相关的 hiddenimports
hiddenimports = [h for h in hiddenimports if 'testing' not in h]
hiddenimports += [h for h in collect_submodules('flet') if 'testing' not in h]

try:
    hiddenimports += collect_submodules('flet_core')
except Exception:
    pass
try:
    hiddenimports += collect_submodules('flet_runtime')
except Exception:
    pass
