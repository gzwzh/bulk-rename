@echo off
echo 开始静默安装批量重命名工具...
echo.

REM 检查安装程序是否存在
if not exist "dist\批量重命名_安装程序.exe" (
    echo 错误: 找不到安装程序 "dist\批量重命名_安装程序.exe"
    echo 请先构建安装程序
    pause
    exit /b 1
)

REM 执行静默安装
echo 正在执行静默安装...
"dist\批量重命名_安装程序.exe" /SILENT /NORESTART

REM 检查安装结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo 静默安装完成！
    echo 桌面快捷方式已自动创建
    echo 程序已安装到: %ProgramFiles%\批量重命名\
) else (
    echo.
    echo 安装失败，错误代码: %ERRORLEVEL%
)

echo.
pause