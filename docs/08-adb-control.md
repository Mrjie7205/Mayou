# 08 · ADB 操控通道（红手指云手机）

> 2026-06-27 新增。采集/操控层的实际接入方式。

## 背景：为什么不用模拟鼠标

实测结论（2026-06-27）：**红手指 PC 专业版会过滤"程序注入"的鼠标/键盘事件**
（SendInput 这类合成输入带 injected 标记，被客户端忽略，只认真实硬件输入）。

验证过程：同一时刻，合成点击+打字在记事本里 100% 生效；在红手指四个窗口里
（拖牌、点「玩法」/「普通▾」/「更多」按钮）全部无反应；坐标映射经 `cursor_position`
逐次核对精确无误，拖拽也是按住→移动→松开的真实手势。故排除坐标/手势/遮挡，
确认是红手指的反自动化行为。

> 因此：靠"截屏幕 + 模拟点像素"的方案在红手指上不可行。
> 按 [CLAUDE.md](../CLAUDE.md) 强约束 5，**不写硬件级 HID 模拟等对抗反自动化的代码**。
> 这对 [ADR-001](decisions/ADR-001-platform.md) 的操控假设是一条重要修正：操控层必须走 ADB。

## 方案：红手指官方 ADB 调试通道

红手指 PC 专业版官方支持 ADB（厂商提供的合规控制口，非反作弊对抗）。
官方教程：https://www.gc.com.cn/help/majorpc/adb.htm

- ADB 能力需"单独申请、人工审核"开通（VIP 功能，逐设备）。
- 本账号 4 台（V1-4/5/6/7）均已开通 ADB。V1-4/6/7 = Android 12，V1-5 = Android 15。
- 在客户端「ADB调试」对话框点「全部建立」后，每台分配一个本地端口 `127.0.0.1:<port>`，
  用 `adb connect 127.0.0.1:<port>` 连上。**端口每次重新建立会变**。

### 当前会话端口（仅参考，换会话/换机即失效）

| 设备 | 端口 |
|---|---|
| V1-4 | 127.0.0.1:32702 |
| V1-5 | 127.0.0.1:32704 |
| V1-6 | 127.0.0.1:32705 |
| V1-7 | 127.0.0.1:32707 |

## 目录与脚本（tools/adb/）

- `setup_adb.bat` —— 从国内镜像（清华/腾讯/北外/Google 依次尝试）下载 platform-tools
  到 `tools/platform-tools/adb.exe`。腾讯镜像可用，adb 1.0.41 (37.0.0)。
  （`tools/platform-tools/` 不入 Git，换机重跑此脚本即可。）
- `connect_all.bat` —— 用上面端口连四台 + 打印分辨率 + 各截一张原图到 `assets/adb/`。一次性验证用。
- `connect_test.bat <port>` —— 单台连通性验证。
- `controller.py` —— **文件桥控制器**（核心，见下）。
- `start_controller.bat` —— 启动控制器，跑起来后保持窗口不关。

## 文件桥控制器（controller.py）

Claude 运行在隔离沙箱里，连不到本机 `127.0.0.1` 端口、也不能在终端打字，
但能读写项目目录。于是用"文件桥"让 Claude 自主驱动，无需 computer-use：

```
controller.py（跑在 Windows 本机）
  ├─ 持续把每台画面截到 runtime/frames/<name>.png（原子写）
  ├─ 轮询 runtime/commands/*.cmd，逐行执行 tap/swipe 等
  └─ 写 runtime/status.json（连接结果、分辨率、心跳）

Claude 侧：读 runtime/frames/*.png 看牌；写 runtime/commands/NNNN.cmd 出牌。
```

`runtime/` 全部不入 Git（帧、命令、状态都是临时数据）。

### 命令协议（一个 .cmd 文件可多行，按文件名排序执行）

```
tap    <name> <x> <y>
swipe  <name> <x> <y> <x2> <y2> [dur_ms]
text   <name> <string...>
key    <name> <KEYCODE_or_int>
wmsize <name>
cap    <name>            # 立即重新截一帧
```
`<name>` ∈ V1-4 V1-5 V1-6 V1-7，或 `all`。执行结果写到 `runtime/commands/done/<file>.out`。

## 启动流程（每台机器/每次会话）

1. （换机首次）克隆仓库后，运行 `tools/adb/setup_adb.bat` 装 adb。
2. 红手指客户端 → 右键设备/批量 →「ADB调试」→「全部建立」，记下 4 个端口。
3. 端口若与 `controller.py` 里 `DEVICES` 不一致：**告诉 Claude 更新端口**（Max 不直接改文件）。
4. 双击 `start_controller.bat` 启动控制器，保持窗口开着。
5. Claude 读 `status.json` + `frames/` 确认连通，开始通过 `commands/` 出牌、采集。

## 安全

- 红手指给的 **SSH Key / 连接密码 绝不入库、绝不发给任何人**。脚本只用不敏感的本地端口号。
- 本仓库私有，不开源、不分发（CLAUDE.md 强约束 1）。
