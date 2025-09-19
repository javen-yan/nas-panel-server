# NAS Panel Server

一个用于 NAS 面板显示的系统监控服务，具有内置 MQTT 代理功能。

## 功能特性

- **系统信息采集**: CPU、内存、存储、网络等基本系统信息
- **内置 MQTT 服务**: 无需外部 MQTT 代理，支持客户端订阅
- **外部 MQTT 支持**: 可连接到现有的 MQTT 代理
- **定时采集**: 可配置的数据采集间隔
- **自定义采集器**: 支持通过配置文件添加自定义数据采集
- **温度监控**: 支持 CPU 和内存温度监控（如果硬件支持）
- **磁盘状态**: 监控磁盘健康状态
- **网络流量**: 实时网络上传下载速度
- **自动主机名检测**: 服务运行时自动检测系统主机名

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

## 快速开始

### 1. 安装依赖

```bash
# 使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 或者直接安装
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
# 使用默认配置
python3 -m nas_panel_server.server

# 使用自定义配置
python3 -m nas_panel_server.server -c config_example.yaml

# 测试数据采集
python3 -m nas_panel_server.server -t

# 启用详细日志
python3 -m nas_panel_server.server -v
```

### 3. 使用启动脚本

```bash
# 前台运行
./start.sh

# 后台运行
./start.sh -d

# 测试模式
./start.sh -t

# 停止后台服务
./stop.sh
```

## 命令行选项

```bash
# 指定配置文件
python3 -m nas_panel_server.server -c /path/to/config.yaml

# 测试数据采集
python3 -m nas_panel_server.server -t

# 启用详细日志
python3 -m nas_panel_server.server -v

# 生成示例配置文件
python3 -m nas_panel_server.server --generate-config config.yaml
```

## 配置说明

### 基本配置

```yaml
# NAS Panel Server Configuration
server:
  hostname: "auto"  # auto to detect hostname automatically, or specify manually
  ip: "auto"        # auto to detect, or specify manually like "192.168.1.100"
  
mqtt:
  type: "builtin"   # "builtin" for built-in MQTT server, "external" for external MQTT broker
  host: "0.0.0.0"   # MQTT服务器地址
  port: 1883        # MQTT端口
  topic: "nas/panel/data"  # 发布主题
  qos: 1            # QoS级别
  
collection:
  interval: 5       # 采集间隔（秒）
  
# Custom collection parameters
custom_collectors: []
```

### 环境变量覆盖

可以使用环境变量覆盖配置文件中的设置：

```bash
export NAS_PANEL_HOSTNAME="My-NAS"
export NAS_PANEL_IP="192.168.1.100"
export NAS_PANEL_MQTT_HOST="localhost"
export NAS_PANEL_MQTT_PORT="1883"
export NAS_PANEL_MQTT_TOPIC="nas/panel/data"
export NAS_PANEL_MQTT_QOS="1"
export NAS_PANEL_INTERVAL="10"
python3 -m nas_panel_server.server
```

支持的环境变量：
- `NAS_PANEL_HOSTNAME`
- `NAS_PANEL_IP`
- `NAS_PANEL_MQTT_HOST`
- `NAS_PANEL_MQTT_PORT`
- `NAS_PANEL_MQTT_TOPIC`
- `NAS_PANEL_MQTT_QOS`
- `NAS_PANEL_INTERVAL`

## MQTT 配置

NAS Panel Server 支持两种 MQTT 模式：

### 1. 内建 MQTT 服务器 (Built-in MQTT Server)

内建 MQTT 服务器是一个完整的 MQTT 代理实现，无需外部依赖。

#### 配置

```yaml
mqtt:
  type: "builtin"
  host: "0.0.0.0"  # 服务器监听地址
  port: 1883       # 服务器监听端口
  topic: "nas/panel/data"
  qos: 1
```

#### 特性

- ✅ 完整的 MQTT 3.1.1 协议支持
- ✅ 支持多客户端连接
- ✅ 支持订阅和发布
- ✅ 支持保留消息 (Retained Messages)
- ✅ 支持通配符订阅 (+ 和 #)
- ✅ 自动客户端管理
- ✅ 服务器统计信息

### 2. 外部 MQTT 客户端 (External MQTT Client)

外部 MQTT 客户端连接到现有的 MQTT 代理（如 Mosquitto、EMQX 等）。

#### 配置

```yaml
mqtt:
  type: "external"
  host: "localhost"        # MQTT 代理地址
  port: 1883              # MQTT 代理端口
  topic: "nas/panel/data"
  qos: 1
  username: "mqtt_user"   # 可选：MQTT 用户名
  password: "mqtt_password"  # 可选：MQTT 密码
  client_id: "nas_panel_server"  # 可选：客户端 ID
  keep_alive: 60          # 可选：保持连接间隔
```

#### 特性

- ✅ 连接到现有 MQTT 代理
- ✅ 支持认证
- ✅ 支持订阅和发布
- ✅ 自动重连
- ✅ 连接状态监控

### 配置切换

#### 从内建切换到外部

1. 修改配置文件：
```yaml
mqtt:
  type: "external"  # 改为 external
  host: "your-mqtt-broker.com"
  port: 1883
  # ... 其他配置
```

2. 重启服务：
```bash
python3 -m nas_panel_server.server -c your_config.yaml
```

#### 从外部切换到内建

1. 修改配置文件：
```yaml
mqtt:
  type: "builtin"  # 改为 builtin
  host: "0.0.0.0"
  port: 1883
  # ... 其他配置
```

2. 重启服务：
```bash
python3 -m nas_panel_server.server -c your_config.yaml
```

## 自定义采集器

支持三种类型的自定义采集器：

### 1. 文件读取 (file)

从系统文件读取数据，适用于 `/proc`、`/sys` 等虚拟文件系统：

```yaml
- name: "cpu_temp"
  type: "file"
  path: "/sys/class/thermal/thermal_zone0/temp"
  transform: "lambda x: float(x) / 1000"
  unit: "°C"
```

### 2. 命令执行 (command)

执行系统命令并获取输出：

```yaml
- name: "docker_containers"
  type: "command"
  command: "docker ps -q | wc -l"
  transform: "lambda x: int(x)"
  unit: "containers"
```

### 3. 环境变量 (env)

读取环境变量：

```yaml
- name: "custom_setting"
  type: "env"
  variable: "CUSTOM_SETTING"
  default: "default_value"
```

### 自定义采集器示例

#### 监控 GPU 温度
```yaml
- name: "gpu_temp"
  type: "command"
  command: "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits"
  transform: "lambda x: float(x)"
  unit: "°C"
```

#### 监控 Docker 服务
```yaml
- name: "docker_status"
  type: "command"
  command: "systemctl is-active docker"
  unit: "status"
```

#### 监控特定目录大小
```yaml
- name: "data_size"
  type: "command"
  command: "du -sh /data | cut -f1"
  unit: "size"
```

## 数据格式

服务器发布的数据格式如下：

```json
{
  "hostname": "LAPTOP-3K464V65",
  "ip": "172.22.123.148",
  "timestamp": "2025-09-19T14:18:31.116320",
  "cpu": {
    "usage": 0.6
  },
  "memory": {
    "usage": 34.0,
    "total": 16603508736,
    "used": 5284749312
  },
  "storage": {
    "capacity": 4324404707328,
    "used": 425683632128,
    "disks": [
      {"id": "sda", "status": "normal"},
      {"id": "sdb", "status": "normal"},
      {"id": "sdc", "status": "normal"}
    ]
  },
  "network": {
    "upload": 0,
    "download": 0
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

# 连接内建 MQTT 服务器
client.connect("localhost", 1883, 60)

# 或连接外部 MQTT 代理
# client.connect("your-mqtt-broker.com", 1883, 60)

client.loop_forever()
```

### 命令行客户端

```bash
# 使用 mosquitto_sub 订阅
mosquitto_sub -h localhost -p 1883 -t "nas/panel/data" -v

# 使用 mosquitto_pub 发布
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "Hello MQTT"
```

## 监控和统计

### 获取 MQTT 统计信息

```python
from nas_panel_server.mqtt import MQTTManager

# 创建 MQTT 管理器
mqtt_manager = MQTTManager(config)

# 获取统计信息
stats = mqtt_manager.get_stats()
print(f"MQTT Type: {stats['mqtt_type']}")
print(f"Connected: {stats.get('connected', stats.get('server_running', False))}")
print(f"Host: {stats['host']}")
print(f"Port: {stats['port']}")
```

### 添加自定义 MQTT 处理

```python
from nas_panel_server.mqtt import MQTTManager

def on_message(client, userdata, msg):
    # 处理接收到的消息
    pass

def on_connect(client, userdata, flags, rc):
    # 处理连接事件
    pass

# 设置回调函数（仅外部 MQTT 支持）
mqtt_manager.set_callbacks(
    on_connect=on_connect,
    on_message=on_message
)
```

## 故障排除

### 内建 MQTT 服务器问题

- **端口被占用**：修改配置文件中的端口号
- **客户端连接失败**：检查防火墙设置
- **消息丢失**：检查 QoS 设置

### 外部 MQTT 客户端问题

- **连接失败**：检查 MQTT 代理是否运行
- **认证失败**：检查用户名和密码
- **网络问题**：检查网络连接和代理地址

### 常见问题

#### Q: 如何添加自定义传感器？
A: 在配置文件的 `custom_collectors` 部分添加新的采集器配置。

#### Q: 温度信息显示不准确？
A: 温度传感器路径可能因硬件而异，请检查 `/sys/class/thermal/` 目录。

#### Q: MQTT连接失败？
A: 检查配置文件中的MQTT设置，确保端口未被占用，防火墙设置正确。

#### Q: 如何监控特定磁盘？
A: 可以通过自定义采集器使用 `smartctl` 或其他磁盘监控工具。

## 性能建议

### 内建 MQTT 服务器

- 适合小到中等规模的部署
- 无需额外依赖
- 性能取决于系统资源

### 外部 MQTT 客户端

- 适合大规模部署
- 利用专业 MQTT 代理的性能
- 支持集群和负载均衡

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
│   ├── mqtt/                  # MQTT 相关模块
│   │   ├── __init__.py
│   │   ├── mqtt_manager.py    # MQTT 管理器
│   │   ├── builtin_server.py  # 内建 MQTT 服务器
│   │   ├── external_client.py # 外部 MQTT 客户端
│   │   ├── client_manager.py  # 客户端管理
│   │   └── protocol.py        # MQTT 协议实现
│   └── collectors/
│       ├── __init__.py
│       ├── base.py           # 采集器基类
│       ├── system_collector.py  # 系统信息采集器
│       └── custom_collector.py  # 自定义采集器
├── main.py                   # 程序入口
├── config.yaml              # 配置文件
├── config_example.yaml      # 配置示例
├── config_external_mqtt.yaml # 外部MQTT配置示例
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

## 配置文件示例

### 内建 MQTT 配置 (config.yaml)

```yaml
server:
  hostname: "auto"  # auto to detect hostname automatically
  ip: "auto"        # auto to detect IP automatically
  
mqtt:
  type: "builtin"
  host: "0.0.0.0"
  port: 1883
  topic: "nas/panel/data"
  qos: 1
  
collection:
  interval: 5  # seconds
  
custom_collectors: []
```

### 外部 MQTT 配置 (config_external_mqtt.yaml)

```yaml
server:
  hostname: "auto"  # auto to detect hostname automatically
  ip: "auto"        # auto to detect IP automatically
  
mqtt:
  type: "external"
  host: "localhost"
  port: 1883
  topic: "nas/panel/data"
  qos: 1
  username: "mqtt_user"
  password: "mqtt_password"
  client_id: "nas_panel_server"
  keep_alive: 60
  
collection:
  interval: 5  # seconds
  
custom_collectors: []
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！