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

## 转转麻将牌型 28 类

- 9 种筒（tong_1 ~ tong_9）
- 9 种条/索（tiao_1 ~ tiao_9）
- 9 种万（wan_1 ~ wan_9）
- 1 种背面（back）

⚠️ **没有红中、没有字牌**。详见 [../../docs/06-zhuanzhuan-rules.md](../../docs/06-zhuanzhuan-rules.md)。

## 采集目标

每种牌至少 5 张样本，覆盖云游戏中可能的轻微色彩偏移和动画稳定后的几个视觉变体。
