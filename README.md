# 🛡️ Seoul Shieldus

> 서울시 공공데이터와 지도 API를 활용한 **서울 생활안전 정보 통합 서비스**


## 🌐 서비스

### ▶ 실제 배포 서비스 카카오 버전

https://inchan-jv29njctxrhykcy8zazpj9.streamlit.app/

> Streamlit Cloud를 이용하여 실제 서비스 형태로 배포했습니다.



## 📌 주요 기능

| 기능 | 설명 |
|---|---|
| 🗺️ 시설 찾기 | 서울 지역 경찰시설 및 안전시설 위치 조회 |
| 📍 지도 시각화 | Kakao Maps API 기반 지도 및 마커 표시 |
| 🧭 길찾기 | 출발지와 목적지를 입력하여 경로 확인 |
| 📊 안전 데이터 | 서울시 공공데이터 기반 지역별 안전정보 제공 |
| 🌙 다크 모드 | 보안 관제센터 콘셉트의 Dark UI |
| ☁️ 웹 배포 | Streamlit Cloud를 통한 실제 서비스 배포 |



## 🛠️ 기술 스택

| 구분 | 기술 |
|---|---|
| Frontend | Streamlit |
| Language | Python |
| Map | Kakao Maps API |
| Navigation | TMAP API |
| Data | 서울시 공공데이터 |
| Data Processing | Pandas |
| Deployment | Streamlit Cloud |
| Version Control | Git / GitHub |



## 🗺️ Kakao Maps API

본 프로젝트에서는 **Kakao Maps API**를 사용하여 웹 기반 지도와 위치 데이터를 구현했습니다.

Kakao 지도 API는 웹사이트 및 모바일 애플리케이션에서 지도 서비스를 구현할 수 있도록
지도, 장소 검색, 좌표 등의 기능을 제공합니다.

공식 문서:

https://apis.map.kakao.com/

### API 발급

1. Kakao Developers 접속
2. 애플리케이션 생성
3. **JavaScript 키(APP KEY)** 발급
4. 플랫폼 → Web 플랫폼 등록
5. 실제 서비스 도메인 등록

### 도메인 설정 예시

```text
http://localhost:8501
https://inchan-jv29njctxrhykcy8zazpj9.streamlit.app
```

## 🚗 TMAP API
길찾기 및 경로 관련 기능에는 SK Open API / TMAP API를 활용할 수 있도록 구성했습니다.

### 공식 사이트:
```txt
https://openapi.sk.com/products/calc?svcSeq=4&menuSeq=5
```
### API 발급
1. SK Open API 회원가입
2. TMAP 관련 API 상품 선택
3.프로젝트/애플리케이션 생성
4. API Key 발급
5. 사용할 API 및 호출 한도 확인
6. 발급받은 Key를 환경변수 또는 Streamlit Secrets에 등록
TMAP에서는 지도, 경로 안내, 지오코딩, 장소 검색 등 다양한 API를 제공합니다.

## 🔐 환경변수 설정
API Key는 GitHub에 직접 업로드하지 않습니다.

로컬 개발 환경에서는 .env를 사용합니다.
```txt
KAKAO_MAP_APP_KEY=발급받은_카카오_KEY
KAKAO_REST_API_KEY=발급받은_카카오_REST_KEY
TMAP_APP_KEY=발급받은_TMAP_KEY
NAVER_MAPS_CLIENT_ID=발급받은_NAVER_CLIENT_ID
```
.env는 .gitignore에 등록합니다.
```txt
.env
.env.*
!.env.예시
__pycache__/
*.py[cod]
```

## ☁️ Streamlit Cloud Secrets
Streamlit Cloud 배포 시에는 .env를 업로드하지 않고
App Settings → Secrets에 등록합니다.
