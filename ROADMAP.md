# Mayou Roadmap

> 按 Max 实际投入节奏（约 2 小时/周）规划。
> 周数为预估，实际滑动。
> 最后更新：2026-05-12

## 当前状态

🟢 **Sprint -1 ~ Sprint 5 算法层已云端完成**（2026-05-12）。下一步：**Max 本地装环境实测**，校准模板 + 适配区域 + 接入真实截图。

> 一气呵成的开发策略（按 Max 要求）：把所有"不依赖真实截图"的代码在云端做完，包括字牌引擎、状态机、UI 渲染、复盘 JSON、识别层框架、模板采集器、演示模式。本地环境就绪后用 `python -m src.main --demo` 验证完整 UI 跑通。

## 里程碑总览

```
[Sprint -1] 平台 + 游戏选型             ✅ 已完成
    ↓
[S0 ~ S4]  MVP-1 记牌器（~20 周）       ← 当前位置
    ↓
[S5 ~ S8]  MVP-2 完整辅助（~38-44 周累计；字牌引擎从零写、动作多）
    ↓
[Wave 1/2/3]  顶尖人类水平（~60-80 周累计，见 ADR-003）
```

---

## Sprint -1：平台 + 游戏选型（已完成）

**目标**：选定运行平台与核心游戏。

任务：
- [x] 调研云手机方案（红手指 / 多多云 / 雷电 / 网易云手机）
- [x] 基于先验经验确认红手指 PC 客户端可装第三方棋牌 App、可正常截屏
- [x] 横向对比三个候选游戏的工程难度（转转麻将 / 株洲碰胡 / 跑得快）
- [x] 在 [ADR-001](docs/decisions/ADR-001-platform.md) 中选定红手指 + 闲逸棋牌
- [x] 在 [ADR-002](docs/decisions/ADR-002-game-switch.md) 中切换核心游戏为株洲碰胡
- [x] 锁定后不再更改（除非平台下架或玩法下架）

**完成标志**：ADR-001 + ADR-002 状态均为 `accepted`。✅

---

## MVP-1：记牌器

### Sprint 0：脚手架（1-3 周）

- [~] Python 环境 + 依赖安装（云端只到 `requirements.txt` 锁定；本地 `pip install` 待 Max 配环境）
- [x] `tools/region_picker.py`：全屏透明覆盖层 + 鼠标拖框 + 保存到 `assets/configs/redfinger.json`
- [x] PySide6 主控台骨架：左半适配区 + 右半 4 个信息块 + 顶栏暂停（Ctrl+Space）+ 状态栏
- [x] 主循环骨架：QTimer 200ms 心跳，暂停时停拍，状态栏显示心跳计数
- [~] 项目能跑起来，能看到截图区域被框出来（代码完成，等 Max 本地 `python -m src.main` 与 `python -m tools.region_picker` 实测）

> 本地实测前置：Max 在 Y9000K 上装 Python 3.11+ 与 `pip install -r requirements.txt`。Claude 会在 Max 准备好时给手把手指引。

### Sprint 1：模板采集器（4-6 周）

- [x] `tools/template_annotator.py`：截图后让 Max 框 + 打标签，自动入 `assets/templates/`
- [~] 目标：每种牌至少 5 张模板（20 种字 + 1 种背面 = 21 类 × 5 ≈ 105 张） — **代码就绪，模板待 Max 本地采集**
- [x] 模板库索引（template_summary 已有按需加）

### Sprint 2：单牌识别（7-10 周）

- [x] OpenCV 模板匹配实现（`src/recognize/template_match.py`）
- [x] 多尺度匹配处理云手机视频流缩放（默认 ±15%）
- [x] 区域识别框架（`src/recognize/region_recognizer.py`，等距切分 MVP 版）
- [ ] **准确率与切分实测**：等模板采齐后用真实截图测，调阈值 + 改"找牌边界"算法

**完成标志**：自己手牌 14 张识别准确率 ≥99%。— **代码框架完成，准确率验证待本地实测**

### Sprint 3：弃牌区与副露区识别（11-15 周）

- [x] 区域识别接口适用任何区域（弃/副露 = 同一 `recognize_strip`）
- [x] 帧间差分（`src/state/event_detector.py` 简化版：检测 discard / baojing；完整规则推断待本地接通）

### Sprint 4：状态机 v1（16-20 周）

- [x] `GameState` 含 4 家手牌/弃牌/副露/碰次数/报警/胜者
- [x] 事件类型：摸/打/碰/偎/提/跑/吃/报警/胡/臭庄（events.py 列全；apply_event handler 已实现核心几个）
- [x] 复盘 JSON 写入 `data/replays/`
- [ ] 起手判定：小七对/双龙在 deal 时立刻触发 — **判胡逻辑已有，集成到状态机待 Sprint 4 实战**
- [ ] 动画防抖（连续 3 帧稳定才确认）— **框架占位，本地实测时调**
- [ ] UI 事件日志区 ✅（`src/ui/panels/event_log.py`）
- [ ] UI 剩余牌统计 ✅（`src/ui/panels/counter.py` 按大小写 × 红黑分组）

**🚩 MVP-1 完成标志**：
- 一整局牌打完，事件序列回放与实际一致
- 准确率 ≥95%
- Max 实战使用一周不崩

---

## MVP-2：完整辅助

### Sprint 5：字牌胡牌判定 + shanten（21-25 周）

- [x] 字牌胡牌判定（`src/engine/win_check.py`）—— 句话/绞牌/坎/提 + 大小写不混 + 二七十特例
- [x] 特殊胡型：小七对 / 双龙；天胡 / 地胡 / 五福靠状态机配合识别
- [x] shanten 启发式（`src/engine/shanten.py`）
- [x] 听张枚举 `waiting_tiles`
- [x] 32 个引擎单测覆盖 docs/07 §11 大部分局面
- [ ] ⚠️ 待实战补充：俚到/垄到例外、shanten 含提的精度提升

### Sprint 6：蒙特卡洛进攻评分（26-30 周）

- [x] `src/engine/monte_carlo.py` evaluate_attack + evaluate_all_discards
- [x] 听牌时直接概率公式，多向听用 300 次模拟
- [x] 期望积分（按 docs/07 §6 计分表）
- [x] UI 显示各张牌的进攻分（`SuggestionPanel`）

### Sprint 7：防守评分（31-35 周）

- [x] `src/engine/defense.py`：现物 + 筋（标准三连）+ 壁
- [x] 五福报警家高警戒（is_baojing → +0.6 危险）
- [x] UI 牌局分析显示三家危险度（`AnalysisPanel`，三色标记）
- [ ] ⚠️ 待 Sprint 7 实战调参：筋的特殊连张（2-7-10）逻辑、对手听张推测启发式

### Sprint 8：决策融合与调参（36-44 周）

- [x] 进攻分 × 防守分加权（`src/engine/recommend.py`）
- [x] 局势识别动态调整权重：自己已听 α=0.85；对手报警 β=0.7；其他均衡
- [x] UI 高亮推荐 + 分项展示（`SuggestionPanel`）
- [ ] **Max 实战调参周** — 待本地接通真实数据后做

**🚩 MVP-2 Wave 1 起点**：建议能给到、击败中等人类玩家（≥ 50% 胜率，50 局样本）。

---

## MVP-2 进阶 — 目标顶尖人类水平

> 2026-05-13 [ADR-003](docs/decisions/ADR-003-target-upgrade.md)：把 MVP-2 验收从「中等人类」升级为「顶尖人类」。
> 周期从 38-44 周延长到 60-80 周，分三波渐进。

### Wave 1（45-55 周）：核心算法重构

- [ ] 简化版 EV 公式（替代线性加权 α×attack + β×defense）
- [ ] 对手向听粗估（3 档：≤1 / ≤2 / ≥3）
- [ ] MC 启发式弃牌 `_fast_eval_discard`
- [ ] 卡位防守（peng_count ≥ 3 时高警戒）
- [ ] 配套单测

**完成标志**：实战 50 局 ≥ 50% 胜率（对中等人类）

### Wave 2（56-68 周）：算法精度升级

- [ ] shanten 真 DP + 20 维数组化（原 Batch 2 搁置项）
- [ ] 简化版对手持有概率向量（3 档启发式：Maybe / Unlikely / Impossible）
- [ ] EV 公式升级（接入持有概率 + 对手向听）

**完成标志**：实战 100 局 ≥ 55% 胜率，Max 主观感觉接近顶尖

### Wave 3（69-80 周）：离线自对弈调参

- [ ] `scripts/bench_engine.py` 两引擎对打 + 胜率统计
- [ ] 参数 grid search（暴力枚举关键超参）
- [ ] 遗传算法 / 贝叶斯优化（自动调参）
- [ ] 基于上百万局自对弈日志的真贝叶斯先验

**完成标志**：对顶尖人类有竞争力（建议质量同档）

### 明确不做（[ADR-003](docs/decisions/ADR-003-target-upgrade.md)）

- 诱导防守 / 造安全假象 / minimax 多层博弈
- 神经网络 / RL / LLM 推断
- 自动出牌

---

## 进度更新规则

- 每完成一个 Sprint，在对应任务前 `[ ]` 改成 `[x]`
- Sprint 跨度大幅偏离预估时，在 Sprint 标题下加一行 `_实际：X周_`
- 滑动里程碑总周数同步更新
- 大方向变更走 ADR 流程，不直接改 Roadmap

---

## 已完成

- **2026-05-12 · Sprint -1**：完成平台 + 游戏选型。锁定红手指 + 闲逸 + 株洲碰胡。详见 [ADR-001](docs/decisions/ADR-001-platform.md)、[ADR-002](docs/decisions/ADR-002-game-switch.md)。
- **2026-05-12 · Sprint 0-8 算法层**：一气呵成把所有不依赖真实截图的代码写完。30+ 个新文件，57 个单元测试全过。包括：字牌引擎（牌张/句话/绞牌/胡牌判定/shanten）、积分/蒙特卡洛/防守/推荐、状态机/复盘 JSON、识别层框架、模板采集器、UI 6 个面板 + 演示模式 + 主循环。`python -m src.main --demo` 可在演示模式跑通完整 UI。
