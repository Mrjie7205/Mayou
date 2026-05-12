# 平台配置

> 每个云游戏平台一份 JSON 配置。
> **不要手工编辑** —— 用 `tools/region_picker.py` 生成。

## 文件命名

`<platform_slug>.json`，例如：
- `netease_cloud.json`（网易云游戏）
- `tencent_start.json`（腾讯先锋）
- `migu.json`（咪咕快游）

## 结构

```jsonc
{
  "platform": "netease_cloud",
  "platform_display_name": "网易云游戏",
  "created_at": "2026-XX-XX",
  
  "window_title_pattern": "网易云游戏.*转转麻将",
  
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
    "qishou_hu": false,
    "guo_shui": false,
    "yipao_duoxiang": true
  },
  
  "ui": {
    "main_window_pos": {"x": 1500, "y": 100},
    "transparency": 0.85
  }
}
```

## 版本化策略

配置文件**纳入 Git**。这样平台改版后能 diff 看出哪些坐标变了，便于补丁式更新。
