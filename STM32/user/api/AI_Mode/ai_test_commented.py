# 导入 PyTorch 深度学习框架，用于运行 YOLOv8 模型
import torch
# 从 ultralytics 库导入 YOLO 类，用于加载和使用 YOLO 目标检测模型
from ultralytics import YOLO
# 导入 OpenCV 库，用于视频捕获、图像处理和显示
import cv2
# 导入 cvzone 库，这是一个基于 OpenCV 的辅助库，用于方便地绘制角矩形等效果
import cvzone
# 导入 math 数学库，用于计算置信度等数学操作
import math
# 导入 os 库，用于设置环境变量
import os
# 导入 numpy 库，用于数组和矩阵运算
import numpy as np
# 从 sort.py 导入 Sort 类，这是一个多目标跟踪算法
from sort import Sort
# 导入 pandas 库，用于处理跟踪目标的数据表格
import pandas as pd
# 从 utils.py 导入工具函数，包括计算角度和获取控制字节的函数
from utils import get_angle, get_control_byte
# 导入 socket 库，用于与 STM32 小车进行网络通信
import socket
# 从 queue 导入 Queue 类，用于线程间安全地传递数据
from queue import Queue
# 导入 threading 库，用于创建和管理多线程
import threading
# 导入 traceback 库，用于打印详细的错误堆栈信息
import traceback
# 导入 copy 库，用于深拷贝列表等数据结构
import copy
# 导入 time 库，用于延时和时间控制
import time

# 设置环境变量，解决 OpenMP 库重复导入导致的冲突问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 初始化线程列表，用于存放所有创建的线程对象
ThreadingList = []
# 创建信号队列，用于线程间传递控制指令（如前进、左转等）
signal_queue = Queue()
# 创建帧队列，用于线程间传递视频帧数据
frame_queue = Queue()
# 定义滤波参数字典，不同的滤波次数对应不同的阈值数组
# 数组索引说明: [状态列表长度, 后退阈值, 前进阈值, 右转阈值, 左转阈值, 停止阈值]
filter_dict = {
    1: [1, 1, 2, 3, 4, 5],      # 不滤波（滤波次数=1）
    2: [2, 2, 4, 6, 8, 10],     # 默认滤波（滤波次数=2）
    3: [3, 3, 6, 9, 12, 15],    # 滤波次数=3
    5: [5, 5, 10, 15, 20, 25]   # 滤波次数=5
}

# 定义网络摄像头的视频流地址（MJPG 格式）
camera_addr = 'http://192.168.1.1:8080/?action=stream'
# 定义 YOLOv8 模型权重文件的路径
weights_path = 'yolov8n.pt'
# 设置滤波次数，默认为 2（开启滤波），可选值：1、2、3、5
filter_nums = 2
# 设置视频帧的宽度为 960 像素
width = 960
# 设置视频帧的高度为 540 像素
height = 540
# 设置前进、后退的最小面积阈值（目标面积占画面总面积的比例）
s1 = 0.22
# 设置前进、后退的最大面积阈值
s2 = 0.35
# 设置横向偏移阈值（目标中心偏离画面中心的比例）
d1 = 0.15


def receive_frame(cap=None):
    """
    线程1：接收视频帧函数
    功能：从网络摄像头持续读取视频帧，并放入 frame_queue 队列
    参数：cap - OpenCV VideoCapture 对象
    """
    # 初始化帧计数器，用于降采样
    i = 0
    # 进入无限循环，持续接收视频
    while True:
        # 检查摄像头是否已打开
        if not cap.isOpened():
            # 如果未打开，尝试重新打开摄像头
            cap = cv2.VideoCapture(camera_addr)
            # 再次检查是否成功打开
            if not cap.isOpened():
                # 如果打开失败，打印错误信息
                print("open err")
                # 等待 1 秒后重试
                time.sleep(1)
                # 跳过本次循环，重新尝试
                continue
        # 读取一帧视频，success 表示是否读取成功，img 是读取到的图像
        success, img = cap.read()
        # 检查是否成功读取到帧
        if success:
            # 帧计数器加 1
            i += 1
            # 降采样处理：只保留偶数帧（每2帧取1帧），降低计算量
            if i % 2 != 0:
                # 如果是奇数帧，跳过本次循环
                continue
            # 将读取到的有效帧放入 frame_queue 队列，供其他线程使用
            frame_queue.put(img)
        else:
            # 如果读取失败，打印错误信息
            print("read err$$$$$$$$$$$$$$$$$$$$$")
            # 释放摄像头资源
            cap.release()


def convert_command(client_socket=None):
    """
    线程2：转换并发送控制命令函数
    功能：从 signal_queue 取出控制指令，转换为字节流后通过 Socket 发送给 STM32
    参数：client_socket - Socket 客户端连接对象
    """
    # 进入无限循环，持续处理控制指令
    while True:
        try:
            # 检查 signal_queue 是否为空
            if signal_queue.empty():
                # 如果队列为空，等待 1 毫秒后继续检查
                time.sleep(0.001)
                # 跳过本次循环
                continue
            else:
                # 如果队列不为空，从队列中取出控制信号（非阻塞方式）
                signal = signal_queue.get(block=False)
                # 打印接收到的控制信号，用于调试
                print('signal: ', signal)
                try:
                    # 判断信号是否为转向指令（左转或右转）
                    if signal[0] in ['左转', '右转']:
                        # 调用 utils.py 中的函数，将信号转换为协议字节
                        data_bytes = get_control_byte(signal=signal[0])
                        # 通过 Socket 发送字节数据到 STM32
                        client_socket.sendall(data_bytes)
                        # 延时 0.2 秒，确保转向动作执行完成
                        time.sleep(0.2)
                    # 判断信号是否为前后移动指令（前进或后退）
                    if signal[0] in ['前进', '后退']:
                        # 检查信号列表中的所有元素是否相同（去重后长度为1）
                        if len(list(set(signal))) == 1:
                            # 如果所有信号相同，转换为协议字节
                            data_bytes = get_control_byte(signal=signal[0])
                            # 发送数据
                            client_socket.sendall(data_bytes)
                        else:
                            # 如果信号不同，仍然转换并发送第一个信号
                            data_bytes = get_control_byte(signal=signal[0])
                            # 发送数据
                            client_socket.sendall(data_bytes)
                            # 延时 0.05 秒，避免命令冲突
                            time.sleep(0.05)
                    # 发送停止指令，防止小车持续运动
                    signal_2 = '停止'
                    # 转换停止信号为协议字节
                    data_bytes = get_control_byte(signal=signal_2)
                    # 发送停止指令
                    client_socket.sendall(data_bytes)
                except:
                    # 如果发生异常，打印详细的错误堆栈信息
                    print(traceback.format_exc())
        except:
            # 外层异常捕获，防止程序崩溃
            print(traceback.format_exc())


def main_fun(model_params=None):
    """
    线程3：主函数，包含目标检测、跟踪和决策逻辑
    功能：使用 YOLOv8 检测人物，SORT 算法跟踪，根据目标位置生成控制指令
    参数：model_params - 包含模型、跟踪器和参数的字典
    """
    # 从参数字典中获取滤波次数并转换为整数
    filter_nums = int(model_params.get('filter_nums'))
    # 根据滤波次数从 filter_dict 中获取对应的滤波参数数组
    params = filter_dict[filter_nums]
    # 从参数字典中获取视频宽度并转换为整数
    width, height = int(model_params.get('width')), int(model_params.get('height'))
    # 获取最小面积阈值 s1，保留4位小数
    s1 = round(float(model_params.get('s1')), 4)
    # 获取最大面积阈值 s2，保留4位小数
    s2 = round(float(model_params.get('s2')), 4)
    # 获取横向偏移阈值 d1，保留4位小数
    d1 = round(float(model_params.get('d1')), 4)
    # 初始化帧计数器
    i = 0
    # 初始化状态列表，用于存储连续帧的状态值（用于滤波）
    status_list = []
    # 初始化指令队列，用于存储待发送的控制指令
    queue_list = []
    # 初始化跟踪目标 ID，初始为 None 表示还未选择目标
    tracker_id = None
    # 从参数字典中获取 YOLO 模型对象
    model = model_params.get('model')
    # 从参数字典中获取 SORT 跟踪器对象
    tracker = model_params.get('tracker')
    # 进入无限循环，持续处理视频帧
    while True:
        # 检查 frame_queue 是否为空
        if frame_queue.empty():
            # 如果队列为空，等待 1 毫秒
            time.sleep(0.001)
            # 跳过本次循环
            continue
        else:
            # 如果队列不为空，取出一帧图像（非阻塞方式）
            img = frame_queue.get(block=False)
            # 帧计数器加 1
            i += 1
            # 将图像调整为指定的宽高尺寸
            img = cv2.resize(img, (width, height))
            # 使用 torch.no_grad() 禁用梯度计算，节省内存并加速推理
            with torch.no_grad():
                # 使用 YOLO 模型对图像进行检测，stream=True 表示流式处理
                results = model(img, stream=True)
            # 初始化检测结果数组，形状为 (0, 6)，6列分别是：x1,y1,x2,y2,conf,cls
            detections = np.empty((0, 6))
            # 遍历 YOLO 检测结果（可能有多个结果，但通常只有一个）
            for r in results:
                # 获取检测到的所有边界框
                boxes = r.boxes
                # 打印检测到的边界框数量，用于调试
                print('len(boxes): ', len(boxes))
                # 遍历每一个检测框
                for box in boxes:
                    # 获取检测框的左上角和右下角坐标 (xyxy 格式)
                    x1, y1, x2, y2 = box.xyxy[0]
                    # 将坐标转换为整数类型
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    # 获取检测置信度，乘以100并向上取整后再除以100，保留两位小数
                    conf = math.ceil((box.conf[0] * 100)) / 100
                    # 获取检测类别索引
                    cls = int(box.cls[0])
                    # 根据类别索引获取类别名称（如 "person"）
                    currentClass = model.names[cls]
                    # 只保留 "person" 类别的检测结果（只检测人）
                    if currentClass in ["person"]:
                        # 将检测信息组装成 numpy 数组
                        currentArray = np.array([x1, y1, x2, y2, conf, cls])
                        # 将当前检测结果垂直堆叠到 detections 数组中
                        detections = np.vstack((detections, currentArray))
                # 提取所有检测结果的类别列（最后一列）
                classes_array = detections[:, -1:]
                # 使用 SORT 跟踪器更新跟踪状态，传入检测结果
                resultsTracker = tracker.update(detections)
                try:
                    # 尝试将类别信息水平拼接到跟踪结果后面
                    resultsTracker = np.hstack((resultsTracker, classes_array))
                except ValueError:
                    # 如果拼接出错（可能是行数不匹配），截取类别数组的前 N 行
                    classes_array = classes_array[:resultsTracker.shape[0], :]
                    # 再次尝试拼接
                    resultsTracker = np.hstack((resultsTracker, classes_array))
                # 初始化详情列表，用于存储每个跟踪目标的详细信息
                detail_list = []
                # 检查是否有跟踪结果
                if len(resultsTracker) == 0:
                    # 如果没有跟踪结果，跳过本次循环
                    continue
                # 遍历每个跟踪结果
                for result in resultsTracker:
                    # 解析跟踪结果：坐标、跟踪ID、类别
                    x1, y1, x2, y2, id, cls = result
                    # 将所有值转换为整数类型
                    x1, y1, x2, y2, id, cls = int(x1), int(y1), int(x2), int(y2), int(id), int(cls)
                    # 计算检测框的宽度
                    w, h = x2 - x1, y2 - y1
                    # 组装详细信息字典
                    detail = {
                        'x1': x1,      # 左上角 x 坐标
                        'y1': y1,      # 左上角 y 坐标
                        'x2': x2,      # 右下角 x 坐标
                        'y2': y2,      # 右下角 y 坐标
                        'id': id,      # 跟踪 ID
                        'cls': cls,    # 类别
                        'w': w,        # 宽度
                        'h': h,        # 高度
                        's': w * h,    # 面积
                        'cx': x1 + w // 2,  # 中心点 x 坐标
                        'cy': y1 + h // 2   # 中心点 y 坐标
                    }
                    # 将详细信息添加到列表中
                    detail_list.append(detail)
                # 将详细信息列表转换为 pandas DataFrame，方便处理
                df = pd.DataFrame(detail_list)
                # 判断是否还未选择跟踪目标
                if tracker_id is None:
                    # 初始阶段：选择面积最大的目标作为跟踪对象
                    # 按面积降序排序，取第一个（最大的）的索引
                    max_s_index = int(df.sort_values(by='s', ascending=False).index[0])
                    # 记录目标索引
                    tracker_index = max_s_index
                    # 获取该目标的跟踪 ID
                    tracker_id = df[df.index == tracker_index]['id'].item()
                else:
                    # 跟踪阶段：检查之前的跟踪 ID 是否还存在
                    id_flag = df['id'].isin([tracker_id]).any()
                    # 如果 ID 仍然存在
                    if id_flag:
                        # 找到该 ID 在 DataFrame 中的索引
                        tracker_id_index = df[df['id'] == tracker_id].index[0]
                        # 更新跟踪目标索引
                        tracker_index = tracker_id_index
                    else:
                        # 如果目标丢失，重新选择面积最大的目标
                        max_s_index = int(df.sort_values(by='s', ascending=False).index[0])
                        # 更新跟踪目标索引
                        tracker_index = max_s_index
                        # 获取新目标的跟踪 ID
                        tracker_id = df[df.index == tracker_index]['id'].item()
                # 获取跟踪目标的左上角 x 坐标
                x1 = detail_list[tracker_index]['x1']
                # 获取跟踪目标的左上角 y 坐标
                y1 = detail_list[tracker_index]['y1']
                # 获取跟踪目标的宽度
                w = detail_list[tracker_index]['w']
                # 获取跟踪目标的高度
                h = detail_list[tracker_index]['h']
                # 获取跟踪目标的中心点 x 坐标
                cx = detail_list[tracker_index]['cx']
                # 获取跟踪目标的面积
                s = detail_list[tracker_index]['s']

                # 初始化状态列表的和
                list_sum = 0
                # 打印状态列表，用于调试
                print('status_list: ', status_list)
                # 检查状态列表长度是否达到设定的滤波长度
                if len(status_list) == params[0]:
                    # 如果达到长度，计算状态列表的总和
                    list_sum = sum(status_list)
                    # 清空状态列表，准备下一轮滤波
                    status_list = []
                # 打印目标面积，用于调试
                print('s: ', s)
                # 判断目标中心是否在画面右侧（超出右转阈值）
                if cx > (width / 2) + width * d1:
                    # 添加状态码 3（右转）到状态列表
                    status_list.append(3)
                    # 检查状态和是否达到右转阈值
                    if list_sum == params[3]:
                        # 如果达到阈值，添加右转指令到队列
                        queue_list.append('右转')
                # 判断目标中心是否在画面左侧（超出左转阈值）
                elif cx < (width / 2) - width * d1:
                    # 添加状态码 4（左转）到状态列表
                    status_list.append(4)
                    # 检查状态和是否达到左转阈值
                    if list_sum == params[4]:
                        # 如果达到阈值，添加左转指令到队列
                        queue_list.append('左转')
                else:
                    # 如果目标在中心区域，判断面积是否过大（需要后退）
                    if s > width * height * s2:
                        # 添加状态码 1（后退）到状态列表
                        status_list.append(1)
                        # 检查状态和是否达到后退阈值
                        if list_sum == params[1]:
                            # 如果达到阈值，添加后退指令到队列
                            queue_list.append('后退')
                    # 判断面积是否过小（需要前进）
                    elif s < width * height * s1:
                        # 添加状态码 2（前进）到状态列表
                        status_list.append(2)
                        # 检查状态和是否达到前进阈值
                        if list_sum == params[2]:
                            # 如果达到阈值，添加前进指令到队列
                            queue_list.append('前进')
                    else:
                        # 距离适中，添加状态码 5（停止）
                        status_list.append(5)
                        # 检查状态和是否达到停止阈值
                        if list_sum == params[5]:
                            # 如果达到阈值，添加停止指令到队列
                            queue_list.append('停止')
                # 打印指令队列，用于调试
                print('queue_list: ', queue_list)

                # 检查指令队列长度是否达到 2
                if len(queue_list) == 2:
                    # 深拷贝指令队列，避免引用问题
                    temp_list = copy.deepcopy(queue_list)
                    # 将指令放入 signal_queue，供发送线程使用
                    signal_queue.put(temp_list)
                    # 移除队列的第一个元素，保持队列滑动
                    queue_list.pop(0)

                # 使用 cvzone 在图像上绘制角矩形框，标注跟踪目标
                cvzone.cornerRect(img, (x1, y1, w, h), l=12, rt=4, colorR=(255, 0, 255))
            # 检查图像是否不为空
            if img is not None:
                # 显示带有标注的图像，窗口标题为 "car following"
                cv2.imshow('car following', img)
            # 等待 1 毫秒，刷新图像显示
            cv2.waitKey(1)


def run():
    """
    主运行函数，程序入口
    功能：初始化模型、跟踪器、Socket连接，创建并启动三个线程
    """
    # 创建 TCP Socket 客户端对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 解析服务器地址：IP 为 192.168.1.1，端口为 2002
    server_address = ('192.168.1.1'.split(':')[0], int('2002'))
    # 连接到 STM32 服务器
    client_socket.connect(server_address)

    # 创建 VideoCapture 对象，打开网络摄像头
    cap = cv2.VideoCapture(camera_addr)
    # 打印提示信息
    print('读取视频')
    # 加载 YOLOv8 模型
    model = YOLO(weights_path)
    # 初始化 SORT 跟踪器
    # max_age=20: 目标丢失后保持跟踪的最大帧数
    # min_hits=3: 最小检测次数才确认为有效跟踪
    # iou_threshold=0.3: IOU 匹配阈值
    tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
    # 组装模型参数字典
    model_params = {
        'model': model,        # YOLO 模型
        'tracker': tracker,    # SORT 跟踪器
        'filter_nums': filter_nums,  # 滤波次数
        'width': width,        # 图像宽度
        'height': height,      # 图像高度
        's1': s1,              # 最小面积阈值
        's2': s2,              # 最大面积阈值
        'd1': d1               # 横向偏移阈值
    }
    # 创建线程1：接收视频帧线程，设置为守护线程
    ThreadingList.append(threading.Thread(target=receive_frame, args=(cap,), daemon=True, name='receive_frame'))
    # 创建线程2：转换并发送控制指令线程，设置为守护线程
    ThreadingList.append(threading.Thread(target=convert_command, args=(client_socket,), daemon=True, name='convert_command'))
    # 创建线程3：目标检测、跟踪和决策线程，设置为守护线程
    ThreadingList.append(threading.Thread(target=main_fun, args=(model_params,), daemon=True, name='main_fun'))
    # 遍历线程列表，启动所有线程
    for t in ThreadingList:
        t.start()
    # 等待所有线程结束（阻塞主线程）
    for t in ThreadingList:
        t.join()


# 判断是否直接运行该脚本
if __name__ == '__main__':
    # 调用 run() 函数启动程序
    run()
