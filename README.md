# Wuthering Waves CN Server Monitor

监控《鸣潮》国服服务器开服状态的脚本。支持 Python 和 Bash 两个版本，检测到服务器开放时可以播放提示音。

> 隐私说明：本仓库不包含真实服务器 IP/端口。请通过环境变量在本地配置，避免公开仓库泄露服务器地址。

## 文件

- `wuthering_waves_monitor.py`：Python 版，Windows 下可用，支持播放 MP3 闹铃。
- `wuthering_waves_monitor.sh`：Bash 版，适合 Linux / Git Bash 环境。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `WW_SERVER_IP` | 是 | 无 | 要监控的服务器 IP 地址 |
| `WW_SERVER_PORT` | 否 | `13102` | 服务器 UDP 端口 |
| `WW_INTERVAL` | 否 | Python `5` / Bash `30` | 探测间隔（秒） |

## 使用方法

### Python 版

```bash
export WW_SERVER_IP=你的服务器IP
export WW_SERVER_PORT=13102
python wuthering_waves_monitor.py "/path/to/alarm.mp3"
```

### Bash 版

```bash
export WW_SERVER_IP=你的服务器IP
export WW_SERVER_PORT=13102
./wuthering_waves_monitor.sh
```

## 快捷键

- Python 版：按 `Enter` 停止当前闹铃，按 `Ctrl+C` 退出监控。
- Bash 版：直接 `Ctrl+C` 退出。

## 隐私与安全

- 不要将真实服务器 IP、端口、Token、密码等敏感信息提交到仓库。
- 建议通过环境变量或本地配置文件注入敏感信息，并确保它们不被 Git 跟踪。
