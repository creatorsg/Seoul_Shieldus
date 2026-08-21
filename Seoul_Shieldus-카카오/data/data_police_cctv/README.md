# data_police_cctv — 지구대/파출소 · CCTV 데이터 (담당: 정세진)

서울쉴더스 프로젝트의 "치안 인프라" 파트 중 1) 지구대/파출소 현황, 2) 자치구별 CCTV 설치현황 데이터
수집·정제 결과물입니다.

## 폴더 구조

```
data_police_cctv/
├── raw/
│   ├── police_raw.csv        # 원본: 경찰청_전국 지구대 파출소 주소 현황
│   └── cctv_raw.xlsx         # 원본: 서울시 자치구 (목적별) CCTV 설치현황
├── scripts/
│   ├── .env                  # KAKAO_API_KEY (git에 올리지 않음)
│   ├── clean_police.py       # 1) 지구대/파출소 정제
│   ├── geocode_police.py     # 1) 위도/경도 채우기 (카카오 지오코딩)
│   ├── clean_cctv.py         # 2) CCTV 정제
│   └── verify_result.py      # 1) 최종 결과 검증
└── processed/
    ├── jigudae_seoul.csv     # 1) 최종 결과물
    ├── jigudae_seoul_unmatched.csv  # (있는 경우) 자치구 추출 실패 행
    └── cctv_seoul.csv        # 2) 최종 결과물
```

## 데이터 출처

- 지구대/파출소: [경찰청_전국 지구대 파출소 주소 현황](https://www.data.go.kr/data/15077036/fileData.do) (공공데이터포털)
- CCTV: [서울시 자치구 (목적별) CCTV 설치현황](https://data.seoul.go.kr/dataList/OA-2722/F/1/datasetView.do) (서울 열린데이터광장)
- 위도/경도 변환: [카카오 로컬 API](https://developers.kakao.com/docs/latest/ko/local/dev-guide) (주소 검색 / 키워드 검색)

## 사전 준비

1. `pip install -r requirements.txt`
2. [카카오 디벨로퍼스](https://developers.kakao.com/)에서 앱 생성 후 REST API 키 발급
   ([앱] > [플랫폼 키] > [REST API 키], [제품 링크 관리]에서 카카오맵 활성화 필요)
3. `scripts/.env` 파일 생성 후 아래 한 줄 작성 (절대 git에 커밋하지 말 것)
   ```
   KAKAO_API_KEY=발급받은_REST_API_키
   ```
4. `raw/` 폴더에 원본 파일 두기 (파일명은 위 폴더 구조와 동일하게)

## 실행 순서

`scripts` 폴더 안에서 순서대로 실행합니다.

```
python clean_police.py      # raw/police_raw.csv -> processed/jigudae_seoul.csv (위도/경도는 빈 값)
python geocode_police.py    # jigudae_seoul.csv의 위도/경도를 카카오 API로 채움
python verify_result.py     # 최종 결과 검증 (25개 자치구, 결측치, 좌표 범위, 중복)
python clean_cctv.py        # raw/cctv_raw.xlsx -> processed/cctv_seoul.csv
```

## 컬럼 설명

### jigudae_seoul.csv

| 컬럼 | 설명 |
|---|---|
| 자치구 | 25개 자치구명 (예: 강남구) |
| 관서명 | 지구대/파출소 정식 명칭 (예: 신림파출소) |
| 구분 | 지구대 / 파출소 |
| 주소 | 도로명 주소 |
| 위도 | WGS84 위도 |
| 경도 | WGS84 경도 |

- 총 243행, 25개 자치구 전수 포함
- `jigudae_seoul_unmatched.csv`가 있다면 주소에서 자치구를 추출하지 못한 행이니 수동 확인 필요

### cctv_seoul.csv

| 컬럼 | 설명 |
|---|---|
| 자치구 | 25개 자치구명 |
| CCTV수량 | 자치구별 CCTV 총 설치 대수 (필수 스펙 컬럼) |
| 범죄예방수사_소계 / 방범 / 어린이보호구역 / 공원놀이터 / 쓰레기무단투기 / 시설안전화재예방 / 교통단속 / 교통정보수집분석 / 기타다른법령 | 목적별 세부 대수 (참고용, 스펙 필수는 아님) |

- 25개 자치구 전수, 합계 검산(원본 총계 124,581 = 25개 구 합산) 통과
- 원본에 "동대문/서대문/영등포"로 "구" 표기가 누락되어 있어 자동 보정함

## 검증 결과 요약

- 25개 자치구 전수 확인 (두 데이터 모두)
- 필수 컬럼 결측치 0건
- 지구대/파출소 위도/경도 전체 지오코딩 성공
- CCTV 합계 검산 일치
- 중복 행 없음
