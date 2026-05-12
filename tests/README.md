# tests/

> 自动化测试。

## 结构

```
tests/
├── README.md
├── cv_fixtures/            # CV 层测试数据
│   ├── tiles/              # 单牌识别测试集（截图+标签）
│   └── full_frames/        # 全图测试集
├── state_fixtures/         # 状态机测试数据
│   └── *.jsonl             # 事件流回放文件
├── engine_fixtures/        # 引擎测试数据
│   └── hands/              # 手牌局面 + 期望输出
├── test_cv.py
├── test_state.py
├── test_engine.py
└── test_integration.py
```

## 优先级

按 Sprint 推进，不强求 TDD：

- **CV 层**：必有回归测试。每次改识别逻辑跑一遍。准确率不达标禁止合并。
- **状态机**：必有边角情况测试。一炮多响、抢杠胡等都要有 fixture。
- **引擎**：胡牌型判定必须单元测试覆盖。
- **集成测试**：跑通完整一局牌的回放，验证 e2e。

## 运行

```bash
pytest tests/
pytest tests/test_engine.py -v
pytest tests/ --cov=src
```

## 不测的东西

- UI 渲染：人眼验收
- 截屏：依赖具体平台，手工验收
- 性能：单独的基准测试，不混在功能测试里
