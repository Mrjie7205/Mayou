# Architecture Decision Records (ADRs)

> 关键决策的记录。任何一个"以后会被人问起为什么这么做"的决定都应该在这里有一份。

## 何时写一个新 ADR

- 选型决策（库、平台、模式）
- 架构变更（新增层、合并层、改职责）
- 工程惯例确立（命名规范、测试策略）
- 推翻之前 ADR（写新的 ADR，旧的标记为 Superseded）

## 模板

```markdown
# ADR-NNN · 标题

- **状态**：Proposed / Accepted / Rejected / Superseded by ADR-XXX
- **日期**：YYYY-MM-DD
- **决策者**：
- **影响范围**：

## 背景
（为什么需要做这个决策）

## 候选
（评估过的方案）

## 决策记录
（最终选了哪个、为什么）

## 后果
（这个决策带来的好处和成本）
```

## 索引

| 编号 | 标题 | 状态 |
|---|---|---|
| [001](ADR-001-platform.md) | 运行平台选型（红手指 + 闲逸棋牌） | ✅ Accepted |
| [002](ADR-002-game-switch.md) | 核心游戏切换：转转麻将 → 株洲碰胡 | ✅ Accepted |
