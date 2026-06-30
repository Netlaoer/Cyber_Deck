-- ============================================================================
-- 覆盖 Fuyutsui/main.lua 中的函数
-- ============================================================================

local F = Fuyutsui

-- 覆盖 updatePlayerConfig：初始化时写入驱散开关像素，同时修复 Fuyutsui 本体 nil 字段崩溃
local origUpdatePlayerConfig = F.updatePlayerConfig
function F:updatePlayerConfig()
    local c = self.db and self.db.char
    if not c then return end
    -- 修复 Fuyutsui 本体在 db.char 尚未被 defaults 填充时字段为 nil 导致的崩溃
    c.aoeMode = c.aoeMode or 0
    c.cooldowns = c.cooldowns or 0
    c.dpsMode = c.dpsMode or 0
    c.potion = c.potion or 0
    origUpdatePlayerConfig(self)
    if not self.blocks then return end
    if self.blocks.state["驱散开关"] then
        self:CreatTexture(self.blocks.state["驱散开关"], (c.dispel or 1) / 255)
    end
end

-- 覆盖 updateEnemyCount：追加5码内敌人计数
local origUpdateEnemyCount = F.updateEnemyCount
function F:updateEnemyCount()
    origUpdateEnemyCount(self)
    local count5y = 0
    local inTestMap = self.state.mapID and self.state.mapID == 2393
    for unit, data in pairs(self.nameplate) do
        if data.canAttack and data.maxRange and data.maxRange <= 5 and (data.affectingCombat or inTestMap) then
            count5y = count5y + 1
        end
    end
    self.state.enemyCount5y = count5y / 255 or 0
    if self.blocks and self.blocks.state["5码敌人"] then
        self:CreatTexture(self.blocks.state["5码敌人"], self.state.enemyCount5y)
    end
end

-- 覆盖 updateUnitCastingOrChannelingInfo：修复焦点引导报错（pcall 防崩）
local origUpdateCasting = F.updateUnitCastingOrChannelingInfo
function F:updateUnitCastingOrChannelingInfo(unit)
    pcall(origUpdateCasting, self, unit)
end
