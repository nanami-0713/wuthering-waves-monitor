#!/bin/bash
# Wuthering Waves 国服服务器状态监测脚本
# 服务器地址通过环境变量配置，避免在代码中提交真实地址。

GAME_IP="${WW_SERVER_IP:?请设置 WW_SERVER_IP 环境变量}"
GAME_PORT="${WW_SERVER_PORT:-13102}"
INTERVAL="${WW_INTERVAL:-30}"  # 检测间隔秒数

echo "============================================"
echo "  Wuthering Waves 国服服务器状态监测"
echo "  目标: $GAME_IP:$GAME_PORT (UDP)"
echo "  启动时间: $(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')"
echo "  检测间隔: ${INTERVAL}s"
echo "============================================"
echo ""

prev_status=""

while true; do
    timestamp=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')

    # 方法1: ICMP ping (网络层可达性)
    ping -n 1 -w 2 "$GAME_IP" > /dev/null 2>&1
    ping_ok=$?

    # 方法2: UDP 端口探测 (用 timeout + nc)
    # nc -u -z 发送一个空 UDP 包，看 ICMP 是否回 port unreachable
    # 如果端口开放，通常不回复；如果服务器不可达则收到 ICMP 错误
    timeout 2 bash -c "echo 'test' | nc -u -w 1 '$GAME_IP' '$GAME_PORT'" 2>/dev/null
    nc_exit=$?

    # 判断逻辑:
    # - ping 通 + 没有 ICMP port unreachable = 服务器在线
    # - ping 不通 = 服务器离线/维护
    # - ping 通 + ICMP port unreachable = 服务器在但游戏进程没开

    if [ $ping_ok -eq 0 ]; then
        # 再试一次 UDP 探测，看是否返回 port unreachable
        udp_result=$(timeout 2 nmap -sU -p "$GAME_PORT" "$GAME_IP" 2>/dev/null | grep -E "open|closed|filtered")

        if echo "$udp_result" | grep -q "open"; then
            status="🟢 在线 - 游戏服正常运行"
        elif echo "$udp_result" | grep -q "closed"; then
            status="🟡 端口关闭 - 服务器在线但游戏进程可能未启动"
        elif echo "$udp_result" | grep -q "filtered"; then
            status="🟠 端口过滤 - 可能维护中"
        else
            status="🟢 在线 (ping 可达)"
        fi
    else
        status="🔴 离线 - 服务器不可达"
    fi

    # 仅在状态变化时输出
    if [ "$status" != "$prev_status" ]; then
        echo "[$timestamp] $status"
        prev_status="$status"
    else
        echo "[$timestamp] $status (无变化)"
    fi

    sleep "$INTERVAL"
done
