# 서울쉴더스 (Seoul Shieldus)

**서울시 25개 자치구의 치안 인프라를 하나의 지표로 비교하고, 내 주변 안전 시설을 찾아보는 인터랙티브 웹 대시보드**
<img width="1472" height="778" alt="image" src="https://github.com/user-attachments/assets/fe5e9a39-8ca5-4857-bfa5-74e5d384ac22" />
<img width="1483" height="711" alt="image" src="https://github.com/user-attachments/assets/89abc146-eda2-4359-9f96-95bca9aabf56" />
<img width="1542" height="485" alt="image" src="https://github.com/user-attachments/assets/ef3468fd-bffd-4ea8-bcb1-45c8540f238c" />


![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B?logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![License](https://img.shields.io/badge/status-mini--project-lightgrey)

CCTV, 지구대·파출소, 여성안심귀갓길, 가로등, 범죄 통계 등 서울시가 공개한 5종의 공공데이터를 자치구 단위로 결합하고 인구·면적 기준으로 정규화해, "우리 동네가 다른 동네보다 얼마나 안전한가"를 지도 한 장으로 비교할 수 있게 만든 미니 프로젝트입니다.

---

## 데모
<img width="1918" height="803" alt="image" src="https://github.com/user-attachments/assets/8d3ede73-d92f-4eb4-979c-ef568268bfb4" />

![서울쉴더스 실행 화면 데모](docs/demo.gif)

> 위 GIF는 홈 화면과 안심지수 히트맵(자치구 랭킹 · 상세 점수 · CCTV 목적별 통계)을 보여줍니다. 시설찾기 · 길찾기 페이지는 네이버 지도 / TMAP API 키가 있어야 지도가 그려지므로, 실제 배포된 서비스에서 확인해 주세요.

## 주요 기능

- **🛡️ 안심지수 히트맵** — 서울시 25개 자치구를 CCTV · 파출소 접근성 · 안심귀갓길 · 가로등 · 범죄안전 5개 지표의 가중합(0~100점)으로 계산한 "안심지수"로 비교합니다. 지도에서 자치구를 호버하면 해당 폴리곤이 강조되고, 랭킹 표와 자치구별 상세 점수 막대, CCTV 목적별 설치 현황 차트를 확인할 수 있습니다.
- **📍 시설찾기** — 지도 위에 지구대 · 파출소 · 가로등 · 안심귀갓길을 표시하고, 이름 · 구 · 주소 · 종류 · 범죄율을 표로 제공합니다.
- **🧭 길찾기** — 브라우저 위치 정보로 현재 위치를 확인하고, 가장 가까운(또는 직접 선택한) 지구대 · 파출소까지 도보/자동차 경로를 TMAP 보행자 경로 API로 안내합니다.
- **🏠 홈** — 서울 평균 안심지수, 안심지수 1위 자치구, 3개 기능 바로가기 카드를 제공합니다.

안심지수 산출 방식과 검증 과정(회귀분석 잔차 0.005점 이내, 각 지표-원본 수치 간 상관계수 0.99 이상)은 [`docs/`](docs/) 폴더의 프로젝트 기획서를 참고해 주세요.

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| 프론트엔드 | Streamlit, folium / streamlit-folium, 네이버 지도 API, TMAP API |
| 데이터 처리 | pandas |
| 데이터베이스 | SQLAlchemy (SQLite 기본 / MySQL 선택) |
| 배포 | Streamlit Community Cloud |

## 설치 및 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/creatorsg/Seoul_Shieldus.git
cd Seoul_Shieldus
```

### 2. 가상환경 생성 및 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사해 `.env`를 만들고 API 키를 채워 넣습니다.

```bash
cp .env.example .env
```

```dotenv
# 지도 API (필수 - 시설찾기 · 길찾기 페이지에 필요)
NAVER_MAPS_CLIENT_ID=발급받은_클라이언트_ID
TMAP_APP_KEY=발급받은_앱_키

# Database (선택 - 비워두면 자동으로 SQLite 사용)
DB_USER=
DB_PASSWORD=
DB_NAME=
DB_HOST=
DB_PORT=
```

- 네이버 지도 API 키: [네이버 클라우드 플랫폼](https://www.ncloud.com)에서 Maps 서비스를 신청해 발급받습니다.
- TMAP API 키: [SK Open API](https://tmapapi.sktelecom.com)에서 발급받습니다.
- DB 관련 값을 모두 비워두면 별도 서버 설치 없이 `backend/seoul_shieldus.db`(SQLite)를 자동 생성해 사용합니다. 앱을 처음 실행하면 `data/processed/`의 JSON 원본이 자동으로 시딩됩니다.

### 4. 앱 실행

```bash
streamlit run frontend/app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 됩니다.

## 프로젝트 구조

```
Seoul_Shieldus/
├── README.md
├── requirements.txt
├── .env.example              API 키/DB 접속 정보 키 목록만 공유
├── frontend/
│   ├── app.py                화면 조립 (Streamlit)
│   ├── data_access.py        데이터 로딩 계층 (DB 우선 조회, JSON 폴백)
│   ├── colors.py             점수 → 색상 매핑 단일 소스
│   ├── naver_map.py          네이버 지도 HTML 생성
│   ├── route_finder.py       TMAP 경로 조회
│   └── static/                PWA manifest.json · 아이콘
├── data/
│   ├── raw/                  원본 데이터
│   ├── processed/            정제된 자치구별 안심지수 · 시설 데이터
│   └── (팀원별 작업 폴더 — 담당 데이터셋 정제 스크립트 포함)
├── backend/
│   ├── database.py           SQLAlchemy 연결 (SQLite/MySQL 자동 분기)
│   ├── models.py             ORM 테이블 6종
│   └── init_db.py            DB 테이블 생성 + JSON 데이터 시딩
└── docs/                     프로젝트 기획서 · 산출 방식 설명
```

## 데이터 출처

- [서울 열린데이터광장](https://data.seoul.go.kr) — 지구대/파출소 위치, CCTV 설치현황, 여성안심귀갓길, 자치구별 인구/면적
- [공공데이터포털](https://data.go.kr) — 범죄 발생 통계(경찰청), 가로등 설치현황

## 팀원 (Team Seoul-Shielders)

| 이름 | GitHub | 역할 |
| --- | --- | --- |
| 손인선 (조장) | [@creatorsg](https://github.com/creatorsg) | 프론트엔드 · 화면·백엔드 통합 |
| 강대현 | [@user4753](https://github.com/user4753) | 발표 |
| 황인찬 | [@bluejals13](https://github.com/bluejals13) | 서울 지역별 범죄율 · 가로등 설치현황 데이터 처리 |
| 이승혁 | [@sheok13](https://github.com/sheok13) | 데이터 정규화 |
| 전승호 | [@kdb1828-hub](https://github.com/kdb1828-hub) | 여성안심귀갓길 · 자치구별 인구/면적 데이터 처리 |
| 정예빈 | [@benniejung](https://github.com/benniejung) | 백엔드 |
| 정세진 | [@tpwlswjd3026](https://github.com/tpwlswjd3026) | 지구대·파출소 · CCTV 현황 데이터 처리 |

## 알려진 한계

- 안심지수는 25개 자치구 내 상대적 순위(min-max 정규화)이며, 절대적인 위험도를 의미하지 않습니다.
- 여성안심귀갓길은 노선 요약 정보(노선 수, 총 길이)는 DB로 이관했지만, 지도에 표시할 좌표 데이터는 아직 DB 스키마에 포함되어 있지 않아 원본 JSON 파일에 의존합니다.
- 네이버 지도 API 이용약관상 좌표 데이터를 API 호출 없이 재사용/캐싱하는 것이 금지되어 있어, 위치 데이터는 공공데이터 출처에서 직접 수집·저장하고 지도는 화면 표시용으로만 사용합니다.
