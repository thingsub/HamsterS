import re
import math
from roboid import *


h = HamsterS() 
SCALE = 0.06 # 간단 확인 : 0.03 / 테스트용 : 0.06
path_d = "M261.83,204.9H12.06c-6.55,0-11.32-6.19-9.66-12.53L36.43,63.02c2.36-8.95,10.45-15.19,19.71-15.19h167.71c9.26,0,17.35,6.24,19.71,15.19l32.48,123.46c2.45,9.32-4.58,18.43-14.21,18.43Z"

# --- SVG Path 해석 함수 (직선 세그먼트 일반화 및 상대 좌표 처리) ---
def extract_points(path_d):
    tokens = re.findall(r'([MLHVZCcmlhvzc])([^MLHVZCcmlhvzc]*)', path_d)
    points = [] # 경로 상의 점들 저장
    current_pos = (0.0, 0.0) # 현재 로봇의 위치
    start_pos = (0.0, 0.0) # 경로의 시작점

    for cmd, vals in tokens:  # 각 명령과 좌표 처리
        cmd_upper = cmd.upper()  # 명령어를 대문자로 바꿔서 처리 (대소문자 구분)
        is_relative = cmd == cmd.lower() # 소문자는 상대좌표, 대문자는 절대좌표
        vals = vals.strip() # 좌표 부분에서 공백 제거
        coords = list(map(float, re.findall(r'-?\d+\.?\d*', vals)))
        
        # 상대 좌표를 처리 시 기준이 될 위치 (이전 위치 사용)
        base_x, base_y = current_pos if is_relative and cmd_upper != 'M' else (0.0, 0.0)

        if cmd_upper in ['M', 'L']:
            for i in range(0, len(coords), 2):
                x = base_x + coords[i]
                y = base_y + coords[i+1]
                
                new_pos = (x, -y) # Y축 반전 적용(로봇은 Y축이 반전돼서 그려져야 해서 Y값을 -로 바꿈)
                
                if cmd_upper == 'M' and i == 0:
                    start_pos = new_pos 
                    points.append(new_pos)
                elif cmd_upper == 'L' or (cmd_upper == 'M' and i > 0):
                    points.append(new_pos)
                
                current_pos = new_pos # 현재 위치를 업데이트

        elif cmd_upper == 'H': # 수평 직선 이동
            for val in coords:
                x = base_x + val if is_relative else val
                current_pos = (x, current_pos[1]) 
                points.append(current_pos)

        elif cmd_upper == 'V': # 수직 직선 이동
            for val in coords:
                y_svg = current_pos[1] if not is_relative else 0
                y = y_svg + (-val) if is_relative else -val # 로봇 Y = -SVG Y
                current_pos = (current_pos[0], y)
                points.append(current_pos)

        elif cmd_upper == 'Z':
            if points and points[-1] != start_pos:
                current_pos = start_pos
                points.append(start_pos) 
            break
        
        elif cmd_upper in ['C', 'S', 'Q', 'T']:
             continue
            
    return points

#  절대 방향 기준 상대 회전 계산 함수
def turn_to_direction(current_angle, target_vec):
    target_angle = math.degrees(math.atan2(target_vec[1], target_vec[0]))
    delta_angle = target_angle - current_angle
    
    while delta_angle > 180:
        delta_angle -= 360
    while delta_angle < -180:
        delta_angle += 360
        
    return delta_angle, target_angle

# -------------------------------------------------------------------
## 🐹햄스터🐹 실행 로직 (동작 활성화)
# -------------------------------------------------------------------

# 1. 포인트 추출
points = extract_points(path_d)

current_angle = 0 # 햄스터 초기 방향: x축(0도) 기준

if len(points) < 2:
    print("경로를 따라 이동할 포인트가 부족합니다.")
else:
    print(f"로봇 동작 시작 (SCALE={SCALE})")
    print("-" * 40)
    
    for i in range(1, len(points)):
        x0, y0 = points[i-1]
        x1, y1 = points[i]
        dx, dy = x1 - x0, y1 - y0
        
        distance_svg = math.hypot(dx, dy)
        distance = distance_svg * SCALE

        # 회전각 및 새 절대 각도 계산
        delta_angle, current_angle = turn_to_direction(current_angle, (dx, dy))
        
        # 회전 명령 활성화
        if abs(delta_angle) > 1.0: # 1.0도 이하의 미세 회전 무시
            turn_abs_angle = abs(delta_angle)
            if delta_angle > 0: 
                h.turn_left(turn_abs_angle)  # <--- 활성화
                print(f"[{i}단계] 좌회전 {turn_abs_angle:.2f}도")
            elif delta_angle < 0: 
                h.turn_right(turn_abs_angle) # <--- 활성화
                print(f"[{i}단계] 우회전 {turn_abs_angle:.2f}도")
        else:
            print(f"[{i}단계] 회전: 미세 회전 (무시)")
        
        # 이동 명령 활성화
        if distance > 0.0:
            h.move_forward(distance) # <--- 활성화
            print(f"[{i}단계] 이동: {distance:.2f} cm ({distance_svg:.1f} SVG units)")

    print("-" * 40)
    print(f"동작 완료. 최종 방향: {current_angle:.2f}도")
