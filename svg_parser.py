# svg_parser.py
from svgpathtools import svg2paths, Line, CubicBezier, QuadraticBezier, Arc
import xml.etree.ElementTree as ET

def parse_svg(file_path):
    paths, attributes = svg2paths(file_path)
    parsed_paths = []

    # ----- 일반 path 처리 -----
    for path in paths:
        path_data = []

        #   1. 경로의 시작점 (M)을 첫 세그먼트 시작 전에 명시적으로 추가
        # path[0].start는 항상 첫 번째 세그먼트의 시작점을 나타냅니다.
        if len(path) > 0:
            start_point = (path[0].start.real, path[0].start.imag)
            path_data.append({
                "type": "M",
                "start": start_point, 
                "end": start_point # M 명령은 제자리 이동으로 기록
            })

        #   2. 실제 세그먼트들 (L, C, Q, A) 처리 (M 명령 처리는 생략)
        for segment in path:
            if isinstance(segment, Line):
                path_data.append({
                    "type": "L",
                    "start": (segment.start.real, segment.start.imag),
                    "end": (segment.end.real, segment.end.imag)
                })

            elif isinstance(segment, CubicBezier):
                path_data.append({
                    "type": "C",
                    "start": (segment.start.real, segment.start.imag),
                    "control1": (segment.control1.real, segment.control1.imag),
                    "control2": (segment.control2.real, segment.control2.imag),
                    "end": (segment.end.real, segment.end.imag)
                })

            elif isinstance(segment, QuadraticBezier):
                path_data.append({
                    "type": "Q",
                    "start": (segment.start.real, segment.start.imag),
                    "control": (segment.control.real, segment.control.imag),
                    "end": (segment.end.real, segment.end.imag)
                })

            elif isinstance(segment, Arc):
                path_data.append({
                    "type": "A",
                    "start": (segment.start.real, segment.start.imag),
                    "end": (segment.end.real, segment.end.imag),
                    "radius": (segment.radius.real, segment.radius.imag),
                    "center": (segment.center.real, segment.center.imag),
                })

# 닫힌 경로 처리 (Z)
        if path.isclosed() and path_data:
            first_segment_start = path_data[0]['end'] # M 명령의 end (첫 시작점)

            path_data.append({
                "type": "Z",
                #   보정 없이 SVG가 파싱한 그대로의 마지막 끝점을 start로 사용
                "start": (path[-1].end.real, path[-1].end.imag), 
                "end": first_segment_start
            })

        parsed_paths.append(path_data)

    # ----- circle 요소 추가 처리 -----
    tree = ET.parse(file_path)
    root = tree.getroot()
    # 네임스페이스 정의를 반드시 포함
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    for circle in root.findall(".//svg:circle", ns):
        cx = float(circle.attrib.get('cx', 0))
        cy = float(circle.attrib.get('cy', 0))
        r = float(circle.attrib.get('r', 0))
        path_data = [{
            "type": "circle",
            "center": (cx, cy),
            "radius": r
        }]
        parsed_paths.append(path_data)

    return parsed_paths