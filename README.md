# nas-panel-server


实现一个服务，可以采集到机器的信息，按照一下的json格式发送的mqtt服务中， 为了简化实现， 该服务内置mqtt， 允许客户端使用 topic 进行订阅， 本身定时采集机器信息，然后发送到 topic 中

代码针对不同数据需要合理化设计，为了好扩展实现，最后支持自定义参数采集的功能

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
  }
}
```
