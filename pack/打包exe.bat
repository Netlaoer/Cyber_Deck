@echo off
chcp 65001 >nul
echo ====================================
echo 赛博义肢 - 一键打包工具
echo ====================================
echo.

REM 检查是否在Cyber_Deck目录
cd /d "%~dp0.."
if not exist "logic_gui_Tools.py" (
    echo ❌ 错误：未找到 logic_gui_Tools.py！
    echo 当前目录：%cd%
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
python -m PyInstaller --version >nul 2>&1
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
if exist "build" (
    echo 清理旧的构建文件...
    rmdir /s /q build
)


if exist "Cyber_Deck.exe" (
    echo 删除旧的 exe...
    del "Cyber_Deck.exe"
)

echo.
echo 📦 正在打包，这可能需要几分钟...
echo.

REM 设置环境变量，阻止打包过程中误启动 GUI
set "CYBER_LIMB_BUILDING=1"

REM 执行PyInstaller打包，直接输出到当前目录
python -m PyInstaller --clean --onefile --noconsole --name="Cyber_Deck" --noconfirm ^
    --distpath="." --workpath="build" ^
    --icon="laoer/other/icon.ico" ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module PIL ^
    --exclude-module tkinter.test ^
    --hidden-import yaml ^
    --hidden-import mss ^
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
echo    1. 将 exe 放到任意目录，双击运行即可
echo    2. exe 会自动通过注册表/进程定位 WoW 插件目录
echo    3. 所有配置、键位、职业逻辑均从 WoW AddOns/Cyber_Deck/ 加载
echo.

REM 清理 build 文件夹和 spec 文件
if exist "build" (
    echo 🧹 清理 build 临时文件...
    rmdir /s /q build
)
if exist "Cyber_Deck.spec" (
    del "Cyber_Deck.spec"
)

pause
