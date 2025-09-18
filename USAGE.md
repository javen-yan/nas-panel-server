# NAS Panel Server 使用指南

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
python3 main.py

# 使用自定义配置
python3 main.py -c config_example.yaml

# 测试数据采集
python3 main.py -t

# 启用详细日志
python3 main.py -v
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

## 配置说明

### 基本配置

```yaml
server:
  hostname: "NAS-Server"      # 服务器名称
  ip: "auto"                  # IP地址，"auto"自动检测

mqtt:
  host: "0.0.0.0"            # MQTT服务器地址
  port: 1883                  # MQTT端口
  topic: "nas/panel/data"     # 发布主题
  qos: 1                      # QoS级别

collection:
  interval: 5                 # 采集间隔（秒）
```

### 自定义采集器

#### 文件读取类型
```yaml
- name: "cpu_temp"
  type: "file"
  path: "/sys/class/thermal/thermal_zone0/temp"
  transform: "lambda x: float(x) / 1000"
  unit: "°C"
```

#### 命令执行类型
```yaml
- name: "disk_usage"
  type: "command"
  command: "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'"
  transform: "lambda x: int(x)"
  unit: "%"
```

#### 环境变量类型
```yaml
- name: "custom_var"
  type: "env"
  variable: "MY_CUSTOM_VAR"
  default: "default_value"
```

## 环境变量

可以使用环境变量覆盖配置：

```bash
export NAS_PANEL_HOSTNAME="My-NAS"
export NAS_PANEL_MQTT_PORT=1884
export NAS_PANEL_INTERVAL=10
python3 main.py
```

支持的环境变量：
- `NAS_PANEL_HOSTNAME`
- `NAS_PANEL_IP`
- `NAS_PANEL_MQTT_HOST`
- `NAS_PANEL_MQTT_PORT`
- `NAS_PANEL_MQTT_TOPIC`
- `NAS_PANEL_MQTT_QOS`
- `NAS_PANEL_INTERVAL`

## 数据格式

输出的JSON格式：

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
    "total": 17179869184,
    "used": 11659091968
  },
  "storage": {
    "capacity": 32000000000000,
    "used": 18000000000000,
    "disks": [
      {"id": "sda", "status": "normal"}
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

## 常见问题

### Q: 如何添加自定义传感器？
A: 在配置文件的 `custom_collectors` 部分添加新的采集器配置。

### Q: 温度信息显示不准确？
A: 温度传感器路径可能因硬件而异，请检查 `/sys/class/thermal/` 目录。

### Q: MQTT连接失败？
A: 当前版本使用简化的MQTT实现，主要用于演示。生产环境建议使用专门的MQTT代理。

### Q: 如何监控特定磁盘？
A: 可以通过自定义采集器使用 `smartctl` 或其他磁盘监控工具。

## 示例用法

### 监控 GPU 温度
```yaml
- name: "gpu_temp"
  type: "command"
  command: "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits"
  transform: "lambda x: float(x)"
  unit: "°C"
```

### 监控 Docker 服务
```yaml
- name: "docker_status"
  type: "command"
  command: "systemctl is-active docker"
  unit: "status"
```

### 监控特定目录大小
```yaml
- name: "data_size"
  type: "command"
  command: "du -sh /data | cut -f1"
  unit: "size"
```