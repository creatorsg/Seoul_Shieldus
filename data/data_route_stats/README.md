# 여성안심귀갓길 · 인구/면적 데이터
 
## 폴더 구조
 
```
data_route_stats/
├── raw/            # 원본 데이터
└── processed/
    ├── 3. saferoute_seoul_location.csv # 안심귀갓길 시설물 위치
    ├── 3. saferoute_seoul.csv   # 안심귀갓길 현황
    └── 4. stats_seoul.csv       # 인구·면적 통계
```
 
## saferoute_seoul.csv
 
| 컬럼 | 의미 |
|---|---|
| 자치구 | 서울시 25개 자치구 |
| 노선수 | 안심귀갓길 노선 개수 |
| 총길이 | 노선 총 길이(km) |
 
- 노선수: 최소 4개(양천구) ~ 최대 24개(강남구·성북구)
- 총길이: 최소 1.91km(양천구) ~ 최대 10.54km(강남구)
## saferoute_seoul_location.csv

| 컬럼 | 의미 |
|---|---|
| 자치구 | 서울시 25개 자치구 |
| 안심귀갓길 명 | 노선명 (예: 강남안심01) |
| 위도 | WGS84 위도 |
| 경도 | WGS84 경도 |

- 원본(`raw/saferoute_location_raw.csv`, 안심귀갓길 안전시설물 데이터)의 `포인트 wkt`를 위도/경도로 분리하고, 시군구명을 팀 표준 표기로 정리한 파일
- 총 11,883행 (노선 1개당 여러 시설물 위치가 포함된 시설물 단위 데이터)
- 자치구 가나다순 → 안심귀갓길명 가나다·숫자순으로 정렬
- `saferoute_seoul.csv`(자치구 단위 노선수·총길이)와는 단위가 달라 별도 파일로 유지, 필요 시 `자치구` 컬럼으로 조인 가능
## stats_seoul.csv
 
| 컬럼 | 의미 |
|---|---|
| 자치구 | 서울시 25개 자치구 |
| 인구수 | 등록인구(명) |
| 면적 | 행정구역 면적(km²) |
 
- 인구수: 최소 127,819명(중구) ~ 최대 656,460명(송파구)
- 면적: 최소 9.96km²(중구) ~ 최대 46.97km²(서초구)
## 출처
 
- 안심귀갓길: (https://data.seoul.go.kr/dataList/OA-21695/S/1/datasetView.do)
- 안심귀갓길 안전시설물(위치): (https://data.seoul.go.kr/dataList/OA-21697/S/1/datasetView.do)
- 등록인구: (https://data.seoul.go.kr/dataList/DT201004O020003/S/2/datasetView.do)
- 면적: (https://data.seoul.go.kr/dataList/DT201004O010001/S/2/datasetView.do)
## 비고
 
- 자치구명은 팀 표준 표기("OO구")로 통일
- saferoute_seoul.csv, stats_seoul.csv 두 파일은 25개 자치구 전수 포함, 결측치·중복 행 없음
- saferoute_seoul_location.csv는 시설물 단위 데이터라 같은 자치구·노선명이 여러 행에 반복됨
