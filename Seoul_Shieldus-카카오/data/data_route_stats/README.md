# 여성안심귀갓길 · 인구/면적 데이터
 
## 폴더 구조
 
```
data_route_stats/
├── raw/            # 원본 데이터
└── processed/
    ├── saferoute_seoul.csv   # 안심귀갓길 현황
    └── stats_seoul.csv       # 인구·면적 통계
```
 
## saferoute_seoul.csv
 
| 컬럼 | 의미 |
|---|---|
| 자치구 | 서울시 25개 자치구 |
| 노선수 | 안심귀갓길 노선 개수 |
| 총길이 | 노선 총 길이(km) |
 
- 노선수: 최소 4개(양천구) ~ 최대 24개(강남구·성북구)
- 총길이: 최소 1.91km(양천구) ~ 최대 10.54km(강남구)
## stats_seoul.csv
 
| 컬럼 | 의미 |
|---|---|
| 자치구 | 서울시 25개 자치구 |
| 인구수 | 등록인구(명) |
| 면적 | 행정구역 면적(km²) |
 
- 인구수: 최소 127,819명(중구) ~ 최대 656,460명(송파구)
- 면적: 최소 9.96km²(중구) ~ 최대 46.97km²(서초구)
## 출처
 
- 여성안심귀갓길: (https://data.seoul.go.kr/dataList/OA-21695/S/1/datasetView.do)
- 등록인구: (https://data.seoul.go.kr/dataList/DT201004O020003/S/2/datasetView.do)
- 면적: (https://data.seoul.go.kr/dataList/DT201004O010001/S/2/datasetView.do)
## 비고
 
- 자치구명은 팀 표준 표기("OO구")로 통일
- 두 파일 모두 25개 자치구 전수 포함, 결측치·중복 행 없음
