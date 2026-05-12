# Mayou

转转麻将云游戏辅助工具 · 个人项目 · 仅用于欢乐场

## 这是什么

一个挂在 PC 上的桌面工具。在电脑上开云游戏玩转转麻将时，Mayou 实时读取屏幕、追踪牌局、给出出牌建议。我手动按建议出牌。

## 文档入口

| 文档 | 用途 | 何时读 |
|---|---|---|
| [PRD.md](PRD.md) | 项目定位、范围、里程碑 | 开工前 / 评估改动是否越界 |
| [ROADMAP.md](ROADMAP.md) | Sprint 拆分与当前进度 | 每次开工对一下进度 |
| [CLAUDE.md](CLAUDE.md) | 给 Claude Code 的指令 | Claude Code 自动读 |
| [docs/01-architecture.md](docs/01-architecture.md) | 五层架构总览 | 想理解系统怎么跑的时候 |
| [docs/02-cv-pipeline.md](docs/02-cv-pipeline.md) | 截图与识别层细节 | 改 CV 相关代码前 |
| [docs/03-state-machine.md](docs/03-state-machine.md) | 牌局状态机 | 改账本逻辑前 |
| [docs/04-decision-engine.md](docs/04-decision-engine.md) | 决策引擎 | 改建议逻辑前 |
| [docs/05-ui-spec.md](docs/05-ui-spec.md) | UI 规格 | 改界面前 |
| [docs/06-zhuanzhuan-rules.md](docs/06-zhuanzhuan-rules.md) | 转转麻将规则参考 | 调引擎、对胡牌型时 |
| [docs/decisions/](docs/decisions/) | 关键决策记录（ADR） | 回顾"为什么这么定"时 |

## 当前状态

🟡 **规划阶段**。还没写任何代码。

下一步：
1. 确定云游戏平台（见 [ADR-001](docs/decisions/ADR-001-platform.md)）
2. 进入 Sprint 0（脚手架），见 [ROADMAP.md](ROADMAP.md)

## 项目惯例

继承自 trading-terminal 的工程习惯：

- **Max 不直接改文件**：所有数据修改通过 UI 或 Claude Code 进行，不存在"手动编辑 JSON"的设计。
- **前端优先**：新功能涉及数据写入的，必须先有前端入口。
- **欢乐场原则**：本项目永不用于现金桌、永不分发。
