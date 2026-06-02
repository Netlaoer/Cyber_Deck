# -*- coding: utf-8 -*-
"""
无 GUI 版本：核心逻辑与 logic_gui.py 一致，终端展示内容与 GUI 主界面 + 实时信息 + 队伍信息一致。
"""
import ctypes
import ctypes.wintypes
import importlib
import sys
import threading
import time
from pathlib import Path

from GetPixels import get_info
from utils import *

TOGGLE_INTERVAL = 0.1
LOGIC_INTERVAL = 0.2
GUI_UPDATE_MS = 0.2  # 与 logic_gui.GUI_UPDATE_MS 对齐（秒）
TOGGLE_DEBOUNCE_SEC = 0.12
_RUNTIME_DIR_NAME = ".runtime_tmp"

_DEFAULT_STATUS_KEYS = ["生命值", "能量值", "有效性", "战斗", "移动", "施法", "引导"]
_GUI_SKIP_STATE_KEYS = frozenset({"锚点", "职业", "专精"})
_SEND_MODE_LABELS = {"switch": "开关", "click": "单击", "hold": "按住"}


def _load_logic_module(module_name: str):
    m = importlib.import_module(f"class.{module_name}")
    return getattr(m, f"run_{module_name.replace('_logic', '')}_logic")


run_priest_logic = _load_logic_module("priest_logic")
run_druid_logic = _load_logic_module("druid_logic")
run_paladin_logic = _load_logic_module("paladin_logic")
run_deathknight_logic = _load_logic_module("deathknight_logic")
run_warrior_logic = _load_logic_module("warrior_logic")
run_hunter_logic = _load_logic_module("hunter_logic")
run_rogue_logic = _load_logic_module("rogue_logic")
run_shaman_logic = _load_logic_module("shaman_logic")
run_mage_logic = _load_logic_module("mage_logic")
run_warlock_logic = _load_logic_module("warlock_logic")
run_monk_logic = _load_logic_module("monk_logic")
run_demonhunter_logic = _load_logic_module("demonhunter_logic")
run_evoker_logic = _load_logic_module("evoker_logic")

LOGIC_FUNCS_BY_CLASS = {
    1: run_warrior_logic,
    2: run_paladin_logic,
    3: run_hunter_logic,
    4: run_rogue_logic,
    5: run_priest_logic,
    6: run_deathknight_logic,
    7: run_shaman_logic,
    8: run_mage_logic,
    9: run_warlock_logic,
    10: run_monk_logic,
    11: run_druid_logic,
    12: run_demonhunter_logic,
    13: run_evoker_logic,
}


def _default_logic(state_dict, spec_name):
    return None, "无逻辑定义", {}


_toggle_lock = threading.Lock()
_toggle_key_str = "XBUTTON2"
_toggle_vk = get_vk(_toggle_key_str)

_MOUSE_XBUTTON_VKS = {0x05, 0x06}
_xbutton_pressed = False
_xbutton_hook = None
_mouse_hook_proc_ref = None

WH_MOUSE_LL = 14
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
XBUTTON1_FLAG = 0x0001
XBUTTON2_FLAG = 0x0002

_LowLevelMouseProc = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)
)

_send_mode = "switch"
_click_pending = False

_state_lock = threading.Lock()
_logic_enabled = False
_state_dict = {}
_class_name = None
_class_id = None
_spec_name = None
_spec_id = None
_current_step = ""
_unit_info = {}
_scan_ms = 0.0

_CONFIG_CACHE = None


def _get_config_cached():
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_config()
    return _CONFIG_CACHE


def _get_global_state_display_keys():
    config = _get_config_cached()
    raw = config.get("state")
    if not isinstance(raw, dict):
        return list(_DEFAULT_STATUS_KEYS)
    items = []
    for k, v in raw.items():
        if k in ("group", "spells") or k in _GUI_SKIP_STATE_KEYS:
            continue
        if not isinstance(v, dict) or "step" not in v:
            continue
        try:
            step = int(v["step"])
        except (TypeError, ValueError):
            step = 0
        items.append((step, k))
    if not items:
        return list(_DEFAULT_STATUS_KEYS)
    items.sort(key=lambda x: x[0])
    return [k for _, k in items]


def _get_class_spec_cfg(class_id, spec_id):
    if class_id is None or spec_id is None:
        return {}
    config = _get_config_cached()
    class_dict = config.get(class_id) or config.get(str(class_id)) or {}
    if not isinstance(class_dict, dict):
        return {}
    return class_dict.get(spec_id) or class_dict.get(str(spec_id)) or {}


def get_group_config_for_class_spec(class_id, spec_id):
    spec_cfg = _get_class_spec_cfg(class_id, spec_id)
    group_cfg = spec_cfg.get("group") if isinstance(spec_cfg, dict) else None
    if not isinstance(group_cfg, dict):
        return (0, [])
    try:
        num_units = int(group_cfg.get("num", 0))
    except (TypeError, ValueError):
        num_units = 0
    fields = [k for k in group_cfg.keys() if k not in ("start", "num")]
    return (num_units, fields)


def get_class_spec_view_data(class_id, spec_id):
    fixed = _get_global_state_display_keys()
    spec_cfg = _get_class_spec_cfg(class_id, spec_id)
    if not isinstance(spec_cfg, dict) or not spec_cfg:
        return fixed, (0, []), []

    extra_keys = [k for k in spec_cfg.keys() if k not in ("spells", "group", "keymap")]
    status_keys = list(fixed)
    seen = set(fixed)
    for k in extra_keys:
        if k not in seen and k not in _GUI_SKIP_STATE_KEYS:
            status_keys.append(k)
            seen.add(k)

    spells_cfg = spec_cfg.get("spells")
    spells_list = list(spells_cfg.keys()) if isinstance(spells_cfg, dict) else []

    group_cfg = spec_cfg.get("group")
    if not isinstance(group_cfg, dict):
        group_num = 0
        fields = []
    else:
        try:
            group_num = int(group_cfg.get("num", 0))
        except (TypeError, ValueError):
            group_num = 0
        fields = [k for k in group_cfg.keys() if k not in ("start", "num")]

    return status_keys, (group_num, fields), spells_list


def _display_key_str(key_str: str) -> str:
    if key_str == " ":
        return "SPACE"
    return str(key_str)


def _format_value(v):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "是" if v else "否"
    return str(v)


def _get_party_count(sd) -> int:
    """从 state 读取队伍人数；缺失或无效视为 0。"""
    val = sd.get("队伍人数")
    if val is None:
        return 0
    try:
        return max(0, int(val))
    except (TypeError, ValueError):
        return 0


def _build_team_text(sd, spec_name, class_id, spec_id, unit_info):
    if spec_name is None:
        return None

    party_count = _get_party_count(sd)
    if party_count <= 0:
        return None

    group = sd.get("group") or {}
    unit_keys = [str(i) for i in range(1, party_count + 1)]

    ordered_fields = []
    if spec_name and class_id is not None and spec_id is not None:
        try:
            _, fields_for_spec = get_group_config_for_class_spec(class_id, spec_id)
            ordered_fields.extend([f for f in fields_for_spec if f not in ordered_fields])
        except Exception:
            pass

    rest_fields = set()
    for uk in unit_keys:
        unit_data = group.get(uk) or {}
        for f in unit_data.keys():
            if f not in ordered_fields:
                rest_fields.add(f)
    ordered_fields.extend(sorted(rest_fields))

    lines = []
    lines.append(f"队伍人数: {party_count}")
    lines.append(f"字段数: {len(ordered_fields)}")
    lines.append("")

    for uk in unit_keys:
        unit_data = group.get(uk) or {}
        field_parts = [f"{f}={_format_value(unit_data.get(f))}" for f in ordered_fields]
        lines.append(f"Unit {uk}: " + " | ".join(field_parts))

    if unit_info:
        lines.append("")
        lines.append("逻辑推荐/目标单位（unit_info）")
        for k in sorted(unit_info.keys()):
            lines.append(f"  {k}: {_format_value(unit_info.get(k))}")

    return "\n".join(lines)


def _status_text_for_gui(mode: str, enabled: bool) -> str:
    if mode == "click":
        return "状态: 单击"
    return f"状态: {'开启' if enabled else '关闭'}"


def _format_status_row(keys, sd, cols: int = 6) -> list[str]:
    """每行 cols 组「键: 值」。"""
    pairs = []
    for k in keys:
        v = sd.get(k)
        txt = str(v) if v is not None else "-"
        pairs.append(f"{k}: {txt}")
    rows = []
    for i in range(0, len(pairs), cols):
        rows.append("    ".join(pairs[i : i + cols]))
    return rows


def _format_cooldown_rows(spell_list, spells_data, cols: int = 6) -> list[str]:
    pairs = []
    for name in spell_list:
        val = spells_data.get(name)
        pairs.append(f"{name}: {'-' if val is None else str(int(val))}")
    rows = []
    for i in range(0, len(pairs), cols):
        rows.append("    ".join(pairs[i : i + cols]))
    return rows


_console_prev_line_count = 0
_console_ansi_ready = False


def _enable_console_ansi() -> None:
    """Windows 终端需开启 VT 模式，才能用光标回顶覆写，避免每帧 cls 闪烁。"""
    global _console_ansi_ready
    if _console_ansi_ready:
        return
    if sys.platform == "win32":
        try:
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        except Exception:
            pass
    _console_ansi_ready = True


def _write_console_lines(lines: list[str]) -> None:
    """原地更新终端内容，不反复整屏清屏。"""
    global _console_prev_line_count
    _enable_console_ansi()
    text = "\n".join(lines)
    n = len(lines)

    if _console_prev_line_count == 0:
        sys.stdout.write(text + "\n")
    else:
        # 光标回到上次输出块的首行，逐行覆写
        sys.stdout.write(f"\033[{_console_prev_line_count}A")
        for line in lines:
            sys.stdout.write("\033[K" + line + "\n")
        # 新内容行数变少时，擦掉多出来的旧行
        for _ in range(_console_prev_line_count - n):
            sys.stdout.write("\033[K\n")

    _console_prev_line_count = n
    sys.stdout.flush()


def _render_console():
    with _state_lock:
        enabled = _logic_enabled
        mode = _send_mode
        class_name = _class_name
        spec_name = _spec_name
        class_id = _class_id
        spec_id = _spec_id
        sd = dict(_state_dict)
        unit_info = dict(_unit_info)
        step = _current_step
        scan_ms = _scan_ms
        bound = _toggle_key_str

    lines = []
    lines.append("=" * 72)
    lines.append(
        f"职业: {class_name or '-'}    专精: {spec_name or '-'}    {_status_text_for_gui(mode, enabled)}"
    )
    mode_parts = []
    for m, label in _SEND_MODE_LABELS.items():
        mark = "【" if m == mode else "  "
        end = "】" if m == mode else "  "
        mode_parts.append(f"{mark}{label}{end}")
    lines.append(f"已绑定: {_display_key_str(bound)}    发送模式: {' '.join(mode_parts)}")
    lines.append("=" * 72)

    if spec_name is None:
        lines.append("")
        lines.append("【实时信息】")
        lines.append("扫描: -")
        lines.append("当前步骤: 专精未知")
        _write_console_lines(lines)
        return

    status_keys, _, spell_list = get_class_spec_view_data(class_id, spec_id)
    spells_data = sd.get("spells") or {}

    lines.append("")
    lines.append("【实时信息】")
    lines.append(f"扫描: {scan_ms:.1f} ms")
    lines.append("")
    lines.append("实时状态")
    lines.extend(_format_status_row(status_keys, sd))
    lines.append("")
    lines.append(f"当前步骤: {step or '-'}")
    lines.append("")
    lines.append("技能冷却")
    if spell_list:
        lines.extend(_format_cooldown_rows(spell_list, spells_data))
    else:
        lines.append("（无技能配置）")

    party_count = _get_party_count(sd)
    if party_count > 0:
        team_text = _build_team_text(sd, spec_name, class_id, spec_id, unit_info)
        if team_text:
            lines.append("")
            lines.append("=" * 72)
            lines.append(f"【队伍信息】（职业: {class_name or '-'} / 专精: {spec_name or '-'}）")
            lines.append(team_text.rstrip())

    _write_console_lines(lines)


def _make_mouse_hook_proc():
    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt_x", ctypes.c_long),
            ("pt_y", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("flags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    def _proc(nCode, wParam, lParam):
        global _xbutton_pressed
        if nCode >= 0 and wParam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
            info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT))[0]
            hi_word = (info.mouseData >> 16) & 0xFFFF
            vk_now = _toggle_vk
            if vk_now in _MOUSE_XBUTTON_VKS:
                want_xb2 = vk_now == 0x06
                is_xb2 = hi_word == XBUTTON2_FLAG
                if want_xb2 == is_xb2:
                    _xbutton_pressed = wParam == WM_XBUTTONDOWN
        return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

    return _LowLevelMouseProc(_proc)


def _install_mouse_hook():
    global _xbutton_hook, _mouse_hook_proc_ref
    if _xbutton_hook is not None:
        return
    _mouse_hook_proc_ref = _make_mouse_hook_proc()
    _xbutton_hook = ctypes.windll.user32.SetWindowsHookExW(
        WH_MOUSE_LL, _mouse_hook_proc_ref, None, 0
    )


def _start_mouse_hook_thread():
    def _hook_thread():
        _install_mouse_hook()
        msg = ctypes.wintypes.MSG()
        while True:
            ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    t = threading.Thread(target=_hook_thread, daemon=True)
    t.start()


def _run_logic_loop():
    """与 logic_gui._run_priest_loop 一致的后台逻辑循环。"""
    global _logic_enabled, _state_dict, _class_name, _class_id, _spec_name, _spec_id
    global _current_step, _unit_info, _send_mode, _click_pending, _scan_ms

    prev_pressed = False
    prev_vk = _toggle_vk
    last_logic_time = 0.0
    last_toggle_time = 0.0

    while True:
        vk_now = _toggle_vk
        if vk_now is None:
            time.sleep(TOGGLE_INTERVAL)
            continue

        if vk_now != prev_vk:
            prev_pressed = False
            prev_vk = vk_now

        if vk_now in _MOUSE_XBUTTON_VKS:
            current_pressed = _xbutton_pressed
            rising_raw = current_pressed and not prev_pressed
        else:
            key_state = ctypes.windll.user32.GetAsyncKeyState(vk_now)
            current_pressed = (key_state & 0x8000) != 0
            rising_raw = (current_pressed and not prev_pressed) or ((key_state & 0x0001) != 0)

        now = time.time()
        rising = rising_raw and (now - last_toggle_time >= TOGGLE_DEBOUNCE_SEC)
        if rising:
            last_toggle_time = now
        falling = (not current_pressed) and prev_pressed

        mode = _send_mode
        if mode == "switch":
            if rising:
                with _state_lock:
                    _logic_enabled = not _logic_enabled
                    _click_pending = False
                _current_step = "逻辑 " + ("开启" if _logic_enabled else "关闭")
        elif mode == "click":
            if rising:
                with _state_lock:
                    _logic_enabled = True
                    _click_pending = True
                _current_step = "单击触发"
        elif mode == "hold":
            with _state_lock:
                _logic_enabled = current_pressed
                _click_pending = False
            if falling:
                _current_step = "按住结束"
        else:
            if rising:
                with _state_lock:
                    _logic_enabled = not _logic_enabled
                    _click_pending = False
                _current_step = "逻辑 " + ("开启" if _logic_enabled else "关闭")

        prev_pressed = current_pressed

        if now - last_logic_time >= LOGIC_INTERVAL:
            last_logic_time = now
            t0 = time.perf_counter()
            state_dict = get_info()
            _scan_ms = (time.perf_counter() - t0) * 1000
            class_name, spec_name = None, None
            class_id, spec_id = None, None
            if state_dict:
                class_id = state_dict.get("职业")
                spec_id = state_dict.get("专精")
                config = _get_config_cached()
                class_name, spec_name = get_class_and_spec_name(config, class_id, spec_id)
                select_keymap_for_class(class_id)

            with _state_lock:
                _state_dict = state_dict or {}
                _class_name = class_name
                _class_id = class_id
                _spec_name = spec_name
                _spec_id = spec_id

        if not _logic_enabled:
            time.sleep(TOGGLE_INTERVAL)
            continue

        with _state_lock:
            sd = _state_dict
            class_id = _class_id
            spec_name = _spec_name

        if not sd or not sd.get("有效性"):
            _current_step = "等待游戏状态"
            time.sleep(TOGGLE_INTERVAL)
            continue

        _current_step = "无操作"
        logic_func = LOGIC_FUNCS_BY_CLASS.get(class_id, _default_logic)
        action_hotkey, _current_step, unit_info_update = logic_func(sd, spec_name)
        if unit_info_update:
            with _state_lock:
                _unit_info = unit_info_update

        delay_after_send = 0.0
        if mode == "click":
            with _state_lock:
                pending = _click_pending
            if pending:
                if action_hotkey:
                    send_key_to_wow(action_hotkey)
                    delay_after_send = unit_info_update.get("_delay", 0.0) if unit_info_update else 0.0
                with _state_lock:
                    _logic_enabled = False
                    _click_pending = False
        else:
            if action_hotkey:
                send_key_to_wow(action_hotkey)
                delay_after_send = unit_info_update.get("_delay", 0.0) if unit_info_update else 0.0

        if delay_after_send > 0:
            time.sleep(delay_after_send)
        else:
            time.sleep(TOGGLE_INTERVAL)


def run_logic_nogui():
    _start_mouse_hook_thread()
    worker = threading.Thread(target=_run_logic_loop, daemon=True)
    worker.start()

    try:
        while True:
            _render_console()
            time.sleep(GUI_UPDATE_MS)
    except KeyboardInterrupt:
        sys.stdout.write("\n已退出。\n")
        sys.stdout.flush()


def _cleanup_runtime_copy_if_needed() -> None:
    """由 launch 复制到 .runtime_tmp/ 的副本在退出时自行删除。"""
    try:
        p = Path(__file__).resolve()
        if _RUNTIME_DIR_NAME not in p.parts:
            return
        p.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        run_logic_nogui()
    finally:
        _cleanup_runtime_copy_if_needed()
