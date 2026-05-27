# 导入 math 数学库，用于数学计算
import math


def distance(p1, p2):
    """
    计算两点之间的欧氏距离
    参数：
        p1: 第一个点，格式为 (x, y)
        p2: 第二个点，格式为 (x, y)
    返回：
        两点之间的距离值
    """
    # 使用欧氏距离公式：sqrt((x1-x2)² + (y1-y2)²)
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def dot_product(u, v):
    """
    计算两个二维向量的点积
    参数：
        u: 第一个向量，格式为 (x, y)
        v: 第二个向量，格式为 (x, y)
    返回：
        点积结果
    """
    # 点积公式：u·v = ux*vx + uy*vy
    return u[0] * v[0] + u[1] * v[1]


def cross_product(u, v):
    """
    计算两个二维向量的叉积（实际上是二维叉积的标量值）
    参数：
        u: 第一个向量，格式为 (x, y)
        v: 第二个向量，格式为 (x, y)
    返回：
        叉积结果
    """
    # 二维叉积公式：u × v = ux*vy - uy*vx
    return u[0] * v[1] - u[1] * v[0]


def angle_between(u, v):
    """
    计算两个向量之间的夹角（弧度）
    参数：
        u: 第一个向量，格式为 (x, y)
        v: 第二个向量，格式为 (x, y)
    返回：
        夹角（弧度）
    """
    # 计算两个向量的点积
    dot = dot_product(u, v)
    # 计算第一个向量的模长（范数）
    norm_u = math.sqrt(dot_product(u, u))
    # 计算第二个向量的模长（范数）
    norm_v = math.sqrt(dot_product(v, v))
    # 使用反余弦函数计算夹角：θ = arccos( u·v / (|u|*|v|) )
    return math.acos(dot / (norm_u * norm_v))


def get_angle(p1, p2, p3):
    """
    计算三个点组成的角的角度（以 p1 为顶点）
    参数：
        p1: 角的顶点
        p2: 角的第一个边上的点
        p3: 角的第二个边上的点
    返回：
        角度（整数，单位为度）
    """
    # 计算从 p1 到 p2 的向量 v1
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    # 计算从 p1 到 p3 的向量 v2
    v2 = (p3[0] - p1[0], p3[1] - p1[1])

    # 计算两个向量之间的夹角（弧度）
    angle = math.degrees(angle_between(v1, v2))
    # 将弧度转换为角度，并转换为整数返回
    return int(angle)


# 定义协议字节映射字典，用于将字符串指令转换为对应的十六进制字节
hex_dict = {
    'AA': 0xAA,      # 帧头字节1
    '55': 0x55,      # 帧头字节2
    '00': 0x00,      # 小车方向：停止
    '01': 0x01,      # 小车方向：前进
    '02': 0x02,      # 小车方向：后退
    '03': 0x03,      # 小车方向：左转
    '04': 0x04,      # 小车方向：右转
    '05': 0x05,      # 舵机方向
    '06': 0x06,      # 舵机方向：左
    '07': 0x07,      # 舵机方向：右
    '08': 0x08,      # 舵机方向：上
    '09': 0x09,      # 舵机方向：下
    '0A': 0x0A,      # 速度：低速
    '0B': 0x0B,      # 速度：正常
    '0C': 0x0C,      # 速度：高速
}


def translate_byte(control_list):
    """
    将控制指令列表转换为完整的协议字节流
    参数：
        control_list: 控制指令列表，格式为 ['AA', '55', '01', ...]
    返回：
        完整的字节流（包含校验和）
    """
    # 初始化校验和为0
    hex_sum = 0
    # 初始化空字节流
    data_bytes = ''.encode('utf-8')
    # 遍历控制列表中的每个指令
    for i in control_list:
        # 从字典中获取对应的十六进制数值
        hex_num = hex_dict[i]
        # 将数值累加到校验和
        hex_sum += hex_num
        # 将数值转换为1字节的小端序字节
        hex_bytes = hex_num.to_bytes(1, 'little')
        # 将字节追加到字节流中
        data_bytes += hex_bytes
    # 取校验和的低8位（1字节）
    hex_sum = hex_sum & 0xFF
    # 将校验和转换为字节并追加到字节流末尾
    data_bytes += hex_sum.to_bytes(1, 'little')
    # 返回完整的协议字节流
    return data_bytes


def get_control_byte(signal=None):
    """
    根据控制信号生成对应的协议字节流
    参数：
        signal: 控制信号字符串，可选值：'前进'、'后退'、'左转'、'右转'、'停止'
    返回：
        完整的协议字节流
    """
    # 初始化控制列表，首先添加帧头 AA 和 55
    control_list = ['AA', '55']
    # 判断是否为前进信号
    if signal == '前进':
        # 添加前进方向字节 01
        control_list.append('01')
        # 添加舵机方向字节 05
        control_list.append('05')
        # 添加速度字节 0A（低速）
        control_list.append('0A')
        # 调用 translate_byte 生成完整字节流
        data_bytes = translate_byte(control_list)
        # 返回字节流
        return data_bytes
    # 判断是否为后退信号
    if signal == '后退':
        # 添加后退方向字节 02
        control_list.append('02')
        # 添加舵机方向字节 05
        control_list.append('05')
        # 添加速度字节 0A
        control_list.append('0A')
        # 生成字节流
        data_bytes = translate_byte(control_list)
        # 返回
        return data_bytes
    # 判断是否为左转信号
    if signal == '左转':
        # 添加左转方向字节 03
        control_list.append('03')
        # 添加舵机方向字节 05
        control_list.append('05')
        # 添加速度字节 0A
        control_list.append('0A')
        # 生成字节流
        data_bytes = translate_byte(control_list)
        # 返回
        return data_bytes
    # 判断是否为右转信号
    if signal == '右转':
        # 添加右转方向字节 04
        control_list.append('04')
        # 添加舵机方向字节 05
        control_list.append('05')
        # 添加速度字节 0A
        control_list.append('0A')
        # 生成字节流
        data_bytes = translate_byte(control_list)
        # 返回
        return data_bytes
    # 判断是否为停止信号
    if signal == '停止':
        # 添加停止方向字节 00
        control_list.append('00')
        # 添加舵机方向字节 05
        control_list.append('05')
        # 添加速度字节 0A
        control_list.append('0A')
        # 生成字节流
        data_bytes = translate_byte(control_list)
        # 返回
        return data_bytes


# 判断是否直接运行该脚本
if __name__ == '__main__':
    # 定义测试点1：原点 (0, 0)
    p1 = (0, 0)
    # 定义测试点2：(1, 0)
    p2 = (1, 0)
    # 定义测试点3：(1, 1)
    p3 = (1, 1)
    # 调用 get_angle 计算角度
    angle = get_angle(p1, p2, p3)
    # 打印角度和类型
    print(angle, type(angle))

    # 测试前进指令
    data_bytes = get_control_byte(signal='前进')
    # 打印字节流和十六进制字符串
    print(data_bytes, data_bytes.hex())

    # 测试停止指令
    data_bytes = get_control_byte(signal='停止')
    # 打印字节流和十六进制字符串
    print(data_bytes, data_bytes.hex())
