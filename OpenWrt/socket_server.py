#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenWRT Socket TCP服务端
接收上位机AI指令，通过串口转发给STM32
"""

import socket
import serial
import time
import threading
import logging
from queue import Queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CarController:
    def __init__(self, host='0.0.0.0', port=2002, serial_port='/dev/ttyUSB0', baudrate=115200):
        self.host = host
        self.port = port
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.ser = None
        self.sock = None
        self.command_queue = Queue()
        self.running = False
        
    def init_serial(self):
        """初始化串口"""
        try:
            self.ser = serial.Serial(
                port=self.serial_port,
                baudrate=self.baudrate,
                timeout=1
            )
            logger.info(f"串口 {self.serial_port} 初始化成功")
            return True
        except Exception as e:
            logger.error(f"串口初始化失败: {e}")
            return False
    
    def init_socket(self):
        """初始化Socket服务端"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            logger.info(f"Socket服务端启动成功，监听 {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Socket初始化失败: {e}")
            return False
    
    def calculate_checksum(self, data):
        """计算校验和"""
        checksum = sum(data) & 0xFF
        return checksum
    
    def verify_checksum(self, data):
        """验证校验和"""
        if len(data) < 4:
            return False
        received_checksum = data[-1]
        calculated_checksum = sum(data[:-1]) & 0xFF
        return received_checksum == calculated_checksum
    
    def send_to_stm32(self, data):
        """发送数据到STM32"""
        if not self.ser or not self.ser.is_open:
            logger.warning("串口未打开，无法发送数据")
            return False
        
        try:
            # 添加校验和
            checksum = self.calculate_checksum(data)
            data_with_checksum = data + bytes([checksum])
            
            self.ser.write(data_with_checksum)
            logger.info(f"发送到STM32: {data_with_checksum.hex()}")
            return True
        except Exception as e:
            logger.error(f"发送到STM32失败: {e}")
            return False
    
    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        logger.info(f"新客户端连接: {client_address}")
        
        try:
            while self.running:
                # 接收数据
                data = client_socket.recv(1024)
                if not data:
                    break
                
                logger.info(f"收到上位机数据: {data.hex()}")
                
                # 验证帧头
                if len(data) >= 2 and data[0] == 0xAA and data[1] == 0x55:
                    # 转发给STM32
                    self.send_to_stm32(data)
                else:
                    logger.warning("收到无效数据，帧头不正确")
                    
        except Exception as e:
            logger.error(f"处理客户端连接出错: {e}")
        finally:
            client_socket.close()
            logger.info(f"客户端断开连接: {client_address}")
    
    def serial_receive_thread(self):
        """串口接收线程"""
        while self.running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    logger.info(f"收到STM32数据: {data.hex()}")
            except Exception as e:
                logger.error(f"串口接收出错: {e}")
                time.sleep(1)
            time.sleep(0.01)
    
    def start(self):
        """启动服务"""
        self.running = True
        
        # 初始化串口
        if not self.init_serial():
            logger.error("无法初始化串口，退出")
            return
        
        # 初始化Socket
        if not self.init_socket():
            logger.error("无法初始化Socket，退出")
            return
        
        # 启动串口接收线程
        serial_thread = threading.Thread(target=self.serial_receive_thread, daemon=True)
        serial_thread.start()
        
        logger.info("服务启动完成，等待客户端连接...")
        
        try:
            while self.running:
                # 等待客户端连接
                client_socket, client_address = self.sock.accept()
                
                # 处理客户端连接
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止服务")
        except Exception as e:
            logger.error(f"服务运行出错: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务"""
        self.running = False
        
        if self.sock:
            self.sock.close()
        
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        logger.info("服务已停止")

def main():
    """主函数"""
    controller = CarController(
        host='0.0.0.0',
        port=2002,
        serial_port='/dev/ttyUSB0',
        baudrate=115200
    )
    controller.start()

if __name__ == '__main__':
    main()
