# scripts

`data_accident_list` 데이터 수집용 스크립트를 모아둔 폴더입니다.

## accident_list.py

서울 안전누리(safecity.seoul.go.kr)의 "재난사고속보" 데이터를 API 호출로 수집하는 스크립트입니다.

### 무엇을 하는가

- `https://safecity.seoul.go.kr/news/acdnt/getAcdntList.do`를 호출해서 현재 등록된 재난·사고 목록(JSON)을 그대로 받아옵니다.
- 화면에 보이는 "재난사고속보" 팝업이 실제로 호출하는 내부 API로, 브라우저 개발자도구(Network 탭)에서 확인한 요청입니다.
- 받은 JSON을 가공 없이 그대로 `../raw/`에 저장합니다.

### 실행 방법

```bash
python accident_list.py
```

사전에 `requests` 패키지가 설치되어 있어야 합니다.

```bash
pip install requests
```

### 저장 결과

실행할 때마다 `accident_list_{오늘날짜}_{순번}.json` 형식으로 새 파일이 생깁니다. 같은 날 여러 번 실행하면 순번이 1, 2, 3...으로 늘어나고, 날짜가 바뀌면 다시 1부터 시작합니다. (실시간으로 계속 바뀌는 데이터라 매 실행 결과를 스냅샷으로 남기는 방식입니다.)

예: `accident_list_20260820_1.json`, `accident_list_20260820_2.json`

저장 위치: `data_accident_list/raw/`

### 참고

- 세션 쿠키(JSESSIONID)를 받기 위해 메인 페이지(`main.do`)를 먼저 한 번 방문한 뒤 API를 호출합니다.
- 과도한 반복 호출은 피하고, 몇 분~몇십 분 간격으로 실행하는 걸 권장합니다.