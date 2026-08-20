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
from kakao_map import write_route_map as write_kakao_route_map, write_static_map as write_kakao_static_map
from naver_map import write_route_map as write_naver_route_map, write_static_map as write_naver_static_map
from route_finder import TMAP_APP_KEY, fetch_route, find_nearest_facility, get_current_location
from styles import (
    apply_dark_theme,
    render_dashboard_header,
    render_route_summary_card,
    render_score_bar_html,
)

load_dotenv(BASE_DIR / ".env")
KAKAO_MAP_APP_KEY = os.getenv("KAKAO_MAP_APP_KEY")
NAVER_MAPS_CLIENT_ID = os.getenv("NAVER_MAPS_CLIENT_ID")

ROUTE_MODES = {"도보": "pedestrian", "자동차": "car"}

# 자치구 상세 패널에 표시할 세부 점수 (라벨, df 컬럼명)
DETAIL_SCORE_FIELDS = [
    ("CCTV 점수", "CCTV_점수"),
    ("귀갓길 점수", "귀갓길_점수"),
    ("파출소 접근성", "파출소_접근성"),
    ("가로등 점수", "가로등_점수"),
]


def _warn_missing_env(var_name: str) -> None:
    """API 키 등 .env 설정이 빠졌을 때 공통 문구로 경고한다."""
    st.warning(
        f"{var_name}가 설정되지 않았습니다. "
        f"프로젝트 루트의 .env 파일에 `{var_name}=발급받은값`를 추가하세요."
    )


def render_district_detail(row) -> None:
    """선택된 자치구 하나의 안심지수/세부 점수를 그린다."""
    score_color = score_to_color(row['안심지수'])
    st.markdown(
        f"""
        <div class="dark-card">
            <div style="font-size: 13px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">선택 자치구 분석</div>
            <div style="font-size: 22px; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">{row['구']} 상세 리포트</div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px;">
                <span style="font-size: 32px; font-weight: 800; color: {score_color};">{row['안심지수']:.1f}</span>
                <span style="font-size: 14px; color: #94A3B8;">/ 100 점 (종합 안심지수)</span>
            </div>
            <hr style="border: none; border-top: 1px solid #263449; margin: 12px 0 16px 0;" />
        """,
        unsafe_allow_html=True,
    )
    for label, col in DETAIL_SCORE_FIELDS:
        st.markdown(render_score_bar_html(label, row[col]), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_index_page(geo: dict, df) -> None:
    """안심지수 히트맵 페이지."""
    render_dashboard_header("안심지수 히트맵", "서울시 25개 자치구별 치안 보안 인프라 종합 평가 현황")

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
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

    choropleth.geojson.add_child(
        folium.GeoJsonTooltip(fields=["name"], aliases=["자치구"])
    )

    st_folium(m, height=550, returned_objects=[], use_container_width=True)

    view = st.radio(
        "보기 방식", ["전체 확인", "지역별 상세"], horizontal=True, label_visibility="collapsed"
    )

    if view == "전체 확인":
        st.markdown("<h4 style='margin-top:16px; margin-bottom:8px;'>자치구 안심지수 랭킹</h4>", unsafe_allow_html=True)
        ranking = df.sort_values("안심지수", ascending=False)[["구", "안심지수"]]
        st.dataframe(ranking, width="stretch", hide_index=True)
    else:
        selected_gu = st.selectbox("자치구 선택", sorted(df["구"].tolist()))
        render_district_detail(df[df["구"] == selected_gu].iloc[0])


def render_facility_page(facilities) -> None:
    """시설 찾기 페이지."""
    render_dashboard_header("치안 인프라 시설 찾기", "서울시 주요 지구대/파출소 위치 및 여성 안심 가로등 분포")

    street_lights = get_street_light_markers()
    map_url = None
    provider_name = ""

    if KAKAO_MAP_APP_KEY:
        try:
            map_url = write_kakao_static_map(KAKAO_MAP_APP_KEY, facilities, street_lights)
            provider_name = "Kakao Maps"
        except Exception:
            pass

    if not map_url and NAVER_MAPS_CLIENT_ID:
        try:
            map_url = write_naver_static_map(NAVER_MAPS_CLIENT_ID, facilities, street_lights)
            provider_name = "Naver Maps (Fallback)"
        except Exception:
            pass

    if not map_url:
        _warn_missing_env("KAKAO_MAP_APP_KEY 또는 NAVER_MAPS_CLIENT_ID")
        return

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#111827; border:1px solid #263449; padding:10px 16px; border-radius:6px; margin-bottom:12px; font-size:13px; color:#94A3B8;">
            <div>지도 제공: <strong style="color:#06B6D4;">{provider_name}</strong></div>
            <div>※ 위치 권한 허용 시 '내 위치'가 지도 상에 함께 표시됩니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.iframe(map_url, height=620)
    st.markdown(
        f"""
        <div style="background:#111827; border:1px solid #263449; padding:10px 16px; border-radius:6px; margin-top:12px; margin-bottom:12px; font-size:12px; color:#94A3B8;">
            💡 <strong>가로등 마커 안내:</strong> 서울시 가로등 데이터는 총 <strong style="color:#F59E0B;">{len(street_lights):,}개</strong>로 개수가 많아 기본은 꺼짐 상태이며, 지도 상단 필터 체크박스를 켜면 클러스터로 표시됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(facilities, width="stretch", hide_index=True)


def render_route_page(facilities) -> None:
    """길찾기 페이지."""
    render_dashboard_header("최적 안심 길찾기", "내 위치 기반 가장 가까운 지구대/파출소 도보 및 차량 최적 경로")

    mode_label = st.radio("이동수단 선택", list(ROUTE_MODES.keys()), horizontal=True)

    location = get_current_location()
    if location is None:
        st.info("브라우저 위치 권한을 확인하는 중입니다...")
        return
    my_lat, my_lng = location

    nearest = find_nearest_facility(my_lat, my_lng, facilities)
    facility_names = facilities["이름"].tolist()
    selected_name = st.selectbox(
        "목적지 선택 (기본: 가장 가까운 치안 시설)",
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

    map_url = None
    provider_name = ""
    route_coords = route_info["coords"] if route_info else None

    if KAKAO_MAP_APP_KEY:
        try:
            map_url = write_kakao_route_map(
                KAKAO_MAP_APP_KEY,
                facilities,
                (my_lat, my_lng),
                selected_name,
                route_coords,
            )
            provider_name = "Kakao Maps"
        except Exception:
            pass

    if not map_url and NAVER_MAPS_CLIENT_ID:
        try:
            map_url = write_naver_route_map(
                NAVER_MAPS_CLIENT_ID,
                facilities,
                (my_lat, my_lng),
                selected_name,
                route_coords,
            )
            provider_name = "Naver Maps (Fallback)"
        except Exception:
            pass

    if not map_url:
        _warn_missing_env("KAKAO_MAP_APP_KEY 또는 NAVER_MAPS_CLIENT_ID")
        return

    if route_info:
        render_route_summary_card(selected_name, mode_label, route_info['distance_km'], route_info['time_min'])
    elif TMAP_APP_KEY:
        st.warning("TMAP 경로를 가져오지 못했습니다. 이동수단 및 옵션을 확인하세요.")

    st.iframe(map_url, height=560)


def main() -> None:
    st.set_page_config(
        page_title="서울시 치안 안전 지수 관제 대시보드",
        layout="wide",
        menu_items={"Get help": None, "Report a bug": None, "About": None},
    )
    apply_dark_theme()

    geo = load_geojson()
    df = get_district_scores(geo)
    facilities = get_facility_markers(geo)

    pages = [
        st.Page(lambda: render_index_page(geo, df), title="안심지수 히트맵", url_path="index"),
        st.Page(lambda: render_facility_page(facilities), title="시설 찾기", url_path="facilities"),
        st.Page(lambda: render_route_page(facilities), title="길찾기", url_path="route"),
    ]
    st.navigation(pages).run()


main()

