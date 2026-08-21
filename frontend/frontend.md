# 프론트엔드 정리 문서

`app.py`/`styles.py`/`constants.py`에는 "무엇을 하는지"만 간단히 적어두고, "왜 이렇게 했는지"
(설계 배경 · 트레이드오프 · 실제로 겪은 버그와 그 원인)는 전부 이 문서에 모아둔다. 코드를 고치기
전에 관련 섹션을 먼저 읽으면, 왜 지금 이렇게 짜여 있는지 없이 "더 깔끔해 보이는" 방향으로 고쳤다가
같은 버그를 다시 만드는 걸 막을 수 있다.

## 파일 구성

- `app.py` — 화면 조립. 페이지 렌더링 함수(`render_*`)와 `main()`만 있다.
- `styles.py` — CSS/HTML 문자열 상수 모음.
- `constants.py` — 화면 여러 곳에서 재사용하는 데이터 형태 상수 모음.
- `data_access.py` — 데이터 로딩 계층 (DB 우선 조회, JSON 폴백).
- `colors.py` — 점수 → 색상 매핑 단일 소스.
- `naver_map.py` — 네이버 지도 HTML 생성.
- `route_finder.py` — TMAP 경로 조회.

---

## styles.py

### PRETENDARD_FONT_CSS
전체 화면에 Pretendard 폰트를 적용한다. `<link>`가 `<head>`에 로드되고 나면, 실제 font-family
지정은 body 안에 있는 이 `<style>` 블록만으로도 문서 전체에 적용된다(CSS는 삽입 위치와 무관하게
셀렉터에 매칭되는 모든 요소에 적용됨). code/pre류는 모노스페이스를 유지해 코드 블록이 깨지지
않게 한다.

### SIDEBAR_CSS
사이드바(secondaryBackgroundColor, 진한 남색)와 본문(backgroundColor, 거의 흰색)을 분리했다.
Streamlit 테마는 textColor 하나를 본문/사이드바에 공통으로 쓰기 때문에, 본문 기준(어두운 남색)
글자색이 사이드바에서는 그대로 안 보인다 - 사이드바 안에서만 밝은 글자색으로 덮어쓴다.

브랜드 워드마크를 stLogoSpacer로 옮긴 뒤(`_inject_head_scripts`) 원래 자리인
`stSidebarUserContent`는 항상 빈 채로 남는다 - Streamlit이 이 요소에 "남은 세로 공간을 채우는"
크기 규칙을 갖고 있어서, 비어 있어도 넓은 여백을 차지한다. 그 여백을 접는다
(`flex: none; min-height: 0; height: 0;`).

로고를 화면 크기와 무관하게 항상 사이드바 좌측 하단에 고정한다(`main()`의 `st.sidebar` 블록
참고). `position:absolute`의 기준(containing block)이 되도록 사이드바 자체에
`position:relative`를 준다. `<br>`을 여러 개 넣어 로고를 아래로 밀어내던 예전 방식은 화면(사이드바)
높이에 따라 "얼마나 내려가는지"가 달라져서, 화면이 큰 모니터에서는 로고가 하단에 못 닿고 중간에
떠 있는 문제가 있었다 - `.sidebar-logo-marker` 마커 + `:has()`로 항상 정확히 같은 자리(16px,
16px)에 고정한다.

### MAP_CARD_CSS
지도(folium/네이버 지도)는 모두 iframe 기반 커스텀 컴포넌트(`stCustomComponentV1`)로
렌더링되는데, 기본은 radius 0px로 페이지에 그냥 얹혀있는 모양이다. 홈 화면 카드와 같은 12px
코너 + 옅은 테두리로 감싸서, 세 지도(히트맵/시설 찾기/길찾기) 모두 같은 "카드" 톤으로 보이게
통일한다.

### HIDE_STREAMLIT_CHROME_CSS
Streamlit 기본 UI 중 "이거 Streamlit으로 만들었어요" 티가 나는 요소를 숨긴다.
`toolbarMode="minimal"`(`.streamlit/config.toml`)이 Deploy 버튼/개발자 메뉴는 이미 지워주지만,
하단 "Made with Streamlit" 푸터와 헤더 위 무지개색 장식 줄은 config로 못 지워서 CSS로 숨긴다.

`_inject_head_scripts()`/`_restore_scroll_position()`/`_replay_score_bar_animations()`는
화면에 아무것도 안 그리고 streamlit_js_eval로 스크립트만 실행하는 용도인데, 그 컴포넌트(iframe)가
기본 높이(~25px)를 차지해서 페이지 맨 위(제목 위)에 빈 상자가 쌓여 보이는 문제가 있었다. 각
컴포넌트의 key로 만들어지는 class(`st-key-...`)를 잡아서 높이를 0으로 접는다.

`stHeader`(사이드바 접기 버튼이 있는 상단 바)는 `position:absolute`라 실제 여백을 차지하지
않는다 - 진짜 빈 공간의 정체는 `stMainBlockContainer`의 기본 `padding-top`(96px, 헤더 높이
60px보다 훨씬 큼)이다. 헤더 버튼이 안 가려질 만큼만(64px) 남기고 나머지는 줄인다.

### PAGE_TRANSITION_CSS
페이지가 바뀔 때 화면이 뚝 끊기지 않고 살짝 떠오르듯 나타나게 하는 CSS. `st.navigation`으로
다른 페이지로 이동하면 이전 페이지의 엘리먼트가 통째로 사라지고 새 페이지 엘리먼트가 새로
마운트되기 때문에, 이 애니메이션이 그 타이밍에 자동으로 재생된다. (같은 페이지 안에서 위젯만
바꾸는 리런일 때는 Streamlit이 기존 엘리먼트를 재사용할 수도 있어서 100% 매번 재생을 보장하진
않는다 - 완벽한 SPA 전환 효과가 아니라 "느낌만 내는" 수준.)

⚠ iframe(`:has(iframe)`)이 들어있는 박스는 애니메이션 대상에서 제외한다. 네이버 지도처럼 "로드되는
순간 자기 컨테이너 크기를 한 번 재서" 초기화하는 JS 위젯은, 그 순간 부모가 transform 애니메이션
중이면 크기를 잘못 재거나 레이아웃이 안 잡힌 채로 초기화가 끝나버려 이후 다시 안 살아날 수 있다
(실제로 "시설 찾기" 지도가 이 애니메이션 때문에 안 뜨는 문제가 있어서 이렇게 제외했다).

### SELECTBOX_CSS
`st.selectbox`(예: 히트맵 "지역별 상세"의 자치구 선택, 길찾기의 목적지 선택) 위젯은 배경색을
테마의 secondaryBackgroundColor(사이드바에 쓰는 진한 남색 #1E3A5F)에서 그대로 물려받는다.
텍스트는 어두운 textColor(#0F172A)라 남색 배경 위에서 안 보인다 - 이 위젯만 배경을 흰색으로
바꿔서(텍스트는 원래도 어두운 색이라 흰 배경에서 자연스럽게 잘 보인다) 해결한다.

### VIEW_TOGGLE_CSS
"보기 방식"(전체 확인 / 지역별 상세) 라디오를 segmented-button 탭처럼 보이게 한다.
⚠ Streamlit 내부 DOM/testid는 버전마다 바뀔 수 있다. 이 앱이 이미 `stElementContainer` 같은
비교적 최신 testid를 쓰고 있어 이것도 같은 세대 기준(`stRadio`)으로 맞췄지만, 실제 반영 후
브라우저 devtools로 한 번은 구조를 확인해보는 게 안전하다.

### GPS_WAIT_SPINNER_HTML
GPS 위치를 기다리는 동안 보여줄 스피너. `st.spinner()`는 "with 블록 안 코드가 실행되는 동안"만
애니메이션이 도는데, 위치 권한 대기는 브라우저 응답을 기다리며 리런 사이사이에 걸쳐 있는 대기라
`st.spinner`로는 애니메이션이 뚝뚝 끊긴다. 대신 매 리런마다 완전히 똑같은 HTML/CSS를 그리는
방식을 쓰면, 브라우저 쪽 CSS 애니메이션은 리런과 무관하게 계속 자연스럽게 돌아간다.

### SCORE_BAR_CSS / `_replay_score_bar_animations()`
점수 막대가 0%에서 실제 값까지 좌→우로 차오르는 애니메이션. 목표 너비(%)는 자치구마다 달라서
공유 스타일시트에 고정값으로 못 박을 수 없다 - CSS 커스텀 프로퍼티(`--fill-width`)를 막대마다
인라인으로 넘기고, keyframe의 도착 지점(to)에서 그 변수를 읽게 한다. 색은 그대로
`score_to_color` 값을 쓰고(색 기준 변경 없음), 채워지는 움직임만 추가한 것이다.

`_replay_score_bar_animations()`가 매 리런마다 이 애니메이션을 강제로 다시 재생시키는 이유:
처음 자치구를 고를 때만 애니메이션이 재생되고 그다음부터 안 재생되는 문제가 있었다 - 원인은
Streamlit이 같은 `st.markdown()` 호출 "자리"에 대해 매번 새 DOM 노드를 만드는 게 아니라 기존
노드를 재사용하면서 style만 고쳐 쓴다는 점이다(내용 문자열이 달라져도 노드 자체는 그대로). CSS
애니메이션은 노드가 처음 생성될 때만 자동 재생되는 특성이 있어서, 재사용된 노드는 style이
바뀌어도 애니메이션이 다시 돌지 않는다.

표준 트릭(animation을 none으로 껐다가 강제로 reflow를 한 번 읽은 뒤 다시 켜기)으로 매번 강제
재시작시킨다. `_restore_scroll_position()`과 같은 이유로 key를 세션 카운터로 계속 바꿔서 매
리런마다 이 streamlit_js_eval 자체가 실행되게 한다(직전과 완전히 같은 JS 문자열이면 재실행을
건너뛰는 특성이 있어서) - `want_output=False`라 리턴값이 없으니
`_restore_scroll_position`에서 겪었던 무한 리런 위험은 없다.

### DISTRICT_DETAIL_CSS
자치구 상세 패널의 소제목 3개(구 상세/안심지수/CCTV 목적별 설치 현황) 글씨 크기를 통일한다.
"안심지수"는 `st.metric`의 라벨이라 기본이 14px(캡션 수준)로 작게 나오고, "CCTV 목적별 설치
현황"은 h5(20px)라 "구 상세" h4(24px)보다 한 단계 작다 - 셋 다 24px/굵게로 맞춘다.

### GLASS_CARD_CSS
안심지수 섹션/CCTV 목적별 설치 현황 섹션을 반투명 유리(glass) 박스로 감싼다. 두
`st.container(border=True)`를 서로 구분 없이 똑같은 유리 스타일로 골라내려고, 각 컨테이너 맨
앞에 숨겨진 마커(`.glass-card-marker`)를 하나 심고 `:has()`로 그 마커를 가진 컨테이너만 골라
스타일을 건다.

### HOME_CARD_CSS
홈 화면 기능 카드(`st.container(border=True)`)의 radius를 12px로 맞춘다. Streamlit 기본
bordered container radius(테마 baseRadius 기준, 보통 8px)는 그대로 두면 다른 화면의 카드/모달과는
맞지만 홈 소개 카드에는 살짝 각져 보여서, 이 페이지 안에서만 살짝 더 둥글게 조정한다. 그림자는
원래도 없어서(플랫 스타일) box-shadow는 명시적으로만 none을 못박아 둔다.

호버 시 카드가 살짝 떠오르고(translateY) 테두리가 그 카드의 서비스 색(accent)으로 진해지게 해서
그림자 없이도 "클릭 가능한 카드"라는 느낌을 준다. 3개 카드가 각각 다른 accent를 쓰기 때문에,
`nth-of-type`으로 같은 행(`stHorizontalBlock`)의 1/2/3번째 컬럼을 구분해서 색을 다르게 건다 -
이 CSS는 `render_home_page` 안에서만 주입되므로 다른 화면의 `st.columns`에는 영향이 없다.

---

## constants.py

### CCTV_PURPOSE_FIELDS
`get_cctv_stats()`의 CCTV_STATS_COLUMNS 중 "구"/"총_CCTV"/"방범_합계"를 뺀 목적별 세부 8개만
막대그래프로 보여준다.

---

## app.py

### `_warn_missing_env`
API 키 등 `.env` 설정이 빠졌을 때 공통 문구로 경고한다. "설정을 안 해서 그런 것"과 "시도했는데
실패한 것"을 구분하려고, 이건 `st.warning`(주의)만 쓰고 실제 호출 실패는
`st.error`(`route_finder.fetch_route`)로 분리해뒀다.

### `_render_score_bar`
`st.progress`는 막대 색이 테마 색 하나로 고정이라 점수가 높든 낮든 같은 색으로 보여서, 점수에
따라 색(빨강~초록)이 바뀌게 직접 HTML로 그린다.

### `render_ranking_table`
자치구 랭킹 표에 안심지수 색상을 입힌다. 색은 새로 정하지 않고 `colors.score_to_color`를 그대로
쓴다 - 사이드바 점수바/지도와 같은 기준으로 읽히게 하기 위해서다. 배경은 "22"(약 13% 불투명도)
접미사를 붙여 옅게 깔아서, 글자 대비를 해치지 않으면서 색만 살짝 보이게 한다.

### `render_district_detail` — CCTV 소제목
점수 막대 섹션과 간격을 더 벌리려고(요청사항) 기본 heading 대신 `margin-top`을 직접 준 div로
바꿨다 - font-size/weight는 "구 상세"(h4)와 같은 24px/600으로 맞춘다.

### `render_district_detail` / `_sorted_cctv_purpose_counts` — `sort=False, horizontal=True`
`sort=False`가 중요하다: `st.bar_chart`는 기본값(`sort=True`)일 때 Altair가 카테고리(구매목적명)를
알아서 다시 정렬해버려서, 값(대수) 기준 내림차순으로 미리 만들어둔 dict 순서가 무시되고 조용히
다른 순서(사실상 알파벳/가나다순)로 그려진다. `sort=False`를 줘야 넘겨준 dict 순서 그대로("많은
순") 막대가 그려진다.

`horizontal=True`도 같이 준다: 세로 막대(기본값)는 "방범용"/"무단투기단속용"처럼 4글자 이상인
라벨이 가로 폭에 안 들어가서 Altair가 자동으로 90도 눕혀버린다. 막대를 가로로 눕히면 목적명이
y축 왼쪽에 원래 방향(가로) 그대로 나오기 때문에 이 문제가 자체로 해결된다.

### `_sorted_cctv_purpose_counts`
CCTV 목적별 대수를 많은 순으로 정렬해서 반환한다. `CCTV_PURPOSE_FIELDS`에 적어둔 순서(방범→
어린이보호→...→기타) 그대로 막대그래프를 그리면 구마다 값이 들쭉날쭉이라 막대 높이가 뒤죽박죽으로
보인다. 값 기준 내림차순으로 정렬해두면 어느 구를 보든 "가장 많이 설치된 목적이 왼쪽부터" 순서로
읽혀서 비교하기 쉽다. dict의 삽입 순서를 `st.bar_chart`가 그대로 x축 순서로 써주기 때문에, 여기서
미리 정렬한 순서대로 dict를 만들어주기만 하면 된다.

### `_geo_with_score_properties`
`GeoJsonTooltip`/`GeoJsonPopup`은 항상 geojson feature의 properties만 읽는다 - `Choropleth`에
따로 넘긴 `data=df`는 색칠(fill-color 매칭)에만 쓰이고 툴팁/팝업 쪽에서는 안 보인다. 그래서
호버/클릭했을 때 점수까지 같이 보여주려면, 지도를 그리기 전에 df의 안심지수를 구 이름으로 매칭해서
geojson properties 안에 미리 넣어둬야 한다. 원본 geo(= `@st.cache_data`로 캐싱된 객체)를 그대로
고치면 캐시에 값이 계속 누적/오염될 수 있어 깊은 복사본을 만들어 고친다.

### `_add_district_labels`
자치구 이름을 각 자치구 중심점에 고정 텍스트로 올린다 (지금까지는 색으로만 구분되던 것).
DivIcon으로 만든 라벨이라 클릭/호버 이벤트를 가로채지 않도록 `pointer-events:none`을 줘서,
라벨 아래에 깔린 히트맵 폴리곤의 클릭/호버는 그대로 통과되게 한다.

### `render_index_page`
Leaflet은 지역(폴리곤)을 클릭 가능한 SVG `<path>`로 그리는데, 클릭하면 그 `<path>`에 브라우저
포커스가 잡혀서 기본 포커스 표시(검은 네모 테두리, outline)가 뜬다 - 키보드 접근성을 위한 브라우저
기본 동작이라 folium/Leaflet 옵션으로는 못 끄고, 지도 iframe 안에 CSS를 직접 넣어야 한다.
`st_folium`은 이 HTML을 그대로 iframe으로 렌더링하므로, `<head>`에 스타일을 하나 추가해서 그
포커스 테두리만 지운다.

지도 배색: RdYlGn(낮은 안심지수=위험은 빨강, 높은 안심지수=안전은 초록)으로 직관적으로 읽히는
배색을 쓴다. `highlight=True`: 마우스가 올라간(호버된) 칸의 테두리를 굵게, 채우기를 더 진하게
바꿔서 "지금 이 칸을 가리키고 있다"는 게 시각적으로 보이게 한다 (`folium.Choropleth` 내장 기능 -
기본값은 line_weight+2, fill_opacity+0.2). 원래는 색으로 칠해진 구가 다 똑같이 밋밋해서 어느 구
위에 커서가 있는지 구분이 안 됐는데, 이 옵션 하나로 자체 해결된다.

`highlight=True`는 "칸 자체를 강조해서 보여주는" 기능이고, 툴팁/팝업은 별개로 "이름/점수 텍스트를
보여주는" 기능이라 서로 안 겹친다. `Choropleth`가 이미 만든 geojson 레이어에 그대로 얹는다 -
별도 `GeoJson` 레이어를 하나 더 추가하면 폴리곤 데이터를 브라우저로 두 번 보내는 셈이라
비효율적이다. 모바일은 호버가 없으니 클릭해도 같은 정보(`GeoJsonPopup`)가 뜨게 둘 다 붙인다.

(참고: 예전 버전은 `folium.Choropleth` 대신 `folium.GeoJson` + 직접 만든 style_function/범례를
썼다. 지금은 `Choropleth` 내장 기능(자체 범례 + highlight)으로 리팩터링해서 코드가 더 짧다.)

### `_facility_display_table`
시설 찾기 표에 위도/경도 대신 사용자에게 실제로 쓸모 있는 정보(구/주소/범죄안전 점수)를 보여준다.
위도/경도는 애초에 지도에 마커 찍을 때 좌표로 쓰려던 값이지 사용자가 표에서 볼 이유가 없다는
피드백을 반영했다. df(자치구별 안심지수 점수표)의 범죄안전_점수를 "구" 기준으로 매칭해 붙인다.

(참고: 예전 버전은 정규화 점수 대신 원본 범죄율(`CRIME_RATE_COLUMN`)을 보여줬다 - "0점"만 보면
왜 0점인지 감이 안 온다는 이유였는데, 이후 정규화 점수로 되돌리는 방향으로 다시 피드백을
반영했다.)

### `render_route_page` — `tmap_app_key`
`TMAP_APP_KEY`를 상수로 들고 있지 않고 매번 `get_tmap_app_key()`로 새로 읽는다 - `.env`를 고친
뒤 서버를 완전히 재시작하지 않고 리런만 해도 최신 키가 바로 반영되게 하기 위해서다
(`route_finder.get_tmap_app_key()`의 docstring에 이 문제가 왜 생기는지 자세히 적혀있다).

### `render_home_page`
페이지 상단 `st.title("서울 쉴더스 : ...")`은 모든 페이지에 공통이라 여기서 위치를 바꿀 수 없다 -
대신 이 페이지 콘텐츠(사진 이하)를 아래로 밀어서 제목과의 간격을 벌린다.

공간이 넉넉한 홈 히어로에는 원본 크레스트(텍스트 배너 포함)를 그대로 쓴다 - 사이드바 아이콘과
달리 여기선 디테일이 뭉개질 걱정이 없다. `st.image`는 기본 좌측 정렬이라, 좌우로 빈 컬럼을 두는
3분할(1:12:1) 레이아웃으로 가운데 컬럼에만 넣어서 중앙 정렬한다.

`hero.png`/`logo.png` 같은 상대경로는 `streamlit run`을 어느 폴더에서 실행했느냐(cwd)에 따라
찾는 위치가 달라진다 - 리포 루트에서 실행하면 `frontend/hero.png`를 못 찾아 `MediaFileStorageError`가
난다(실제로 겪은 버그). `BASE_DIR`(리포 루트, `data_access.py`에서 정의)를 기준으로 절대경로를
만들어서 어디서 실행하든 항상 같은 파일을 가리키게 한다.

이모지(🛡️📍🧭) 대신 인라인 SVG 아웃라인 아이콘을 쓴다 - 이모지는 OS/브라우저마다 모양이 달라지고
만화 같은 느낌이 나서, 사이드바 내비게이션과 같은 계열(Material Symbols 아웃라인 톤)의 SVG로
바꿔 더 "제품다운" 느낌을 준다. stroke 색을 accent로 지정해서 배지 배경(같은 accent의 10%
불투명도)과 세트로 보이게 한다.

### `_restore_scroll_position`
(베스트 에포트) Streamlit은 위젯 조작 등으로 리런될 때마다 본문 스크롤을 맨 위로 되돌리는데,
이건 Streamlit 자체 프레임워크 동작이라 앱 코드에서 끌 수 있는 옵션이 없다. 대신
streamlit_js_eval로 상위 문서(`window.parent`)의 실제 스크롤 컨테이너(`stMain`)에 스크롤 위치를
`sessionStorage`에 저장했다가 복원하는 리스너를 붙여서 흉내만 낸다.

streamlit_js_eval 컴포넌트 소스를 직접 확인해보니, "직전 리런과 완전히 똑같은 JS 문자열"이면
재실행 자체를 건너뛰는 구조다. 그래서 매 리런마다 반드시 다시 실행되도록 key를 세션 카운터로
계속 바꿔서 컴포넌트를 매번 새로 마운트시킨다.

⚠ **사고 이력**: 실제로 배포해서 써보니 이 방식이 심각한 버그를 냈었다. streamlit_js_eval처럼
"값을 돌려주는" 커스텀 컴포넌트는, 이전과 다른 값을 Python에 보고할 때마다 Streamlit이 그 값을
반영하려고 스크립트를 다시 리런시킨다. 그런데 매 리런마다 key를 새로 바꾸면 그때마다 "새 위젯"이
되어서 이전 리턴값 캐시가 없으니, 이 컴포넌트가 응답을 보낼 때마다 매번 "값이 바뀌었다"고
처리돼 리런이 또 걸리고, 그 리런이 다시 새 key를 만들고... 하는 식으로 사용자 조작 없이도 초당
3~4번씩 무한 리런되는 루프가 생겼다 (실측: 8초에 28번 리런). 이 루프가 길찾기 페이지에서 돌면
`fetch_route()`가 그만큼 반복 호출돼서 TMAP API가 429(요청 과다)를 뱉는 원인이 됐다.

**고친 방법**: `want_output=False`를 줘서 이 컴포넌트가 아예 Python에 값을 돌려보내지 않게 한다
(streamlit_js_eval 패키지 프론트엔드 코드 기준 - `want_output`이 False면 `sendDataToPython` 자체를
호출 안 함). 그러면 "리턴값이 바뀌어서 리런을 유발"할 방법이 없어지므로, key를 매번 바꿔서 JS를
강제로 재실행시키는 건 그대로 유지해도 안전하다 - 실행은 여전히 매 리런마다 되지만(스크롤 복원
자체는 계속 시도됨), 그 실행 결과가 Streamlit으로 다시 흘러들어가서 리런을 만드는 순환 고리만
끊었다.

⚠ 이 세션 안에서는 iframe↔상위 문서 간 스크롤 조작을 브라우저로 직접 확인할 방법이 없었다
(자동화 테스트 환경 한계). 배포 후 실제 브라우저에서 한 번은 꼭 확인해봐야 한다 - 안 되더라도
앱이 깨지진 않고 "스크롤이 안 유지되는" 정도로 그친다.

### `_inject_head_scripts`
`<head>` 태그 추가 + 사이드바 브랜드 워드마크 재배치까지, 화면에 아무것도 안 그리는 JS 우회
작업 세 가지(PWA manifest/테마색, Pretendard 폰트, 사이드바 워드마크 이동)를 한
streamlit_js_eval 호출로 합쳤다.

원래는 함수 세 개로 나눠서 streamlit_js_eval을 세 번 따로 불렀는데, 각 호출이 (높이는 0이어도)
부모 stVerticalBlock의 flex gap을 하나씩 차지해서 - 다른 여러 개의 "높이 0짜리" CSS
`st.markdown` 호출들과 합쳐져 - 페이지 맨 위에 제목이 밀려 내려갈 만큼 여백이 쌓였다. 호출을
하나로 합치면 그 gap도 하나만 차지한다.

Streamlit 오픈소스는 `<head>`에 커스텀 태그를 넣는 공식 API가 없어서 `window.parent.document`로
직접 DOM을 추가하는 방식으로 우회한다. 이미 넣은 태그/이미 옮긴 노드면 건너뛰게 만들어서 리런마다
중복 작업하지 않는다. `want_output=False`로 이 컴포넌트가 Python에 값을 돌려보내지 않게 한다 -
streamlit_js_eval처럼 "값을 돌려주는" 컴포넌트는 리턴값이 바뀔 때마다 Streamlit이 스크립트를
다시 리런시키는데, 여기선 그 리턴값이 필요 없으니 아예 안 받는 게 맞다
(`_restore_scroll_position`에서 이걸 안 해서 무한 리런 버그가 났던 적이 있다 - 위 섹션 참고).

⚠ manifest.json/아이콘/테마색만으로 "홈 화면에 추가"가 항상 뜨는 건 아니다 - 브라우저마다 설치
가능 판정 기준이 다르고(크롬 계열은 서비스 워커 등록까지 요구하는 경우가 있음), HTTPS로 실제
배포된 뒤 진짜 기기에서 확인이 필요하다. 지금은 기반(manifest/아이콘/테마색)까지만 깔아둔 상태다.

사이드바 워드마크 이동: `st.navigation`이 만드는 nav는 항상 `stSidebarUserContent`보다 먼저 오는
고정 자리에 배치돼서, `st.sidebar.markdown()`을 nav보다 먼저 호출해도 실제 DOM에서는 nav 뒤에
놓인다. `stSidebarUserContent`를 통째로 nav 앞으로 옮기면 "남은 세로 공간을 다 채우는" 크기
규칙을 그대로 들고 와서 nav가 화면 훨씬 아래로 밀리는 부작용이 있었다 - 대신 그 규칙이 없는
`stLogoSpacer`(`st.logo()`를 쓸 때 이미지가 들어가는, 작고 고정된 자리)로 워드마크의
element-container만 옮긴다.

### `main`
사이드바 상단(내비게이션 항목들 위)에 브랜드 워드마크를 넣는다. `SIDEBAR_CSS`가 사이드바 안 모든
글자를 밝은 회색(#E2E8F0)으로 강제하기 때문에, 완전한 흰색으로 보이려면 별도 클래스가 필요하다 -
인라인 style에 `!important`를 직접 써도 Streamlit의 HTML sanitizer가 인라인 `!important`만
조용히 제거해버려서(다른 속성은 안 건드림) 적용이 안 됐다. 대신 클래스(`.sidebar-brand`,
`SIDEBAR_CSS`에 정의)에 `!important`를 넣어서 우회한다.

사이드바가 "자치구 필터"가 아니라 페이지를 고르는 앱 내비게이션 역할을 한다 (기본 동작 - 왼쪽에서
접었다 펼 수 있는 사이드바 형태). 네 page 콜백이 다 lambda라서 이름이 똑같이 `<lambda>`로 잡혀
`url_path`가 자동으로 안 정해진다 (Streamlit이 콜러블 이름/파일명/title에서 `url_path`를
유추하는데, lambda는 넷 다 이름이 같아서 충돌한다) - `url_path`를 직접 지정해서 각 페이지 주소가
겹치지 않게 한다.

`page_home`의 lambda가 `page_heatmap`/`page_facility`/`page_route`를 참조하는데, 코드상
`page_home`이 먼저 나온다 - 그래도 lambda 안 코드는 "호출되는 시점"에야 이름을 찾기 때문에
(클로저), 실제 페이지 전환이 일어나는 시점엔 셋 다 이미 정의돼 있어 문제없다.

`current_page.url_path`가 빈 문자열로 나올 때(기본/첫 페이지) 스크롤 복원용 대체 키도 "home"으로
맞춘다 (다른 페이지와 구분만 되면 되는 저장용 키라 값 자체는 임의로 정해도 무방).

---

## 알려진 이슈 / 배포 전 확인할 것

- `_restore_scroll_position`의 스크롤 복원 동작은 이 개발 환경(자동화 테스트 샌드박스)에서
  브라우저로 직접 검증하지 못했다 - 실제 배포 후 브라우저에서 한 번 확인 필요. 실패해도 앱이
  깨지지는 않는다.
- `_inject_head_scripts`의 PWA "홈 화면에 추가" 배너는 HTTPS 배포 + 실제 기기에서만 확실히
  확인할 수 있다.
- `VIEW_TOGGLE_CSS`가 의존하는 Streamlit 내부 testid(`stRadio` 등)는 버전이 바뀌면 깨질 수 있는
  비공식 API다.
