# 从 __future__ 导入 print_function，确保 Python 2/3 兼容性
from __future__ import print_function
# 导入 os 库
import os
# 导入 numpy 库，用于数组和矩阵运算
import numpy as np
# 导入 matplotlib 库
import matplotlib
# 从 filterpy.kalman 导入 KalmanFilter 类，用于卡尔曼滤波
from filterpy.kalman import KalmanFilter

# 设置 matplotlib 的后端为 TkAgg
matplotlib.use('TkAgg')
# 设置 numpy 随机种子为0，确保结果可复现
np.random.seed(0)


def linear_assignment(cost_matrix):
    """
    使用匈牙利算法解决线性分配问题（指派问题）
    参数：
        cost_matrix: 代价矩阵，形状为 (N, M)
    返回：
        匹配结果数组，形状为 (K, 2)，每行为 [检测索引, 跟踪索引]
    """
    try:
        # 尝试导入 lap 库（更高效的线性分配库）
        import lap
        # 使用 lap.lapjv 求解线性分配问题，extend_cost=True 表示扩展代价矩阵
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
        # 整理匹配结果，只保留有效匹配（x[i] >= 0）
        return np.array([[y[i], i] for i in x if i >= 0])
    except ImportError:
        # 如果 lap 库不可用，回退到使用 scipy 的 linear_sum_assignment
        from scipy.optimize import linear_sum_assignment
        # 使用 scipy 求解线性分配问题
        x, y = linear_sum_assignment(cost_matrix)
        # 整理匹配结果
        return np.array(list(zip(x, y)))


def iou_batch(bb_test, bb_gt):
    """
    批量计算两组边界框之间的 IOU（交并比）
    参数：
        bb_test: 测试边界框数组，形状为 (N, 4)，格式为 [x1, y1, x2, y2]
        bb_gt: 真实边界框数组，形状为 (M, 4)，格式为 [x1, y1, x2, y2]
    返回：
        IOU 矩阵，形状为 (N, M)
    """
    # 将真实框扩展维度，形状变为 (1, M, 4)
    bb_gt = np.expand_dims(bb_gt, 0)
    # 将测试框扩展维度，形状变为 (N, 1, 4)

    # 计算交集区域的左上角坐标（取最大值）
    xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
    yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
    # 计算交集区域的右下角坐标（取最小值）
    xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
    yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])

    # 计算交集区域的宽度（不小于0）
    w = np.maximum(0., xx2 - xx1)
    # 计算交集区域的高度（不小于0）
    h = np.maximum(0., yy2 - yy1)
    # 计算交集面积
    wh = w * h

    # 计算 IOU：交集 / (面积1 + 面积2 - 交集)
    o = wh / ((bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1]) +
              (bb_gt[..., 2] - bb_gt[..., 0]) * (bb_gt[..., 3] - bb_gt[..., 1]) - wh)

    # 返回 IOU 矩阵
    return o


def convert_bbox_to_z(bbox):
    """
    将边界框格式从 [x1, y1, x2, y2] 转换为卡尔曼滤波观测格式 [x, y, s, r]
    参数：
        bbox: 边界框，格式为 [x1, y1, x2, y2]
    返回：
        卡尔曼观测格式数组，形状为 (4, 1)
    """
    # 计算边界框宽度
    w = bbox[2] - bbox[0]
    # 计算边界框高度
    h = bbox[3] - bbox[1]
    # 计算边界框中心点 x 坐标
    x = bbox[0] + w / 2.
    # 计算边界框中心点 y 坐标
    y = bbox[1] + h / 2.
    # 计算边界框面积
    s = w * h
    # 计算边界框宽高比
    r = w / float(h)
    # 返回形状为 (4, 1) 的数组
    return np.array([x, y, s, r]).reshape((4, 1))


def convert_x_to_bbox(x, score=None):
    """
    将卡尔曼滤波状态格式转换回边界框格式 [x1, y1, x2, y2]
    参数：
        x: 卡尔曼状态数组，格式为 [x, y, s, r, ...]
        score: 置信度（可选）
    返回：
        边界框数组，形状为 (1, 4) 或 (1, 5)（包含置信度）
    """
    # 从面积 s 和宽高比 r 反推宽度和高度
    w = np.sqrt(x[2] * x[3])
    h = x[2] / w

    # 判断是否提供置信度
    if score is None:
        # 没有置信度，返回形状为 (1, 4) 的边界框
        return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2.]).reshape((1, 4))
    else:
        # 有置信度，返回形状为 (1, 5) 的边界框（包含置信度）
        return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2., score]).reshape((1, 5))


class KalmanBoxTracker(object):
    """
    卡尔曼边界框跟踪器类
    使用卡尔曼滤波器对单个目标的边界框进行跟踪
    """
    # 类变量：跟踪器 ID 计数器
    count = 0

    def __init__(self, bbox):
        """
        初始化卡尔曼跟踪器
        参数：
            bbox: 初始边界框，格式为 [x1, y1, x2, y2]
        """
        # 创建卡尔曼滤波器，状态维度 dim_x=7，观测维度 dim_z=4
        # 状态向量：[x, y, s, r, vx, vy, vs]
        # 其中：x,y=中心坐标，s=面积，r=宽高比，vx,vy,vs=对应速度
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        # 状态转移矩阵 F（7x7）
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0],
                              [0, 1, 0, 0, 0, 1, 0],
                              [0, 0, 1, 0, 0, 0, 1],
                              [0, 0, 0, 1, 0, 0, 0],
                              [0, 0, 0, 0, 1, 0, 0],
                              [0, 0, 0, 0, 0, 1, 0],
                              [0, 0, 0, 0, 0, 0, 1]])
        # 观测矩阵 H（4x7），只观测 x, y, s, r
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0],
                              [0, 1, 0, 0, 0, 0, 0],
                              [0, 0, 1, 0, 0, 0, 0],
                              [0, 0, 0, 1, 0, 0, 0]])

        # 设置观测噪声协方差矩阵 R，面积和宽高比的噪声放大10倍
        self.kf.R[2:, 2:] *= 10.
        # 设置初始状态协方差矩阵 P，速度部分放大1000倍
        self.kf.P[4:, 4:] *= 1000.
        # 整体初始协方差再放大10倍
        self.kf.P *= 10.
        # 设置过程噪声协方差矩阵 Q，面积速度的噪声缩小100倍
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        # 使用初始边界框初始化卡尔曼状态的前4个状态
        self.kf.x[:4] = convert_bbox_to_z(bbox)
        # 记录距离上次更新的帧数
        self.time_since_update = 0
        # 分配跟踪器 ID
        self.id = KalmanBoxTracker.count
        # 跟踪器计数器加1
        KalmanBoxTracker.count += 1
        # 历史跟踪结果历史记录
        self.history = []
        # 总命中次数
        self.hits = 0
        # 连续命中次数
        self.hit_streak = 0
        # 跟踪器存在的帧数
        self.age = 0

    def update(self, bbox):
        """
        使用新的检测框更新卡尔曼滤波器
        参数：
            bbox: 新的检测边界框
        """
        # 重置距离上次更新的帧数为0
        self.time_since_update = 0
        # 清空历史记录
        self.history = []
        # 总命中次数加1
        self.hits += 1
        # 连续命中次数加1
        self.hit_streak += 1
        # 使用新的边界框更新卡尔曼滤波器
        self.kf.update(convert_bbox_to_z(bbox))

    def predict(self):
        """
        预测下一帧的边界框位置
        返回：
            预测的边界框
        """
        # 防止面积和面积速度的和为负数
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            # 如果为负，将面积速度设为0
            self.kf.x[6] *= 0
        # 执行卡尔曼预测步骤
        self.kf.predict()
        # 跟踪器年龄加1
        self.age += 1
        # 如果距离上次更新超过0帧
        if (self.time_since_update > 0):
            # 连续命中次数清零
            self.hit_streak = 0
        # 距离上次更新的帧数加1
        self.time_since_update += 1
        # 将预测结果添加到历史记录
        self.history.append(convert_x_to_bbox(self.kf.x))
        # 返回最新的预测结果
        return self.history[-1]

    def get_state(self):
        """
        获取当前的跟踪状态（边界框）
        返回：
            当前的边界框
        """
        # 将卡尔曼状态转换为边界框格式并返回
        return convert_x_to_bbox(self.kf.x)


def associate_detections_to_trackers(detections, trackers, iou_threshold=0.3):
    """
    将检测框与跟踪框进行关联匹配
    参数：
        detections: 检测框数组，形状为 (N, 5)
        trackers: 跟踪框数组，形状为 (M, 5)
        iou_threshold: IOU 阈值
    返回：
        matches: 匹配结果数组，形状为 (K, 2)
        unmatched_detections: 未匹配的检测框索引
        unmatched_trackers: 未匹配的跟踪框索引
    """
    # 如果没有跟踪框
    if (len(trackers) == 0):
        # 返回空匹配，所有检测框都未匹配
        return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)

    # 计算检测框和跟踪框之间的 IOU 矩阵
    iou_matrix = iou_batch(detections, trackers)

    # 如果 IOU 矩阵不为空
    if min(iou_matrix.shape) > 0:
        # 创建二进制矩阵，表示 IOU 大于阈值的位置
        a = (iou_matrix > iou_threshold).astype(np.int32)
        # 如果每行每列最多只有一个匹配（理想情况）
        if a.sum(1).max() == 1 and a.sum(0).max() == 1:
            # 直接提取匹配索引
            matched_indices = np.stack(np.where(a), axis=1)
        else:
            # 否则使用匈牙利算法进行最优匹配（代价为 -IOU）
            matched_indices = linear_assignment(-iou_matrix)
    else:
        # IOU 矩阵为空，没有匹配
        matched_indices = np.empty(shape=(0, 2))

    # 初始化未匹配的检测框列表
    unmatched_detections = []
    # 遍历所有检测框
    for d, det in enumerate(detections):
        # 如果检测框未匹配
        if (d not in matched_indices[:, 0]):
            # 添加到未匹配列表
            unmatched_detections.append(d)
    # 初始化未匹配的跟踪框列表
    unmatched_trackers = []
    # 遍历所有跟踪框
    for t, trk in enumerate(trackers):
        # 如果跟踪框未匹配
        if (t not in matched_indices[:, 1]):
            # 添加到未匹配列表
            unmatched_trackers.append(t)

    # 初始化有效匹配列表
    matches = []
    # 遍历所有初步匹配
    for m in matched_indices:
        # 再次检查 IOU 是否大于阈值
        if (iou_matrix[m[0], m[1]] < iou_threshold):
            # 如果小于阈值，视为未匹配
            unmatched_detections.append(m[0])
            unmatched_trackers.append(m[1])
        else:
            # 如果大于阈值，视为有效匹配
            matches.append(m.reshape(1, 2))
    # 如果没有有效匹配
    if (len(matches) == 0):
        # 返回空匹配
        matches = np.empty((0, 2), dtype=int)
    else:
        # 否则将匹配结果拼接成数组
        matches = np.concatenate(matches, axis=0)

    # 返回匹配结果和未匹配结果
    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)


class Sort(object):
    """
    SORT（Simple Online and Realtime Tracking）多目标跟踪器类
    """
    def __init__(self, max_age=1, min_hits=3, iou_threshold=0.3):
        """
        初始化 SORT 跟踪器
        参数：
            max_age: 目标丢失后保持跟踪的最大帧数
            min_hits: 最小检测次数才确认为有效跟踪
            iou_threshold: IOU 匹配阈值
        """
        # 保存最大年龄参数
        self.max_age = max_age
        # 保存最小命中次数参数
        self.min_hits = min_hits
        # 保存 IOU 阈值参数
        self.iou_threshold = iou_threshold
        # 初始化跟踪器列表
        self.trackers = []
        # 初始化帧计数器
        self.frame_count = 0

    def update(self, dets=np.empty((0, 5))):
        """
        更新跟踪器状态（核心函数）
        参数：
            dets: 检测框数组，形状为 (N, 5)，格式为 [x1, y1, x2, y2, score]
        返回：
            跟踪结果数组，形状为 (M, 5)，格式为 [x1, y1, x2, y2, id]
        """
        # 帧计数器加1
        self.frame_count += 1

        # 初始化跟踪框预测结果数组
        trks = np.zeros((len(self.trackers), 5))
        # 初始化待删除的跟踪器索引列表
        to_del = []
        # 初始化返回结果列表
        ret = []
        # 遍历所有跟踪器
        for t, trk in enumerate(trks):
            # 预测跟踪框的位置
            pos = self.trackers[t].predict()[0]
            # 保存预测结果
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            # 如果预测结果包含 NaN
            if np.any(np.isnan(pos)):
                # 添加到待删除列表
                to_del.append(t)

        # 过滤掉无效的跟踪框（包含 NaN）
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        # 倒序遍历待删除列表，从后往前删除避免索引错乱
        for t in reversed(to_del):
            # 删除跟踪器
            self.trackers.pop(t)

        # 将检测框与跟踪框进行关联匹配
        matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets, trks, self.iou_threshold)

        # 更新匹配的跟踪器
        for m in matched:
            # 使用对应的检测框更新跟踪器
            self.trackers[m[1]].update(dets[m[0], :])

        # 为未匹配的检测框创建新的跟踪器
        for i in unmatched_dets:
            # 创建新的卡尔曼跟踪器
            trk = KalmanBoxTracker(dets[i, :])
            # 添加到跟踪器列表
            self.trackers.append(trk)

        # 从后往前遍历跟踪器
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            # 获取跟踪器的当前状态
            d = trk.get_state()[0]
            # 判断是否为有效跟踪（最近有更新且命中次数足够）
            if (trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                # 将跟踪结果添加到返回列表，ID 加1（MOT 基准要求 ID 为正数）
                ret.append(np.concatenate((d, [trk.id + 1])).reshape(1, -1))
            # 索引减1
            i -= 1
            # 如果跟踪器超过最大年龄未更新
            if (trk.time_since_update > self.max_age):
                # 删除该跟踪器
                self.trackers.pop(i)

        # 如果有返回结果
        if len(ret) > 0:
            # 将结果拼接成数组返回
            return np.concatenate(ret)
        # 否则返回空数组
        return np.empty((0, 5))
