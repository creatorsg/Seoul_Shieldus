"""
서울시 치안 안전 지수 대시보드 - 프론트엔드 (Streamlit + folium)

이 파일은 화면 조립만 담당한다. 데이터를 어떻게 읽어오는지는 data_access.py,
네이버 지도 HTML을 어떻게 만드는지는 naver_map.py에 있다.

페이지 이동은 st.navigation을 써서 사이드바가 "필터"가 아니라 안심지수 히트맵/시설 찾기/길찾기를
고르는 앱 내비게이션 역할을 하게 했다 (웹앱처럼 보이려는 디자인 방향).
"""

import copy
import os

import folium
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

from colors import SCORE_COLOR_BANDS, score_to_color
from data_access import (
    BASE_DIR,
    CRIME_RATE_COLUMN,
    _polygon_centroid,
    get_cctv_stats,
    get_district_scores,
    get_facility_markers,
    get_safe_paths,
    get_street_light_markers,
    load_geojson,
)
from naver_map import write_route_map, write_static_map
from route_finder import fetch_route, find_nearest_facility, get_current_location, get_tmap_app_key

# override=True: load_dotenv는 기본적으로 os.environ에 이미 들어있는 값은 안 덮어쓴다.
# 이 줄 자체는 리런마다 다시 실행되지만(app.py 최상단이라), override 없이는 "맨 처음 리런 때
# 읽은 값"이 프로세스 안에 계속 남아있어서 .env를 나중에 고쳐도 서버를 완전히 재시작하기
# 전까진 반영이 안 된다 - route_finder.get_tmap_app_key()에서 실제로 겪었던 것과 같은 종류의
# 문제라 여기도 미리 막아둔다.
load_dotenv(BASE_DIR / ".env", override=True)
NAVER_MAPS_CLIENT_ID = os.getenv("NAVER_MAPS_CLIENT_ID")

ROUTE_MODES = {"도보": "pedestrian", "자동차": "car"}

# Streamlit 기본 UI 중 "이거 Streamlit으로 만들었어요" 티가 나는 요소를 숨긴다.
# toolbarMode="minimal"(.streamlit/config.toml)이 Deploy 버튼/개발자 메뉴는 이미 지워주지만,
# 하단 "Made with Streamlit" 푸터와 헤더 위 무지개색 장식 줄은 config로 못 지워서 CSS로 숨긴다.
HIDE_STREAMLIT_CHROME_CSS = """
<style>
footer { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
</style>
"""

# 페이지가 바뀔 때 화면이 뚝 끊기지 않고 살짝 떠오르듯 나타나게 하는 CSS.
# st.navigation으로 다른 페이지로 이동하면 이전 페이지의 엘리먼트가 통째로 사라지고 새 페이지
# 엘리먼트가 새로 마운트되기 때문에, 이 애니메이션이 그 타이밍에 자동으로 재생된다.
# (같은 페이지 안에서 위젯만 바꾸는 리런일 때는 Streamlit이 기존 엘리먼트를 재사용할 수도 있어서
# 100% 매번 재생을 보장하진 않는다 - 완벽한 SPA 전환 효과가 아니라 "느낌만 내는" 수준.)
#
# ⚠ iframe(:has(iframe))이 들어있는 박스는 애니메이션 대상에서 제외한다. 네이버 지도처럼 "로드되는
# 순간 자기 컨테이너 크기를 한 번 재서" 초기화하는 JS 위젯은, 그 순간 부모가 transform 애니메이션
# 중이면 크기를 잘못 재거나 레이아웃이 안 잡힌 채로 초기화가 끝나버려 이후 다시 안 살아날 수 있다
# (실제로 "시설 찾기" 지도가 이 애니메이션 때문에 안 뜨는 문제가 있어서 이렇게 제외했다).
PAGE_TRANSITION_CSS = """
<style>
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
div[data-testid="stMain"] div[data-testid="stElementContainer"]:not(:has(iframe)) {
    animation: fadeSlideIn 0.28s ease-out;
}
</style>
"""

# GPS 위치를 기다리는 동안 보여줄 스피너.
# st.spinner()는 "with 블록 안 코드가 실행되는 동안"만 애니메이션이 도는데, 위치 권한 대기는
# 브라우저 응답을 기다리며 리런 사이사이에 걸쳐 있는 대기라 st.spinner로는 애니메이션이
# 뚝뚝 끊긴다. 대신 매 리런마다 완전히 똑같은 HTML/CSS를 그리는 방식을 쓰면, 브라우저 쪽
# CSS 애니메이션은 리런과 무관하게 계속 자연스럽게 돌아간다.
GPS_WAIT_SPINNER_HTML = """
<style>
@keyframes gpsSpin { to { transform: rotate(360deg); } }
</style>
<div style="display:flex;align-items:center;gap:12px;padding:16px;
            background:#F5F7F5;border-radius:8px;margin-bottom:8px;">
  <div style="width:22px;height:22px;border-radius:50%;flex-shrink:0;
              border:3px solid #C8E6C9;border-top-color:#2E7D32;
              animation:gpsSpin 0.8s linear infinite;"></div>
  <span style="font-size:14px;color:#1B1B1B;">
    브라우저가 위치 권한을 물어보면 허용해주세요. 내 위치를 가져오는 중입니다...
  </span>
</div>
"""

# 자치구 상세 패널에 표시할 세부 점수 (라벨, df 컬럼명)
DETAIL_SCORE_FIELDS = [
    ("CCTV 점수", "CCTV_점수"),
    ("귀갓길 점수", "귀갓길_점수"),
    ("파출소 접근성", "파출소_접근성"),
    ("가로등 점수", "가로등_점수"),
    ("범죄안전 점수", "범죄안전_점수"),
]

# CCTV 목적별 통계 표시 라벨 (df 컬럼명, 라벨) - get_cctv_stats()의 CCTV_STATS_COLUMNS 중
# "구"/"총_CCTV"/"방범_합계"를 뺀 목적별 세부 8개만 막대그래프로 보여준다.
CCTV_PURPOSE_FIELDS = [
    ("방범용", "방범"),
    ("어린이보호용", "어린이보호"),
    ("공원놀이터용", "공원/놀이터"),
    ("무단투기단속용", "무단투기단속"),
    ("화재감시용", "화재감시"),
    ("교통단속용", "교통단속"),
    ("교통정보용", "교통정보"),
    ("기타용", "기타"),
]


# 홈 화면의 "핵심 기능" 카드 3개 - (아이콘, 제목, 설명, 그 기능 페이지의 url_path).
# url_path는 main()에서 만드는 st.Page들의 url_path와 정확히 같아야 st.page_link가 연결된다.
HOME_FEATURE_CARDS = [
    (
        "🛡️",
        "안심지수 히트맵",
        "자치구별 안심지수를 지도로 한눈에 비교하고, 어떤 지표가 점수에 영향을 줬는지 확인하세요.",
        "index",
    ),
    (
        "📍",
        "시설 찾기",
        "내 주변 지구대·파출소·CCTV·안심귀갓길·가로등 위치를 지도에서 찾아보세요.",
        "facilities",
    ),
    (
        "🧭",
        "길찾기",
        "가장 가까운 지구대·파출소까지 도보/자동차 경로와 예상 소요시간을 안내받으세요.",
        "route",
    ),
]


def _warn_missing_env(var_name: str) -> None:
    """
    API 키 등 .env 설정이 빠졌을 때 공통 문구로 경고한다.
    "설정을 안 해서 그런 것"과 "시도했는데 실패한 것"을 구분하려고, 이건 st.warning(주의)만 쓰고
    실제 호출 실패는 st.error(route_finder.fetch_route)로 분리해뒀다.
    """
    st.warning(
        f"{var_name}가 설정되지 않았습니다. "
        f"프로젝트 루트의 .env 파일에 `{var_name}=발급받은값`를 추가하세요."
    )


def _render_score_bar(label: str, score: float) -> None:
    """
    점수만큼 채워지는 막대를 그린다. st.progress는 막대 색이 테마 색 하나로 고정이라
    점수가 높든 낮든 같은 색으로 보여서, 점수에 따라 색(빨강~초록)이 바뀌게 직접 HTML로 그린다.
    글자 크기(13→14px)/막대 두께(8→10px)/간격(10→16px)을 살짝 키워서, 5개 지표가 다닥다닥
    붙어 보이던 걸 한 항목씩 눈에 들어오게 여백을 넉넉히 줬다.
    """
    color = score_to_color(score)
    width = max(0, min(100, score))
    st.markdown(
        f"""
        <div style="margin-bottom:16px;">
          <div style="font-size:14px;margin-bottom:5px;color:#1B1B1B;">{label} <strong>{score:.1f}</strong></div>
          <div style="background:#E0E0E0;border-radius:5px;height:10px;">
            <div style="width:{width}%;background:{color};height:10px;border-radius:5px;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_district_detail(row, cctv_stats) -> None:
    """선택된 자치구 하나의 안심지수/세부 점수 + CCTV 목적별 통계를 그린다."""
    st.subheader(f"{row['구']} 상세")
    st.metric("안심지수", f"{row['안심지수']}점")
    st.caption(
        "아래 5개 지표(CCTV·귀갓길·파출소·가로등·범죄안전)를 종합해 계산한 점수입니다. "
        "산정 방식은 위쪽 '안심지수는 어떻게 계산되나요?'에서 확인할 수 있습니다."
    )
    st.write("")
    for label, col in DETAIL_SCORE_FIELDS:
        _render_score_bar(label, row[col])

    if cctv_stats.empty:
        return
    district_cctv = cctv_stats[cctv_stats["구"] == row["구"]]
    if district_cctv.empty:
        return
    c = district_cctv.iloc[0]
    st.divider()
    st.subheader("CCTV 목적별 설치 현황")
    st.caption(f"총 {c['총_CCTV']:,}대 (그중 방범 목적 {c['방범_합계']:,}대)")
    # sort=False가 중요하다: st.bar_chart는 기본값(sort=True)일 때 Altair가 카테고리(구매목적명)를
    # 알아서 다시 정렬해버려서, 우리가 값(대수) 기준 내림차순으로 미리 만들어둔 dict 순서가
    # 무시되고 조용히 다른 순서(사실상 알파벳/가나다순)로 그려진다. sort=False를 줘야 넘겨준
    # dict 순서 그대로("많은 순") 막대가 그려진다.
    #
    # horizontal=True도 같이 준다: 세로 막대(기본값)는 "방범용"/"무단투기단속용"처럼 4글자
    # 이상인 라벨이 가로 폭에 안 들어가서 Altair가 자동으로 90도 눕혀버린다. 막대를 가로로
    # 눕히면 목적명이 y축 왼쪽에 원래 방향(가로) 그대로 나오기 때문에 이 문제가 자체로 해결된다.
    st.bar_chart(_sorted_cctv_purpose_counts(c), height=220, sort=False, horizontal=True)


def _sorted_cctv_purpose_counts(c) -> dict:
    """
    CCTV 목적별 대수를 많은 순으로 정렬해서 반환한다.
    CCTV_PURPOSE_FIELDS에 적어둔 순서(방범→어린이보호→...→기타) 그대로 막대그래프를 그리면
    구마다 값이 들쭉날쭉이라 막대 높이가 뒤죽박죽으로 보인다. 값 기준 내림차순으로 정렬해두면
    어느 구를 보든 "가장 많이 설치된 목적이 왼쪽부터" 순서로 읽혀서 비교하기 쉽다.
    dict의 삽입 순서를 st.bar_chart가 그대로 x축 순서로 써주기 때문에, 여기서 미리 정렬한
    순서대로 dict를 만들어주기만 하면 된다.
    """
    counts = {label: c[col] for col, label in CCTV_PURPOSE_FIELDS}
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def _geo_with_score_properties(geo: dict, df) -> dict:
    """
    geojson feature.properties에 안심지수를 미리 섞어 넣은 사본을 반환한다.

    GeoJsonTooltip/GeoJsonPopup은 항상 geojson feature의 properties만 읽는다 - Choropleth에
    따로 넘긴 data=df는 색칠(fill-color 매칭)에만 쓰이고 툴팁/팝업 쪽에서는 안 보인다. 그래서
    호버/클릭했을 때 점수까지 같이 보여주려면, 지도를 그리기 전에 df의 안심지수를 구 이름으로
    매칭해서 geojson properties 안에 미리 넣어둬야 한다. 원본 geo(= @st.cache_data로 캐싱된
    객체)를 그대로 고치면 캐시에 값이 계속 누적/오염될 수 있어 깊은 복사본을 만들어 고친다.
    """
    scores = dict(zip(df["구"], df["안심지수"]))
    geo_copy = copy.deepcopy(geo)
    for feat in geo_copy["features"]:
        name = feat["properties"]["name"]
        feat["properties"]["score"] = scores.get(name)
    return geo_copy


def _district_style_function(feature: dict) -> dict:
    """
    geojson feature(구 하나)의 채우기 색을 colors.py의 score_to_color()로 정한다.
    folium.Choropleth의 자체 배색(fill_color="RdYlGn") 대신 이걸 쓰는 이유는 colors.py
    docstring에 적어뒀다 - 요약하면 "지도만 다른 기준으로 칠해지는 문제"를 없애기 위해서다.
    """
    score = feature["properties"].get("score")
    color = score_to_color(score) if score is not None else "#BDBDBD"
    return {"fillColor": color, "color": "#424242", "weight": 1, "fillOpacity": 0.75}


def _district_highlight_function(feature: dict) -> dict:
    """마우스가 올라간 구의 칸을 강조한다 (테두리를 굵게, 채우기를 더 진하게)."""
    return {"weight": 3, "fillOpacity": 0.95}


def _build_score_legend_html() -> str:
    """
    지도 오른쪽 아래에 얹을 범례 HTML. colors.py의 SCORE_COLOR_BANDS를 그대로 읽어서 만들기
    때문에, 나중에 임계값/색이 바뀌어도 이 범례가 알아서 같이 바뀐다(따로 손댈 곳이 없다).
    """
    labels = ["위험 (40점 미만)", "주의 (40~60점)", "보통 (60~75점)", "안전 (75점 이상)"]
    rows = "".join(
        f'<div style="display:flex;align-items:center;margin-top:2px;">'
        f'<span style="display:inline-block;width:11px;height:11px;background:{color};'
        f'border-radius:2px;margin-right:6px;flex-shrink:0;"></span>{label}</div>'
        for (_, color, _text_color), label in zip(SCORE_COLOR_BANDS, labels)
    )
    return (
        '<div style="position:fixed;bottom:24px;right:24px;z-index:9999;background:#fff;'
        'padding:10px 14px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.3);'
        'font-size:12px;line-height:1.5;color:#1B1B1B;">'
        '<div style="font-weight:700;margin-bottom:4px;">안심지수</div>'
        f"{rows}</div>"
    )


def _add_district_labels(m: "folium.Map", geo: dict) -> None:
    """
    자치구 이름을 각 자치구 중심점에 고정 텍스트로 올린다 (지금까지는 색으로만 구분되던 것).
    DivIcon으로 만든 라벨이라 클릭/호버 이벤트를 가로채지 않도록 pointer-events:none을 줘서,
    라벨 아래에 깔린 히트맵 폴리곤의 클릭/호버는 그대로 통과되게 한다.
    """
    for feat in geo["features"]:
        name = feat["properties"]["name"]
        lat, lng = _polygon_centroid(feat["geometry"])
        folium.map.Marker(
            [lat, lng],
            icon=folium.DivIcon(
                html=(
                    '<div style="pointer-events:none;font-size:11px;font-weight:600;'
                    'color:#212121;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;'
                    'white-space:nowrap;transform:translate(-50%,-50%);">'
                    f"{name}</div>"
                )
            ),
        ).add_to(m)


def render_home_page(df, pages: dict) -> None:
    """
    홈(소개) 페이지: 처음 들어온 사람이 "이게 뭐 하는 서비스인지" 바로 알 수 있게 하는 첫 화면.
    지금까지는 로그인하자마자 바로 히트맵부터 보여줘서 설명이 하나도 없었는데, 앱이라면 첫
    화면에 프로젝트 소개/핵심 기능/데이터 출처 정도는 있어야 처음 쓰는 사람이 헤매지 않는다는
    피드백을 반영했다.

    pages: main()에서 만든 {url_path: st.Page} 딕셔너리. 카드마다 "바로가기" 링크를 연결하려면
    실제 st.Page 객체가 필요한데(st.page_link는 경로 문자열이 아니라 Page 객체를 받는 방식이라),
    main()이 pages를 다 만든 뒤에 넘겨받아 쓴다. 클로저로 pages를 참조하는 lambda가 이 함수보다
    먼저 만들어지긴 하지만, 실제로 이 함수가 호출되는 시점(페이지 렌더링 시)에는 이미 pages
    딕셔너리에 4개 페이지가 다 채워져 있어서 문제 없다.
    """
    st.subheader("서울시 25개 자치구의 치안 정보를 한눈에")
    st.markdown(
        "CCTV, 지구대·파출소, 안심귀갓길, 가로등, 범죄율 데이터를 종합해 자치구별 **안심지수**를 "
        "계산하고, 내 주변 치안 시설을 찾고 길안내까지 받을 수 있는 서비스입니다."
    )

    if not df.empty:
        avg_score = df["안심지수"].mean()
        top = df.sort_values("안심지수", ascending=False).iloc[0]
        col1, col2 = st.columns(2)
        col1.metric("서울 평균 안심지수", f"{avg_score:.1f}점")
        col2.metric("안심지수 1위 자치구", f"{top['구']} ({top['안심지수']:.1f}점)")

    st.divider()
    st.subheader("핵심 기능")
    cols = st.columns(3)
    for col, (icon, title, desc, url_path) in zip(cols, HOME_FEATURE_CARDS):
        with col:
            st.markdown(
                f"""
                <div style="border:1px solid #E0E0E0;border-radius:10px;padding:18px 16px;
                            min-height:170px;">
                  <div style="font-size:28px;">{icon}</div>
                  <div style="font-weight:700;font-size:16px;margin:8px 0 6px;">{title}</div>
                  <div style="font-size:13px;color:#555555;line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(pages[url_path], label=f"{title} 바로가기", icon="➡️")

    st.divider()
    st.subheader("데이터 출처")
    st.caption(
        "지구대·파출소 위치, CCTV 설치 현황, 여성안심귀갓길 — 서울 열린데이터광장(data.seoul.go.kr)  \n"
        "범죄 통계, 가로등 등 안전시설물 — 공공데이터포털(data.go.kr)  \n"
        "지도 표시 — 네이버 클라우드 플랫폼 Maps API · 도보/자동차 경로 안내 — TMAP(SK Open API)"
    )


def render_index_page(geo: dict, df, cctv_stats) -> None:
    """
    안심지수 히트맵 페이지: 지도를 위에 크게 띄우고, 아래에서 "전체 확인"(표) /
    "지역별 상세"(자치구 하나 골라서 점수 + CCTV 목적별 통계 뜯어보기) 를 토글로 전환한다.
    """
    st.header("안심지수 히트맵")

    with st.expander("안심지수는 어떻게 계산되나요?"):
        st.markdown(
            "구별 **CCTV 설치 현황**, **지구대/파출소 접근성**, **안심귀갓길**, **가로등**, "
            "**범죄 안전도**, 이렇게 5개 지표를 종합해 0~100점으로 계산합니다. "
            "각 지표는 자치구 상세 보기에서 점수별로 따로 확인할 수 있습니다.\n\n"
            "⚠️ 지표별 정확한 반영 비율(가중치)은 데이터팀 확인 후 업데이트할 예정입니다."
        )

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
    # Leaflet은 지역(폴리곤)을 클릭 가능한 SVG <path>로 그리는데, 클릭하면 그 <path>에 브라우저
    # 포커스가 잡혀서 기본 포커스 표시(검은 네모 테두리, outline)가 뜬다 - 키보드 접근성을 위한
    # 브라우저 기본 동작이라 folium/Leaflet 옵션으로는 못 끄고, 지도 iframe 안에 CSS를 직접
    # 넣어야 한다. st_folium은 이 HTML을 그대로 iframe으로 렌더링하므로, <head>에 스타일을
    # 하나 추가해서 그 포커스 테두리만 지운다.
    m.get_root().header.add_child(
        folium.Element("<style>.leaflet-interactive:focus { outline: none; }</style>")
    )
    geo_scored = _geo_with_score_properties(geo, df)
    tooltip_popup_fields = ["name", "score"]
    tooltip_popup_aliases = ["자치구", "안심지수"]
    # folium.Choropleth 대신 GeoJson을 직접 써서 style_function으로 색칠한다 - colors.py의
    # score_to_color()를 그대로 호출하기 때문에, 이 지도의 색이 랭킹 표/상세 페이지 점수 막대와
    # 항상 같은 기준으로 맞는다(자세한 이유는 colors.py 모듈 docstring 참고).
    # highlight_function: 마우스가 올라간(호버된) 칸의 테두리를 굵게, 채우기를 더 진하게 바꿔서
    # "지금 이 칸을 가리키고 있다"는 게 시각적으로 보이게 한다. 원래는 색칠된 구가 다 똑같이
    # 밋밋해서 어느 구 위에 커서가 있는지 구분이 안 됐는데, 이걸로 해결된다.
    folium.GeoJson(
        geo_scored,
        style_function=_district_style_function,
        highlight_function=_district_highlight_function,
        tooltip=folium.GeoJsonTooltip(fields=tooltip_popup_fields, aliases=tooltip_popup_aliases),
        popup=folium.GeoJsonPopup(fields=tooltip_popup_fields, aliases=tooltip_popup_aliases),
    ).add_to(m)

    # colors.py 기준 4단계 범례를 지도 위에 얹는다. Choropleth 내장 범례(legend_name)를 쓰던
    # 자리를 대신한다 - 이제 범례/지도/표/상세 점수 막대가 전부 같은 색-점수 대응표를 본다.
    m.get_root().html.add_child(folium.Element(_build_score_legend_html()))

    # 색만으로는 어느 구인지 바로 안 읽혀서, 중심점에 구 이름 텍스트를 고정으로 얹는다.
    _add_district_labels(m, geo)

    st_folium(m, height=550, returned_objects=[], use_container_width=True)

    view = st.radio(
        "보기 방식", ["전체 확인", "지역별 상세"], horizontal=True, label_visibility="collapsed"
    )

    if view == "전체 확인":
        st.subheader("자치구 랭킹")
        # 처음엔 지도/상세 페이지와 맞춰 점수 칸에 배경색(빨강~초록)을 칠했었는데, 25행 전체가
        # 색으로 뒤덮이니 오히려 눈이 피로하다는 피드백을 받고 뺐다. 표는 순위를 빠르게 훑어보는
        # 용도라 색 없이 숫자만 보는 게 더 편하다고 판단 - 색 기준(빨강=위험~초록=안전)은
        # 지도 범례와 지역별 상세의 점수 막대에서 여전히 확인할 수 있다.
        ranking = df.sort_values("안심지수", ascending=False)[["구", "안심지수"]]
        st.dataframe(
            ranking.style.format({"안심지수": "{:.1f}"}), width="stretch", hide_index=True
        )
    else:
        selected_gu = st.selectbox("자치구 선택", sorted(df["구"].tolist()))
        render_district_detail(df[df["구"] == selected_gu].iloc[0], cctv_stats)


def _facility_display_table(facilities, df):
    """
    시설 찾기 표에 위도/경도 대신 사용자에게 실제로 쓸모 있는 정보(구/주소/범죄율)를 보여준다.
    위도/경도는 애초에 지도에 마커 찍을 때 좌표로 쓰려던 값이지 사용자가 표에서 볼 이유가 없다는
    피드백을 반영했다.

    범죄안전_점수(0~100 정규화 점수) 대신 원본 범죄율(CRIME_RATE_COLUMN)을 보여주도록 바꿨다 -
    정규화 점수만 보면 "0점"이 왜 0점인지 감이 안 오는데(실제로 이 때문에 데이터 오류로
    오해한 적이 있었다), 원본 비율 숫자가 그대로 보이면 근거가 바로 눈에 들어온다. 안심지수
    히트맵/상세 페이지는 기존 그대로(정규화 점수) 두고, 이 표만 바꾼다. df(자치구별 안심지수
    점수표)의 CRIME_RATE_COLUMN을 "구" 기준으로 매칭해 붙인다.
    """
    rate_by_district = dict(zip(df["구"], df[CRIME_RATE_COLUMN]))
    table = facilities[["이름", "구", "주소", "종류"]].copy()
    table[CRIME_RATE_COLUMN] = table["구"].map(rate_by_district)
    return table


def render_facility_page(facilities, df) -> None:
    """시설 찾기 페이지: 네이버 지도 위에 지구대/파출소/가로등 마커 + 안심귀갓길 + 내 위치 표시."""
    st.header("시설 찾기")

    if not NAVER_MAPS_CLIENT_ID:
        _warn_missing_env("NAVER_MAPS_CLIENT_ID")
        return

    st.caption("브라우저가 위치 권한을 물어보면 허용해야 '내 위치'가 표시됩니다.")
    street_lights = get_street_light_markers()
    safe_paths = get_safe_paths()
    map_url = write_static_map(NAVER_MAPS_CLIENT_ID, facilities, street_lights, safe_paths)
    st.iframe(map_url, height=620)
    st.caption(
        f"가로등({len(street_lights):,}개)과 안심귀갓길({len(safe_paths):,}개 노선)은 기본은 꺼져 있고, "
        "켜면 표시됩니다. 가로등은 개수가 많아 클러스터로 묶여서 나옵니다. "
        "지도 위 지구대/파출소 마커를 클릭(모바일은 터치)하면 주소가 복사됩니다."
    )
    table = _facility_display_table(facilities, df)
    if table[CRIME_RATE_COLUMN].isna().all():
        # 원본 범죄율은 데이터 파일이 한글(alt) 스키마일 때만 들어있다 - 영문 스키마나 더미
        # 데이터일 땐 전부 NaN이라, 표가 텅 비어보이지 않게 미리 이유를 알려준다.
        st.caption(
            f"'{CRIME_RATE_COLUMN}'는 원본 데이터 파일에 실제 범죄율 값이 있을 때만 표시됩니다."
        )
    st.dataframe(
        table.style.format({CRIME_RATE_COLUMN: "{:.1f}"}, na_rep="-"),
        width="stretch",
        hide_index=True,
    )


def render_route_page(facilities) -> None:
    """길찾기 페이지: 내 위치 → 가장 가까운(또는 직접 고른) 지구대/파출소까지 도보/자동차 경로."""
    st.header("길찾기")

    if not NAVER_MAPS_CLIENT_ID:
        _warn_missing_env("NAVER_MAPS_CLIENT_ID")
        return

    mode_label = st.radio("이동수단", list(ROUTE_MODES.keys()), horizontal=True)

    location = get_current_location()
    if location is None:
        st.markdown(GPS_WAIT_SPINNER_HTML, unsafe_allow_html=True)
        return
    my_lat, my_lng = location

    nearest = find_nearest_facility(my_lat, my_lng, facilities)
    facility_names = facilities["이름"].tolist()
    selected_name = st.selectbox(
        "목적지 (기본값: 가장 가까운 지구대/파출소)",
        facility_names,
        index=facility_names.index(nearest["이름"]),
    )
    destination = facilities[facilities["이름"] == selected_name].iloc[0]

    # TMAP_APP_KEY를 여기서 상수로 들고 있지 않고 매번 get_tmap_app_key()로 새로 읽는다 - .env를
    # 고친 뒤 서버를 완전히 재시작하지 않고 리런만 해도 최신 키가 바로 반영되게 하기 위해서다
    # (route_finder.get_tmap_app_key()의 docstring에 이 문제가 왜 생기는지 자세히 적어뒀다).
    tmap_app_key = get_tmap_app_key()
    if not tmap_app_key:
        _warn_missing_env("TMAP_APP_KEY")
        route_info = None
    else:
        route_info = fetch_route(
            (my_lat, my_lng),
            (destination["위도"], destination["경도"]),
            mode=ROUTE_MODES[mode_label],
        )

    map_url = write_route_map(
        NAVER_MAPS_CLIENT_ID,
        facilities,
        (my_lat, my_lng),
        selected_name,
        route_info["coords"] if route_info else None,
    )
    st.iframe(map_url, height=560)
    st.caption("지도 위 지구대/파출소 마커를 클릭(모바일은 터치)하면 주소가 복사됩니다.")

    if route_info:
        st.caption(
            f"내 위치 → {selected_name} {mode_label} 경로: "
            f"약 {route_info['distance_km']}km, {route_info['time_min']}분 예상"
        )
    elif tmap_app_key:
        st.caption("경로를 가져오지 못했습니다. TMAP 앱에 해당 이동수단 상품이 등록되어 있는지 확인하세요.")


def _restore_scroll_position(page_key: str) -> None:
    """
    (베스트 에포트) Streamlit은 위젯 조작 등으로 리런될 때마다 본문 스크롤을 맨 위로 되돌리는데,
    이건 Streamlit 자체 프레임워크 동작이라 앱 코드에서 끌 수 있는 옵션이 없다. 대신
    streamlit_js_eval로 상위 문서(window.parent)의 실제 스크롤 컨테이너(stMain)에 스크롤 위치를
    sessionStorage에 저장했다가 복원하는 리스너를 붙여서 흉내만 낸다.

    streamlit_js_eval 컴포넌트 소스를 직접 확인해보니, "직전 리런과 완전히 똑같은 JS 문자열"이면
    재실행 자체를 건너뛰는 구조다. 그래서 매 리런마다 반드시 다시 실행되도록 key를 세션 카운터로
    계속 바꿔서 컴포넌트를 매번 새로 마운트시킨다.

    ⚠ 실제로 배포해서 써보니 이 방식이 심각한 버그를 냈었다: streamlit_js_eval처럼 "값을
    돌려주는" 커스텀 컴포넌트는, 이전과 다른 값을 Python에 보고할 때마다 Streamlit이 그 값을
    반영하려고 스크립트를 다시 리런시킨다. 그런데 매 리런마다 key를 새로 바꾸면 그때마다
    "새 위젯"이 되어서 이전 리턴값 캐시가 없으니, 이 컴포넌트가 응답을 보낼 때마다 매번
    "값이 바뀌었다"고 처리돼 리런이 또 걸리고, 그 리런이 다시 새 key를 만들고... 하는 식으로
    사용자 조작 없이도 초당 3~4번씩 무한 리런되는 루프가 생겼다 (실측: 8초에 28번 리런).
    이 루프가 길찾기 페이지에서 돌면 fetch_route()가 그만큼 반복 호출돼서 TMAP API가
    429(요청 과다)를 뱉는 원인이 됐다.

    고친 방법: want_output=False를 줘서 이 컴포넌트가 아예 Python에 값을 돌려보내지 않게 한다
    (streamlit_js_eval 패키지 프론트엔드 코드 기준 - want_output이 False면 sendDataToPython
    자체를 호출 안 함). 그러면 "리턴값이 바뀌어서 리런을 유발"할 방법이 없어지므로, key를 매번
    바꿔서 JS를 강제로 재실행시키는 건 그대로 유지해도 안전하다 - 실행은 여전히 매 리런마다
    되지만(스크롤 복원 자체는 계속 시도됨), 그 실행 결과가 Streamlit으로 다시 흘러들어가서
    리런을 만드는 순환 고리만 끊었다.

    ⚠ 이 세션 안에서는 iframe↔상위 문서 간 스크롤 조작을 브라우저로 직접 확인할 방법이 없었다
    (자동화 테스트 환경 한계). 배포 후 실제 브라우저에서 한 번은 꼭 확인해봐야 한다 - 안 되더라도
    앱이 깨지진 않고 "스크롤이 안 유지되는" 정도로 그친다.
    """
    st.session_state["_scroll_tick"] = st.session_state.get("_scroll_tick", 0) + 1
    js = f"""
    (function() {{
        var d = window.parent.document;
        var c = d.querySelector('[data-testid="stMain"]') || d.querySelector('[data-testid="stAppViewContainer"]');
        if (!c) return false;
        var storeKey = 'shieldus_scrollpos_{page_key}';
        c.dataset.currentScrollKey = storeKey;
        var saved = window.parent.sessionStorage.getItem(storeKey);
        if (saved !== null) {{ c.scrollTop = parseInt(saved, 10); }}
        if (!c.dataset.scrollListenerAttached) {{
            c.dataset.scrollListenerAttached = "1";
            var t = null;
            c.addEventListener('scroll', function () {{
                if (t) clearTimeout(t);
                t = setTimeout(function () {{
                    window.parent.sessionStorage.setItem(c.dataset.currentScrollKey, c.scrollTop);
                }}, 150);
            }});
        }}
        return true;
    }})()
    """
    streamlit_js_eval(
        js_expressions=js,
        key=f"scroll_restore_{st.session_state['_scroll_tick']}",
        want_output=False,
    )


def _inject_pwa_head() -> None:
    """
    PWA manifest/테마색 메타 태그를 <head>에 넣는다.

    Streamlit 오픈소스는 <head>에 커스텀 태그를 넣는 공식 API가 없다. st.markdown(unsafe_allow_html=True)은
    body 안에 삽입되고, <script> 태그도 innerHTML로 넣으면 브라우저가 실행을 안 해줘서, streamlit_js_eval로
    상위 문서(window.parent.document.head)에 직접 DOM을 추가하는 방식으로 우회했다. 이미 넣은 태그가
    있으면 건너뛰게 만들어서, 이 함수가 여러 번 불려도 <head>에 중복으로 쌓이지 않는다.

    want_output=False로 이 컴포넌트가 Python에 값을 돌려보내지 않게 했다 - streamlit_js_eval처럼
    "값을 돌려주는" 컴포넌트는 리턴값이 바뀔 때마다 Streamlit이 스크립트를 다시 리런시키는데,
    이 함수는 그 리턴값이 전혀 필요 없으니 아예 안 받는 게 맞다 (_restore_scroll_position에서
    이걸 안 해서 무한 리런 버그가 났던 걸 고치면서 여기도 같이 정리했다).

    ⚠ manifest.json/아이콘/테마색만으로 "홈 화면에 추가"가 항상 뜨는 건 아니다 - 브라우저마다 설치
    가능 판정 기준이 다르고(크롬 계열은 서비스 워커 등록까지 요구하는 경우가 있음), HTTPS로 실제
    배포된 뒤 진짜 기기에서 확인이 필요하다. 오늘은 기반(manifest/아이콘/테마색)까지만 깔아둔다.
    """
    js = """
    (function() {
        var d = window.parent.document;
        if (!d.querySelector('link[rel="manifest"]')) {
            var link = d.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/static/manifest.json';
            d.head.appendChild(link);
        }
        if (!d.querySelector('meta[name="theme-color"]')) {
            var meta = d.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#2E7D32';
            d.head.appendChild(meta);
        }
        return true;
    })()
    """
    streamlit_js_eval(js_expressions=js, key="pwa_head_inject", want_output=False)


def main() -> None:
    st.set_page_config(
        page_title="서울시 치안 안전 지수",
        layout="wide",
        # 햄버거 메뉴의 "도움말/버그 신고/정보" 항목도 지운다. 셋 다 None이면 메뉴 자체가 사라진다.
        menu_items={"Get help": None, "Report a bug": None, "About": None},
    )
    st.markdown(HIDE_STREAMLIT_CHROME_CSS, unsafe_allow_html=True)
    st.markdown(PAGE_TRANSITION_CSS, unsafe_allow_html=True)
    _inject_pwa_head()
    st.title("자치구별 치안 안전 지수 대시보드")

    geo = load_geojson()
    df = get_district_scores(geo)
    facilities = get_facility_markers(geo)
    cctv_stats = get_cctv_stats()

    # 사이드바가 "자치구 필터"가 아니라 페이지를 고르는 앱 내비게이션 역할을 한다 (기본 동작 -
    # 왼쪽에서 접었다 펼 수 있는 사이드바 형태). 각 페이지에 icon을 지정해서 사이드바 목록에서도
    # 어떤 탭인지 아이콘으로 바로 구분되게 했다.
    # 모든 page 콜백이 lambda라서 이름이 똑같이 <lambda>로 잡혀 url_path가 자동으로 안 정해진다.
    # (Streamlit이 콜러블 이름/파일명/title에서 url_path를 유추하는데, lambda는 다 이름이 같아서 충돌한다)
    # url_path를 직접 지정해서 각 페이지 주소가 겹치지 않게 한다.
    #
    # list가 아니라 {url_path: st.Page} 딕셔너리로 만드는 이유: 홈 페이지의 "바로가기" 카드가
    # 다른 페이지로 이동하려면 st.page_link에 그 페이지의 st.Page 객체를 그대로 넘겨야 한다.
    # render_home_page(df, pages)가 이 딕셔너리를 통째로 받아서 pages["index"]처럼 이름으로
    # 찾아 쓴다 - render_home_page의 lambda가 pages보다 먼저 줄에 쓰여 있지만, 실제로 호출되는
    # 시점(페이지가 열릴 때)엔 아래 줄들까지 다 실행된 뒤라 4개 페이지가 이미 다 채워져 있다.
    pages = {}
    pages["home"] = st.Page(
        lambda: render_home_page(df, pages),
        title="홈",
        icon="🏠",
        url_path="home",
        default=True,
    )
    pages["index"] = st.Page(
        lambda: render_index_page(geo, df, cctv_stats),
        title="안심지수 히트맵",
        icon="🛡️",
        url_path="index",
    )
    pages["facilities"] = st.Page(
        lambda: render_facility_page(facilities, df),
        title="시설 찾기",
        icon="📍",
        url_path="facilities",
    )
    pages["route"] = st.Page(
        lambda: render_route_page(facilities),
        title="길찾기",
        icon="🧭",
        url_path="route",
    )
    current_page = st.navigation(list(pages.values()))
    current_page.run()
    # 기본(첫 번째) 페이지는 url_path가 빈 문자열로 나와서, 스크롤 저장 키가 비어도 괜찮게
    # "index"로 대체해준다 (다른 페이지와 구분만 되면 되는 저장용 키라 값 자체는 임의로 정해도 무방).
    _restore_scroll_position(current_page.url_path or "index")


main()
