#!/usr/bin/env python3
"""
Wuthering Waves 国服服务器开服监控
每 5 秒探测一次，检测到开服时自动播放指定 MP3。

服务器地址通过环境变量配置，避免在代码中提交真实地址。

用法:
  WW_SERVER_IP=<server-ip> python wuthering_waves_monitor.py ".mp3"

快捷键:
  Enter  = 立刻停止当前播放的闹铃
  Ctrl+C = 退出整个监控
"""
import ctypes
import msvcrt
import socket
import subprocess
import time
import sys
import os
from datetime import datetime

GAME_IP   = os.environ.get("WW_SERVER_IP", "").strip()
GAME_PORT = int(os.environ.get("WW_SERVER_PORT", "13102").strip())
INTERVAL  = int(os.environ.get("WW_INTERVAL", "5").strip())

# ── MCI 音频控制 ────────────────────────────────────────

MCI_ALIAS = "mc_alarm"

def mci_err_text(code):
    """将 MCI 错误码转为可读文本"""
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.winmm.mciGetErrorStringW(code, buf, 256)
    return buf.value

def mci(cmd):
    """发送 MCI 命令，成功返回 0，失败返回错误文本并打印"""
    code = ctypes.windll.winmm.mciSendStringW(cmd, None, 0, None)
    if code != 0:
        err = mci_err_text(code)
        print(f"  [MCI错误] 命令: {cmd}")
        print(f"  [MCI错误] 原因: {err}")
    return code

def alarm_start(mp3_path):
    """打开并播放 MP3，返回 True=成功  False=失败"""
    abs_path = os.path.abspath(mp3_path)
    # 先关旧的（首次没有别名会报错，静默忽略）
    ctypes.windll.winmm.mciSendStringW(
        f'close {MCI_ALIAS}', None, 0, None
    )

    # 尝试 mpegvideo 类型
    code = ctypes.windll.winmm.mciSendStringW(
        f'open "{abs_path}" type mpegvideo alias {MCI_ALIAS}', None, 0, None
    )
    if code != 0:
        # 回退：不指定类型，让 Windows 自动匹配
        code = ctypes.windll.winmm.mciSendStringW(
            f'open "{abs_path}" alias {MCI_ALIAS}', None, 0, None
        )
    if code != 0:
        err = mci_err_text(code)
        print(f"  [MCI打开失败] {err}")
        return False

    code = ctypes.windll.winmm.mciSendStringW(
        f'play {MCI_ALIAS}', None, 0, None
    )
    if code != 0:
        err = mci_err_text(code)
        print(f"  [MCI播放失败] {err}")
        return False

    return True

def alarm_stop():
    """停止并关闭 MCI 别名（静默，忽略错误）"""
    ctypes.windll.winmm.mciSendStringW(f'stop {MCI_ALIAS}', None, 0, None)
    ctypes.windll.winmm.mciSendStringW(f'close {MCI_ALIAS}', None, 0, None)

# ── 探测函数 ────────────────────────────────────────────

def ping_ms():
    """返回 ping 延迟(ms)，不通返回 None"""
    try:
        r = subprocess.run(
            ["ping", "-n", "1", "-w", "1500", GAME_IP],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode != 0:
            return None
        for line in r.stdout.splitlines():
            if "Average" in line or "平均" in line:
                return int(line.split("=")[-1].replace("ms", "").strip())
        return 999
    except:
        return None

def udp_port_open():
    """发送空 UDP 包探测端口。True=开放，False=关闭"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.5)
        sock.sendto(b"\x00", (GAME_IP, GAME_PORT))
        try:
            sock.recvfrom(1)
        except socket.timeout:
            return True
        except ConnectionRefusedError:
            return False
        finally:
            sock.close()
        return True
    except OSError:
        return False

# ── 状态判定 ────────────────────────────────────────────

def get_status():
    delay = ping_ms()
    udp   = udp_port_open()
    if delay is None:
        return "OFFLINE",  "服务器不可达"
    if udp:
        return "OPEN",     f"游戏服在线 (ping={delay}ms)"
    else:
        return "CLOSED",   f"游戏端口关闭，维护中 (ping={delay}ms)"

def check_keypress():
    """非阻塞检测键盘输入，返回按下的键或 None"""
    if msvcrt.kbhit():
        return msvcrt.getch()
    return None

# ── 主循环 ──────────────────────────────────────────────

def main():
    if not GAME_IP:
        print("缺少环境变量 WW_SERVER_IP，请先设置服务器地址。")
        print("示例: WW_SERVER_IP=1.2.3.4 python wuthering_waves_monitor.py \"alarm.mp3\"")
        sys.exit(1)

    mp3_path = sys.argv[1] if len(sys.argv) > 1 else None

    print()
    print("=" * 55)
    print("  Wuthering Waves 国服开服监控")
    print(f"  目标: {GAME_IP}:{GAME_PORT} (UDP)")
    print(f"  启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  间隔: {INTERVAL}s  |  Enter=停闹铃  |  Ctrl+C=退出")
    if mp3_path:
        print(f"  闹铃: {os.path.basename(mp3_path)}  (开服时自动播放)")
    print("=" * 55)
    print()

    if mp3_path:
        if os.path.isfile(mp3_path):
            print(f"[OK] 闹铃文件已找到: {mp3_path}")
        else:
            print(f"[警告] 文件不存在: {mp3_path}")
            print("       继续监控，但开服时无法播放闹铃")
            mp3_path = None
        print()

    prev_code   = ""
    alarm_fired = False
    count       = 0
    start       = time.time()

    try:
        while True:
            # ── 非阻塞键盘检测 ──
            key = check_keypress()
            if key in (b'\r', b'\n'):
                alarm_stop()
                print("\n[已手动停止闹铃]")
                print("按 Enter 继续监控（不停止脚本）...")
                # 等待任意键继续
                while check_keypress() is None:
                    time.sleep(0.1)

            # ── 服务器探测 ──
            timestamp = datetime.now().strftime("%H:%M:%S")
            code, detail = get_status()
            elapsed = int(time.time() - start)

            if code != prev_code or count % 12 == 0:
                tag = {"OPEN": "[OPEN]  ", "CLOSED": "[MAINT] ", "OFFLINE": "[DOWN]  "}[code]
                print(f"{tag}[{timestamp}] {detail}  (运行 {elapsed}s)")

                if code != prev_code:
                    print(f"  >>> 状态变更: {prev_code} -> {code} <<<")
                    if code != "OPEN":
                        alarm_fired = False
                    print()

                # 检测到开服 且 本轮未响过 → 播放 MP3
                if code == "OPEN" and not alarm_fired and mp3_path:
                    print(f"  >>> 已开服！播放闹铃 (按 Enter 停止) <<<")
                    try:
                        ok = alarm_start(mp3_path)
                        if ok:
                            alarm_fired = True
                        else:
                            print(f"  >>> MCI 播放失败，尝试 os.startfile 回退... <<<")
                            os.startfile(os.path.abspath(mp3_path))
                            alarm_fired = True
                    except Exception as e:
                        print(f"  >>> 播放失败: {e} <<<")
                    print()

                prev_code = code
                count = 0
            else:
                sys.stdout.write(".")
                sys.stdout.flush()

            count += 1
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        alarm_stop()
        total = int(time.time() - start)
        m, s  = divmod(total, 60)
        print(f"\n\n监控结束。运行时长: {m}m{s}s")

if __name__ == "__main__":
    main()
