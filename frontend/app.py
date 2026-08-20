"""
서울시 치안 안전 지수 대시보드 - 프론트엔드 (Streamlit + folium)

이 파일은 화면 조립만 담당한다. 데이터를 어떻게 읽어오는지는 data_access.py,
네이버 지도 HTML을 어떻게 만드는지는 naver_map.py에 있다.

페이지 이동은 st.navigation을 써서 사이드바가 "필터"가 아니라 안심지수 히트맵/시설 찾기/길찾기를
고르는 앱 내비게이션 역할을 하게 했다 (웹앱처럼 보이려는 디자인 방향).
"""

import os

import folium
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

from colors import score_to_color
from data_access import (
    BASE_DIR,
    get_district_scores,
    get_facility_markers,
    get_street_light_markers,
    load_geojson,
)
from naver_map import write_route_map, write_static_map
from route_finder import TMAP_APP_KEY, fetch_route, find_nearest_facility, get_current_location

load_dotenv(BASE_DIR / ".env")
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

# 자치구 상세 패널에 표시할 세부 점수 (라벨, df 컬럼명)
DETAIL_SCORE_FIELDS = [
    ("CCTV 점수", "CCTV_점수"),
    ("귀갓길 점수", "귀갓길_점수"),
    ("파출소 접근성", "파출소_접근성"),
    ("가로등 점수", "가로등_점수"),
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
    """
    color = score_to_color(score)
    width = max(0, min(100, score))
    st.markdown(
        f"""
        <div style="margin-bottom:10px;">
          <div style="font-size:13px;margin-bottom:3px;">{label} {score:.1f}</div>
          <div style="background:#E0E0E0;border-radius:4px;height:8px;">
            <div style="width:{width}%;background:{color};height:8px;border-radius:4px;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_district_detail(row) -> None:
    """선택된 자치구 하나의 안심지수/세부 점수를 그린다."""
    st.markdown(f"#### {row['구']} 상세")
    st.metric("안심지수", f"{row['안심지수']}점")
    for label, col in DETAIL_SCORE_FIELDS:
        _render_score_bar(label, row[col])


def render_index_page(geo: dict, df) -> None:
    """
    안심지수 히트맵 페이지: 지도를 위에 크게 띄우고, 아래에서 "전체 확인"(표) /
    "지역별 상세"(자치구 하나 골라서 점수 뜯어보기) 를 토글로 전환한다.
    """
    st.header("안심지수 히트맵")

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
    # RdYlGn: 낮은 안심지수(위험)는 빨강, 높은 안심지수(안전)는 초록으로 직관적으로 읽히는 배색.
    choropleth = folium.Choropleth(
        geo_data=geo,
        data=df,
        columns=["구", "안심지수"],
        key_on="feature.properties.name",
        fill_color="RdYlGn",
        fill_opacity=0.75,
        line_opacity=0.5,
        legend_name="안심 지수",
    ).add_to(m)

    # Choropleth가 이미 만든 geojson 레이어에 툴팁만 얹는다.
    # 별도 GeoJson 레이어를 하나 더 추가하면 폴리곤 데이터를 브라우저로 두 번 보내는 셈이라 비효율적이다.
    choropleth.geojson.add_child(
        folium.GeoJsonTooltip(fields=["name"], aliases=["자치구"])
    )

    st_folium(m, height=550, returned_objects=[], use_container_width=True)

    view = st.radio(
        "보기 방식", ["전체 확인", "지역별 상세"], horizontal=True, label_visibility="collapsed"
    )

    if view == "전체 확인":
        st.subheader("자치구 랭킹")
        ranking = df.sort_values("안심지수", ascending=False)[["구", "안심지수"]]
        st.dataframe(ranking, width="stretch", hide_index=True)
    else:
        selected_gu = st.selectbox("자치구 선택", sorted(df["구"].tolist()))
        render_district_detail(df[df["구"] == selected_gu].iloc[0])


def render_facility_page(facilities) -> None:
    """시설 찾기 페이지: 네이버 지도 위에 지구대/파출소/가로등 마커 + 내 위치 표시."""
    st.header("시설 찾기")

    if not NAVER_MAPS_CLIENT_ID:
        _warn_missing_env("NAVER_MAPS_CLIENT_ID")
        return

    st.caption("브라우저가 위치 권한을 물어보면 허용해야 '내 위치'가 표시됩니다.")
    street_lights = get_street_light_markers()
    map_url = write_static_map(NAVER_MAPS_CLIENT_ID, facilities, street_lights)
    st.iframe(map_url, height=620)
    st.caption(f"가로등은 {len(street_lights):,}개로 많아서 기본은 꺼져 있고, 켜면 클러스터로 묶여서 표시됩니다.")
    st.dataframe(facilities, width="stretch", hide_index=True)


def render_route_page(facilities) -> None:
    """길찾기 페이지: 내 위치 → 가장 가까운(또는 직접 고른) 지구대/파출소까지 도보/자동차 경로."""
    st.header("길찾기")

    if not NAVER_MAPS_CLIENT_ID:
        _warn_missing_env("NAVER_MAPS_CLIENT_ID")
        return

    mode_label = st.radio("이동수단", list(ROUTE_MODES.keys()), horizontal=True)

    location = get_current_location()
    if location is None:
        st.info("브라우저가 위치 권한을 물어보면 허용해주세요. 내 위치를 가져오는 중입니다...")
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

    if not TMAP_APP_KEY:
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

    if route_info:
        st.caption(
            f"내 위치 → {selected_name} {mode_label} 경로: "
            f"약 {route_info['distance_km']}km, {route_info['time_min']}분 예상"
        )
    elif TMAP_APP_KEY:
        st.caption("경로를 가져오지 못했습니다. TMAP 앱에 해당 이동수단 상품이 등록되어 있는지 확인하세요.")


def main() -> None:
    st.set_page_config(
        page_title="서울시 치안 안전 지수",
        layout="wide",
        # 햄버거 메뉴의 "도움말/버그 신고/정보" 항목도 지운다. 셋 다 None이면 메뉴 자체가 사라진다.
        menu_items={"Get help": None, "Report a bug": None, "About": None},
    )
    st.markdown(HIDE_STREAMLIT_CHROME_CSS, unsafe_allow_html=True)
    st.title("자치구별 치안 안전 지수 대시보드")
    st.caption("※ data/processed/*.json이 있으면 실제 데이터를, 없으면 더미 데이터를 사용합니다.")

    geo = load_geojson()
    df = get_district_scores(geo)
    facilities = get_facility_markers(geo)

    # 예전엔 사이드바가 "자치구 필터"였는데, 이제 사이드바는 페이지를 고르는 앱 내비게이션이 되고
    # 자치구 선택은 "안심지수 히트맵" 페이지 안(지역별 상세 토글)으로 옮겼다.
    # 세 page 콜백이 다 lambda라서 이름이 똑같이 <lambda>로 잡혀 url_path가 자동으로 안 정해진다.
    # (Streamlit이 콜러블 이름/파일명/title에서 url_path를 유추하는데, lambda는 셋 다 이름이 같아서 충돌한다)
    # url_path를 직접 지정해서 각 페이지 주소가 겹치지 않게 한다.
    pages = [
        st.Page(lambda: render_index_page(geo, df), title="안심지수 히트맵", url_path="index"),
        st.Page(lambda: render_facility_page(facilities), title="시설 찾기", url_path="facilities"),
        st.Page(lambda: render_route_page(facilities), title="길찾기", url_path="route"),
    ]
    st.navigation(pages).run()


main()
