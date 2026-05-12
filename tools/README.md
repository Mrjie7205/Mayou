# tools/

> 辅助工具脚本，独立于主程序。

## 计划中的工具

| 工具 | Sprint | 用途 |
|---|---|---|
| `region_picker.py` | S0 | 截屏 + 鼠标框选屏幕区域，生成平台配置 JSON |
| `template_annotator.py` | S1 | 截图后让 Max 框 + 打标签，自动入模板库 |
| `accuracy_eval.py` | S2 | 跑测试集，统计识别准确率 |
| `replay_viewer.py` | S4 | 加载事件日志，回放任意中间状态 |
| `weight_tuner.py` | S8 | 引擎权重交互式调参 |

## 设计原则

- 每个工具一个 Python 文件，能 `python tools/xxx.py` 直接跑
- 工具的 UI 简陋，但**必须易用**（不能让 Max 调参时还要写代码）
- 工具的输出（配置、模板、报告）**必须能被主程序消费**

## 调试帧目录

`tools/debug_frames/YYYYMMDD/` 由主程序在调试模式下写入，工具可读取。

不进 Git，`.gitignore` 已排除。
