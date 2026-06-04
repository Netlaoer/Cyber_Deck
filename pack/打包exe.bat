@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ====================================
echo 赛博义肢 - 一键打包工具
echo ====================================
echo.

REM 检查是否在Cyber_Deck目录
if not exist "logic_gui_Tools.py" (
    echo ❌ 错误：未找到 logic_gui_Tools.py，请将本脚本放在 Cyber_Deck 目录下运行！
    echo 当前目录：%cd%
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
.venv\Scripts\python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：PyInstaller 未安装！
    echo 请先安装：pip install pyinstaller
    pause
    exit /b 1
)

REM 打包前结束已运行的赛博义肢进程（防止旧进程干扰）
tasklist /FI "IMAGENAME eq Cyber_Deck.exe" 2>nul | find /I "Cyber_Deck.exe" >nul
if not errorlevel 1 (
    echo 🔄 检测到正在运行的 Cyber_Deck 进程，正在关闭...
    taskkill /F /IM "Cyber_Deck.exe" >nul 2>&1
    timeout /t 1 /nobreak >nul
)
echo ✅ 开始打包...
echo.

REM 删除旧的构建文件
if exist "pack\build" (
    echo 清理旧的构建文件...
    rmdir /s /q pack\build
)
if exist "Cyber_Deck.exe" (
    echo 清理旧输出...
    del "Cyber_Deck.exe"
)
if exist "Cyber_Deck.spec" (
    del "Cyber_Deck.spec"
)

echo.
echo 📦 正在打包，这可能需要几分钟...
echo.

REM 设置环境变量，阻止打包过程中误启动 GUI
set "CYBER_LIMB_BUILDING=1"

REM 生成随机加密密钥（每次打包不同）
set "CHARS=abcdefghijklmnopqrstuvwxyz0123456789"
set "BUILD_KEY="
for /l %%i in (1,1,16) do call :genkey
goto :pkg_start
:genkey
set /a R=%random% %% 36
call set "BUILD_KEY=%BUILD_KEY%%%CHARS:~%R%,1%%"
goto :eof
:pkg_start
echo %BUILD_KEY%>pack\.build_key

REM 执行PyInstaller打包
.venv\Scripts\python -m PyInstaller --clean --onefile --noconsole --name="Cyber_Deck" --noconfirm ^
    --distpath . ^
    --workpath pack/build ^
    --key %BUILD_KEY% ^
    --paths Arasaka ^
    --icon="laoer/other/icon.ico" ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module PIL ^
    --exclude-module tkinter.test ^
    --exclude-module utils ^
    --exclude-module GetPixels ^
    --add-data "laoer/other/icon.ico;other" ^
    logic_gui_Tools.py

REM 清除环境变量
set "CYBER_LIMB_BUILDING="

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo ====================================
echo ✅ 打包成功！
echo ====================================
echo.

REM 计算文件大小（MB）
set "FILE=Cyber_Deck.exe"
for %%F in ("%FILE%") do set "SIZE_BYTES=%%~zF"
set /a "SIZE_MB=SIZE_BYTES / 1048576"
set /a "SIZE_MB_R=SIZE_BYTES %% 1048576 * 1000 / 1048576"

echo 📂 输出文件：%cd%\Cyber_Deck.exe
echo 📊 文件大小：%SIZE_MB%.%SIZE_MB_R:~0,1% MB
echo.
echo 💡 使用说明：
echo    1. exe 可放任意位置运行，自动通过注册表/进程定位 WoW 插件目录
echo.

REM 清理临时文件
if exist "Cyber_Deck.spec" (
    del "Cyber_Deck.spec"
)
if exist "pack\build" (
    echo 🧹 清理构建缓存...
    rmdir /s /q pack\build
)

pause
