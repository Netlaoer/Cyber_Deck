#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛博义肢 - 一键打包工具 (Python版本)
"""
import os
import sys
import shutil
import subprocess
import secrets
from pathlib import Path

# 自动切换到项目 venv（如果当前不在 venv 中）
_venv_python = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
if _venv_python.is_file() and sys.executable != str(_venv_python.resolve()):
    print("🔄 切换到项目虚拟环境...")
    sys.exit(subprocess.run([str(_venv_python), str(Path(__file__).resolve())]).returncode)
import time
from pathlib import Path

def check_environment():
    """检查环境和依赖"""
    print("=" * 50)
    print("赛博义肢 - 一键打包工具")
    print("=" * 50)
    print()
    
    # 检查当前目录
    if not Path("logic_gui_Tools.py").exists():
        print("❌ 错误：未找到 logic_gui_Tools.py，请将本脚本放在 Cyber_Deck 目录下运行！")
        print(f"当前目录：{Path.cwd()}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 检查/安装 PyInstaller 5.x
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception()
        version = result.stdout.strip().split()[-1]
        if version.startswith("6."):
            raise Exception("v6 不支持 --key")
    except:
        print("📦 安装 PyInstaller 5.x ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "setuptools", "pyinstaller<6.0", "-q"],
                       check=False)
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ 错误：PyInstaller 安装失败！")
            input("\n按回车键退出...")
            sys.exit(1)
    
    return True

def clean_build_files():
    """清理旧的构建文件"""
    print("🧹 清理旧的构建文件...")
    
    # 删除build目录
    if Path("pack/build").exists():
        shutil.rmtree("pack/build", ignore_errors=True)
    
    # 删除旧exe
    exe = Path("Cyber_Deck.exe")
    if exe.exists():
        exe.unlink()
    
    # 删除spec文件
    spec_file = Path("Cyber_Deck.spec")
    if spec_file.exists():
        spec_file.unlink()
    
    print("✅ 清理完成")
    print()

def kill_old_process():
    """关闭已运行的Cyber_Deck进程"""
    if os.name == 'nt':
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq Cyber_Deck.exe'],
                capture_output=True, text=True
            )
            if 'Cyber_Deck.exe' in result.stdout:
                print("🔄 检测到正在运行的 Cyber_Deck 进程，正在关闭...")
                subprocess.run(['taskkill', '/F', '/IM', 'Cyber_Deck.exe'],
                             capture_output=True)
                time.sleep(1)
        except Exception:
            pass

def build_exe():
    """执行打包"""
    print("📦 开始打包，这可能需要几分钟...")
    print()
    
    # 确保 PyInstaller 5.x
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "setuptools", "pyinstaller<6.0", "-q"], check=True)

    # 设置环境变量，阻止打包过程中误启动 GUI
    os.environ['CYBER_LIMB_BUILDING'] = '1'

    # 生成随机加密密钥（每次打包不同）
    build_key = secrets.token_hex(8)
    with open("pack/.build_key", "w") as f:
        f.write(build_key)

    # PyInstaller命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--onefile",  # 单文件
        "--noconsole",  # 不显示控制台窗口
        "--name=Cyber_Deck",  # exe名称
        "--noconfirm",  # 不询问确认，直接覆盖
        "--paths", "Arasaka",  # 添加子目录到搜索路径，使 PyInstaller 能找到 utils/GetPixels/class
        "--distpath", ".",  # 输出到项目根目录
        "--workpath", "pack/build",  # 构建缓存目录
        "--key=" + build_key,  # 每次打包随机 AES 密钥
        "--icon=laoer/other/icon.ico",  # exe图标
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=PIL",
        "--exclude-module=tkinter.test",
        "--add-data", "laoer/other/icon.ico;other",
        "logic_gui_Tools.py"  # 主程序
    ]
    
    # 执行打包
    result = subprocess.run(cmd)
    
    # 清除环境变量
    os.environ.pop('CYBER_LIMB_BUILDING', None)
    
    if result.returncode != 0:
        print()
        print("❌ 打包失败！")
        input("\n按回车键退出...")
        sys.exit(1)
    
    return True

def show_result():
    """显示打包结果"""
    print()
    print("=" * 50)
    print("✅ 打包成功！")
    print("=" * 50)
    print()
    
    exe_path = Path("Cyber_Deck.exe")
    if exe_path.exists():
        print(f"📂 输出文件位置：")
        print(f"   {exe_path.absolute()}")
        print()
        
        # 文件大小
        size = exe_path.stat().st_size
        print(f"📊 文件大小：{size:,} 字节 ({size/1024/1024:.1f} MB)")
        print()
    
    print("📝 包含的内容：")
    print("   ✓ 所有Python依赖库")
    print("   ✓ 核心程序代码（加密）")
    print()

    print("⚠️  不包含（exe自动定位 WoW 插件目录读取）：")
    print("   - Arasaka/config.yml（主配置文件）")
    print("   - Arasaka/class/ 目录（职业逻辑）")
    print("   - Arasaka/keymap/ 目录（键位配置）")
    print()

    print("💡 使用说明：")
    print("   1. 将exe发送给其他人")
    print("   2. exe 可放任意位置运行，会自动通过注册表/进程定位 WoW 插件目录")
    print()
    
    print("⚠️  重要提示：")
    print("   打包完成后不会自动运行exe")
    print("   请手动双击运行项目根目录的 Cyber_Deck.exe")
    print()

def main():
    """主函数"""
    try:
        # 检查环境
        check_environment()
        
        # 关闭旧进程
        kill_old_process()
        
        # 清理旧文件
        clean_build_files()
        
        # 开始打包
        build_exe()
        
        # 显示结果
        show_result()
        
        # 清理spec文件
        spec_file = Path("Cyber_Deck.spec")
        if spec_file.exists():
            spec_file.unlink()
        # 清理构建缓存
        build_dir = Path("pack/build")
        if build_dir.exists():
            print("🧹 清理构建缓存...")
            shutil.rmtree(build_dir, ignore_errors=True)
        
        input("\n打包完成！按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n\n打包已取消！")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()
