# svg_parser.py
import re
import math
import xml.etree.ElementTree as ET

# --- 전역 변수: SVG 좌표계 원점을 로봇 좌표 (0,0)에 고정 ---
global_offset_x = 100
global_offset_y = 50


# --- 베지어 곡선 분해 함수 (Cubic Bézier Curve) ---
def interpolate_cubic_bezier(p0, p1, p2, p3, steps=15):
    """3차 베지어 곡선을 steps 만큼의 직선 세그먼트로 분할하여 좌표 목록을 반환합니다."""
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        one_minus_t = 1 - t
        x = (one_minus_t**3 * p0[0] +
             3 * one_minus_t**2 * t * p1[0] +
             3 * one_minus_t * t**2 * p2[0] +
             t**3 * p3[0])
        y = (one_minus_t**3 * p0[1] +
             3 * one_minus_t**2 * t * p1[1] +
             3 * one_minus_t * t**2 * p2[1] +
             t**3 * p3[1])
        points.append((x, y))
    return points


# --- 베지어 곡선 분해 함수 (Quadratic Bézier Curve) ---
def interpolate_quadratic_bezier(p0, p1, p2, steps=15):
    """2차 베지어 곡선을 steps 만큼의 직선 세그먼트로 분할하여 좌표 목록을 반환합니다."""
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        one_minus_t = 1 - t
        x = (one_minus_t**2 * p0[0] +
             2 * one_minus_t * t * p1[0] +
             t**2 * p2[0])
        y = (one_minus_t**2 * p0[1] +
             2 * one_minus_t * t * p1[1] +
             t**2 * p2[1])
        points.append((x, y))
    return points


# --- SVG Path 및 Circle 해석 함수 ---
def extract_points(path_d):
    """SVG path 문자열 또는 Circle 튜플에서 절대 좌표(로봇 좌표계)를 추출합니다."""
    global global_offset_x, global_offset_y

    # Circle 처리
    if isinstance(path_d, tuple) and len(path_d) == 3:
        cx, cy, r = path_d
        steps = 24
        circle_points_svg = []
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            x_svg = cx + r * math.cos(angle)
            y_svg = cy + r * math.sin(angle)
            circle_points_svg.append((x_svg, y_svg))
        points = [(x - global_offset_x, -(y - global_offset_y)) for x, y in circle_points_svg]
        return points

    # Path 문자열 전처리
    path_d = path_d.replace(',', ' ')
    path_d = re.sub(r'(\d)-', r'\1 -', path_d)
    tokens = re.findall(r'([MLHVZCcmlhvzcQTAa])([^MLHVZCcmlhvzcQTAa]*)', path_d)

    points = []
    current_pos_svg = (0.0, 0.0)
    start_pos_svg = (0.0, 0.0)
    prev_control_point_svg = None

    for cmd, vals in tokens:
        cmd_upper = cmd.upper()
        is_relative = cmd.islower()
        coords = list(map(float, re.findall(r'-?\d+\.?\d*(?:e[-+]?\d+)?', vals.strip())))

        if cmd_upper in ['M', 'L']:
            for i in range(0, len(coords), 2):
                x_svg = coords[i] + (current_pos_svg[0] if is_relative else 0)
                y_svg = coords[i+1] + (current_pos_svg[1] if is_relative else 0)
                x_robot = x_svg - global_offset_x
                y_robot = -(y_svg - global_offset_y)
                points.append((x_robot, y_robot))
                current_pos_svg = (x_svg, y_svg)
                prev_control_point_svg = None
                if cmd_upper == 'M' and i == 0:
                    start_pos_svg = current_pos_svg

        elif cmd_upper == 'H':
            for val in coords:
                x_svg = val + (current_pos_svg[0] if is_relative else 0)
                y_svg = current_pos_svg[1]
                x_robot = x_svg - global_offset_x
                y_robot = -(y_svg - global_offset_y)
                points.append((x_robot, y_robot))
                current_pos_svg = (x_svg, y_svg)
                prev_control_point_svg = None

        elif cmd_upper == 'V':
            for val in coords:
                x_svg = current_pos_svg[0]
                y_svg = val + (current_pos_svg[1] if is_relative else 0)
                x_robot = x_svg - global_offset_x
                y_robot = -(y_svg - global_offset_y)
                points.append((x_robot, y_robot))
                current_pos_svg = (x_svg, y_svg)
                prev_control_point_svg = None

        elif cmd_upper == 'C':
            for i in range(0, len(coords), 6):
                if is_relative:
                    p1_svg = (current_pos_svg[0] + coords[i], current_pos_svg[1] + coords[i+1])
                    p2_svg = (current_pos_svg[0] + coords[i+2], current_pos_svg[1] + coords[i+3])
                    p3_svg = (current_pos_svg[0] + coords[i+4], current_pos_svg[1] + coords[i+5])
                else:
                    p1_svg = (coords[i], coords[i+1])
                    p2_svg = (coords[i+2], coords[i+3])
                    p3_svg = (coords[i+4], coords[i+5])
                bezier_points = interpolate_cubic_bezier(current_pos_svg, p1_svg, p2_svg, p3_svg, steps=15)
                for x_svg, y_svg in bezier_points:
                    x_robot = x_svg - global_offset_x
                    y_robot = -(y_svg - global_offset_y)
                    points.append((x_robot, y_robot))
                current_pos_svg = p3_svg
                prev_control_point_svg = p2_svg

        elif cmd_upper == 'S':
            for i in range(0, len(coords), 4):
                if prev_control_point_svg:
                    p1_svg = (2*current_pos_svg[0] - prev_control_point_svg[0],
                              2*current_pos_svg[1] - prev_control_point_svg[1])
                else:
                    p1_svg = current_pos_svg
                if is_relative:
                    p2_svg = (current_pos_svg[0] + coords[i], current_pos_svg[1] + coords[i+1])
                    p3_svg = (current_pos_svg[0] + coords[i+2], current_pos_svg[1] + coords[i+3])
                else:
                    p2_svg = (coords[i], coords[i+1])
                    p3_svg = (coords[i+2], coords[i+3])
                bezier_points = interpolate_cubic_bezier(current_pos_svg, p1_svg, p2_svg, p3_svg, steps=15)
                for x_svg, y_svg in bezier_points:
                    x_robot = x_svg - global_offset_x
                    y_robot = -(y_svg - global_offset_y)
                    points.append((x_robot, y_robot))
                current_pos_svg = p3_svg
                prev_control_point_svg = p2_svg

        elif cmd_upper == 'Q':
            for i in range(0, len(coords), 4):
                if is_relative:
                    p1_svg = (current_pos_svg[0] + coords[i], current_pos_svg[1] + coords[i+1])
                    p2_svg = (current_pos_svg[0] + coords[i+2], current_pos_svg[1] + coords[i+3])
                else:
                    p1_svg = (coords[i], coords[i+1])
                    p2_svg = (coords[i+2], coords[i+3])
                bezier_points = interpolate_quadratic_bezier(current_pos_svg, p1_svg, p2_svg, steps=15)
                for x_svg, y_svg in bezier_points:
                    x_robot = x_svg - global_offset_x
                    y_robot = -(y_svg - global_offset_y)
                    points.append((x_robot, y_robot))
                current_pos_svg = p2_svg
                prev_control_point_svg = p1_svg

        elif cmd_upper == 'T':
            for i in range(0, len(coords), 2):
                if prev_control_point_svg:
                    p1_svg = (2*current_pos_svg[0] - prev_control_point_svg[0],
                              2*current_pos_svg[1] - prev_control_point_svg[1])
                else:
                    p1_svg = current_pos_svg
                if is_relative:
                    p2_svg = (current_pos_svg[0] + coords[i], current_pos_svg[1] + coords[i+1])
                else:
                    p2_svg = (coords[i], coords[i+1])
                bezier_points = interpolate_quadratic_bezier(current_pos_svg, p1_svg, p2_svg, steps=15)
                for x_svg, y_svg in bezier_points:
                    x_robot = x_svg - global_offset_x
                    y_robot = -(y_svg - global_offset_y)
                    points.append((x_robot, y_robot))
                current_pos_svg = p2_svg
                prev_control_point_svg = p1_svg

        elif cmd_upper == 'Z':
            x_svg, y_svg = start_pos_svg
            x_robot = x_svg - global_offset_x
            y_robot = -(y_svg - global_offset_y)
            points.append((x_robot, y_robot))
            current_pos_svg = start_pos_svg
            prev_control_point_svg = None

    return points


# --- 회전각 계산 함수 ---
def turn_to_direction(current_angle, target_vec):
    """현재 각도에서 목표 벡터로 향하는 회전 각도(delta_angle)를 계산합니다."""
    target_angle = math.degrees(math.atan2(target_vec[1], target_vec[0]))
    delta_angle = target_angle - current_angle
    while delta_angle > 180:
        delta_angle -= 360
    while delta_angle < -180:
        delta_angle += 360
    return delta_angle, target_angle


# --- SVG XML 파싱 함수 ---
def extract_all_path_d(svg_xml_content):
    """SVG XML 컨텐츠에서 <path> 및 <circle> 요소를 추출."""
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    try:
        root = ET.fromstring(svg_xml_content)
        all_path_data = []

        # 네임스페이스 유무 모두 지원
        path_elements = root.findall('.//svg:path', svg_ns) + root.findall('.//path')
        circle_elements = root.findall('.//svg:circle', svg_ns) + root.findall('.//circle')

        for path_element in path_elements:
            d_attr = path_element.get('d')
            if d_attr:
                all_path_data.append(d_attr)

        for circle_element in circle_elements:
            cx = float(circle_element.get('cx', 0))
            cy = float(circle_element.get('cy', 0))
            r = float(circle_element.get('r', 0))
            if r > 0:
                all_path_data.append((cx, cy, r))

        return all_path_data
    except ET.ParseError as e:
        print(f"❌ SVG 파싱 오류: {e}")
        return []


# --- SVG 전체를 로봇 좌표로 변환하는 함수 ---
def svg_to_robot_points(svg_xml_content):
    all_path_data = extract_all_path_d(svg_xml_content)
    all_points = []
    for path_or_circle in all_path_data:
        points = extract_points(path_or_circle)
        all_points.extend(points)
    return all_points
