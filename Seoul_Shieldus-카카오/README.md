# 프로젝트 정리 
주제 : 서울지역 보안 인프라 

# 프로젝트 목표
사용자가 지도 하나로 서울시 전체의 치안 상태를 한눈에 파악하고, 내 근처 파출소나 안심귀갓길을 찾아보게 만드는 것 
# 프로젝트 범위 
서울특별시 25개 자치구 전체

# 필요한 데이터 정의 

1. 서울시 지구대/ 파출소 (위치, 운영 시간 등 필요)
2. 서울시 CCTV 현황 (위치 등 필요하나 없을 수 있음)
3. 서울시 여성안심귀갓길 데이터 
4. 자치구별 인구 및 면적 데이터 
5. 서울 지역별 범죄율 (장소 ,수치 필요)
6. 안전 관련 공공시설물 설치현황(가로등 등) (위치, 장소별 개수 등 필요)

# 사용 api

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

1. 치안 인프라 데이터(공공API)
- cctv 수 / 지구대, 파출소 위치 / 여성안심귀갓길

2. 기초 통계 데이터(공공 데이터)
- 자치구별 인구수 및 면적

3. 치안 공지 및 텍스트 데이터(웹 스크래핑)
- 경찰청 및 서울시 치안 소식 / 안전  공지사항

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

4. API 키 관리 및 `.env` 설정
   - API 키는 프로젝트 루트의 `.env` 파일에 보관합니다.
   - 키 이름 예시 (`.env.example` 참고):
     ```env
     KAKAO_MAP_APP_KEY=발급받은_카카오_JS_앱키
     KAKAO_REST_API_KEY=발급받은_카카오_REST_API키
     TMAP_APP_KEY=발급받은_TMAP_앱키
     ```

5. Kakao Developers Web 도메인 설정
   - [Kakao Developers Console](https://developers.kakao.com/) > 내 애플리케이션 > 앱 설정 > 플랫폼 > Web
   - 사이트 도메인에 아래 주소를 등록해야 카카오 지도가 정상 렌더링됩니다.
     ```
     http://localhost:8501
     http://127.0.0.1:8501
     ```

6. 접속 주소 및 실행 방법
   - 실행 명령:
     ```bash
     streamlit run frontend/app.py
     ```
   - 로컬 접속 주소: `http://localhost:8501`

7. 문제 발생 시 점검 항목
   - **Kakao 지도 미표시**: `KAKAO_MAP_APP_KEY`가 JavaScript 키인지 확인하고(REST 키 금지), Kakao Developers 플랫폼 웹 도메인에 `http://localhost:8501`이 등록되어 있는지 확인합니다.
   - **TMAP 길찾기 오류**: `TMAP_APP_KEY` 설정 여부 및 TMAP 보행자 경로 서비스 신청 상태를 확인합니다.

