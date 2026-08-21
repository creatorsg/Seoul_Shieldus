# backend/database.py
"""
DB 연결 설정.

.env에 DB_HOST/DB_USER/DB_PASSWORD/DB_NAME이 전부 채워져 있으면 그 MySQL/MariaDB에
연결하고, 하나라도 비어있으면(오늘 배포 환경처럼 별도 DB 서버를 아직 준비 못 했을 때)
이 폴더 안의 SQLite 파일(seoul_shieldus.db)로 자동 대체한다.

왜 이렇게 하나: 배포를 오늘 나가야 하는데 MySQL 서버를 새로 준비하면 가입/설정 시간이
더 걸리고, Streamlit Community Cloud엔 자체 DB가 없어서 외부 DB를 어차피 따로 붙여야
한다. SQLite는 파일 하나로 끝나서 지금 당장은 이게 훨씬 안전하다. 그렇다고 MySQL 전용
코드로 못박아두면 나중에 실제 MySQL 서버가 생겼을 때 이 파일과 models.py를 다시 고쳐야
하는데, SQLAlchemy는 두 DB 방언을 거의 같은 코드로 다루므로 여기서 분기만 해두면 나중엔
.env만 채우면 된다(코드 변경 불필요).

SQLite 파일은 seed 스크립트(init_db.py)가 실행될 때마다 새로 만들어질 수 있는 생성물이라
git에는 커밋하지 않는다(.gitignore 참고) - data/processed/의 원본 JSON만 있으면 언제든
다시 만들어낼 수 있다.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

# .env는 프로젝트 루트(backend/의 부모)에 있다 - frontend 쪽 코드들과 동일한 위치 규칙.
load_dotenv(BASE_DIR.parent / ".env", override=True)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

USE_MYSQL = bool(DB_HOST and DB_USER and DB_PASSWORD and DB_NAME)

if USE_MYSQL:
    # DB 접속 URL (PyMySQL 드라이버 사용) - requirements.txt에 pymysql을 추가해야 동작한다.
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(DATABASE_URL, echo=False)
else:
    SQLITE_PATH = BASE_DIR / "seoul_shieldus.db"
    # check_same_thread=False: Streamlit은 요청마다 다른 스레드에서 콜백을 실행할 수 있는데,
    # SQLite 기본 설정은 커넥션을 만든 스레드가 아닌 다른 스레드에서 쓰면 에러를 낸다.
    # SQLAlchemy가 커넥션 풀링/동시성을 다뤄주므로 이 옵션으로 그 제약만 풀어준다.
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# SQLAlchemy Engine 및 Session 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 모델이 상속받을 Base 클래스
Base = declarative_base()
