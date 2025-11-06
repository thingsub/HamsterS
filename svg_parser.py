# svg_parser_extended.py
from svgpathtools import svg2paths, Line, CubicBezier, QuadraticBezier, Arc, Path
import numpy as np

def parse_svg(file_path):
    """
    SVG 파일을 파싱하여 경로(path)와 세그먼트 정보 추출
    모든 기본 SVG 명령어(M,L,H,V,C,S,Q,T,A,Z)를 처리
    :param file_path: SVG 파일 경로
    :return: 파싱된 경로 목록
    """
    paths, attributes = svg2paths(file_path)
    parsed_paths = []

    for path in paths:
        path_data = []
        current_point = None

        for i, segment in enumerate(path):
            # 첫 segment이면 무조건 Move
            if i == 0:
                current_point = segment.start
                path_data.append({
                    "type": "M",
                    "start": (segment.start.real, segment.start.imag),
                    "end": (segment.end.real, segment.end.imag),
                })
                continue

            # Line
            if isinstance(segment, Line):
                path_data.append({
                    "type": "L",
                    "start": (segment.start.real, segment.start.imag),
                    "end": (segment.end.real, segment.end.imag),
                })

            # CubicBezier
            elif isinstance(segment, CubicBezier):
                path_data.append({
                    "type": "C",
                    "start": (segment.start.real, segment.start.imag),
                    "control1": (segment.control1.real, segment.control1.imag),
                    "control2": (segment.control2.real, segment.control2.imag),
                    "end": (segment.end.real, segment.end.imag),
                })

            # QuadraticBezier
            elif isinstance(segment, QuadraticBezier):
                path_data.append({
                    "type": "Q",
                    "start": (segment.start.real, segment.start.imag),
                    "control": (segment.control.real, segment.control.imag),
                    "end": (segment.end.real, segment.end.imag),
                })

            # Arc
            elif isinstance(segment, Arc):
                path_data.append({
                    "type": "A",
                    "start": (segment.start.real, segment.start.imag),
                    "end": (segment.end.real, segment.end.imag),
                    "radius": (segment.radius.real, segment.radius.imag),
                    "center": (segment.center.real, segment.center.imag),
                })

            # Z (닫기)
            if hasattr(segment, "isclosed") and segment.isclosed:
                path_data.append({
                    "type": "Z",
                    "start": (segment.end.real, segment.end.imag),
                    "end": (path[0].start.real, path[0].start.imag),
                })

        parsed_paths.append(path_data)

    return parsed_paths
