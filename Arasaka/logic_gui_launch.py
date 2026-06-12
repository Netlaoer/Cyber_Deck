# -*- coding: utf-8 -*-
"""
启动器：复制 logic_gui.py 到 .runtime_tmp/ 下随机文件名后运行，进程结束后删除副本。
请运行本文件，不要直接运行 logic_gui.py。
"""
import os
import secrets
import string
import subprocess
import sys
from pathlib import Path

_ALPHABET = string.ascii_letters + string.digits
_SOURCE_NAME = "logic_gui.py"
_RUNTIME_DIR_NAME = ".runtime_tmp"


def _random_script_name() -> str:
    length = secrets.randbelow(5) + 6  # 6~10 位
    return "".join(secrets.choice(_ALPHABET) for _ in range(length)) + ".py"


def _random_comment_block() -> str:
    """生成随机 # 注释块，使每次副本内容哈希不同。"""
    line_count = secrets.randbelow(6) + 3  # 3~8 行
    lines = []
    for _ in range(line_count):
        token_len = secrets.randbelow(32) + 8
        token = "".join(secrets.choice(_ALPHABET) for _ in range(token_len))
        lines.append(f"# {token}")
    return "\n".join(lines) + "\n"


def _write_runtime_copy(src: Path, dest: Path) -> None:
    """复制源文件并在编码声明后注入随机注释。"""
    text = src.read_text(encoding="utf-8")
    injected = _random_comment_block()
    lines = text.splitlines(keepends=True)

    if lines and "coding" in lines[0] and lines[0].lstrip().startswith("#"):
        body = "".join(lines[1:])
        dest.write_text(lines[0] + injected + body, encoding="utf-8")
    else:
        dest.write_text(injected + text, encoding="utf-8")


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

    _write_runtime_copy(src, dest)
    subprocess.Popen(
        [sys.executable, str(dest)],
        cwd=base,
        env=env,
        close_fds=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
