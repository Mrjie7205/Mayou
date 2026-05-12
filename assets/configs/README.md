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
    "my_hand": {"x": 100, "y": 600, "w": 800, "h": 100},
    "discard_self": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_left": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_across": {"x": 0, "y": 0, "w": 0, "h": 0},
    "discard_right": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_self": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_left": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_across": {"x": 0, "y": 0, "w": 0, "h": 0},
    "meld_right": {"x": 0, "y": 0, "w": 0, "h": 0},
    "last_played_highlight": {"x": 0, "y": 0, "w": 0, "h": 0},
    "turn_indicator": {"x": 0, "y": 0, "w": 0, "h": 0}
  },
  
  "tile_size_hint": {
    "min_w": 30, "max_w": 50,
    "min_h": 40, "max_h": 60
  },
  
  "rule_variant": {
    // 株洲碰胡变体开关，详见 docs/07 §8。所有字段 Sprint 0 实测后填实
    "tile_set": "three_suit",      // "three_suit"(108张) | "single_suit"(36张) ⚠️ 待实测
    "qishou_hu": false,             // 起手胡 ⚠️
    "qiang_gang_hu": true,          // 抢杠胡（暗杠通常不可抢）⚠️
    "qi_dui_zi": false,             // 七对子 ⚠️
    "quan_qiu_ren_fan": 0,          // 全求人加番值 ⚠️
    "si_an_ke_fan": 0,              // 四暗刻加番值 ⚠️
    "yipao_duoxiang": true,         // 一炮多响 ⚠️
    "haidi_hu_fan": 0               // 海底胡加番值 ⚠️
  },
  
  "ui": {
    "main_window_pos": {"x": 1500, "y": 100},
    "transparency": 0.85
  }
}
```

## 版本化策略

配置文件**纳入 Git**。这样平台改版后能 diff 看出哪些坐标变了，便于补丁式更新。
