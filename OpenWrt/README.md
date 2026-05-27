# 智能小车 - OpenWRT网络与视频中心

## 项目简介

本模块是智能小车项目的网络与视频核心，基于OpenWRT嵌入式Linux系统，负责摄像头视频推流、Socket网络通信和指令转发功能。

## 核心功能

1. **MJPG-Streamer视频推流** - USB摄像头实时视频流推送，支持网页访问，开机自启
2. **Socket TCP服务端** - 接收上位机AI发送的控制指令
3. **USART串口转发** - 将指令通过串口转发给STM32
4. **指令校验与重传** - 自定义帧格式，确保指令传输可靠性
5. **双systemd服务管理** - 控制服务和推流服务独立管理

## 目录结构

```
OpenWrt/
├── socket_server.py         # Socket服务端主程序
├── car_controller.service   # 控制服务systemd文件
├── mjpg_streamer.service    # 推流服务systemd文件
├── mjpg_streamer.sh         # 推流管理脚本（启动/停止/重启/状态）
├── config.json              # 控制服务配置文件
├── install.sh               # 一键安装脚本
└── README.md                # 说明文档
```

## 视频推流功能

### 功能概述

使用MJPG-Streamer实现USB摄像头视频推流，支持：
- 实时视频流访问
- 快照抓取
- 网页监控界面
- 可配置分辨率和帧率
- systemd服务管理

### 推流服务管理

#### 使用systemd管理（推荐）

```bash
# 启动视频推流
systemctl start mjpg_streamer.service

# 停止视频推流
systemctl stop mjpg_streamer.service

# 重启视频推流
systemctl restart mjpg_streamer.service

# 查看推流状态
systemctl status mjpg_streamer.service

# 查看推流日志
journalctl -u mjpg_streamer.service -f

# 开机自启推流服务
systemctl enable mjpg_streamer.service
```

#### 使用脚本管理

```bash
# 启动视频推流
/opt/car_controller/mjpg_streamer.sh start

# 停止视频推流
/opt/car_controller/mjpg_streamer.sh stop

# 重启视频推流
/opt/car_controller/mjpg_streamer.sh restart

# 查看推流状态
/opt/car_controller/mjpg_streamer.sh status
```

### 访问视频流

在浏览器中访问以下地址：

| 功能 | URL |
|------|-----|
| 视频流监控页面 | `http://192.168.1.1:8080/` |
| 实时视频流 | `http://192.168.1.1:8080/?action=stream` |
| 抓取快照 | `http://192.168.1.1:8080/?action=snapshot` |

### 视频流配置

创建或编辑配置文件 `/etc/mjpg_streamer.conf`：

```bash
# 视频设备
DEVICE="/dev/video0"

# 分辨率
WIDTH="640"
HEIGHT="480"

# 帧率
FPS="30"

# HTTP端口
PORT="8080"

# Web目录
WWW_DIR="/www/webcam"
```

## 安装部署

### 快速安装（推荐）

```bash
# 1. 将所有文件上传到OpenWrt设备的临时目录
cd /tmp

# 2. 运行一键安装脚本
chmod +x install.sh
./install.sh

# 3. 安装完成后，启动两个服务
systemctl start car_controller
systemctl start mjpg_streamer
```

### 手动安装

#### 1. 安装依赖包

```bash
# 更新包列表
opkg update

# 安装Python3和pyserial
opkg install python3 python3-pyserial

# 安装MJPG-Streamer和UVC驱动
opkg install mjpg-streamer kmod-video-uvc
```

#### 2. 部署程序文件

```bash
# 创建工作目录
mkdir -p /opt/car_controller
cd /opt/car_controller

# 复制文件到目标目录
cp socket_server.py /opt/car_controller/
cp config.json /opt/car_controller/
cp mjpg_streamer.sh /opt/car_controller/

# 设置执行权限
chmod +x /opt/car_controller/socket_server.py
chmod +x /opt/car_controller/mjpg_streamer.sh
```

#### 3. 配置systemd服务

```bash
# 复制服务文件
cp car_controller.service /etc/systemd/system/
cp mjpg_streamer.service /etc/systemd/system/

# 重载systemd配置
systemctl daemon-reload

# 启用开机自启动
systemctl enable car_controller.service
systemctl enable mjpg_streamer.service

# 启动服务
systemctl start car_controller.service
systemctl start mjpg_streamer.service

# 查看服务状态
systemctl status car_controller.service
systemctl status mjpg_streamer.service
```

#### 4. 配置WiFi

```bash
# 编辑网络配置文件
vi /etc/config/network

# 编辑无线配置文件
vi /etc/config/wireless

# 重启网络服务
/etc/init.d/network restart
```

## 配置说明

### config.json配置文件

```json
{
    "socket": {
        "host": "0.0.0.0",      # 监听地址
        "port": 2002            # 监听端口
    },
    "serial": {
        "port": "/dev/ttyUSB0", # 串口设备
        "baudrate": 115200,     # 波特率
        "timeout": 1            # 超时时间(秒)
    },
    "logging": {
        "level": "INFO",        # 日志级别
        "file": "/var/log/car_controller.log"
    }
}
```

### 串口配置

根据实际硬件连接修改串口设备：
- CH340/CP2102: `/dev/ttyUSB0`
- 板载串口: `/dev/ttyS0` 或 `/dev/ttyAMA0`

### 摄像头兼容性

支持大部分UVC标准的USB摄像头，常见型号：
- Logitech C270/C310/C920
- 普通USB免驱摄像头

检查摄像头支持的分辨率和格式：
```bash
# 安装v4l2-utils（可选）
opkg install v4l-utils

# 查看摄像头信息
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

## 通信协议

### 指令帧格式

```
┌────────┬────────┬──────────┬─────────┬──────────┐
│ 帧头1  │ 帧头2  │ 指令字节 │ 数据... │ 校验和   │
│ 0xAA   │ 0x55   │ 1字节    │ N字节   │ 1字节    │
└────────┴────────┴──────────┴─────────┴──────────┘
```

### 指令定义

| 指令字节 | 功能说明 |
|---------|---------|
| 0x00    | 停止    |
| 0x01    | 前进    |
| 0x02    | 后退    |
| 0x03    | 左转    |
| 0x04    | 右转    |
| 0x05    | 舵机控制|

### 速度控制

| 速度字节 | 速度等级 |
|---------|---------|
| 0x0A    | 低速    |
| 0x0B    | 中速    |
| 0x0C    | 高速    |

### 校验和计算

```python
checksum = sum(frame_data[:-1]) & 0xFF
```

## 服务管理

### 控制服务管理

```bash
# 启动服务
systemctl start car_controller.service

# 停止服务
systemctl stop car_controller.service

# 重启服务
systemctl restart car_controller.service

# 查看服务状态
systemctl status car_controller.service

# 查看实时日志
journalctl -u car_controller.service -f

# 禁用开机自启
systemctl disable car_controller.service
```

### 推流服务管理

```bash
# 启动服务
systemctl start mjpg_streamer.service

# 停止服务
systemctl stop mjpg_streamer.service

# 重启服务
systemctl restart mjpg_streamer.service

# 查看服务状态
systemctl status mjpg_streamer.service

# 查看实时日志
journalctl -u mjpg_streamer.service -f

# 禁用开机自启
systemctl disable mjpg_streamer.service
```

## 故障排查

### 串口无法打开

1. 检查串口设备是否存在：`ls /dev/tty*`
2. 检查串口权限：`ls -l /dev/ttyUSB0`
3. 检查是否有其他程序占用串口
4. 查看系统日志：`dmesg | grep tty`

### Socket端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep 2002

# 杀掉占用进程
kill -9 <PID>
```

### 摄像头无法识别

1. 检查摄像头是否连接：`lsusb`
2. 检查视频设备：`ls /dev/video*`
3. 查看系统日志：`dmesg | grep video`
4. 确认UVC驱动已加载：`lsmod | grep uvcvideo`

### 视频推流启动失败

1. 查看推流日志：`journalctl -u mjpg_streamer.service -f`
2. 检查MJPG-Streamer是否安装：`which mjpg_streamer`
3. 检查摄像头设备是否被占用：`lsof /dev/video0`
4. 尝试降低分辨率或帧率

### 视频流卡顿

1. 降低分辨率：修改配置文件中的WIDTH/HEIGHT
2. 降低帧率：修改配置文件中的FPS
3. 检查WiFi信号强度
4. 避免同时多个客户端访问视频流

## 关联项目

- **STM32端** - 实时运动控制
- **PC端AI** - 视觉识别与决策算法

