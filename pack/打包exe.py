#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛博义肢 - 一键打包工具 (Python版本)
"""
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def check_environment():
    """检查环境和依赖"""
    print("=" * 50)
    print("赛博义肢 - 一键打包工具")
    print("=" * 50)
    print()
    
    # 检查当前目录（脚本在 pack/ 子目录，需回到 Cyber_Deck 根目录）
    root_dir = Path(__file__).parent.parent
    if not (root_dir / "logic_gui_Tools.py").exists():
        print("❌ 错误：未找到 logic_gui_Tools.py！")
        print(f"期望目录：{root_dir}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 检查PyInstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("PyInstaller not found")
    except:
        print("❌ 错误：PyInstaller 未安装！")
        print("请先安装：pip install pyinstaller")
        input("\n按回车键退出...")
        sys.exit(1)
    
    return True

def clean_build_files(root_dir):
    """清理旧的构建文件"""
    print("🧹 清理旧的构建文件...")
    
    # 删除build目录
    build_dir = root_dir / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    
    
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

def build_exe(root_dir):
    """执行打包"""
    print("📦 开始打包，这可能需要几分钟...")
    print()
    
    # 设置环境变量，阻止打包过程中误启动 GUI
    os.environ['CYBER_LIMB_BUILDING'] = '1'
    
    icon_path = root_dir / "laoer" / "other" / "icon.ico"
    main_script = root_dir / "logic_gui_Tools.py"
    
    # 输出目录直接为根目录
    output_dir = str(root_dir)
    
    # PyInstaller命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--onefile",  # 单文件
        "--noconsole",  # 不显示控制台窗口
        "--name=Cyber_Deck",  # exe名称
        "--noconfirm",  # 不询问确认，直接覆盖
        f"--distpath={output_dir}",  # 直接输出到根目录
        f"--workpath={output_dir}/build",  # 临时文件放 build
        f"--icon={icon_path}",  # exe图标
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=PIL",
        "--exclude-module=tkinter.test",
        # utils.py / GetPixels.py 外部加载，其依赖需显式声明
        "--hidden-import=yaml",
        "--hidden-import=mss",
        str(main_script)  # 主程序
    ]
    
    # 切换到根目录执行打包
    result = subprocess.run(cmd, cwd=str(root_dir))
    
    # 清除环境变量
    os.environ.pop('CYBER_LIMB_BUILDING', None)
    
    if result.returncode != 0:
        print()
        print("❌ 打包失败！")
        input("\n按回车键退出...")
        sys.exit(1)
    
    return True

def show_result(root_dir):
    """显示打包结果"""
    print()
    print("=" * 50)
    print("✅ 打包成功！")
    print("=" * 50)
    print()
    
    exe_path = root_dir / "Cyber_Deck.exe"
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
    print("   ✓ 核心程序代码（GUI + WoW 目录检测）")
    print("   ✗ 不内置 config.yml / keymap / class / utils / GetPixels")
    print("   → 全部从外部 WoW 插件目录加载")
    print()
    
    print("💡 使用说明：")
    print("   1. 将exe文件放到任意目录，双击运行即可")
    print("   2. exe 会自动通过注册表/进程定位 WoW 插件目录")
    print("   3. 所有配置、键位、职业逻辑均从 WoW AddOns/Cyber_Deck/ 加载")
    print()

def main():
    """主函数"""
    try:
        # 根目录 = 脚本所在目录的上级（pack/ -> Cyber_Deck/）
        root_dir = Path(__file__).parent.parent
        
        # 检查环境
        check_environment()
        
        # 关闭旧进程
        kill_old_process()
        
        # 清理旧文件
        clean_build_files(root_dir)
        
        # 开始打包
        build_exe(root_dir)
        
        # 显示结果
        show_result(root_dir)
        
        # 清理 build 文件夹和 spec 文件
        build_dir = root_dir / "build"
        if build_dir.exists():
            print("🧹 清理 build 临时文件...")
            shutil.rmtree(build_dir, ignore_errors=True)
        spec_file = root_dir / "Cyber_Deck.spec"
        if spec_file.exists():
            spec_file.unlink()
        
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
