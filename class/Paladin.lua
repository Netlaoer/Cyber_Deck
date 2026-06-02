if UnitClassBase("player") ~= "PALADIN" then return end

-- 仅神圣专精添加扩展像素块
if Fuyutsui.ClassBlocks and Fuyutsui.ClassBlocks[1] then
    Fuyutsui.ClassBlocks[1][48] = { type = "block", name = "驱散开关" }
    Fuyutsui.ClassBlocks[1][49] = { type = "block", name = "5码敌人" }
end

-- 覆盖 MacrosList：进攻技能施法目标
if GetSpecialization() == 1 then
    if Fuyutsui.MacrosList and Fuyutsui.MacrosList.staticSpells then
        Fuyutsui.MacrosList.staticSpells[6] = "[@targettarget,harm,nodead][harm,nodead]审判"
        Fuyutsui.MacrosList.staticSpells[10] = "[@player]正义盾击"
        Fuyutsui.MacrosList.staticSpells[14] = "[@targettarget,harm,nodead][harm,nodead]神圣震击"
    end
end
