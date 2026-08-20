import json
import os

# database 및 models 모듈 불러오기
# pyrefly: ignore [missing-import]
from database import engine, Base


# -------------------------------------------------------------
# 1. DB 테이블 전체 생성 함수
# -------------------------------------------------------------
def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ [성공] 모든 테이블이 성공적으로 생성되었습니다!\n")
