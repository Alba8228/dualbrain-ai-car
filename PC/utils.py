import math


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def dot_product(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross_product(u, v):
    return u[0] * v[1] - u[1] * v[0]


def angle_between(u, v):
    dot = dot_product(u, v)
    norm_u = math.sqrt(dot_product(u, u))
    norm_v = math.sqrt(dot_product(v, v))
    return math.acos(dot / (norm_u * norm_v))


def get_angle(p1, p2, p3):
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p3[0] - p1[0], p3[1] - p1[1])

    angle = math.degrees(angle_between(v1, v2))
    return int(angle)


hex_dict = {
    'AA': 0xAA,
    '55': 0x55,
    '00': 0x00,  # 小车方向
    '01': 0x01,  # 前
    '02': 0x02,  # 后
    '03': 0x03,  # 左
    '04': 0x04,  # 右
    '05': 0x05,  # 舵机方向
    '06': 0x06,  # 左
    '07': 0x07,  # 右
    '08': 0x08,  # 上
    '09': 0x09,  # 下
    '0A': 0x0A,  # 低速
    '0B': 0x0B,  # 正常
    '0C': 0x0C,  # 高速
}


def translate_byte(control_list):
    hex_sum = 0
    data_bytes = ''.encode('utf-8')
    for i in control_list:
        hex_num = hex_dict[i]
        hex_sum += hex_num
        hex_bytes = hex_num.to_bytes(1, 'little')
        data_bytes += hex_bytes
    hex_sum = hex_sum & 0xFF
    data_bytes += hex_sum.to_bytes(1, 'little')
    return data_bytes


def get_control_byte(signal=None):
    control_list = ['AA', '55']
    if signal == '前进':
        control_list.append('01')
        control_list.append('05')
        control_list.append('0A')
        data_bytes = translate_byte(control_list)
        return data_bytes
    if signal == '后退':
        control_list.append('02')
        control_list.append('05')
        control_list.append('0A')
        data_bytes = translate_byte(control_list)
        return data_bytes
    if signal == '左转':
        control_list.append('03')
        control_list.append('05')
        control_list.append('0A')
        data_bytes = translate_byte(control_list)
        return data_bytes
    if signal == '右转':
        control_list.append('04')
        control_list.append('05')
        control_list.append('0A')
        data_bytes = translate_byte(control_list)
        return data_bytes
    if signal == '停止':
        control_list.append('00')
        control_list.append('05')
        control_list.append('0A')
        data_bytes = translate_byte(control_list)
        return data_bytes

if __name__ == '__main__':
    p1 = (0, 0)
    p2 = (1, 0)
    p3 = (1, 1)
    angle = get_angle(p1, p2, p3)
    print(angle, type(angle))

    data_bytes = get_control_byte(signal='前进')
    print(data_bytes, data_bytes.hex())

    data_bytes = get_control_byte(signal='停止')
    print(data_bytes, data_bytes.hex())
