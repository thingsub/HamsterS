실행 명령어: `python hamster.py`  

프로젝트는 **HAMSTERS** 폴더 내에 네 개의 파일로 구성됩니다.  

├── HAMSTERS  
│   ├── `hamster.py`       # 메인 실행 파일 (Entry Point)  
│   ├── `svg_parser.py`    # SVG 경로 파싱 모듈  
│   ├── `Mouse.svg`        # 입력 SVG 파일 (로봇이 그릴 그림)  
│   └── `utils.py`         # 실제 로봇 동작(이동 및 회전) 실행 로직  


## svg_parser.py
- SVG 파일을 읽어 경로(Path) 정보를 파싱합니다.
- svgpathtools를 이용해 Line, Bezier, Arc 등의 세그먼트를 구분하고, 각 좌표 정보를 리스트 형태로 정리하여 반환합니다
- <circle> 태그 등 별도 도형도 인식하여 경로 리스트에 포함합니다.

## utils.py

- 로봇의 실제 동작을 위한 연산 기능을 제공합니다.
- move_to() 함수로 로봇의 전진(move_forward) 및 회전(turn_left / turn_right)을 제어하며, execute_path()는 SVG에서 파싱된 경로를 순차적으로 읽어 로봇이 실제로 그리게 합니다.
- Bezier 곡선, 원호(Arc), 원(circle) 등 다양한 도형을 점 단위 이동 경로로 근사하여 실행합니다.

## 🐹 hamster.py

- 프로젝트의 메인 실행 스크립트입니다.
- parse_svg()를 통해 SVG 파일(Mouse.svg)을 파싱한 후, execute_path()를 호출하여 로봇이 실제 경로를 따라 움직이게 합니다.
- Hamster 로봇 객체를 초기화하고, 보정값(ANGLE_OFFSET)을 설정합니다.
