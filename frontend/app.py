
import json
import os
import random
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

BASE_DIR = Path(__file__).resolve().parent.parent
GEOJSON_PATH = BASE_DIR / "data" / "seoul_districts.geojson"
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")
NAVER_MAPS_CLIENT_ID = os.getenv("NAVER_MAPS_CLIENT_ID")


@st.cache_data
def load_geojson():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_district_scores(geo):

    districts = [feat["properties"]["name"] for feat in geo["features"]]

    random.seed(42)
    df = pd.DataFrame(
        {
            "구": districts,
            "안심지수": [random.randint(40, 100) for _ in districts],
            "CCTV_점수": [random.randint(0, 100) for _ in districts],
            "귀갓길_점수": [random.randint(0, 100) for _ in districts],
            "파출소_접근성": [random.randint(0, 100) for _ in districts],
        }
    )
    return df


def _polygon_centroid(geometry: dict) -> tuple:

    def flatten(coords):
        if isinstance(coords[0], (int, float)):
            yield coords
        else:
            for c in coords:
                yield from flatten(c)

    points = list(flatten(geometry["coordinates"]))
    lats = [p[1] for p in points]
    lngs = [p[0] for p in points]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


@st.cache_data
def get_facility_markers(geo):

    rows = []
    for feat in geo["features"]:
        name = feat["properties"]["name"]
        lat, lng = _polygon_centroid(feat["geometry"])
        rows.append({"이름": f"{name} 대표지점(더미)", "위도": lat, "경도": lng, "종류": "더미"})
    return pd.DataFrame(rows)


def render_naver_map(client_id: str, facilities: pd.DataFrame, height: int = 550) -> str:

    markers_json = json.dumps(
        facilities.rename(columns={"위도": "lat", "경도": "lng", "이름": "name"})
        [["name", "lat", "lng"]]
        .to_dict(orient="records"),
        ensure_ascii=False,
    )

    return f"""
    <div id="naver-map" style="width:100%;height:{height}px;"></div>
    <script type="text/javascript"
        src="https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId={client_id}"></script>
    <script>
        var map = new naver.maps.Map('naver-map', {{
            center: new naver.maps.LatLng(37.5665, 126.9780),
            zoom: 11
        }});

        var facilities = {markers_json};
        facilities.forEach(function(f) {{
            new naver.maps.Marker({{
                position: new naver.maps.LatLng(f.lat, f.lng),
                map: map,
                title: f.name
            }});
        }});

        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(function(pos) {{
                var myLatLng = new naver.maps.LatLng(pos.coords.latitude, pos.coords.longitude);
                new naver.maps.Marker({{
                    position: myLatLng,
                    map: map,
                    icon: {{
                        content: '<div style="background:#4285F4;border:2px solid white;border-radius:50%;width:14px;height:14px;"></div>',
                        anchor: new naver.maps.Point(7, 7)
                    }},
                    title: '내 위치'
                }});
                map.setCenter(myLatLng);
            }}, function(err) {{
                console.log('위치 정보를 가져오지 못했습니다: ' + err.message);
            }});
        }}
    </script>
    """


st.set_page_config(page_title="서울시 치안 안전 지수", layout="wide")
st.title("자치구별 치안 안전 지수 대시보드")
st.caption("※ 현재 백엔드 데이터 연동 전, 더미 데이터로 화면을 확인 중입니다.")

geo = load_geojson()
df = get_district_scores(geo)

st.sidebar.header("필터")
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + sorted(df["구"].tolist()))

tab_index, tab_naver = st.tabs(["안심지수 히트맵", "경찰서·시설 위치"])

with tab_index:
    col_map, col_detail = st.columns([2, 1])

    with col_map:
        m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
        choropleth = folium.Choropleth(
            geo_data=geo,
            data=df,
            columns=["구", "안심지수"],
            key_on="feature.properties.name",
            fill_color="YlGnBu",
            fill_opacity=0.75,
            line_opacity=0.5,
            legend_name="안심 지수(더미)",
        ).add_to(m)

        choropleth.geojson.add_child(
            folium.GeoJsonTooltip(fields=["name"], aliases=["자치구"])
        )

        st_folium(m, width=700, height=550, returned_objects=[])

    with col_detail:
        st.subheader("자치구 랭킹")
        st.dataframe(
            df.sort_values("안심지수", ascending=False)[["구", "안심지수"]],
            width="stretch",
            hide_index=True,
        )

with tab_naver:
    if not NAVER_MAPS_CLIENT_ID:
        st.warning(
            "NAVER_MAPS_CLIENT_ID가 설정되지 않았습니다. "
            "프로젝트 루트의 .env 파일에 `***REMOVED***발급받은값`를 추가하세요."
        )
    else:
        st.caption("브라우저가 위치 권한을 물어보면 허용해야 '내 위치'가 표시됩니다.")
        facilities = get_facility_markers(geo)
        (STATIC_DIR / "naver_map.html").write_text(
            render_naver_map(NAVER_MAPS_CLIENT_ID, facilities), encoding="utf-8"
        )
        st.iframe("/app/static/naver_map.html", height=560)
        st.dataframe(facilities, width="stretch", hide_index=True)

if selected_gu != "전체":
    row = df[df["구"] == selected_gu].iloc[0]
    st.sidebar.markdown(f"### {selected_gu} 상세")
    st.sidebar.metric("안심지수", f"{row['안심지수']}점")
    st.sidebar.progress(row["CCTV_점수"] / 100, text=f"CCTV 점수 {row['CCTV_점수']}")
    st.sidebar.progress(row["귀갓길_점수"] / 100, text=f"귀갓길 점수 {row['귀갓길_점수']}")
    st.sidebar.progress(
        row["파출소_접근성"] / 100, text=f"파출소 접근성 {row['파출소_접근성']}"
    )
