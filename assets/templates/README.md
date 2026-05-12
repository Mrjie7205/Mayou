# 模板库

> 牌面识别用的模板图像。
> **不要手工编辑** —— 用 `tools/template_annotator.py` 采集。

## 结构

```
assets/templates/
├── index.json              # 总索引（程序生成）
├── <platform>/             # 每个平台一份模板
│   ├── tiles/
│   │   ├── tong_1/         # 一筒
│   │   ├── tong_2/         # 二筒
│   │   ├── ...
│   │   ├── tiao_1/         # 一条
│   │   ├── ...
│   │   ├── wan_1/          # 一万
│   │   ├── ...
│   │   └── back/           # 背面
│   └── markers/
│       ├── peng/
│       ├── gang/
│       └── ...
└── _unrecognized/          # 识别置信度低的图像，待补模板
```

## 株洲碰胡牌型 28 类（三色版本）

- 9 种筒（tong_1 ~ tong_9）
- 9 种条/索（tiao_1 ~ tiao_9）
- 9 种万（wan_1 ~ wan_9）
- 1 种背面（back）

⚠️ **没有红中、没有字牌、没有花牌**。详见 [../../docs/07-zhuzhou-pengHu-rules.md](../../docs/07-zhuzhou-pengHu-rules.md)。

⚠️ 如果 Sprint 0 实测确认闲逸的株洲碰胡是单色变体（只用万），模板类数降到 10（9 种万 + 背面）。

## 采集目标

每种牌至少 5 张样本，覆盖云游戏中可能的轻微色彩偏移和动画稳定后的几个视觉变体。
