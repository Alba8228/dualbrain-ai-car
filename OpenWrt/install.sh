#!/bin/bash
# OpenWRT智能小车控制程序安装脚本

set -e

echo "=========================================="
echo "  OpenWRT智能小车控制程序安装"
echo "=========================================="

# 配置变量
INSTALL_DIR="/opt/car_controller"
SERVICE_NAME="car_controller"
STREAMER_SERVICE="mjpg_streamer"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用root用户运行此脚本"
    exit 1
fi

# 1. 更新包列表
echo ""
echo "[1/8] 更新包列表..."
opkg update

# 2. 安装依赖
echo ""
echo "[2/8] 安装依赖包..."
opkg install python3 python3-pyserial mjpg-streamer kmod-video-uvc || {
    echo "依赖安装失败，请检查网络连接"
    exit 1
}

# 3. 创建安装目录
echo ""
echo "[3/8] 创建安装目录..."
mkdir -p "$INSTALL_DIR"
cd "$(dirname "$0")"

# 4. 复制程序文件
echo ""
echo "[4/8] 复制程序文件..."
cp socket_server.py "$INSTALL_DIR/"
cp config.json "$INSTALL_DIR/"
cp mjpg_streamer.sh "$INSTALL_DIR/"

# 设置执行权限
chmod +x "$INSTALL_DIR/socket_server.py"
chmod +x "$INSTALL_DIR/mjpg_streamer.sh"

# 5. 配置控制服务systemd（不自动启动）
echo ""
echo "[5/8] 配置Socket控制服务..."
cp car_controller.service /etc/systemd/system/
systemctl daemon-reload

# 6. 配置推流服务systemd（开机自启）
echo ""
echo "[6/8] 配置视频推流服务..."
cp mjpg_streamer.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$STREAMER_SERVICE.service"

# 7. 创建日志目录
echo ""
echo "[7/8] 创建日志目录..."
mkdir -p /var/log

# 8. 检测摄像头
echo ""
echo "[8/8] 检测摄像头设备..."
if ls /dev/video* 1>/dev/null 2>&1; then
    echo "检测到以下摄像头设备:"
    ls -la /dev/video*
else
    echo "警告: 未检测到摄像头设备，请连接USB摄像头"
fi

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "📌 服务说明："
echo "  - 视频推流服务: 已设置为开机自启"
echo "  - Socket控制服务: 需要时手动启动"
echo ""
echo "服务管理命令："
echo "  Socket控制服务:"
echo "    systemctl start $SERVICE_NAME   # 启动"
echo "    systemctl stop $SERVICE_NAME    # 停止"
echo "    systemctl status $SERVICE_NAME  # 状态"
echo "    journalctl -u $SERVICE_NAME -f  # 日志"
echo ""
echo "  视频推流服务:"
echo "    systemctl start $STREAMER_SERVICE   # 启动"
echo "    systemctl stop $STREAMER_SERVICE    # 停止"
echo "    systemctl status $STREAMER_SERVICE  # 状态"
echo "    journalctl -u $STREAMER_SERVICE -f  # 日志"
echo "  或使用脚本: $INSTALL_DIR/mjpg_streamer.sh {start|stop|restart|status}"
echo ""
echo "访问地址："
echo "  视频流: http://$(uci get network.lan.ipaddr 2>/dev/null || echo '192.168.1.1'):8080/?action=stream"
echo "  快照:   http://$(uci get network.lan.ipaddr 2>/dev/null || echo '192.168.1.1'):8080/?action=snapshot"
echo ""
echo "程序安装目录: $INSTALL_DIR"
echo ""

