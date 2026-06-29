#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mayou ADB 控制器（文件桥）。
跑在 Windows 本机，连四台红手指云手机，做两件事：
  1) 持续把每台的画面截图到 runtime/frames/<name>.png（原子写）
  2) 轮询 runtime/commands/*.cmd，执行里面的 tap/swipe 等指令

Claude（在沙箱里）通过读 frames/ + 往 commands/ 写文件来驱动，不需要 computer-use。

启动：双击 start_controller.bat，或  python controller.py
停止：在 runtime/commands/ 放一个名为 STOP 的文件，或直接关窗口。

命令文件格式（每个 .cmd 文件可含多行；按文件名排序、逐行执行）：
  tap    <name> <x> <y>
  swipe  <name> <x> <y> <x2> <y2> [dur_ms]
  text   <name> <string...>
  key    <name> <KEYCODE_or_int>
  wmsize <name>
  cap    <name>            # 立即重新截一帧
其中 <name> ∈ V1-4 V1-5 V1-6 V1-7，或 all
"""
import os, sys, time, json, subprocess, glob, shutil, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(HERE, "..", "platform-tools", "adb.exe")
if not os.path.exists(ADB):
    ADB = "adb"  # 退回 PATH

# 端口来自红手指 ADB调试-全部建立；每次重建会变，由 Claude 维护这里。
DEVICES = {
    "V1-4": "127.0.0.1:32702",
    "V1-5": "127.0.0.1:32704",
    "V1-6": "127.0.0.1:32705",
    "V1-7": "127.0.0.1:32707",
}

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # D:\AI Projects\Mayou
RUNTIME = os.path.join(ROOT, "runtime")
FRAMES = os.path.join(RUNTIME, "frames")
CMDS = os.path.join(RUNTIME, "commands")
DONE = os.path.join(CMDS, "done")
STATUS = os.path.join(RUNTIME, "status.json")

CAP_INTERVAL = 1.2   # 秒：每台轮流截图的周期
for d in (RUNTIME, FRAMES, CMDS, DONE):
    os.makedirs(d, exist_ok=True)


def run(args, timeout=30, binary=False):
    try:
        p = subprocess.run([ADB] + args, capture_output=True, timeout=timeout)
        out = p.stdout if binary else p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        return p.returncode, out, err
    except Exception as e:
        return -1, (b"" if binary else ""), f"EXC {e}"


def adb_dev(name, args, **kw):
    serial = DEVICES[name]
    return run(["-s", serial] + args, **kw)


def connect_all():
    res = {}
    for name, serial in DEVICES.items():
        code, out, err = run(["connect", serial], timeout=20)
        res[name] = (out + err).strip()
    return res


def wm_size(name):
    code, out, err = adb_dev(name, ["shell", "wm", "size"])
    return out.strip() or err.strip()


def capture(name):
    serial = DEVICES[name]
    code, out, err = adb_dev(name, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
    if code == 0 and out[:8] == b"\x89PNG\r\n\x1a\n":
        dst = os.path.join(FRAMES, name + ".png")
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(out)
        os.replace(tmp, dst)
        return True, len(out)
    return False, err.strip()[:200]


def exec_line(line):
    parts = line.split()
    if not parts:
        return "empty"
    op = parts[0].lower()
    if op in ("#", "rem"):
        return "comment"
    name = parts[1] if len(parts) > 1 else ""
    names = list(DEVICES) if name == "all" else [name]
    out_all = []
    for nm in names:
        if nm not in DEVICES:
            out_all.append(f"{nm}: unknown device")
            continue
        if op == "tap":
            x, y = parts[2], parts[3]
            c, o, e = adb_dev(nm, ["shell", "input", "tap", x, y])
            out_all.append(f"{nm} tap {x},{y} rc={c} {e.strip()}")
            capture(nm)
        elif op == "swipe":
            a = parts[2:7]  # x y x2 y2 [dur]
            c, o, e = adb_dev(nm, ["shell", "input", "swipe"] + a)
            out_all.append(f"{nm} swipe {' '.join(a)} rc={c} {e.strip()}")
            capture(nm)
        elif op == "text":
            s = " ".join(parts[2:])
            c, o, e = adb_dev(nm, ["shell", "input", "text", s])
            out_all.append(f"{nm} text rc={c} {e.strip()}")
        elif op == "key":
            k = parts[2]
            c, o, e = adb_dev(nm, ["shell", "input", "keyevent", k])
            out_all.append(f"{nm} key {k} rc={c} {e.strip()}")
        elif op == "wmsize":
            out_all.append(f"{nm} wmsize {wm_size(nm)}")
        elif op == "cap":
            ok, info = capture(nm)
            out_all.append(f"{nm} cap ok={ok} {info}")
        else:
            out_all.append(f"unknown op: {op}")
    return " | ".join(out_all)


def process_commands():
    files = sorted(glob.glob(os.path.join(CMDS, "*.cmd")))
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            results = [exec_line(ln) for ln in lines if ln.strip()]
            with open(os.path.join(DONE, os.path.basename(fp) + ".out"), "w", encoding="utf-8") as f:
                f.write("\n".join(results))
            shutil.move(fp, os.path.join(DONE, os.path.basename(fp)))
        except Exception as e:
            with open(os.path.join(DONE, os.path.basename(fp) + ".err"), "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            try:
                os.remove(fp)
            except OSError:
                pass


def write_status(extra=None):
    st = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "adb": ADB, "devices": DEVICES}
    if extra:
        st.update(extra)
    tmp = STATUS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATUS)


def main():
    print("Mayou controller starting. ADB =", ADB)
    conn = connect_all()
    sizes = {nm: wm_size(nm) for nm in DEVICES}
    write_status({"connect": conn, "wm_size": sizes, "state": "running"})
    print("connect:", conn)
    print("wm_size:", sizes)
    rr = 0
    names = list(DEVICES)
    last_status = 0
    while True:
        if os.path.exists(os.path.join(CMDS, "STOP")):
            write_status({"state": "stopped"})
            print("STOP found, exit.")
            return
        process_commands()
        # 轮流截一台，避免一次性卡顿
        nm = names[rr % len(names)]
        capture(nm)
        rr += 1
        now = time.time()
        if now - last_status > 5:
            write_status({"state": "running", "loop": rr})
            last_status = now
        time.sleep(CAP_INTERVAL / len(names))


if __name__ == "__main__":
    main()
