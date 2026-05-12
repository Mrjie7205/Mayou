# 平台配置

> 每个云游戏平台一份 JSON 配置。
> **不要手工编辑** —— 用 `tools/region_picker.py` 生成。

## 文件命名

`<platform_slug>.json`，例如：
- `redfinger.json`（红手指云手机，当前选定，见 [ADR-001](../../docs/decisions/ADR-001-platform.md)）
- 未来若扩展：`duoduoyun.json`、`leidian.json` 等

## 结构

```jsonc
{
  "platform": "redfinger",
  "platform_display_name": "红手指云手机 + 闲逸棋牌",
  "created_at": "2026-XX-XX",
  
  "window_title_pattern": "红手指.*",  // Sprint 0 实测后确认
  
  "regions": {
    "my_hand": {"x": 100, "y": 600, "w": 800, "h": 100},  // 庄 15 张 / 闲 14 张
    "discard_self": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_left": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_across": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_right": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_self": {"x": 0, "y": 0, "w": 0, "h": 0},      // 副露区（碰/偎/提/跑/吃）
    "meld_left": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_across": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_right": {"x": 0, "y": 0, "w": 0, "h": 0},
    "last_played_highlight": {"x": 0, "y": 0, "w": 0, "h": 0},
    "turn_indicator": {"x": 0, "y": 0, "w": 0, "h": 0},
    "baojing_indicator": {"x": 0, "y": 0, "w": 0, "h": 0}  // 五福报警状态显示位置
  },
  
  "tile_size_hint": {
    "min_w": 30, "max_w": 50,
    "min_h": 40, "max_h": 60
  },
  
  "rule_variant": {
    // 株洲碰胡（湖南字牌）规则开关，详见 docs/07。截图明确的已填默认值，⚠️ 标的需 Max 实战确认
    "ju_shu": 16,                   // 局数：8/12/16/24（截图默认 16）
    "ren_shu": 4,                   // 人数（本项目锁 4 人）
    "zhongzhuang_mode": "lianzhong", // 连胡机制：lianzhong/zhongzhuang/zhongzhuang_x2/sishou_xiangcheng/bashou_xiangcheng/buzhongzhuang/xin_zhongzhuang_x2 ⚠️ 后几种公式待测
    "qiangzhi_hu_pai": "yes_7dui_no_kan", // 强制胡牌：no/yes/7dui_no_kan/7dui_dai_kan
    "speed": "normal",              // 正常 / 快速
    "qiepai": false,                // 切牌 ⚠️ 含义待确认
    "hupai_tishi": true,            // 胡牌提示
    "zidong_zhunbei": false,        // 自动准备 ⚠️ 含义待确认
    "wudui": false,                 // 无对 ⚠️ 含义待确认
    "daniao": false,                // 打鸟 ⚠️ 含义待确认
    "kuaisu_chipai": true,          // 快速吃牌：一吃或一吃一比时不弹选项直接落桌
    "suijizuowei": true,            // 随机坐位
    "shaoren_mode": false,          // 少人模式
    "chaoshi_tuoguan": "off",       // 不托管 / 30s / 1m / 2m / 3m
    "chaoshi_jiesan": "off",        // 不解散 / 90s / 120s / 150s

    // 引擎相关的规则细节（待实战确认）
    "li_dao_long_dao_definition": null,  // ⚠️ 俚到/垄到 定义
    "chouwei_score": null,              // ⚠️ 臭偎计分
    "haidi_hu_fan": null,               // ⚠️ 截图未提海底胡
    "gangshang_hua_fan": null           // ⚠️ 截图未提杠上花
  },
  
  "ui": {
    "main_window_pos": {"x": 1500, "y": 100},
    "transparency": 0.85
  }
}
```

## 版本化策略

配置文件**纳入 Git**。这样平台改版后能 diff 看出哪些坐标变了，便于补丁式更新。
