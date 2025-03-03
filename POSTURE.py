import cv2
import math as m
import numpy as np
import mediapipe as mp
from DRAW import Drawing

def calc_distance(landmarks):
    """
    计算嘴巴中心与肩膀中心之间的欧几里得距离。
    
    参数：
        landmarks: Mediapipe 提取的关键点信息。
    
    返回：
        distance: 嘴巴中心到肩膀中心的距离。
    """
    # 计算嘴巴中心
    mouth_center = np.array([
        (landmarks[9].x + landmarks[10].x) / 2,
        (landmarks[9].y + landmarks[10].y) / 2,
    ])
    
    # 计算肩膀中心
    shoulder_center = np.array([
        (landmarks[11].x + landmarks[12].x) / 2,
        (landmarks[11].y + landmarks[12].y) / 2,
    ])
    
    # 计算欧几里得距离
    distance = np.linalg.norm(shoulder_center - mouth_center)
    return distance

def find_hor_angle(x1, y1, x2, y2):
    """
    计算水平倾斜角度。
    
    参数：
        x1, y1: 第一个点的坐标（通常是左侧特征点）。
        x2, y2: 第二个点的坐标（通常是右侧特征点）。
    
    返回：
        角度值（度）。
    """
    if (m.sqrt((x2 - x1)**2 + (y2 - y1)**2) * y1) == 0:
        return 0
    theta = m.acos((y2 - y1) * (-y1) / (m.sqrt((x2 - x1)**2 + (y2 - y1)**2) * y1))
    degree = (180 / m.pi) * theta
    return abs(degree - 90)

def detect_pose_landmarks(frame):
    """
    处理输入帧并检测人体姿势关键点。
    
    参数：
        frame: 视频帧。
    
    返回：
        world_landmarks: 3D 世界坐标关键点。
        landmarks: 2D 图像坐标关键点。
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)
    
    if results.pose_world_landmarks and results.pose_landmarks:
        world_landmarks = results.pose_world_landmarks.landmark
        landmarks = results.pose_landmarks
        return world_landmarks, landmarks
    
    return None, None

# --- 主程序 --- #
cap = cv2.VideoCapture(0)

# 初始化 MediaPipe 姿势检测
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(model_complexity=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# 低头 & 倾斜 状态标志
nod = False
incline = False

frame_count = 0  # 帧计数器
thres = 0  # 低头检测的阈值

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 水平翻转帧以避免镜像显示
    frame = cv2.flip(frame, 1)

    # 获取视频帧的宽度、高度和帧率
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_size = [frame_width, frame_height]

    frame_count += 1
    
    world_3d_landmarks, landmarks = detect_pose_landmarks(frame)
    
    if landmarks is not None and world_3d_landmarks is not None:
        drawing = Drawing()
        
        # 低头检测
        d = calc_distance(world_3d_landmarks)
        
        if frame_count <= 50:
            # 等待 1.67s (50 帧 / 30fps) 进行初始化
            thres += d
            drawing.label(frame, d, nod, incline, initializing=True)
        else:
            if d < (thres / 50) * 3 / 4:
                nod = True
            else:
                nod = False
            drawing.label(frame, d, nod, incline)
        
        # 倾斜检测
        l_ear_x, l_ear_y = int(landmarks.landmark[7].x * frame_width), int(landmarks.landmark[7].y * frame_height)
        r_ear_x, r_ear_y = int(landmarks.landmark[8].x * frame_width), int(landmarks.landmark[8].y * frame_height)
        l_eye_x, l_eye_y = int(landmarks.landmark[2].x * frame_width), int(landmarks.landmark[2].y * frame_height)
        r_eye_x, r_eye_y = int(landmarks.landmark[5].x * frame_width), int(landmarks.landmark[5].y * frame_height)
        
        eye_incline = find_hor_angle(l_eye_x, l_eye_y, r_eye_x, r_eye_y)
        ear_incline = find_hor_angle(l_ear_x, l_ear_y, r_ear_x, r_ear_y)
        
        if ear_incline > 10 and eye_incline > 10:
            incline = True
        else:
            incline = False
        
        drawing.label(frame, d, nod, incline)
        frame = drawing.draw_skeleton_on_frame(frame, frame_size, landmarks)
    
    cv2.imshow("SitPosture", frame)
    
    # 计算窗口居中位置
    center_x = int((1920 - frame_width) / 2)
    center_y = int((1080 - frame_height) / 2)
    cv2.moveWindow("SitPosture", center_x, center_y)
    
    # 按 'q' 退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
# --- 主程序结束 --- #