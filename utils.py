# utils.py
import math
import numpy as np
from roboid import * # --- 기본 계산 함수 (동일) ---
def calculate_distance(start, end):
    return math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)

def calculate_angle(start, end):
    return math.degrees(math.atan2(-(end[1]-start[1]), end[0]-start[0]))


# --- Bezier 곡선 근사 (동일) ---
def cubic_bezier_curve(p0, p1, p2, p3, steps=10):
    points = []
    for t in [i/steps for i in range(steps+1)]:
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        points.append((x, y))
    return points

def quadratic_bezier_curve(p0, p1, p2, steps=10):
    points = []
    for t in [i/steps for i in range(steps+1)]:
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        points.append((x, y))
    return points

# --- 이동 함수 (동일) ---
def move_to(h, start, end, current_angle, scale=0.07, angle_offset=0):
    distance = calculate_distance(start, end) * scale
    target_angle = calculate_angle(start, end)

    target_angle += angle_offset

    angle_diff = target_angle - current_angle
    if angle_diff > 180:
        angle_diff -= 360  
    elif angle_diff < -180:
        angle_diff += 360  

    if angle_diff > 0:
        h.turn_right(abs(angle_diff))
    else:
        h.turn_left(abs(angle_diff))

    h.move_forward(distance)

    return target_angle

# --- HamsterS로 path 실행 ---
def execute_path(h, parsed_paths, scale=0.07, steps_bezier=10, steps_arc=10, angle_offset=0): 
    # M 명령이 첫 세그먼트이므로, 그 시작점을 초기 위치로 설정
    current_position = parsed_paths[0][0]['start'] 
    current_angle = 0 

    for path_index, path in enumerate(parsed_paths):
        print(f"Starting Path {path_index+1}...")

        for segment in path:
            seg_type = segment['type']

            # M 명령: 위치만 갱신하고 이동(move_to) 건너뛰기
            if seg_type == 'M': 
                current_position = segment['end'] 
                continue

            elif seg_type == 'L': 
                end = segment['end']
                current_angle = move_to(h, current_position, end, current_angle, scale, angle_offset)
                current_position = end

            elif seg_type == 'C': 
                points = cubic_bezier_curve(segment['start'], segment['control1'], segment['control2'], segment['end'], steps_bezier)
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle, scale, angle_offset)
                current_position = segment['end']

            elif seg_type == 'Q': 
                points = quadratic_bezier_curve(segment['start'], segment['control'], segment['end'], steps_bezier)
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle, scale, angle_offset)
                current_position = segment['end']

            elif seg_type == 'A': 
                cx, cy = segment['center']
                rx, ry = segment['radius']
                start_point = segment['start']
                end_point = segment['end']
                
                start_angle = math.degrees(math.atan2(start_point[1]-cy, start_point[0]-cx))
                end_angle = math.degrees(math.atan2(end_point[1]-cy, end_point[0]-cx))
                if end_angle < start_angle:
                    end_angle += 360 

                angles = np.linspace(start_angle, end_angle, steps_arc)
                points = [(cx + rx*math.cos(math.radians(a)), cy + ry*math.sin(math.radians(a))) for a in angles]
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle, scale, angle_offset)
                current_position = points[-1]

            elif seg_type == 'Z': 
                end = segment['end']
                current_angle = move_to(h, current_position, end, current_angle, scale, angle_offset)
                current_position = end


            elif seg_type == 'circle': 
                cx, cy = segment['center']
                r = segment['radius']
                angles = np.linspace(0, 360, steps_arc)
                points = [(cx + r*math.cos(math.radians(a)), cy + r*math.sin(math.radians(a))) for a in angles]
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle, scale, angle_offset)
                current_position = points[-1]

        print(f"Path {path_index+1} completed.\n")

        #   다음 path로 이동 (KeyError 방지 로직 추가)
        if path_index + 1 < len(parsed_paths):
            next_path = parsed_paths[path_index+1]
            
            # 다음 경로가 리스트이고, 첫 요소가 'start' 키를 가질 때만 이동 로직 실행
            if isinstance(next_path, list) and next_path and 'start' in next_path[0]:
                next_path_start = next_path[0]['start']
                
                # 현재 위치와 다음 시작점이 다를 경우에만 이동
                if current_position != next_path_start:
                    current_angle = move_to(h, current_position, next_path_start, current_angle, scale, angle_offset)
                    current_position = next_path_start