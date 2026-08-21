# 서울쉴더스 (Seoul Shieldus)

**서울시 25개 자치구의 치안 인프라를 하나의 지표로 비교하고, 내 주변 안전 시설을 찾아보는 인터랙티브 웹 대시보드**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B?logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![License](https://img.shields.io/badge/status-mini--project-lightgrey)

CCTV, 지구대·파출소, 여성안심귀갓길, 가로등, 범죄 통계 등 서울시가 공개한 5종의 공공데이터를 자치구 단위로 결합하고 인구·면적 기준으로 정규화해, "우리 동네가 다른 동네보다 얼마나 안전한가"를 지도 한 장으로 비교할 수 있게 만든 미니 프로젝트입니다.

---

1. 서울 열린데이터광장 (data.seoul.go.kr)
   - 지구대/파출소 위치, CCTV 설치 현황, 여성안심귀갓길, 자치구별 인구/면적 등 공공API 형태로 제공

2. 공공데이터포털 (data.go.kr)
   - 경찰청 범죄 통계, 안전시설물(가로등 등) 관련 데이터

3. 지도 표시 - 네이버 클라우드 플랫폼 Maps API
   - 자치구 경계, 지구대/CCTV/귀갓길 등 좌표를 지도 위에 "표시"하는 용도로만 사용
   - 서비스 이용약관 제7조 11항에 따라 결과로 받은 좌표 데이터를 API 호출 없이 재사용/캐싱하는 것은 금지되어 있으므로,
     위치 데이터는 위 공공 데이터 출처에서 직접 수집·저장하고, 네이버 지도는 화면에 그리는 용도로만 사용

4. 길찾기(보행자 경로 안내) - TMAP API (SK Open API)
   - 네이버 Directions API는 자동차 경로만 지원하므로, 도보 기반 안심귀갓길 안내에는 TMAP 보행자 경로 API 사용

# 데이터 수집 방법
데이터 수집 방법

![서울쉴더스 실행 화면 데모](docs/demo.gif)

> 위 GIF는 홈 화면과 안심지수 히트맵(자치구 랭킹 · 상세 점수 · CCTV 목적별 통계)을 보여줍니다. 시설찾기 · 길찾기 페이지는 네이버 지도 / TMAP API 키가 있어야 지도가 그려지므로, 실제 배포된 서비스에서 확인해 주세요.

## 주요 기능

4. 보안 및 데이터 정제
- API Key 보안 관리, 데이터 통합 및 저장 

# 실행 방법 (프론트엔드 - 더미 데이터 기준)

1. 의존성 설치
   ```
   pip install -r requirements.txt
   ```

2. 프로젝트 루트에서 앱 실행
   ```
   streamlit run frontend/app.py
   ```

3. 현재 상태
   - `data/seoul_districts.geojson` : 서울 25개 자치구 경계 데이터 (southkorea/seoul-maps 저장소 출처)
   - `frontend/app.py` : 백엔드 데이터 연동 전까지 랜덤 더미 값으로 화면 확인용
   - 백엔드 데이터가 준비되면 `frontend/app.py` 의 `get_district_scores()` 함수 내부만
     실제 데이터 조회 코드로 교체하면 됩니다 (반환 컬럼 형식은 함수 docstring 참고)

4. API 키 관리
   - 네이버/TMAP 등 API 키는 `.env` 파일에 저장하고 절대 커밋하지 않습니다 (`.gitignore`에 포함됨)
   - 팀원 공유용으로 `.env.example` 에 키 이름만 적어 배포 예정
