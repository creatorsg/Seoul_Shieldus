"""
서울시 치안 안전 지수 메인 앱 진입점
Streamlit 실행: streamlit run main.py
"""

import sys
from pathlib import Path

# frontend 경로를 파이썬 모듈 검색 경로에 포함
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import app  # frontend/app.py 실행
