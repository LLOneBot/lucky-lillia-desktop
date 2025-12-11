# PyInstaller hook for flet
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas, binaries, hiddenimports = collect_all('flet')
datas += collect_data_files('flet_core')
datas += collect_data_files('flet_runtime')

# 收集 flet_desktop 包（包含 flet.exe 桌面客户端）
datas += collect_data_files('flet_desktop', include_py_files=True)
hiddenimports += collect_submodules('flet_desktop')

hiddenimports += collect_submodules('flet')
hiddenimports += collect_submodules('flet_core')
hiddenimports += collect_submodules('flet_runtime')
