#!/bin/bash
# MJPG-Streamer启动/停止/重启脚本

CONFIG_FILE="/etc/mjpg_streamer.conf"
PID_FILE="/var/run/mjpg_streamer.pid"

# 默认配置
DEVICE="/dev/video0"
WIDTH="640"
HEIGHT="480"
FPS="30"
PORT="8080"
WWW_DIR="/www/webcam"

# 加载配置文件
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# 检查MJPG-Streamer是否安装
check_install() {
    if ! command -v mjpg_streamer &> /dev/null; then
        echo "错误: MJPG-Streamer 未安装"
        echo "请运行: opkg update && opkg install mjpg-streamer"
        exit 1
    fi
}

# 检查摄像头设备
check_device() {
    if [ ! -e "$DEVICE" ]; then
        echo "错误: 摄像头设备 $DEVICE 不存在"
        echo "可用设备:"
        ls -la /dev/video* 2>/dev/null || echo "  无视频设备"
        exit 1
    fi
}

# 创建web目录
create_www_dir() {
    if [ ! -d "$WWW_DIR" ]; then
        mkdir -p "$WWW_DIR"
        echo "创建web目录: $WWW_DIR"
        # 创建简单的index.html
        cat > "$WWW_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>智能小车视频监控</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #f0f0f0; }
        h1 { color: #333; }
        .container { background: white; padding: 20px; margin: 20px auto; border-radius: 10px; display: inline-block; }
        img { max-width: 100%; border: 2px solid #333; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>智能小车视频监控</h1>
    <div class="container">
        <img src="/?action=stream" alt="视频流" id="stream">
    </div>
    <p>访问 /?action=snapshot 获取快照</p>
</body>
</html>
EOF
    fi
}

# 启动MJPG-Streamer
start_streamer() {
    check_install
    check_device
    create_www_dir

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if kill -0 "$PID" 2>/dev/null; then
            echo "MJPG-Streamer 已在运行 (PID: $PID)"
            return 1
        fi
    fi

    echo "启动MJPG-Streamer..."
    echo "  设备: $DEVICE"
    echo "  分辨率: ${WIDTH}x${HEIGHT}"
    echo "  帧率: ${FPS}fps"
    echo "  端口: $PORT"

    mjpg_streamer \
        -i "input_uvc.so -d $DEVICE -r ${WIDTH}x${HEIGHT} -f $FPS" \
        -o "output_http.so -p $PORT -w $WWW_DIR" \
        > /var/log/mjpg_streamer.log 2>&1 &
    
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
        echo "MJPG-Streamer 启动成功 (PID: $PID)"
        echo "视频流地址: http://$(uci get network.lan.ipaddr 2>/dev/null || echo '192.168.1.1'):$PORT/?action=stream"
        echo "快照地址: http://$(uci get network.lan.ipaddr 2>/dev/null || echo '192.168.1.1'):$PORT/?action=snapshot"
        return 0
    else
        echo "MJPG-Streamer 启动失败，请查看日志: /var/log/mjpg_streamer.log"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止MJPG-Streamer
stop_streamer() {
    if [ ! -f "$PID_FILE" ]; then
        echo "MJPG-Streamer 未运行"
        return 0
    fi

    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -z "$PID" ]; then
        rm -f "$PID_FILE"
        echo "MJPG-Streamer 未运行"
        return 0
    fi

    echo "停止MJPG-Streamer (PID: $PID)..."
    kill "$PID" 2>/dev/null
    
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            rm -f "$PID_FILE"
            echo "MJPG-Streamer 已停止"
            return 0
        fi
        sleep 0.5
    done

    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "MJPG-Streamer 已强制停止"
    return 0
}

# 查看状态
status_streamer() {
    if [ ! -f "$PID_FILE" ]; then
        echo "MJPG-Streamer: 未运行"
        return 1
    fi

    PID=$(cat "$PID_FILE" 2>/dev/null)
    if kill -0 "$PID" 2>/dev/null; then
        echo "MJPG-Streamer: 运行中 (PID: $PID)"
        echo "  视频流: http://$(uci get network.lan.ipaddr 2>/dev/null || echo '192.168.1.1'):$PORT/?action=stream"
        return 0
    else
        echo "MJPG-Streamer: 未运行 (PID文件残留)"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 主函数
case "$1" in
    start)
        start_streamer
        ;;
    stop)
        stop_streamer
        ;;
    restart)
        stop_streamer
        sleep 1
        start_streamer
        ;;
    status)
        status_streamer
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        echo ""
        echo "示例:"
        echo "  $0 start    # 启动视频推流"
        echo "  $0 stop     # 停止视频推流"
        echo "  $0 restart  # 重启视频推流"
        echo "  $0 status   # 查看状态"
        exit 1
        ;;
esac

