#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛博义肢 - 一键打包工具 (Python版本)

用法:
    python pack/打包exe.py              # 编译 .pyd + 打包 exe
    python pack/打包exe.py --clean      # 清理 .pyd / .c / build
"""
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

# ── 路径 ──
ROOT = Path(__file__).parent.parent
PY_FILE = ROOT / "logic_gui_Tools.py"
PYD_NAME = "Cyber_Deck"  # .pyd 模块名
PYD_FILE = ROOT / "pack" / f"{PYD_NAME}.cp314-win_amd64.pyd"
LAUNCHER = ROOT / "pack" / "launcher.py"
ICON = ROOT / "laoer" / "other" / "icon.ico"


# ═══════════════════════════════════════════
#  Cython 编译
# ═══════════════════════════════════════════

def check_cython():
    try:
        import Cython
        print(f"[OK] Cython {Cython.__version__}")
        return True
    except ImportError:
        print("[ERROR] Cython 未安装！pip install cython")
        return False


def check_compiler():
    if sys.platform != "win32":
        return True
    try:
        from setuptools._distutils.ccompiler import new_compiler
        cc = new_compiler()
        if cc.compiler_type == 'msvc':
            cc.initialize()
            print("[OK] MSVC 编译器")
            return True
    except Exception:
        pass
    print("[WARN] 未检测到 MSVC 编译器")
    return False


def compile_pyd():
    """编译 logic_gui_Tools.py -> pack/logic_gui_Tools.xxx.pyd"""
    if not PY_FILE.exists():
        print("[ERROR] 未找到 logic_gui_Tools.py")
        return False

    # 输出到 pack/ 目录
    out_dir = PYD_FILE.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"编译: {PY_FILE.name} ...", end=" ", flush=True)

    setup_code = f'''# Auto-generated
from setuptools import setup, Extension
from Cython.Build import cythonize
import sys, os
os.chdir(r"{out_dir}")
sys.argv = ['setup.py', 'build_ext', '--inplace']
setup(
    ext_modules=cythonize(
        [Extension("{PYD_NAME}", [r"{PY_FILE}"])],
        language_level=3, quiet=True,
    ),
)
'''
    tmp = out_dir / "_setup_cython_tmp.py"
    tmp.write_text(setup_code, encoding='utf-8')

    try:
        result = subprocess.run(
            [sys.executable, str(tmp)],
            capture_output=True, text=True,
            cwd=str(out_dir), timeout=300,
        )
    finally:
        tmp.unlink(missing_ok=True)
        for c in out_dir.glob(f"{PY_FILE.stem}.c"):
            c.unlink(missing_ok=True)

    if result.returncode != 0:
        print("FAILED")
        return False

    if PYD_FILE.exists():
        print(f"OK -> pack/{PYD_FILE.name}")
        return True
    else:
        # 可能版本号不同，尝试匹配
        matches = list(out_dir.glob(f"{PYD_NAME}*.pyd"))
        if matches:
            print(f"OK -> pack/{matches[0].name}")
            return True
        print("FAILED: 未生成 .pyd")
        return False


# ═══════════════════════════════════════════
#  打包
# ═══════════════════════════════════════════

def check_pyinstaller():
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                       capture_output=True, text=True, check=True)
        return True
    except Exception:
        print("[ERROR] PyInstaller 未安装！pip install pyinstaller")
        return False


def clean_build():
    build_dir = ROOT / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    spec = ROOT / "Cyber_Deck.spec"
    if spec.exists():
        spec.unlink()


def clean_pyd():
    """清理 pack/ 下的 .pyd 和 .c 文件"""
    pack_dir = ROOT / "pack"
    for f in pack_dir.glob("*.pyd"):
        f.unlink()
        print(f"  删除: pack/{f.name}")
    for f in pack_dir.glob("*.c"):
        f.unlink()
        print(f"  删除: pack/{f.name}")
    for f in pack_dir.glob("_setup_*.py"):
        f.unlink()
        print(f"  删除: pack/{f.name}")


def kill_old_process():
    if os.name != 'nt':
        return
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Cyber_Deck.exe'],
                           capture_output=True, text=True)
        if 'Cyber_Deck.exe' in r.stdout:
            print("关闭正在运行的 Cyber_Deck 进程...")
            subprocess.run(['taskkill', '/F', '/IM', 'Cyber_Deck.exe'],
                           capture_output=True)
            time.sleep(1)
    except Exception:
        pass


def build_exe():
    """打包 exe (launcher.py + .pyd)"""
    print("模式: .pyd 二进制入口")
    print("打包中，请等待...")
    print()

    os.environ['CYBER_LIMB_BUILDING'] = '1'

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean", "--onefile", "--noconsole",
        "--name=Cyber_Deck", "--noconfirm",
        f"--distpath={ROOT}",
        f"--workpath={ROOT}/build",
        f"--icon={ICON}",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=PIL",
        "--exclude-module=tkinter.test",
        "--hidden-import=yaml",
        "--hidden-import=mss",
        "--add-binary", f"{PYD_FILE}{os.pathsep}.",
        str(LAUNCHER),
    ]

    result = subprocess.run(cmd, cwd=str(ROOT))
    os.environ.pop('CYBER_LIMB_BUILDING', None)

    if result.returncode != 0:
        print("\n[ERROR] 打包失败！")
        return False
    return True


def show_result():
    exe = ROOT / "Cyber_Deck.exe"
    print()
    print("=" * 50)
    print("打包成功！")
    print("=" * 50)
    print()
    if exe.exists():
        print(f"输出: {exe}")
        size = exe.stat().st_size
        print(f"大小: {size:,} 字节 ({size/1024/1024:.1f} MB)")
        print()
    print("包含:")
    if PYD_FILE.exists():
        print("  - logic_gui_Tools.pyd (Cython 二进制，无法反编译)")
    else:
        print("  - logic_gui_Tools.py (源码)")
    print("  - 不内置 config.yml / keymap / class / utils / GetPixels")
    print("  -> 全部从外部 WoW 插件目录加载")
    print()


# ═══════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════

def main():
    print("=" * 50)
    print("赛博义肢 - 一键打包工具")
    print("=" * 50)
    print()

    # --clean
    if "--clean" in sys.argv:
        print("清理编译产物...")
        clean_pyd()
        clean_build()
        print("[OK] 清理完成")
        return

    # 检查环境
    if not check_pyinstaller():
        input("\n按回车键退出...")
        sys.exit(1)
    if not check_cython():
        input("\n按回车键退出...")
        sys.exit(1)
    if not check_compiler():
        resp = input("继续尝试？(y/n): ").strip().lower()
        if resp != 'y':
            sys.exit(1)

    # 编译 .pyd
    print()
    if not compile_pyd():
        print("\n[ERROR] Cython 编译失败！")
        input("\n按回车键退出...")
        sys.exit(1)
    print()

    # 打包
    kill_old_process()
    clean_build()
    if not build_exe():
        input("\n按回车键退出...")
        sys.exit(1)

    # 清理
    for d in [ROOT / "build", ROOT / "pack" / "build"]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    spec = ROOT / "Cyber_Deck.spec"
    if spec.exists():
        spec.unlink()
    # 清理编译残留
    pack_dir = ROOT / "pack"
    for pattern in ["*.c", "*.pyd", "_setup_*.py"]:
        for f in pack_dir.glob(pattern):
            f.unlink(missing_ok=True)

    show_result()
    input("按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        input("\n按回车键退出...")
        sys.exit(1)
