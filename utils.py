import math
import numpy as np
from roboid import *  # HamsterS 임포트

# --- 기본 계산 함수 ---
def calculate_distance(start, end):
    return math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)

def calculate_angle(start, end):
    # HamsterS 좌표계 기준
    return math.degrees(math.atan2(-(end[1]-start[1]), end[0]-start[0]))

# --- Bezier 곡선 근사 (step 감소) ---
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

# --- 이동 함수 ---
def move_to(h, start, end, current_angle, scale=0.06):
    distance = calculate_distance(start, end) * scale
    target_angle = calculate_angle(start, end)

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

# --- 메인 실행 ---
def execute_path(h, parsed_paths):
    current_position = parsed_paths[0][0]['start']
    current_angle = 0

    for path_index, path in enumerate(parsed_paths):
        print(f"Starting Path {path_index+1}...")

        for segment in path:
            seg_type = segment['type']

            if seg_type in ['M', 'L']:
                end = segment['end']
                current_angle = move_to(h, current_position, end, current_angle)
                current_position = end

            elif seg_type == 'C':
                p0, p1, p2, p3 = segment['start'], segment['control1'], segment['control2'], segment['end']
                points = cubic_bezier_curve(p0, p1, p2, p3)
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle)
                current_position = p3

            elif seg_type == 'Q':
                p0, p1, p2 = segment['start'], segment['control'], segment['end']
                points = quadratic_bezier_curve(p0, p1, p2)
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle)
                current_position = p2

            elif seg_type == 'A':
                cx, cy = segment['center']
                rx, ry = segment['radius']
                start_angle, end_angle = segment['start_angle'], segment['end_angle']
                steps = 10
                angles = np.linspace(start_angle, end_angle, steps)
                points = [(cx + rx*math.cos(math.radians(a)), cy + ry*math.sin(math.radians(a))) for a in angles]
                for i in range(1, len(points)):
                    current_angle = move_to(h, points[i-1], points[i], current_angle)
                current_position = points[-1]

            elif seg_type == 'Z':
                end = segment['end']
                current_angle = move_to(h, current_position, end, current_angle)
                current_position = end

        print(f"Path {path_index+1} completed.\n")

        if path_index + 1 < len(parsed_paths):
            next_path_start = parsed_paths[path_index+1][0]['start']
            current_angle = move_to(h, current_position, next_path_start, current_angle)
            current_position = next_path_start
