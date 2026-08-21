# Seoul Shieldus - 치안 및 안전 인프라 데이터

프론트엔드 팀원의 원활한 개발 및 지도 API 시각화를 위해 원천 데이터를 정제하여 구축한 **치안 인프라 데이터 JSON 파일**. 

---

## 파일별 데이터 명세

### 1. 자치구별 치안 안전 지수 및 통계
* **파일명:** `seoul_safety_index.json`
* **데이터 내용:** 구별 인구, 면적, 범죄율 및 이를 기반으로 산출된 종합 치안 안전 지수 통합 관리
* **활용도:** 자치구별 안전 등급 대시보드 및 요약 지표 출력

### 2. 안심귀갓길 상세 데이터
* **파일명:** `seoul_safe_paths.json`
* **데이터 내용:** 362개 노선별 읍면동명, 링크 길이 등 기본 정보와 하위 방범 시설물(안심벨, 보안등, 112 신고안전판 등)을 계층형(Hierarchy)으로 묶은 마스터 데이터
* **활용도:** 지도 위 안심귀갓길 폴리라인(경로) 렌더링 및 경로 내 포함된 안전 시설물 상세 정보 팝업

### 3. 가로등 위치 데이터
* **파일명:** `seoul_street_lights.json`
* **데이터 내용:** 서울시 전체 가로등의 관리번호 및 위도/경도(lat, lng) 포인트 좌표
* **활용도:** 야간 보행 안전을 위한 가로등 밀집도 시각화 및 개별 마커 렌더링

### 4. CCTV 상세 통계 데이터
* **파일명:** `seoul_cctv_stats.json`
* **데이터 내용:** 자치구별 전체 CCTV 수량 및 세부 목적별(방범, 어린이보호구역, 화재예방 등) 상세 수량 통계
* **활용도:** 자치구별 치안 인프라 비교 차트 및 목적별 비율(Pie, Bar chart 등) 시각화

### 5. 지구대 및 파출소 위치 데이터
* **파일명:** `seoul_jigudae.json`
* **데이터 내용:** 서울시 내 모든 지구대 및 파출소의 관서명, 유형(구분), 상세 주소 및 위도/경도(lat, lng) 좌표
* **활용도:** 사용자 위치 기반 가장 가까운 치안 센터 마커 표시 및 길찾기 연동

---
```md
# 3. 메인 실행 함수
def initialize_database():
    # 1) 테이블 생성
    create_all_tables()

    # 2) JSON 초기 데이터 적재 실행
    db = SessionLocal()
    try:
        # 데이터 폴더 기본 경로 (프로젝트 root 기준 data/processed/)
        base_data_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed"
        )

        # 5개 데이터 세트 초기화 및 데이터 적재
        seed_safety_index(db, os.path.join(base_data_dir, "seoul_safety_index(1).json"))
        seed_safe_routes(db, os.path.join(base_data_dir, "seoul_safe_paths(2).json"))
        seed_street_lights(
            db, os.path.join(base_data_dir, "seoul_street_lights(3).json")
        )
        seed_cctv_stats(db, os.path.join(base_data_dir, "seoul_cctv_stats(4).json"))
        seed_police_stations(db, os.path.join(base_data_dir, "seoul_jigudae(5).json"))

```
