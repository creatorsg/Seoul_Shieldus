# 🛡️ 서울-쉴더스 (Seoul-Shielders) 웹 프레젠테이션 시스템

> **서울지역 보안 인프라 데이터 분석 및 안전지도 서비스**  
> 16:9 와이드 비율 기반 모듈형 프레젠테이션 & 데이터 시각화 웹 플랫폼

---

## 📁 전체 프로젝트 폴더 구조

```text
seoul-shielders/
├── index.html                   # 프레젠테이션 시작 포털 및 전체 슬라이드 뷰어
│
├── pages/                       # 10개 독립 슬라이드 HTML 페이지
│   ├── 01-intro.html            # 01. 프로젝트 소개 & 비전 (Design Anchor)
│   ├── 02-problem.html          # 02. 문제 정의 & 기획 배경 (절대건수 착시)
│   ├── 03-data.html             # 03. 공공데이터 수집 명세 (5대범죄, 인구, 가로등, CCTV)
│   ├── 04-analysis.html         # 04. 데이터 전처리 및 분석 방법론 (품질관리 원칙)
│   ├── 05-map.html              # 05. 서울시 치안 공간 정보 매핑 (GIS Multi-Layer)
│   ├── 06-infrastructure.html   # 06. 보안 인프라 상관성 분석 (도시 규모 효과 검증)
│   ├── 07-safety.html           # 07. 자치구별 지표 비교 및 범죄 유형 분포 (강남 vs 중구)
│   ├── 08-service.html          # 08. 안전지도 서비스 및 Streamlit 대시보드 아키텍처
│   ├── 09-result.html           # 09. 프로젝트 수행 회고 및 4대 과제 해결 (레슨런)
│   └── 10-closing.html          # 10. 라이브 시연 7단계 시나리오 & 질의응답 (Q&A)
│
├── components/                  # 재사용 UI 컴포넌트 템플릿
│   ├── header.html              # 공통 헤더 템플릿
│   ├── footer.html              # 공통 푸터 및 팀원 템플릿
│   ├── stat-card.html           # KPI 지표 카드 템플릿
│   ├── map-card.html            # 지도 시각화 카드 템플릿
│   └── chart-card.html          # 차트/통계 카드 템플릿
│
├── css/                         # 분리된 공통 스타일시트
│   ├── variables.css            # 전역 디자인 토큰 (색상, 폰트, 간격, 그림자)
│   ├── common.css               # 기본 리셋, 16:9 캔버스 스테이지, 유틸리티
│   ├── components.css           # 카드, 배지, 프로세스 플로우, 테이블
│   └── presentation.css         # 발표자 툴바, 썸네일 드로어, 단축키 모달, 애니메이션
│
├── js/                          # 프레젠테이션 인터랙션 엔진
│   ├── presentation.js          # 슬라이드 설정 목록, 페이지 전환, 단축키 제어
│   ├── navigation.js            # 플로팅 네비게이션 독 & 썸네일 드로어 자동 주입
│   └── data.js                  # 25개 자치구 데이터셋 로더 및 통계 연산 헬퍼
│
├── data/                        # 독립 JSON 데이터셋
│   ├── seoul-districts.json     # 서울 25개 자치구 인구·범죄·가로등·CCTV 통계
│   ├── police.json              # 경찰서/지구대/파출소 현황
│   ├── cctv.json                # 자치구별 방범 CCTV 데이터
│   └── safe-path.json           # 안심귀갓길 경로 및 시설물 데이터
│
└── README.md                    # 시스템 유지보수 및 확장 가이드
```

---

## 🚀 1. 프로젝트 실행 방법

1. 별도의 웹 서버 설치나 빌드 과정 없이 `seoul-shielders/index.html` 파일을 브라우저(Chrome, Edge, Safari 등)에서 더블클릭하여 바로 엽니다.
2. 개별 슬라이드(`pages/01-intro.html` ~ `10-closing.html`)를 직접 열어도 독립적으로 정상 작동합니다.

---

## ⌨️ 2. 프레젠테이션 조작 단축키

| 키 | 동작 | 설명 |
| :--- | :--- | :--- |
| `→` / `Space` / `PageDown` | **다음 슬라이드** | 다음 순서 슬라이드로 이동 |
| `←` / `Backspace` / `PageUp` | **이전 슬라이드** | 이전 순서 슬라이드로 이동 |
| `Home` / `End` | **첫 / 마지막** | 1페이지 또는 10페이지로 즉시 점프 |
| `F` | **전체화면** | 프레젠테이션 전체화면 모드 토글 |
| `T` | **목차 드로어** | 10개 슬라이드 전체 썸네일 목차 열기/닫기 |
| `M` | **테마 전환** | 다크 모드 ↔ 라이트 모드 전환 |
| `?` / `H` | **단축키 안내** | 키보드 가이드 팝업 |
| `Esc` | **닫기** | 열린 모달/드로어 닫기 |

---

## 🛠️ 3. 슬라이드 유지보수 가이드 (가장 중요)

### ① 페이지 추가 방법
1. `pages/` 폴더에 새 HTML 파일(예: `pages/11-future.html`)을 만듭니다.  
   (`components/`의 템플릿 또는 기존 `01-intro.html` 구조를 복사하여 내용 작성)
2. `js/presentation.js`의 `slides` 배열에 한 줄만 추가합니다:
   ```javascript
   {
       id: 11,
       file: "pages/11-future.html",
       title: "향후 발전 방향",
       sub: "실시간 IoT 비상벨 연계 및 지능형 안심 경로",
       category: "ROADMAP"
   }
   ```
   👉 **추가 완료!** `index.html` 목차, 플로팅 독 페이지 수, 썸네일 드로어에 자동 반영됩니다.

### ② 페이지 삭제 방법
1. `js/presentation.js`의 `slides` 배열에서 해당 항목을 삭제하거나 주석 처리합니다.
2. `pages/` 폴더에서 해당 HTML 파일을 삭제합니다.

### ③ 페이지 순서 변경 방법
- `js/presentation.js`의 `slides` 배열 순서만 원하는 대로 재배치하고 `id` 번호를 순서대로 정렬하면 끝납니다.

---

## 🎨 4. 디자인 및 색상 커스터마이징

모든 스타일은 `css/variables.css`의 CSS 변수로 중앙 집중 관리됩니다:

- **메인 컬러 변경**: `--color-primary` (기본 `#3b82f6`)
- **안전/민트 포인트 컬러 변경**: `--color-mint` (기본 `#10b981`)
- **경고/인프라 컬러 변경**: `--color-amber` (기본 `#f59e0b`)
- **배경색 변경**: `--slide-bg` (기본 `#0f172a`)
- **글래스 카드 투명도 조절**: `--card-bg` (`rgba(30, 41, 59, 0.75)`)

---

## 📊 5. 실제 데이터 및 지도 API 연결 방법

### ① 서울 25개 자치구 데이터 교체
- `data/seoul-districts.json` 파일을 열어 실제 통계청/경찰청 최신 JSON으로 교체하면 `js/data.js`가 자동으로 수치를 로드하여 통계를 산출합니다.

### ② 실제 지도 API (Leaflet / Folium / Mapbox) 연결
- 현재 `pages/05-map.html`의 `<div class="map-svg-container">` 영역을 `<div id="map"></div>`로 변경한 뒤 Leaflet.js 또는 GeoJSON 인스턴스를 마운트하면 됩니다.
- 데이터 레이어(경찰서, CCTV, 안심귀갓길)는 `data/police.json`, `data/cctv.json`, `data/safe-path.json`의 좌표(`lat`, `lng`)와 1:1 매핑되어 있습니다.
