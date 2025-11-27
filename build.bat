@echo off
REM 幸运莉莉娅打包脚本

echo ========================================
echo 幸运莉莉娅 - 打包脚本
echo ========================================
echo.

REM 检查是否安装了PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [错误] 未安装PyInstaller
    echo 正在安装PyInstaller...
    uv pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo [1/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] 开始打包应用...
pyinstaller lucky-lillia-desktop.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo [3/3] 打包完成！
echo.
echo 可执行文件位置: dist\幸运莉莉娅.exe
echo.
echo ========================================
echo 打包成功完成！
echo ========================================
pause
