# -*- coding: utf-8 -*-

from utils import *
action_map = {
    2: ("火焰吐息", "火焰吐息"),
    3: ("青铜龙的祝福", "青铜龙的祝福"),
    8: ("碧蓝打击", "碧蓝打击"),
    12: ("活化烈焰", "活化烈焰"),
    13: ("裂解", "裂解"),
    16: ("永恒之涌", "永恒之涌"),
    17: ("葬火", "葬火"),
    25: ("碧蓝横扫", "碧蓝打击"),
    26: ("火焰吐息", "火焰吐息"),
    27: ("永恒之涌", "永恒之涌"),
    28: ("喷发", "喷发"),
    29: ("地壳激变", "地壳激变"),
    30: ("先知先觉", "先知先觉"),
    31: ("黑檀之力", "黑檀之力"),
}

failed_spell_map = {
    1: "黑曜鳞片",
    2: "灼烧之焰",
}

# 找到失败法术，必须是法术有冷却时间，并且冷却时间为 0
def _get_failed_spell(state_dict):
    法术失败 = state_dict.get("法术失败", 0)
    spells = state_dict.get("spells") or {}
    spell_name = failed_spell_map.get(法术失败)
    if spell_name and spells.get(spell_name, -1) == 0:
        return spell_name
    return None

def run_evoker_logic(state_dict, spec_name):
    spells = state_dict.get("spells") or {}

    战斗 = state_dict.get("战斗", False)
    移动 = state_dict.get("移动", False)
    施法 = state_dict.get("施法", 0)
    引导 = state_dict.get("引导", 0)
    蓄力 = state_dict.get("蓄力", 0)
    蓄力层数 = state_dict.get("蓄力层数", 0)
    生命值 = state_dict.get("生命值", 0)
    能量值 = state_dict.get("能量值", 0)
    一键辅助 = state_dict.get("一键辅助", 0)
    法术失败 = state_dict.get("法术失败", 0)
    目标类型 = state_dict.get("目标类型", 0)
    队伍类型 = state_dict.get("队伍类型", 0)
    队伍人数 = state_dict.get("队伍人数", 0)
    首领战 = state_dict.get("首领战", 0)
    难度 = state_dict.get("难度", 0)
    英雄天赋 = state_dict.get("英雄天赋", 0)

    精华能量 = state_dict.get("精华能量", 0)

    失败法术 = _get_failed_spell(state_dict)
    tup = action_map.get(一键辅助)
    action_hotkey = None
    current_step = "无匹配技能"
    unit_info = {}

    if spec_name == "湮灭":

        施法技能 = state_dict.get("施法技能", 0)

        火焰吐息CD = spells.get("火焰吐息", -1)
        永恒之涌CD = spells.get("永恒之涌", -1)

        if 引导 > 0:
            current_step = "在引导,不执行任何操作"
        if 蓄力 > 0:
            if 蓄力层数 == 1 and 施法技能 == 26:
                current_step = "施放 火焰吐息"
                action_hotkey = get_hotkey(0, "火焰吐息")
            elif 蓄力层数 == 1 and 施法技能 == 27:
                current_step = "施放 永恒之涌"
                action_hotkey = get_hotkey(0, "永恒之涌")
            else:
                current_step = "蓄力中-无匹配技能"
        elif 一键辅助 == 3:
            current_step = "施放 青铜龙的祝福"
            action_hotkey = get_hotkey(0, "青铜龙的祝福")
        elif 战斗 and 1 <= 目标类型 <= 3 and tup:
            current_step = f"施放 {tup[0]}"
            action_hotkey = get_hotkey(0, tup[1])
            unit_info["_delay"] = 0.5  # 添加延迟
        else:
            current_step = "无匹配技能"
        
    elif spec_name == "恩护":
        if 引导 > 0:
            current_step = "在引导,不执行任何操作"
        elif 一键辅助 == 20:
            current_step = "施放 召唤宠物1"
            action_hotkey = get_hotkey(0, "召唤宠物1")
        elif 战斗 and 1 <= 目标类型 <= 3:
            if tup:
                current_step = f"施放 {tup[0]}"
                action_hotkey = get_hotkey(0, tup[1])
            else:
                current_step = "战斗中-无匹配技能"
        else:
            current_step = "非战斗状态,不执行任何操作"
    elif spec_name == "增辉":

        施法技能 = state_dict.get("施法技能", 0)
        火焰吐息CD = spells.get("火焰吐息", -1)
        地壳激变CD = spells.get("地壳激变", -1)
        扭转天平CD = spells.get("扭转天平", -1)
        火焰吐息CD = spells.get("火焰吐息", -1)
        地壳激变CD = spells.get("地壳激变", -1)
        喷发CD = spells.get("喷发", -1)
        活化烈焰CD = spells.get("活化烈焰", -1)
        黑檀之力CD = spells.get("黑檀之力", -1)
        先知先觉CD = spells.get("先知先觉", -1)
        先知先觉CH = spells.get("先知先觉充能", -1)
        亘古吐息CD = spells.get("亘古吐息", -1)
        净除CD = spells.get("净除", -1)
        青翠之拥CD = spells.get("青翠之拥", -1)

        无先知先觉DPS, _ = get_unit_with_role_and_without_aura_name(state_dict, 3, "先知先觉", reverse=True)
        dispel_unit_poison, _ = get_unit_with_dispel_type(state_dict, 4)

        驱散单位 = None
        # 驱散优先级：毒素
        if 驱散单位 is None:
            驱散单位 = dispel_unit_poison

        if 引导 > 0:
            current_step = "在引导,不执行任何操作"
        elif 净除CD == 0 and 驱散单位 is not None:
            current_step = f"施放: 净除 on {驱散单位}"
            action_hotkey = get_hotkey(int(驱散单位), "净除")
        elif 青翠之拥CD == 0 and 生命值 < 50:
            current_step = "施放: 青翠之拥"
            action_hotkey = get_hotkey(1, "青翠之拥")
        if 蓄力 >0:
            if 蓄力层数 == 1 and 施法技能 == 26:
                current_step = "施放 火焰吐息"
                action_hotkey = get_hotkey(0, "火焰吐息")
            elif 蓄力层数 == 1 and 施法技能 == 29:
                current_step = "施放 地壳激变"
                action_hotkey = get_hotkey(0, "地壳激变")
            else:
                current_step = "蓄力中-无匹配技能"
        # ===== 优先级1: 先知先觉有充能, 给DPS队友（交替目标）=====
        elif 先知先觉CD == 0:
            current_step = f"施放 先知先觉"
            action_hotkey = get_hotkey(0, "先知先觉")
        # ===== 优先级2: 黑檀之力卡CD =====
        elif 黑檀之力CD == 0:
            current_step = f"施放 黑檀之力"
            action_hotkey = get_hotkey(0, "黑檀之力")
        # ===== 优先级3: 火焰吐息卡CD =====
        elif 战斗 and 亘古吐息CD == 0: #亘古爆发
            if 火焰吐息CD == 0 and 地壳激变CD < 3: #双喷对齐
                current_step = "施放 火焰吐息 (卡CD)"
                action_hotkey = get_hotkey(0, "火焰吐息")
            # ===== 优先级4: 扭转天平优先于地壳激变 =====
            elif 战斗 and 扭转天平CD == 0 and 地壳激变CD == 0:
                current_step = "施放 扭转天平 (优先于地壳激变)"
                action_hotkey = get_hotkey(0, "扭转天平")
            # ===== 优先级5: 地壳激变卡CD =====
            elif 战斗 and 地壳激变CD == 0:
                current_step = "施放 地壳激变 (卡CD)"
                action_hotkey = get_hotkey(0, "地壳激变")
                        # ===== 优先级7: 有精华时喷发 =====
            elif 精华能量 >= 2:
                current_step = f"施放 喷发"
                action_hotkey = get_hotkey(0, "喷发")
            # ===== 优先级8: 活化烈焰 =====
            elif 精华能量 < 2:
                if not 移动:
                    current_step = f"施放 活化烈焰"
                    action_hotkey = get_hotkey(0, "活化烈焰")
                else: 
                    current_step = f"施放 碧蓝打击"
                    action_hotkey = get_hotkey(0, "碧蓝打击")
        elif 战斗 and 亘古吐息CD >= 30: #双喷对齐下一次亘古
            if 火焰吐息CD == 0 and 地壳激变CD < 3: #双喷对齐
                current_step = "施放 火焰吐息 (卡CD)"
                action_hotkey = get_hotkey(0, "火焰吐息")
            # ===== 优先级4: 扭转天平优先于地壳激变 =====
            elif 战斗 and 扭转天平CD == 0 and 地壳激变CD == 0:
                current_step = "施放 扭转天平 (优先于地壳激变)"
                action_hotkey = get_hotkey(0, "扭转天平")
            # ===== 优先级5: 地壳激变卡CD =====
            elif 战斗 and 地壳激变CD == 0:
                current_step = "施放 地壳激变 (卡CD)"
                action_hotkey = get_hotkey(0, "地壳激变")
            elif 精华能量 >= 2:
                current_step = f"施放 喷发"
                action_hotkey = get_hotkey(0, "喷发")
            # ===== 优先级8: 活化烈焰 =====
            elif 精华能量 < 2:
                if not 移动:
                    current_step = f"施放 活化烈焰"
                    action_hotkey = get_hotkey(0, "活化烈焰")
                else: 
                    current_step = f"施放 碧蓝打击"
                    action_hotkey = get_hotkey(0, "碧蓝打击")
        elif 战斗:
            if not 移动:
                current_step = f"施放 活化烈焰"
                action_hotkey = get_hotkey(0, "活化烈焰")
            else: 
                current_step = f"施放 碧蓝打击"
                action_hotkey = get_hotkey(0, "碧蓝打击")
        else:
            current_step = "无匹配技能"

    return action_hotkey, current_step, unit_info
