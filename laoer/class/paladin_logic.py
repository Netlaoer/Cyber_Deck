# -*- coding: utf-8 -*-
"""Cyber_Deck 覆盖：圣骑士逻辑（驱散开关支持）"""
import importlib
from utils import get_hotkey

_orig_mod = importlib.import_module("class.paladin_logic")
_orig_run = _orig_mod.run_paladin_logic

# 特殊技能按键（不走keymap，直接按指定键）
direct_key_map = {
    "制裁之锤": "x",
}

# 替换原始模块的 get_hotkey，使制裁之锤走固定按键
_orig_get_hotkey = _orig_mod.get_hotkey

def _patched_get_hotkey(unit, skill_name):
    if skill_name in direct_key_map:
        return direct_key_map[skill_name]
    return _orig_get_hotkey(unit, skill_name)

_orig_mod.get_hotkey = _patched_get_hotkey


def run_paladin_logic(state_dict, spec_name):
    """覆盖：驱散开关支持 + Holy选中友方仍可进攻（配合[@focustarget]）"""
    驱散开关 = state_dict.get("驱散开关", 1)
    removed_dispel = {}

    # 驱散开关关闭时，临时移除 group 中的驱散字段，使原始逻辑跳过队友驱散
    if 驱散开关 == 0:
        group = state_dict.get("group") or {}
        for key, data in group.items():
            if isinstance(data, dict) and "驱散" in data:
                removed_dispel[key] = data["驱散"]
                del data["驱散"]

    # 覆盖：在覆盖层处理驱散（优先级最高），确保驱散不受目标类型修改影响
    orig_目标类型 = state_dict.get("目标类型", 0)
    action_hotkey = None
    current_step = None
    unit_info = {}
    spells = state_dict.get("spells") or {}
    清洁术CD = spells.get("清洁术", -1)

    # 驱散判断（在修改目标类型之前，确保目标驱散正常工作）
    if 清洁术CD == 0:
        # 队友驱散（驱散开关开启时，复用原始逻辑的驱散单位查找）
        if 驱散开关 != 0:
            from utils import get_unit_with_dispel_type
            # 魔法驱散（优先级最高）
            dispel_unit, _ = get_unit_with_dispel_type(state_dict, 1)
            if dispel_unit is not None:
                current_step = f"施放 清毒术 on {dispel_unit}"
                action_hotkey = get_hotkey(int(dispel_unit), "清毒术")
            # 疾病驱散
            if action_hotkey is None:
                dispel_unit, _ = get_unit_with_dispel_type(state_dict, 3)
                if dispel_unit is not None:
                    current_step = f"施放 清毒术 on {dispel_unit}"
                    action_hotkey = get_hotkey(int(dispel_unit), "清毒术")
            # 毒素驱散
            if action_hotkey is None:
                dispel_unit, _ = get_unit_with_dispel_type(state_dict, 4)
                if dispel_unit is not None:
                    current_step = f"施放 清毒术 on {dispel_unit}"
                    action_hotkey = get_hotkey(int(dispel_unit), "清毒术")
        # 目标驱散（无论开关状态都可用）
        if action_hotkey is None and orig_目标类型 in (12, 13, 15):
            current_step = "施放 清毒术 on 目标"
            action_hotkey = get_hotkey(0, "清毒术")

    # 如果驱散未触发，修改目标类型让原始逻辑走进攻路线
    if action_hotkey is None and spec_name == "神圣" and orig_目标类型 >= 11:
        state_dict["目标类型"] = 2

    # 覆盖：5豆正义盾击用5码姓名版敌人判断代替目标距离
    orig_目标距离 = None
    if spec_name == "神圣" and state_dict.get("神圣能量", 0) == 5:
        if state_dict.get("5码敌人", 0) >= 1:
            orig_目标距离 = state_dict.get("目标距离")
            state_dict["目标距离"] = 1

    # 调用原始逻辑（驱散已由覆盖层处理，这里主要走治疗/进攻逻辑）
    if action_hotkey is None:
        action_hotkey, current_step, unit_info = _orig_run(state_dict, spec_name)

    # 恢复目标距离
    if orig_目标距离 is not None:
        state_dict["目标距离"] = orig_目标距离

    # 恢复目标类型
    if orig_目标类型 != state_dict.get("目标类型", 0):
        state_dict["目标类型"] = orig_目标类型

    # 恢复被移除的驱散字段
    if removed_dispel:
        group = state_dict.get("group") or {}
        for key, val in removed_dispel.items():
            if isinstance(group.get(key), dict):
                group[key]["驱散"] = val

    return action_hotkey, current_step, unit_info



