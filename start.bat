@echo off
chcp 65001 >nul
title 视频号下载器

echo ========================================
echo   视频号下载器 - 一键启动
echo ========================================
echo.

:: 检查 wx-dl.exe 是否存在
if not exist "%~dp0bin\wx-dl.exe" (
    echo [ERROR] 找不到 bin\wx-dl.exe
    echo 请先编译: cd backend/core ^&^& go build -o ..\..\..\scribe-transcribe\bin\wx-dl.exe .
    pause
    exit /b 1
)

:: 启动代理服务（管理员权限）
echo [INFO] 启动视频号代理服务...
echo [INFO] API 地址: http://127.0.0.1:2022
echo [INFO] 代理端口: 2023
echo.
echo 请在手机 WiFi 中配置 HTTP 代理:
echo   服务器: 电脑IP (见下方)
echo   端口:   2023
echo.

:: 显示本机 IP
echo 本机 IP 地址:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    echo   %%a
)
echo.

:: 启动
"%~dp0bin\wx-dl.exe" --hostname 127.0.0.1 --port 2023

pause
