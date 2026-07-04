# Cyber Deck（赛博义肢）

**独立的 WoW 辅助决策插件 — 基于 Fuyutsui 架构的完整移植**
<!--
AI_INSTRUCTION（AI 必读）：
1. 在修改此项目任何代码之前，请完整阅读本文件，理解整体架构、所有函数、编码约定和开发规范。
2. 本项目是一个 WoW 辅助决策系统，分为 Lua 插件层（游戏内）和 Python 决策层（外部程序）。
3. 核心原则：直接修改对应文件。Lua 端编辑 Cyber_Deck 目录下文件，Python 端编辑 Arasaka/ 下文件。
4. 完成代码修改后，必须同步更新本文件中对应的章节。
5. 像素块名称、状态字段、GUI 文本统一使用中文。
6. 新增像素块索引建议从 150+ 开始，避免与 config.yml 中已有索引冲突。
-->
<!-- AI: Before making any changes to this project, read this entire file first. After completing code changes, you MUST update the corresponding sections in this file. -->

> 用户使用说明：[使用说明.md](使用说明.md)

---

## 一、项目概述

**Cyber Deck（赛博义肢）** 是一个独立的 WoW 辅助决策系统，分为两层：

1. **WoW 插件层（Lua）**：在游戏内运行，将玩家/目标/队伍/法术等状态编码为屏幕顶部像素条的颜色值
2. **Python 决策层**：在外部运行，通过屏幕像素扫描读取游戏状态，根据职业逻辑做决策，通过后台按键（PostMessage）向游戏发送操作

> 本插件基于 [Fuyutsui](https://github.com/waynebian01/Fuyutsui/) 架构完整移植。原 Fuyutsui 作者已不再维护 Python 决策层，Cyber Deck 将其移植至此并持续更新。当前不依赖 Fuyutsui，可独立运行。

---

## 二、文件结构

```
Cyber_Deck/
├── Cyber_Deck.toc          # 插件定义（v0.0.1, 接口 120000-120005）
├── embeds.xml              # Ace3 库嵌入
├── logic_gui_Tools.py      # 主 GUI 启动器（闭源，Cython 编译加密）
├── Cyber_Deck.exe          # 打包后的独立可执行文件（无需 Python 环境）
├── gui_window_state.json   # GUI 窗口状态持久化
├── README.md               # 完整技术文档（本文件）
├── 使用说明.md              # 用户使用说明
│
├── libs/                   # 第三方库（Ace3 系列, LibRangeCheck-3.0）
│
├── core/                   # Lua 核心模块
│   ├── core.lua            # 插件初始化、AceDB、事件注册、斜杠命令、开关切换
│   ├── config.lua          # spellsList/events/heroTalents/difficulty/keymap 等配置
│   ├── block.lua           # 像素色条创建（255个色块 + 法术充能进度条）
│   ├── macro.lua           # 动态宏创建（@raid/party 智能切换）
│   ├── keybinds.lua        # 扫描动作条按键绑定
│   ├── auras.lua           # 光环状态机（按classId索引）
│   ├── quickbutton.lua     # 四按钮可拖拽面板（爆发/AOE/输出模式/驱散）
│   └── Spell_Misc_EmotionHappy.blp  # 插件图标
│
├── class/                  # 职业模块（13个职业的像素块布局 ClassBlocks）
│   ├── Paladin.lua         # 圣骑士 — 含驱散开关/5码敌人/焦点施法宏
│   └── ...                 # Warrior/Hunter/Rogue/Priest/DK/Shaman/Mage/
│                           #   Warlock/Monk/Druid/DH/Evoker
│
├── main.lua                # 事件处理函数 + OnUpdate 帧循环
├── gui.lua                 # Ace3 配置界面（/fu gui 像素块调试）
│
├── Arasaka/                # Python 决策层
│   ├── config.yml          # 像素块配置（按职业ID分段）
│   ├── utils.py            # 核心工具库（配置加载、按键发送、单位查询）
│   ├── GetPixels.py        # 屏幕像素扫描引擎（mss 截图 + RGB 解码）
│   ├── class/              # 职业逻辑模块（14个.py，13职业 + __init__）
│   │   ├── paladin_logic.py   # 圣骑士（含驱散开关+Holy进攻+5码判断）
│   │   └── ...             # 其余12个职业
│   ├── keymap/             # 按键映射（14个.yml：1个默认 keymap.yml + 13个职业专用）
│   └── other/              # 调试工具 + icon.ico
│
└── pack/                   # 打包工具（Cython + PyInstaller + UPX → exe）
    ├── launcher.py
    ├── 打包exe.py
    ├── 打包exe.bat
    └── upx.exe
```

> **安全说明**：`logic_gui_Tools.py` 通过 Cython 编译为 `.pyd` 后打包进 `Cyber_Deck.exe`。每次打包注入随机数据确保 hash 不同，防特征检测。
>
> **动态加载**：`Arasaka/` 下模块通过 `importlib.import_module` 从磁盘加载，修改 Python 文件后点击 GUI"重载"即生效。
>
> **路径定位**：1. 脚本同级 `Arasaka/` → 2. 注册表 WoW 路径 → 3. WoW 进程路径反推

---

## 三、加载顺序

### Lua 端（按 Cyber_Deck.toc 顺序）

1. `embeds.xml` + `Libs/LibRangeCheck-3.0`
2. `core/core.lua` → `quickbutton.lua` → `config.lua` → `block.lua` → `macro.lua` → `keybinds.lua` → `auras.lua`
3. 13 个 `class/*.lua`（Warrior → Paladin → ... → Evoker）
4. `main.lua` → `gui.lua`

### Python 端

`logic_gui_Tools.py` 启动时：
1. 定位 `Arasaka/` 目录并加入 `sys.path`
2. `importlib.import_module("utils")` + `importlib.import_module("GetPixels")`
3. `_build_class_module_map()` — 构建职业ID→模块名映射
4. `create_gui()` — 创建 GUI，启动按键检测和逻辑执行线程

---

## 四、核心数据流

```
WoW 游戏事件 → Lua 插件 → 编码为像素颜色 → 屏幕顶部 255 像素色块
                                              ↓ 像素扫描 (RGB)
GetPixels.py → state_dict → 职业逻辑 → (hotkey, step, info)
                                              ↓
utils.send_key_to_wow() → PostMessage → WoW 窗口
```

---

## 五、像素编码原理

- **255 个像素**，宽 = 屏幕宽度/255，高 2px
- 颜色编码：`RGB = (0, index/255, value/255)`
  - G 通道 = 索引号（1~255），标识数据含义
  - B 通道 = 数值（0~1），通过颜色曲线映射
- 充能进度条：第二行，255 像素宽，20px 高
- 左边界红/白标记对用于 Python 定位

---

## 六、Lua 端核心机制

### 全局表

```lua
Fuyutsui.state       -- 玩家状态 (classId, className, specName, specID, ...)
Fuyutsui.blocks      -- 当前加载的像素块配置
Fuyutsui.target      -- 目标信息
Fuyutsui.group       -- 队伍单位信息
Fuyutsui.groupList   -- 队伍单位列表
Fuyutsui.defaults    -- AceDB 默认值
Fuyutsui.keybindings -- 按键绑定映射
Fuyutsui.timeElapsed -- OnUpdate 计时器
```

### AceDB 保存变量（`FuyutsuiADB`）

```lua
char = { level, aoeMode, cooldowns, dpsMode, delay, potion,
         quickButtonCX, quickButtonCY, quickButtonShow, dispel }
```

### 关键函数表

| 函数 | 所在文件 | 说明 |
|------|---------|------|
| `F:OnInitialize()` | core.lua | AceDB 初始化，注册 `/fu` 命令 |
| `F:OnEnable()` | core.lua | 获取专精、加载 blocks、注册事件 |
| `F:SwitchCooldown()` | core.lua | 打印爆发状态+写入像素（切换逻辑在 SlashCommand） |
| `F:SwitchAoeMode()` | core.lua | 打印 AOE 模式+写入像素（切换逻辑在 SlashCommand） |
| `F:SwitchDpsMode()` | core.lua | 打印输出模式+写入像素（切换逻辑在 SlashCommand） |
| `F:SwitchDispel()` | core.lua | 切换驱散开关（含切换逻辑+打印+像素写入） |
| `F:OnUpdate(elapsed)` | main.lua | 帧循环（高频+低频轮询） |
| `F:updatePlayerConfig()` | main.lua | 初始化驱散开关等像素 |
| `F:updateEnemyCount()` | main.lua | 敌人计数（含5码姓名版） |
| `CreatTexture(index, value)` | core/block.lua | 写入像素块（参数为索引号+数值） |
| `creatColorCurveScaling(b)` | main.lua | 非线性颜色曲线编码 |
| `InitQuickToggleButton()` | quickbutton.lua | 四按钮面板 |
| `updateAura()` | auras.lua | 光环倒计时 |
| `updateAuraBlocks()` | auras.lua | 光环像素更新 |

**斜杠命令**：`/fu cd/aoemode/dpsmode/potion/delay/dispel/gui/options/macro rebuild/message/help`

完整命令列表：

| 命令 | 说明 |
|------|------|
| `/fu cd` / `cd on` / `cd off` | 切换/开启/关闭爆发 |
| `/fu aoemode` / `auto` / `aoe` | 切换/自动/单体 AOE 模式 |
| `/fu dpsmode` / `manual` / `assistant` | 切换/手写逻辑/一键辅助 |
| `/fu potion` / `on` / `off` | 切换/开启/关闭爆发药水 |
| `/fu delay [秒]` | 临时延迟逻辑（默认 1 秒） |
| `/fu dispel` / `on` / `off` | 切换/开启/关闭驱散 |
| `/fu gui` | 打开像素块调试界面 |
| `/fu options` / `config` | 打开 Ace3 选项界面 |
| `/fu macro rebuild` | 手动重建动态宏 |
| `/fu message <文本>` | 聊天框测试 |
| `/fu help` | 打印帮助信息 |

---

## 七、Python 端核心机制

### logic_gui_Tools.py（闭源）

| 函数 | 说明 |
|------|------|
| `_build_class_module_map()` | 构建职业ID→模块名映射 |
| `reload_logic_modules()` | 热重载所有逻辑模块 |
| `create_gui()` | 创建 GUI，启动线程，进入 mainloop |

**线程模型**：按键检测 50ms / 逻辑执行 200ms / GUI 刷新 100ms

### utils.py

| 函数 | 说明 |
|------|------|
| `load_config()` | 加载 config.yml |
| `load_keymap()` | 加载按键映射（由 `select_keymap_for_class` 动态切换文件） |
| `select_keymap_for_class(class_id)` | 根据职业 ID 切换对应 keymap 文件 |
| `get_hotkey(unit, spell)` | 查找按键 |
| `get_lowest_health_unit(state_dict, threshold)` | 最低血量队友 |
| `get_unit_with_dispel_type(state_dict, dispel_type)` | 需驱散队友 |
| `send_key_to_wow(hotkey, mode)` | PostMessage 发送按键 |

### 职业逻辑统一接口

```python
def run_xxx_logic(state_dict: dict, spec_name: str) -> tuple:
    """返回 (action_hotkey, current_step, unit_info)，无操作时 action_hotkey = None"""
```

---

## 八、状态数据结构

```python
state_dict = {
    "职业": int,          # 1-13
    "专精": str,          # 专精名称
    "生命值": float,      # 玩家血量%
    "能量值": float,      # 玩家能量%
    "战斗": bool,
    "移动": bool,
    "施法": int,          # 施法中
    "引导": int,          # 引导中
    "蓄力": int,          # 蓄力中
    "蓄力层数": int,      # 蓄力层数
    "目标类型": int,      # 0=无, 1-3=敌对, 12-15=友方可驱散
    "目标距离": int,      # 码
    "目标生命值": float,
    "爆发开关": int,      # 0/1
    "AOE开关": int,       # 0=自动, 1=单体
    "输出模式": int,      # 0=一键辅助, 1=手写逻辑
    "敌人人数": int,
    "5码敌人": int,       # Cyber Deck 扩展
    "队伍类型": int,      # 0=单人, 1-40=团本, 46=大秘
    "首领战": int,        # Boss ID
    "难度": int,
    "英雄天赋": int,
    "法术失败": int,
    "驱散开关": int,      # Cyber Deck 扩展
    "spells": { "法术名": 冷却值 },  # 0=就绪
    "group": {
        "1": {
            "生命值": float,     # 血量%
            "职责": int,         # 坦克/治疗/输出
            "驱散": int,         # 需要驱散的类型
            # 职业特定字段如 "永恒之火", "救世道标" 等
        },
        ...
    },
    "auras": { "光环名": int },  # 光环状态（如 "神圣意志", "圣光灌注"）
}
```

### 关键约定

| 概念 | 说明 |
|------|------|
| 冷却值 | 0=就绪, 1~254=冷却中(秒), 255=不可用 |
| 目标类型 | 0=无, 1-3=敌对, 12-15=友方可驱散 |
| 队伍类型 | 0=单人, 1-40=团本, 46=大秘 |
| 职业ID | 1=战士 2=圣骑 3=猎人 4=盗贼 5=牧师 6=DK 7=萨满 8=法师 9=术士 10=武僧 11=德 12=DH 13=唤魔师 |

---

## 九、Cyber Deck 扩展功能

### Lua 端

| 文件 | 功能 | 说明 |
|------|------|------|
| `core/core.lua` | `SwitchDispel` | 驱散开关 |
| `main.lua` | `updatePlayerConfig` | 驱散开关像素初始化 |
| `main.lua` | `updateEnemyCount` | 5码姓名版敌人计数 |
| `main.lua` | `updateUnitCastingOrChannelingInfo` | 修复焦点引导报错 |
| `class/Paladin.lua` | `ClassBlocks[1]` | 追加驱散开关/5码敌人像素块 |
| `class/Paladin.lua` | `MacrosList.staticSpells` | 焦点施法宏 |
| `core/quickbutton.lua` | `InitQuickToggleButton` | 四按钮面板 |

### Python 端

| 文件 | 内容 |
|------|------|
| `Arasaka/config.yml` | Holy(专精1) 追加驱散开关(step 48) + 5码敌人(step 49) + group 块(start:70, num:6)；惩戒(专精3) 含 group(start:70, num:3) |
| `Arasaka/class/paladin_logic.py` | 驱散开关 + Holy进攻优化 + 正义盾击条件判断 + 制裁之锤 + 专精法术限制 |

---

## 十、圣骑士定制详解

### 驱散开关（Lua + Python 双层）

- **Lua**：`SwitchDispel()` 切换 0/1，写入像素块 + SavedVariables
- **Python**：关闭时临时移除 group 中驱散字段 → 原始逻辑跳过队友驱散 → 恢复字段
- 目标驱散不受影响（依赖 `目标类型`，不依赖 group）

### 三专精 config.yml 像素分布

| 专精 | spec ID | 公共 state (step 1-20) | 专精特有 | spells 范围 |
|------|---------|----------------------|----------|------------|
| 神圣 | 1 | 锚点~英雄天赋 | 神圣能量(21)~美德道标(29), 爆发开关(30), 驱散开关(48), 5码敌人(49), group(70+) | step 31-47 |
| 防护 | 2 | 同上 | 神圣能量(21)~圣光之锤(30), 目标距离(31) | step 32-50 |
| 惩戒 | 3 | 同上 | 神圣能量(21)~目标距离(30), group(70+) | step 31-47 |

### Holy 进攻优化

- **MacrosList**：审判/震击 → `[@focustarget,harm][harm]`，正义盾击 → `[@player]`
- **目标类型绕过**：友方目标时强制设为 2（敌方），配合 `@focustarget` 实现"选中友方治疗，自动打焦点目标"
- **正义盾击条件**：5豆 + `5码敌人 >= 1` 才施放

### 四按钮面板

| 按钮 | 功能 |
|------|------|
| 爆发 | 切换爆发开关 |
| 自动/单体 | 切换 AOE 模式 |
| 逻辑/辅助 | 切换输出模式 |
| 驱散 | 切换驱散开关 |

---

## 十一、按键发送机制

Python 通过 `PostMessage(WM_KEYDOWN/WM_KEYUP)` 向 WoW 窗口发送按键：

| 模式 | 说明 |
|------|------|
| `switch` | 按下+释放（默认，适合瞬发） |
| `click` | 鼠标点击 |
| `hold` | 按住不放（持续施法/引导） |

---

## 十二、添加新职业逻辑

### Lua 端

1. 创建/编辑 `class/NewClass.lua`，定义 `Fuyutsui.ClassBlocks[classId]`
2. 在 `core/config.lua` 的 `spellsList` 中添加法术映射
3. 在 `Cyber_Deck.toc` 中注册文件

### Python 端

1. 创建 `Arasaka/class/newclass_logic.py`，实现 `run_newclass_logic(state_dict, spec_name)`
2. 在 `Arasaka/config.yml` 中添加 `keymap: "newclass.yml"`
3. 创建 `Arasaka/keymap/newclass.yml`

---

## 十三、开发规范

### 通用规则

1. **直接修改**：所有功能直接编辑对应文件
2. **中文命名**：像素块、状态字段、GUI 文本
3. **像素索引**：新增从 150+ 开始
4. **SavedVariables**：新增字段在 `core/core.lua` 的 `defaults.char` 注册

### Python 端规则

- 职业逻辑返回 `(action_hotkey, current_step, unit_info)` 三元组
- 优先使用 `utils.py` 工具函数
- 修改后点击 GUI"重载"生效

### 常见陷阱

- **elif 链无法回退**：跳过某优先级需在调用前修改 `state_dict`
- **线程安全**：访问 `_state_dict` 注意 `_state_lock`
- **TOC 顺序**：`core/*.lua` → `class/*.lua` → `main.lua` → `gui.lua`
- **模块缓存**：热重载需 `importlib.reload()`

---

## 十四、调试技巧

- `/fu gui` — 像素块调试界面
- `/fu message 文本` — 聊天框测试
- `/script SetTestSecret(0)` — 关闭秘密值限制（解锁 8 个 CVar，插件启动时默认调用 `SetTestSecret(1)` 开启限制）
- `/fu macro rebuild` — 手动重建宏
- `/fu delay [秒]` — 临时暂停逻辑 N 秒（不写参数默认 1 秒，用于手动插入技能）
- `Arasaka/other/GetRGB.py` — 获取像素 RGB
- `Arasaka/other/GetInfo.py` — 打印 state_dict
- `Arasaka/other/hex_to_decode.py` — 十六进制解码工具
- GUI"重载"按钮 — 热重载 Python 模块

---

## 十五、快速参考（AI 速查）

### 关键文件定位

| 需求 | 文件 |
|------|------|
| Lua 帧循环/事件处理 | `Cyber_Deck/main.lua` |
| Lua 开关/配置 | `Cyber_Deck/core/core.lua` |
| Lua 像素块扩展 | `Cyber_Deck/class/<职业>.lua` |
| Python 职业逻辑 | `Arasaka/class/<职业>_logic.py` |
| 按键映射 | `Arasaka/keymap/<职业>.yml` |
| 像素块配置 | `Arasaka/config.yml` |
| SavedVariables | `Cyber_Deck/core/core.lua` 的 `defaults.char` |

### 像素编码速查

| 概念 | 说明 |
|------|------|
| G 通道 | 索引号 (1~255) |
| B 通道 | 数值 (0~1) |
| 冷却值 | 0=就绪, 1~254=冷却中(秒), 255=不可用 |
| 写入像素 | `self:CreatTexture(index, value)`  (定义在 core/block.lua) |

### 线程模型速查

| 线程 | 间隔 | 职责 |
|------|------|------|
| 按键检测 | 50ms | 轮询绑定按键 |
| 逻辑执行 | 200ms | 扫描→决策→发送 |
| GUI 刷新 | 100ms | 更新状态面板 |

### 职业逻辑返回值

```python
return (action_hotkey, current_step, unit_info)
# action_hotkey: 按键字符串 或 None（无操作）
# current_step: 步骤描述（GUI 显示）
# unit_info: 附加信息字典（GUI 显示）
```
