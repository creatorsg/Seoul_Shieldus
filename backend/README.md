# 🛡️ 서울 쉴더스 (Seoul Shieldus) - 백엔드 & DB 적재 파이프라인

서울시 25개 자치구의 치안 상태 및 보안 인프라(지구대/파출소, CCTV, 여성안심귀갓길, 가로등 등) 데이터를 수집·정제하여 MySQL/MariaDB 데이터베이스에 자동 구축하고 관리하는 백엔드 파이프라인입니다.

---

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [사전 준비사항](#사전-준비사항)
3. [디렉토리 및 주요 파일 설명](#디렉토리-및-주요-파일-설명)
4. [데이터베이스 모델 (ORM Schema)](#데이터베이스-모델-orm-schema)
5. [환경 변수 설정 (.env)](#환경-변수-설정-env)
6. [실행 방법](#실행-방법)
7. [DB 접속 및 데이터 검증 명령](#db-접속-및-데이터-검증-명령)

---

## 📌 프로젝트 개요
- **주제**: 서울 지역 보안 인프라 데이터 구축 및 치안 지도 서비스 백엔드
- **목표**: 서울시 자치구별 치안 인프라(지구대/파출소, 여성안심귀갓길, 가로등, CCTV 용도별 통계, 범죄율 등)를 통합 데이터베이스로 구축하여 한눈에 치안 상태를 파악할 수 있도록 지원
- **데이터 범위**: 서울특별시 25개 자치구 전체

---

## ⚙️ 사전 준비사항

### 1. 필수 라이브러리 및 도구
- **Python**: 3.10 이상 (추천: 3.11+)
- **DBMS**: MySQL 8.0+ 또는 MariaDB 10.5+
- **패키지 관리자**: `pip` 또는 `uv`

### 2. Python 패키지 설치
`backend` 디렉토리에서 아래 명령어로 필요 패키지를 설치합니다:
```bash
pip install sqlalchemy pymysql python-dotenv
```
*(또는 `uv` 사용 시: `uv sync`)*

### 3. MySQL 데이터베이스 생성
MySQL/MariaDB에 접속하여 데이터베이스를 미리 생성합니다:
```sql
CREATE DATABASE seoul_shieldus CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📁 디렉토리 및 주요 파일 설명

```text
backend/
├── README.md              # 백엔드 및 DB 파이프라인 안내 문서 (본 문서)
├── .env               # DB 접속용 환경 변수 (Git 비추적)
├── database.py        # SQLAlchemy 엔진 및 SessionLocal 생성
├── models.py          # SQLAlchemy ORM 데이터베이스 테이블 모델 6종 정의
├── init_db.py         # DB 테이블 자동 생성 및 JSON 데이터 5종 적재 (Seed)
```

### 📄 파일별 주요 역할
- **`database.py`**: `.env` 환경 정보를 읽어 PyMySQL 드라이버로 SQLAlchemy Connection Engine 및 `SessionLocal` 세션 팩토리를 생성합니다.
- **`models.py`**: SQLAlchemy ORM을 사용하여 치안지수, 안심귀갓길 요약/상세, 가로등, CCTV 통계, 경찰서/지구대 등 6개 테이블 스키마를 정의합니다.
- **`init_db.py`**: 실행 시 자동으로 DB 테이블을 일괄 생성(`create_all`)하고, `data/processed/` 하위의 JSON 파일 5종을 순차적으로 읽어 DB에 데이터를 자동 입력/갱신(Seed Data Loading)합니다.

---

## 🗄️ 데이터베이스 모델 (ORM Schema)

| 테이블명 (`__tablename__`) | ORM 클래스명 | 핵심 데이터 및 설명 |
| :--- | :--- | :--- |
| `seoul_safety_index` | `SeoulSafetyIndex` | 자치구별 인구/면적, 2024년 범죄수, 치안지수, 파생 평가 점수 등 |
| `safe_route_districts` | `SafeRouteDistrict` | 자치구별 여성안심귀갓길 요약 (노선수, 총길이) *(SafeRoute와 1:N)* |
| `safe_routes` | `SafeRoute` | 개별 여성안심귀갓길 노선 상세 (위치, 비상벨, CCTV, 보안등, 안내판, 112표지판 수) |
| `street_lights` | `StreetLight` | 가로등 위치 데이터 (관리번호 PK, 위도 lat, 경도 lng) |
| `district_cctv_stats` | `DistrictCctvStat` | 자치구별 CCTV 총량 및 용도별(범죄예방, 어린이보호, 공원, 교통 등) 통계 |
| `police_stations` | `PoliceStation` | 지구대 및 파출소 위치 데이터 (관서명, 구분, 주소, 위도, 경도) |

---

## 🚀 실행 방법

### DB 테이블 생성 및 JSON 데이터 자동 적재 실행

`backend/src` 디렉토리로 이동한 후 `init_db.py`를 실행합니다:

```bash
cd backend/src
python init_db.py
```

또는 `backend` 루트 디렉토리에서 실행:
```bash
cd backend
python src/init_db.py
```

### 💡 실행 처리 순서
1. `create_all_tables()`: DB에 존재하지 않는 6개 테이블 자동 생성
2. `seed_safety_index()`: `seoul_safety_index(1).json` 적재
3. `seed_safe_routes()`: `seoul_safe_paths(2).json` 적재 (요약 및 노선 상세)
4. `seed_street_lights()`: `seoul_street_lights(3).json` 적재
5. `seed_cctv_stats()`: `seoul_cctv_stats(4).json` 적재
6. `seed_police_stations()`: `seoul_jigudae(5).json` 적재
7. 완료 메시지 출력 (`🎉 [완료] 데이터베이스 초기화 및 데이터 적재가 모두 끝났습니다!`)

---

## 🔍 DB 접속 및 데이터 검증 명령

### MySQL CLI 접속
```bash
mysql -u shieldus_user -p seoul_shieldus
```

### DB 검증 SQL 쿼리
```sql
-- 테이블 목록 확인
SHOW TABLES;

-- 각 테이블 레코드 수 확인
SELECT COUNT(*) FROM seoul_safety_index;
SELECT COUNT(*) FROM safe_route_districts;
SELECT COUNT(*) FROM safe_routes;
SELECT COUNT(*) FROM street_lights;
SELECT COUNT(*) FROM district_cctv_stats;
SELECT COUNT(*) FROM police_stations;

-- 안심귀갓길 데이터 샘플 조회
SELECT * FROM safe_routes LIMIT 5;
```
