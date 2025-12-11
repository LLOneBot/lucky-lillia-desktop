# PyInstaller hook for flet
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas, binaries, hiddenimports = collect_all('flet')
datas += collect_data_files('flet_core')
datas += collect_data_files('flet_runtime')
hiddenimports += collect_submodules('flet')
hiddenimports += collect_submodules('flet_core')
hiddenimports += collect_submodules('flet_runtime')
