# -*- coding: utf-8 -*-
"""
启动器：复制 logic_nogui.py 到 .runtime_tmp/ 下随机文件名后运行，进程结束后删除副本。
请运行本文件，不要直接运行 logic_nogui.py。
"""
import os
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path

_ALPHABET = string.ascii_letters + string.digits
_SOURCE_NAME = "logic_nogui.py"
_RUNTIME_DIR_NAME = ".runtime_tmp"


def _random_script_name(length: int = 12) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length)) + ".py"


def _runtime_dir(base_dir: Path) -> Path:
    d = base_dir / _RUNTIME_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cleanup_stale_runtime_scripts(runtime_dir: Path) -> None:
    """清理上次异常退出可能残留的临时脚本。"""
    for p in runtime_dir.glob("*.py"):
        try:
            p.unlink()
        except OSError:
            pass


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    src = base_dir / _SOURCE_NAME
    if not src.is_file():
        print(f"未找到源文件: {src}", file=sys.stderr)
        return 1

    runtime_dir = _runtime_dir(base_dir)
    _cleanup_stale_runtime_scripts(runtime_dir)

    dest = runtime_dir / _random_script_name()
    while dest.exists():
        dest = runtime_dir / _random_script_name()

    env = os.environ.copy()
    base = str(base_dir)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = base + (os.pathsep + prev if prev else "")

    shutil.copy2(src, dest)
    # 不等待子进程，启动器立即退出，避免后台残留 logic_nogui_launch.py 进程
    subprocess.Popen(
        [sys.executable, str(dest)],
        cwd=base,
        env=env,
        close_fds=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
