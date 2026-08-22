"""
서울시 치안 안전 지수 대시보드 - 프론트엔드 (Streamlit + folium)

이 파일은 화면 조립(페이지 렌더링 + main())만 담당한다. CSS/HTML 상수는 styles.py, 데이터 형태
상수는 constants.py, 데이터 로딩은 data_access.py, 네이버 지도 HTML 생성은 naver_map.py에 있다.
각 함수/상수의 자세한 설계 배경·트레이드오프·버그 히스토리는 frontend.md에 정리되어 있다.

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

from colors import score_to_color
from constants import CCTV_PURPOSE_FIELDS, DETAIL_SCORE_FIELDS, ROUTE_MODES
from data_access import (
    BASE_DIR,
    _polygon_centroid,
    get_cctv_stats,
    get_district_scores,
    get_facility_markers,
    get_safe_paths,
    get_street_light_markers,
    load_geojson,
)
from naver_map import build_facility_map_js, build_route_map_js
from route_finder import fetch_route, find_nearest_facility, get_current_location, get_tmap_app_key
from styles import (
    DISTRICT_DETAIL_CSS,
    EXPANDER_CARD_CSS,
    GLASS_CARD_CSS,
    GPS_WAIT_SPINNER_HTML,
    HIDE_STREAMLIT_CHROME_CSS,
    HOME_CARD_CSS,
    MAP_CARD_CSS,
    PAGE_TRANSITION_CSS,
    PRETENDARD_CSS_URL,
    PRETENDARD_FONT_CSS,
    SCORE_BAR_CSS,
    SELECTBOX_CSS,
    SIDEBAR_CSS,
    VIEW_TOGGLE_CSS,
)

# override=True: .env를 나중에 고쳐도 프로세스를 재시작하기 전까진 os.environ의 예전 값이
# 남아있는 문제를 막는다 (route_finder.get_tmap_app_key()에서 겪은 것과 같은 종류의 문제).
load_dotenv(BASE_DIR / ".env", override=True)
NAVER_MAPS_CLIENT_ID = os.getenv("NAVER_MAPS_CLIENT_ID")


def _warn_missing_env(var_name: str) -> None:
    """.env에 API 키가 빠졌을 때 공통 문구로 경고한다 (실패가 아니라 미설정이라 warning)."""
    st.warning(
        f"{var_name}가 설정되지 않았습니다. "
        f"프로젝트 루트의 .env 파일에 `{var_name}=발급받은값`를 추가하세요."
    )


def _render_score_bar(label: str, score: float) -> None:
    """점수만큼 색(빨강~초록)이 바뀌며 채워지는 막대를 그린다."""
    color = score_to_color(score)
    width = max(0, min(100, score))
    st.markdown(
        f"""
        <div style="margin-bottom:10px;">
          <div style="font-size:13px;margin-bottom:3px;">{label} {score:.1f}</div>
          <div style="background:#E0E0E0;border-radius:4px;height:8px;">
            <div class="score-bar-fill" style="--fill-width:{width}%;width:{width}%;
                background:{color};height:8px;border-radius:4px;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _replay_score_bar_animations() -> None:
    """.score-bar-fill 채우기 애니메이션을 매 리런마다 강제로 재생시킨다 (배경: frontend.md)."""
    st.session_state["_score_bar_tick"] = st.session_state.get("_score_bar_tick", 0) + 1
    js = """
    (function() {
        var d = window.parent.document;
        d.querySelectorAll('.score-bar-fill').forEach(function (el) {
            el.style.animation = 'none';
            void el.offsetHeight;
            el.style.animation = '';
        });
        return true;
    })()
    """
    streamlit_js_eval(
        js_expressions=js,
        key=f"score_bar_replay_{st.session_state['_score_bar_tick']}",
        want_output=False,
    )


def render_ranking_table(df) -> None:
    """자치구 랭킹 표에 안심지수 색상(colors.score_to_color 기준)을 옅게 입힌다."""
    ranking = df.sort_values("안심지수", ascending=False)[["구", "안심지수"]]
    styled = ranking.style.apply(
        lambda row: [f"background-color: {score_to_color(row['안심지수'])}22"] * len(row),
        axis=1,
    )
    st.dataframe(styled, width="stretch", hide_index=True)


def render_district_detail(row, df, cctv_stats) -> None:
    """선택된 자치구 하나의 안심지수/세부 점수 + CCTV 목적별 통계를 그린다."""
    st.markdown(DISTRICT_DETAIL_CSS, unsafe_allow_html=True)
    st.markdown(GLASS_CARD_CSS, unsafe_allow_html=True)
    st.markdown(SCORE_BAR_CSS, unsafe_allow_html=True)
    st.markdown(f"#### {row['구']} 상세")
    seoul_avg = round(df["안심지수"].mean(), 1)
    diff = row["안심지수"] - seoul_avg
    with st.container(border=True):
        st.markdown("<span class='glass-card-marker'></span>", unsafe_allow_html=True)
        st.metric(
            "안심지수",
            f"{row['안심지수']}점",
            delta=f"서울 평균({seoul_avg}점) 대비 {diff:+.1f}점",
        )
        for label, col in DETAIL_SCORE_FIELDS:
            _render_score_bar(label, row[col])
    _replay_score_bar_animations()

    if cctv_stats.empty:
        return
    district_cctv = cctv_stats[cctv_stats["구"] == row["구"]]
    if district_cctv.empty:
        return
    c = district_cctv.iloc[0]
    with st.container(border=True):
        st.markdown("<span class='glass-card-marker'></span>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:24px;font-weight:600;margin-top:32px;'>CCTV 목적별 설치 현황</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"총 {c['총_CCTV']:,}대 (그중 방범 목적 {c['방범_합계']:,}대)")
        # sort=False + horizontal=True 유지 필수 (이유: frontend.md #_sorted_cctv_purpose_counts)
        st.bar_chart(_sorted_cctv_purpose_counts(c), height=220, sort=False, horizontal=True)


def _sorted_cctv_purpose_counts(c) -> dict:
    """CCTV 목적별 대수를 많은 순으로 정렬한 dict를 반환한다 (막대그래프 x축 순서로 그대로 쓰임)."""
    counts = {label: c[col] for col, label in CCTV_PURPOSE_FIELDS}
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def _geo_with_score_properties(geo: dict, df) -> dict:
    """geojson feature.properties에 안심지수를 미리 섞어 넣은 깊은 복사본을 반환한다."""
    scores = dict(zip(df["구"], df["안심지수"]))
    geo_copy = copy.deepcopy(geo)
    for feat in geo_copy["features"]:
        name = feat["properties"]["name"]
        feat["properties"]["score"] = scores.get(name)
    return geo_copy


def _add_district_labels(m: "folium.Map", geo: dict) -> None:
    """자치구 이름을 각 자치구 중심점에 고정 텍스트 라벨로 올린다."""
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


def render_index_page(geo: dict, df, cctv_stats) -> None:
    """
    안심지수 히트맵 페이지: 지도를 위에 크게 띄우고, 아래에서 "전체 확인"(표) /
    "지역별 상세"(자치구 하나 골라서 점수 + CCTV 목적별 통계 뜯어보기) 를 토글로 전환한다.
    """
    st.header("안심지수 히트맵")
    st.markdown(EXPANDER_CARD_CSS, unsafe_allow_html=True)

    with st.expander("안심지수는 어떻게 계산되나요?"):
        st.markdown(
            "구별 **CCTV 설치 현황**, **지구대/파출소 접근성**, **안심귀갓길**, **가로등**, "
            "**범죄 안전도**, 이렇게 5개 지표를 종합해 0~100점으로 계산합니다.\n\n "
            "각 지표는 자치구 상세 보기에서 점수별로 따로 확인할 수 있습니다."
        )

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
    # Leaflet 폴리곤 클릭 시 생기는 포커스 테두리 제거 (배경: frontend.md #render_index_page)
    m.get_root().header.add_child(
        folium.Element("<style>.leaflet-interactive:focus { outline: none; }</style>")
    )
    geo_scored = _geo_with_score_properties(geo, df)
    choropleth = folium.Choropleth(
        geo_data=geo_scored,
        data=df,
        columns=["구", "안심지수"],
        key_on="feature.properties.name",
        fill_color="RdYlGn",
        fill_opacity=0.75,
        line_opacity=0.5,
        legend_name="안심 지수",
        highlight=True,
    ).add_to(m)

    tooltip_popup_fields = ["name", "score"]
    tooltip_popup_aliases = ["자치구", "안심지수"]
    choropleth.geojson.add_child(
        folium.GeoJsonTooltip(fields=tooltip_popup_fields, aliases=tooltip_popup_aliases)
    )
    choropleth.geojson.add_child(
        folium.GeoJsonPopup(fields=tooltip_popup_fields, aliases=tooltip_popup_aliases)
    )

    _add_district_labels(m, geo)

    st_folium(m, height=550, returned_objects=[], use_container_width=True)

    view = st.radio(
        "보기 방식", ["전체 확인", "지역별 상세"], horizontal=True, label_visibility="collapsed"
    )

    if view == "전체 확인":
        st.subheader("자치구 랭킹")
        render_ranking_table(df)
    else:
        selected_gu = st.selectbox("자치구 선택", sorted(df["구"].tolist()))
        render_district_detail(df[df["구"] == selected_gu].iloc[0], df, cctv_stats)


def _facility_display_table(facilities, df):
    """시설 찾기 표에 위도/경도 대신 구/주소/범죄안전 점수를 보여준다."""
    score_by_district = dict(zip(df["구"], df["범죄안전_점수"]))
    table = facilities[["이름", "구", "주소", "종류"]].copy()
    table["범죄안전 점수"] = table["구"].map(score_by_district)
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
    st.markdown(
        '<div id="shieldus-facility-filters" style="margin-bottom:8px;display:flex;'
        'flex-wrap:wrap;gap:8px 16px;"></div>'
        '<div id="shieldus-facility-map" style="width:100%;height:620px;"></div>',
        unsafe_allow_html=True,
    )
    _run_map_js(
        build_facility_map_js(NAVER_MAPS_CLIENT_ID, facilities, street_lights, safe_paths),
        "_facility_map_tick",
    )
    st.caption(
        f"가로등({len(street_lights):,}개)과 안심귀갓길({len(safe_paths):,}개 노선)은 기본은 꺼져 있고, "
        "켜면 표시됩니다. 가로등은 개수가 많아 클러스터로 묶여서 나옵니다. "
        "지도 위 지구대/파출소 마커를 클릭(모바일은 터치)하면 주소가 복사됩니다."
    )
    st.dataframe(_facility_display_table(facilities, df), width="stretch", hide_index=True)


def _run_map_js(js: str, tick_key: str) -> None:
    """
    naver_map.py의 build_facility_map_js()/build_route_map_js()가 만든 JS를 window.parent에
    실행시키는 공용 헬퍼(지도 두 개가 같이 쓴다). 페이지가 리런될 때마다(위치/목적지/경로가
    바뀔 수 있으니) 다시 실행돼야 해서, streamlit_js_eval의 key를 매번 새로 만든다 -
    _replay_score_bar_animations/_restore_scroll_position과 같은 패턴이다.

    지도를 별도 static HTML 파일로 만들어 st.iframe(url)로 서빙하던 예전 방식은 배포에서
    "지도 무한로딩"으로 막혔다(Streamlit Community Cloud의 커스텀 static 파일 서빙이 실제로는
    신뢰할 수 없었다 - naver_map.py 모듈 docstring 참고). 그래서 지금은 별도 HTTP 요청도, 별도
    iframe도 만들지 않고 이 함수로 window.parent(진짜 배포 도메인)에 직접 지도를 그린다.
    """
    st.session_state[tick_key] = st.session_state.get(tick_key, 0) + 1
    streamlit_js_eval(
        js_expressions=js,
        key=f"{tick_key}_{st.session_state[tick_key]}",
        want_output=False,
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

    # 매번 get_tmap_app_key()로 새로 읽는다 - .env 수정 후 재시작 없이 리런만으로 반영되게 하기 위함.
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

    st.markdown(
        '<div id="shieldus-route-map" style="width:100%;height:560px;"></div>',
        unsafe_allow_html=True,
    )
    _run_map_js(
        build_route_map_js(
            NAVER_MAPS_CLIENT_ID,
            facilities,
            (my_lat, my_lng),
            selected_name,
            route_info["coords"] if route_info else None,
        ),
        "_route_map_tick",
    )
    st.caption("지도 위 지구대/파출소 마커를 클릭(모바일은 터치)하면 주소가 복사됩니다.")

    if route_info:
        st.caption(
            f"내 위치 → {selected_name} {mode_label} 경로: "
            f"약 {route_info['distance_km']}km, {route_info['time_min']}분 예상"
        )
    elif tmap_app_key:
        st.caption("경로를 가져오지 못했습니다. TMAP 앱에 해당 이동수단 상품이 등록되어 있는지 확인하세요.")


def render_home_page(page_heatmap, page_facility, page_route) -> None:
    """랜딩 페이지: 서비스 소개 + 3개 핵심 기능으로 바로 진입하는 카드."""
    st.markdown(HOME_CARD_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:48px;'></div>", unsafe_allow_html=True)
    img_l, img_c, img_r = st.columns([1, 12, 1])
    with img_c:
        # BASE_DIR 절대경로 필수 (cwd에 따라 못 찾는 문제 - 배경: frontend.md #render_home_page)
        st.image(str(BASE_DIR / "frontend" / "hero.png"), use_container_width=True)

    st.markdown(
        """
        <div style="text-align:center;padding:16px 24px 32px;">
          <h1 style="font-size:40px;font-weight:600;line-height:1.35;margin:0 0 16px;">
            늦은 밤 골목길, 혼자 걸어도 안전할까요?
          </h1>
          <p style="font-size:16px;line-height:1.7;color:#5B7A99;margin:0 auto;max-width:520px;">
            CCTV·가로등·파출소 접근성·귀갓길 안전도를 종합한 안심지수로 서울의 치안을
            \n한눈에 확인하고, 가까운 치안시설과 길찾기까지 지원합니다.
            \n서울 쉴더스와 함께 하세요.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # accent: 사이드바/카드 호버 테두리와 같은 색 기준 (히트맵=브랜드 그린, 시설찾기/길찾기=지도 마커 색)
    icon_shield = (
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" '
        'stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 2.5L4.5 5.5v5.5c0 5.2 3.3 9.6 7.5 10.8c4.2-1.2 7.5-5.6 7.5-10.8V5.5z"/>'
        '<path d="M8.7 12.2l2.3 2.3l4.3-4.6"/>'
        "</svg>"
    )
    icon_pin = (
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" '
        'stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 21.5C12 21.5 5.5 14.7 5.5 9.3C5.5 5.7 8.4 2.8 12 2.8s6.5 2.9 6.5 6.5'
        'C18.5 14.7 12 21.5 12 21.5z"/>'
        '<circle cx="12" cy="9.3" r="2.4"/>'
        "</svg>"
    )
    icon_compass = (
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" '
        'stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="9.2"/>'
        '<path d="M15.3 8.7l-2 4.6l-4.6 2l2-4.6z" fill="{c}" stroke-width="0.6"/>'
        "</svg>"
    )
    cards = [
        (page_heatmap, icon_shield, "#2E7D32", "안심지수 히트맵", "자치구별 안심지수를 지도와 랭킹으로 비교해보세요."),
        (page_facility, icon_pin, "#D81B60", "시설 찾기", "가까운 지구대·파출소·가로등을 지도에서 확인하세요."),
        (page_route, icon_compass, "#1565C0", "길찾기", "가장 가까운 치안시설까지 경로를 안내합니다."),
    ]
    for col, (page, icon_svg, accent, title, desc) in zip(st.columns(3), cards):
        with col, st.container(border=True):
            st.markdown(
                f"<div class='home-card-icon-badge' style='background:{accent}1A;'>"
                f"{icon_svg.format(c=accent)}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{title}**")
            st.caption(desc)
            st.page_link(page, label="바로가기 →")

    st.markdown(
        """
        <div style="text-align:center;margin-top:32px;padding-top:16px;
                    border-top:1px solid rgba(30,111,176,0.15);">
          <p style="font-size:12px;color:#5B7A99;margin:0;">
            데이터 출처: 서울 열린데이터광장, 경찰청, 서울시설공단, 공공데이터 포탈
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _restore_scroll_position(page_key: str) -> None:
    """(베스트 에포트) 리런 시 본문 스크롤 위치를 복원한다 (배경/사고 이력: frontend.md)."""
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


def _inject_head_scripts() -> None:
    """<head> 태그 추가 + 사이드바 워드마크 재배치를 한 번의 JS 호출로 처리한다 (배경: frontend.md)."""
    js = f"""
    (function() {{
        var d = window.parent.document;
        if (!d.querySelector('link[rel="manifest"]')) {{
            var link = d.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/static/manifest.json';
            d.head.appendChild(link);
        }}
        if (!d.querySelector('meta[name="theme-color"]')) {{
            var meta = d.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#2E7D32';
            d.head.appendChild(meta);
        }}
        if (!d.querySelector('link[data-pretendard-font]')) {{
            var fontLink = d.createElement('link');
            fontLink.rel = 'stylesheet';
            fontLink.href = '{PRETENDARD_CSS_URL}';
            fontLink.setAttribute('data-pretendard-font', '1');
            d.head.appendChild(fontLink);
        }}
        var brand = d.querySelector('.sidebar-brand');
        var spacer = d.querySelector('[data-testid="stLogoSpacer"]');
        if (brand && spacer) {{
            var brandContainer = brand.closest('[data-testid="stElementContainer"]');
            if (brandContainer && brandContainer.parentElement !== spacer) {{
                spacer.appendChild(brandContainer);
            }}
        }}
        return true;
    }})()
    """
    streamlit_js_eval(js_expressions=js, key="head_scripts_inject", want_output=False)


def main() -> None:
    st.set_page_config(
        page_title="서울시 치안 안전 지수",
        layout="wide",
        menu_items={"Get help": None, "Report a bug": None, "About": None},
    )
    # !important 우회를 위해 sidebar-brand 클래스를 씀 (배경: frontend.md #main)
    st.sidebar.markdown(
        "<div class='sidebar-brand' style='padding:8px 0 8px 16px;font-size:20px;"
        "font-weight:700;letter-spacing:0.5px;white-space:nowrap;'>SEOUL SHIELDUS</div>",
        unsafe_allow_html=True,
    )
    # 6개를 한 번에 합쳐서 넣는다 - 따로 넣으면 flex gap을 하나씩 차지해 제목이 밀려 내려간다.
    st.markdown(
        HIDE_STREAMLIT_CHROME_CSS
        + PAGE_TRANSITION_CSS
        + VIEW_TOGGLE_CSS
        + PRETENDARD_FONT_CSS
        + SIDEBAR_CSS
        + MAP_CARD_CSS
        + SELECTBOX_CSS,
        unsafe_allow_html=True,
    )
    _inject_head_scripts()
    st.title("서울 쉴더스 : 서울의 안전을 확인하다")

    geo = load_geojson()
    df = get_district_scores(geo)
    facilities = get_facility_markers(geo)
    cctv_stats = get_cctv_stats()

    # url_path를 직접 지정한다 - 콜백이 전부 lambda라 이름으로 자동 유추가 안 된다.
    # page_home의 lambda가 다른 page 변수를 참조하지만, 클로저라 호출 시점엔 이미 다 정의돼 있어 안전하다.
    page_home = st.Page(
        lambda: render_home_page(page_heatmap, page_facility, page_route),
        title="홈",
        url_path="home",
    )
    page_heatmap = st.Page(
        lambda: render_index_page(geo, df, cctv_stats),
        title="안심지수 히트맵",
        url_path="index",
    )
    page_facility = st.Page(
        lambda: render_facility_page(facilities, df),
        title="시설 찾기",
        url_path="facilities",
    )
    page_route = st.Page(
        lambda: render_route_page(facilities),
        title="길찾기",
        url_path="route",
    )
    pages = [page_home, page_heatmap, page_facility, page_route]
    current_page = st.navigation(pages)

    with st.sidebar:
        # position:absolute로 화면 크기 무관하게 좌측 하단 고정 (배경: frontend.md #main)
        st.markdown("<span class='sidebar-logo-marker'></span>", unsafe_allow_html=True)
        st.image(str(BASE_DIR / "frontend" / "logo.png"), width=67)

    current_page.run()
    _restore_scroll_position(current_page.url_path or "home")


main()
