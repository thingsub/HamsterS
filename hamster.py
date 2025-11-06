# hamster.py
from roboid import *  
from svg_parser import parse_svg  
from utils import execute_path  

# Hamster 객체 생성
h = Turtle()

# 로봇의 초기 위치와 각도 설정 (0, 0, 0)
current_position = (0, 0)
current_angle = 0

# 파싱할 SVG 파일 경로
svg_file_path = "Mouse.svg"  

# 파싱된 SVG 경로 데이터 가져오기
parsed_paths = parse_svg(svg_file_path)  # 파일 경로를 인자로 전달

# 경로를 따라 로봇이 움직이도록 실행
execute_path(h, parsed_paths)