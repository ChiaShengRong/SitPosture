import cv2
import numpy as np
import mediapipe as mp

class Drawing:
    def __init__(self):
        pass
    
    def draw_skeleton_on_frame(self, frame, frame_size, landmarks):
        """
        在帧上绘制骨架，包括面部和肩膀的关键点及其连接。
        
        参数：
            frame: 处理的图像帧
            frame_size: (宽度, 高度) 用于缩放关键点
            landmarks: Mediapipe 提取的关键点信息
        """
        w, h = frame_size
        # 将所有关键点坐标缩放到当前帧尺寸
        landmarks = np.array([(int(lm.x * w), int(lm.y * h)) for lm in landmarks.landmark])

        # 需要显示的关键点索引
        landmark_to_show = [2, 5, 9, 10, 11, 12]

        # 定义面部和肩膀的连接
        face_connections = [(2, 5), (2, 9), (9, 10), (10, 5)]
        shoulder_connections = [(11, 12)]
        
        # 画连接线
        self.draw_connections(frame, landmarks, face_connections, frame_size, (0, 0, 255))  # 面部连接（红色）
        self.draw_connections(frame, landmarks, shoulder_connections, frame_size, (255, 0, 0))  # 肩膀连接（蓝色）

        # 画关键点
        for i, lm in enumerate(landmarks):
            if self.is_valid(lm[:2], frame_size) and i in landmark_to_show:
                color = (255, 255, 255)  # 白色关键点
                cv2.circle(frame, tuple(map(int, lm[:2])), 3, color, -1)

        # 计算并绘制嘴巴中心点
        mouth_center = ((landmarks[9][0] + landmarks[10][0]) // 2,
                        (landmarks[9][1] + landmarks[10][1]) // 2)
        cv2.circle(frame, mouth_center, 3, color=(0, 255, 0), thickness=-1)  # 绿色点

        # 计算并绘制肩膀中心点
        shoulder_center = ((landmarks[11][0] + landmarks[12][0]) // 2,
                           (landmarks[11][1] + landmarks[12][1]) // 2)
        cv2.circle(frame, shoulder_center, 3, color=(0, 255, 0), thickness=-1)  # 绿色点

        # 连接嘴巴中心点和肩膀中心点
        cv2.line(frame, mouth_center, shoulder_center, color, 2)

        return frame
    
    def draw_connections(self, frame, landmarks, connection, frame_size, color):
        """
        绘制骨架关键点之间的连接线。
        
        参数：
            frame: 处理的图像帧
            landmarks: 关键点坐标列表
            connection: 关键点连接对列表
            frame_size: (宽度, 高度)
            color: 线条颜色
        """
        w, h = frame_size
        
        for start_idx, end_idx in connection:
            start_point = tuple(map(int, landmarks[start_idx]))
            end_point = tuple(map(int, landmarks[end_idx]))

            if self.is_valid(start_point, frame_size) and self.is_valid(end_point, frame_size):
                cv2.line(frame, start_point, end_point, color, 2)

    def is_valid(self, point, frame_size):
        """
        检查点是否在图像帧内并且不是 NaN。
        
        参数：
            point: (x, y) 坐标
            frame_size: (宽度, 高度)
        
        返回：
            True - 有效，False - 无效
        """
        w, h = frame_size
        x, y = point
        return 0 <= x < w and 0 <= y < h and not np.isnan(x) and not np.isnan(y)
    
    def label(self, frame, distance, nod, incline, initializing=False):
        """
        在图像上添加标签，用于显示姿势信息。
        
        参数：
            frame: 处理的图像帧
            distance: 嘴巴到肩膀的欧几里得距离
            nod: 是否检测到点头动作
            incline: 是否检测到不良姿势
            initializing: 是否正在初始化识别
        
        返回：
            添加标签后的图像帧
        """
        legend_x, legend_y = 20, 20  # 标签位置
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        thickness = 2

        # 显示距离信息
        cv2.putText(frame, 'd: %.2f' % distance, (legend_x + 10, legend_y + 20), font, font_scale, (0, 255, 0), thickness)
        
        # 显示状态信息
        if initializing:
            cv2.putText(frame, "Recognizing Human", (legend_x + 10, legend_y + 50), font, font_scale, (0, 255, 0), thickness)
        elif nod:
            cv2.putText(frame, "Nod", (legend_x + 10, legend_y + 50), font, font_scale, (0, 255, 0), thickness)
        elif incline:
            cv2.putText(frame, "Bad Posture", (legend_x + 10, legend_y + 50), font, font_scale, (0, 255, 0), thickness)
        else:
            cv2.putText(frame, "Good Posture", (legend_x + 10, legend_y + 50), font, font_scale, (0, 255, 0), thickness)
        
        return frame