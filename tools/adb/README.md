# ADB 接入（红手指云手机）

红手指 PC 专业版官方支持 ADB 调试通道。用它做截图(screencap)和操控(input tap/swipe)，
绕开"模拟鼠标被客户端过滤"的问题，且是厂商合规接口（非反作弊对抗）。

> 来源：https://www.gc.com.cn/help/majorpc/adb.htm

## 现状（2026-06-27）

- 当前账号只有 **V1-4** 一台开通了 ADB（VIP，Android 12，剩余 29 天）。
- V1-5 / V1-6 / V1-7 **未开通**；ADB 需"单独申请、人工审核"，四开自动需先给另外三台申请。

## 准备 adb 可执行文件（二选一）

1. **优先**：在红手指 ADB 调试对话框点「启动命令行工具」，在弹出的命令行里输入 `adb version`。
   如果有输出，说明红手指已自带 adb，**无需安装**。
2. 若没有：下载 Google 官方 platform-tools（Windows），解压，把整个 `platform-tools` 文件夹
   放到 `D:\AI Projects\Mayou\tools\platform-tools\`（即让 `tools\platform-tools\adb.exe` 存在）。
   官方下载：https://dl.google.com/android/repository/platform-tools-latest-windows.zip

## 建立连接 + 验证

1. 红手指客户端 → 右键 V1-4 → 「ADB调试」→ 点「建立ADB连接」，记下分配的 **端口号**（127.0.0.1:后面的数字）。
2. 运行验证脚本（命令行里）：

   ```
   D:\AI Projects\Mayou\tools\adb\connect_test.bat 端口号
   ```

   或直接双击 `connect_test.bat`，按提示输入端口号。

3. 脚本会：显示 adb 版本 → 连接 → 列设备 → 打印分辨率 → 截图到 `assets\adb_test.png`。
   把输出和截图反馈给 Claude，确认通道可用后再做出牌(input)与四开扩展。

## 安全

- 红手指给的 **SSH Key / 连接密码 不要发给任何人/不要写进仓库**。客户端"建立ADB连接"会自动管理隧道，
  本脚本只用到不敏感的本地端口号 `127.0.0.1:xxxxx`。
