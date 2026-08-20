# data_accident_list — 재난사고속보 데이터

서울시 안전누리(safecity.seoul.go.kr)에서 제공하는 실시간 재난·사고 속보 데이터입니다. 
미니 프로젝트 기획서 데이터 수집 방법의 "치안 공지 및 텍스트 데이터" 파트의 일환으로 수집했습니다.

## 폴더 구조

```
data_accident_list/
├── raw/
│ ├── accident_list_20260820_1.json
│ ├── accident_list_20260820_2.json
│ └── ...
└── scripts/
└── accident_list.py
```

`raw/`에는 `scripts/accident_list.py`를 실행할 때마다 생성되는 스냅샷 파일이 쌓입니다. 사고 목록은 계속 갱신되는 실시간 데이터라 한 파일에 덮어쓰지 않고, 실행 시점마다 별도 파일로 남깁니다.

## 데이터 출처

- 서울 안전누리 재난사고속보: https://safecity.seoul.go.kr/ (사고속보 팝업)
- 실제 호출 API: `POST https://safecity.seoul.go.kr/news/acdnt/getAcdntList.do`

## 파일 구조 (JSON)

응답은 `timeList` 배열 하나로 구성되어 있고, 배열 안 각 항목은 다음 필드를 가집니다.

| 필드 | 설명 |
|---|---|
| acdntSe | 사고구분 코드 (예: DHTY201) |
| acdntNm | 사고명 (예: 도로돌발_공사, 화재사고) |
| acdntId | 사고 고유 ID |
| title | 사고 제목 |
| message | 상세 내용 (위치·구간·상태 등 텍스트) |
| occurDate | 발생 일시 |
| locX / locY | 사고 위치 좌표 (위경도가 아닌 투영좌표계 값 — 지도에 쓰려면 좌표계 변환 필요) |

## 비고

- 실시간 API 특성상 호출 시점마다 목록 내용이 달라질 수 있습니다 (진행 중인 사고가 종료되거나 새 사고가 추가되는 식).
- `locX`/`locY`는 위경도가 아니라서, folium 등으로 지도에 표시하려면 pyproj로 좌표계 변환이 필요합니다 (정확한 EPSG 코드는 추후 확인 필요).
- 여러 스냅샷 파일을 하나로 합쳐 시계열 데이터로 만드는 정제 작업은 아직 진행 전입니다.