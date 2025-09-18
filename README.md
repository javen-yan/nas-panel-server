# NAS Panel Server

一个用于 NAS 面板显示的系统监控服务，具有内置 MQTT 代理功能。

## 功能特性

- **系统信息采集**: CPU、内存、存储、网络等基本系统信息
- **内置 MQTT 服务**: 无需外部 MQTT 代理，支持客户端订阅
- **定时采集**: 可配置的数据采集间隔
- **自定义采集器**: 支持通过配置文件添加自定义数据采集
- **温度监控**: 支持 CPU 和内存温度监控（如果硬件支持）
- **磁盘状态**: 监控磁盘健康状态
- **网络流量**: 实时网络上传下载速度

## 安装

### 使用 pip 安装

```bash
pip install -r requirements.txt
python setup.py install
```

### 手动安装

```bash
git clone <repository-url>
cd nas-panel-server
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```bash
# 直接运行
python main.py

# 或者使用安装后的命令
nas-panel-server
```

### 命令行选项

```bash
# 指定配置文件
python main.py -c /path/to/config.yaml

# 测试数据采集
python main.py -t

# 启用详细日志
python main.py -v

# 生成示例配置文件
python main.py --generate-config config.yaml
```

## 配置文件

配置文件使用 YAML 格式，默认查找以下位置的配置文件：

- `config.yaml` (当前目录)
- `config.yml` (当前目录)  
- `nas_panel_server.yaml` (当前目录)
- `/etc/nas-panel-server/config.yaml`
- `~/.config/nas-panel-server/config.yaml`

### 基本配置示例

```yaml
# NAS Panel Server Configuration
server:
  hostname: "NAS-Server"
  ip: "auto"  # auto to detect, or specify manually like "192.168.1.100"
  
mqtt:
  host: "0.0.0.0"
  port: 1883
  topic: "nas/panel/data"
  qos: 1
  
collection:
  interval: 5  # seconds
  
# Custom collection parameters
custom_collectors:
  # 文件读取示例
  - name: "gpu_temp"
    type: "file"
    path: "/sys/class/thermal/thermal_zone1/temp"
    transform: "lambda x: float(x) / 1000"
    unit: "°C"
  
  # 命令执行示例
  - name: "docker_containers"
    type: "command"
    command: "docker ps -q | wc -l"
    transform: "lambda x: int(x)"
    unit: "containers"
  
  # 环境变量示例
  - name: "custom_setting"
    type: "env"
    variable: "CUSTOM_SETTING"
    default: "default_value"
```

### 环境变量覆盖

可以使用环境变量覆盖配置文件中的设置：

- `NAS_PANEL_HOSTNAME`: 服务器主机名
- `NAS_PANEL_IP`: 服务器IP地址
- `NAS_PANEL_MQTT_HOST`: MQTT主机地址
- `NAS_PANEL_MQTT_PORT`: MQTT端口
- `NAS_PANEL_MQTT_TOPIC`: MQTT主题
- `NAS_PANEL_MQTT_QOS`: MQTT QoS级别
- `NAS_PANEL_INTERVAL`: 采集间隔（秒）

## 数据格式

服务器发布的数据格式如下：

```json
{
  "hostname": "NAS-Server",
  "ip": "192.168.1.100",
  "timestamp": "2023-12-01T22:58:00",
  "cpu": {
    "usage": 35.5,
    "temperature": 45.2
  },
  "memory": {
    "usage": 67.8,
    "temperature": 38.1,
    "total": 17179869184,
    "used": 11659091968
  },
  "storage": {
    "capacity": 32000000000000,
    "used": 18000000000000,
    "disks": [
      {"id": "hdd1", "status": "normal"},
      {"id": "hdd2", "status": "normal"},
      {"id": "hdd3", "status": "warning"},
      {"id": "hdd4", "status": "normal"},
      {"id": "hdd5", "status": "error"},
      {"id": "hdd6", "status": "normal"}
    ]
  },
  "network": {
    "upload": 2812000,
    "download": 9400000
  },
  "custom": {
    "gpu_temp": {
      "value": 65.0,
      "unit": "°C",
      "type": "file"
    }
  }
}
```

## 自定义采集器

支持三种类型的自定义采集器：

### 1. 文件读取 (file)

从系统文件读取数据，适用于 `/proc`、`/sys` 等虚拟文件系统：

```yaml
- name: "cpu_freq"
  type: "file"
  path: "/proc/cpuinfo"
  transform: "lambda x: x.split('\\n')[7].split(':')[1].strip()"
  unit: "MHz"
```

### 2. 命令执行 (command)

执行系统命令并获取输出：

```yaml
- name: "uptime"
  type: "command"
  command: "uptime -p"
  unit: "time"
```

### 3. 环境变量 (env)

读取环境变量：

```yaml
- name: "custom_path"
  type: "env"
  variable: "PATH"
  default: "/usr/bin"
```

## MQTT 客户端示例

### Python 客户端

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("nas/panel/data")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"CPU Usage: {data['cpu']['usage']}%")
    print(f"Memory Usage: {data['memory']['usage']}%")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()
```

### mosquitto_sub 命令行

```bash
mosquitto_sub -h localhost -p 1883 -t "nas/panel/data" -v
```

## 系统要求

- Python 3.7+
- Linux/Unix 系统（推荐）
- psutil 库支持的系统

## 依赖项

- `paho-mqtt>=2.0.0`: MQTT 客户端库
- `psutil>=5.9.8`: 系统信息采集库
- `pyyaml>=6.0.1`: YAML 配置文件解析
- `schedule>=1.2.1`: 任务调度库

## 开发

### 项目结构

```
nas-panel-server/
├── nas_panel_server/
│   ├── __init__.py
│   ├── server.py              # 主服务器
│   ├── config_manager.py      # 配置管理
│   ├── data_collector.py      # 数据采集器
│   ├── mqtt_server.py         # MQTT 服务器
│   └── collectors/
│       ├── __init__.py
│       ├── base.py           # 采集器基类
│       ├── system_collector.py  # 系统信息采集器
│       └── custom_collector.py  # 自定义采集器
├── main.py                   # 程序入口
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖项
├── setup.py                # 安装脚本
└── README.md               # 说明文档
```

### 扩展开发

要添加新的采集器，继承 `BaseCollector` 类：

```python
from nas_panel_server.collectors.base import BaseCollector

class MyCustomCollector(BaseCollector):
    def collect(self):
        return {"my_data": "some_value"}
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！