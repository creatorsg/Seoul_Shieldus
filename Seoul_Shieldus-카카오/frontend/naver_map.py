"""
네이버 지도 JS SDK 렌더링 - HTML/JS는 templates/naver_map.html에 분리해두고,
여기서는 데이터만 채워서 완성된 HTML을 만들고 파일로 저장하는 역할만 한다.

st.iframe()에 HTML 문자열을 바로 넘기면 안 된다 (srcdoc 방식이라 iframe의 출처가
about:srcdoc이 되어 네이버의 도메인 인증이 항상 실패한다). 반드시 정적 파일로 저장한 뒤,
/app/static/ 경로로 st.iframe에 넘겨서 실제 URL로 서빙해야 한다.
인증 파라미터는 ncpKeyId이며, NCP 콘솔에 Web 서비스 URL을 등록해야 인증이 통과된다.

가로등처럼 마커 개수가 아주 많은 데이터는 낱개로 찍으면 브라우저가 버벅여서,
NAVER가 공식 제공하는 MarkerClustering.js(static/vendor/)로 묶어서 그린다.
"""

import hashlib
import json
from pathlib import Path
from string import Template

import pandas as pd

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ROOT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

FACILITY_TEMPLATE_PATH = TEMPLATE_DIR / "naver_map.html"
FACILITY_STATIC_FILENAME = "naver_map.html"
FACILITY_STATIC_URL_PATH = f"/app/static/{FACILITY_STATIC_FILENAME}"

ROUTE_TEMPLATE_PATH = TEMPLATE_DIR / "route_map.html"
ROUTE_STATIC_FILENAME = "route_map.html"
ROUTE_STATIC_URL_PATH = f"/app/static/{ROUTE_STATIC_FILENAME}"

# 시설 종류별 마커 색상. 여러 종류를 동시에 켜도 구분되도록 색을 다르게 준다.
FACILITY_TYPE_STYLES = {
    "지구대": "#1565C0",
    "파출소": "#2E7D32",
    "가로등": "#F9A825",
}


def _build_filter_controls(counts: dict) -> str:
    """종류별 마커 on/off 체크박스 HTML을 만든다. 가로등은 개수가 많아 기본은 꺼둔다."""
    labels = []
    for type_name, color in FACILITY_TYPE_STYLES.items():
        count = counts.get(type_name, 0)
        checked = "" if type_name == "가로등" else "checked"
        labels.append(
            '<label style="margin-right:14px;font-size:14px;">'
            f'<input type="checkbox" value="{type_name}" {checked}> '
            f'<span style="display:inline-block;width:10px;height:10px;background:{color};'
            'border-radius:50%;margin:0 4px;"></span>'
            f"{type_name} ({count:,})</label>"
        )
    return "".join(labels)


def _versioned_url(base_url: str, html: str) -> str:
    """
    iframe은 src 문자열이 그대로면 내용이 바뀌어도 다시 불러오지 않는다(브라우저가 새 요청을
    보내지 않음). 목적지를 바꿔서 파일 내용이 달라져도 st.iframe에 매번 같은 경로만 넘기면
    지도가 옛날 경로를 계속 보여주는 문제가 생겨서, 내용 해시를 쿼리스트링으로 붙여
    내용이 바뀔 때만 URL도 바뀌게 한다. (Streamlit 정적 서빙은 쿼리스트링을 무시하고
    경로로만 파일을 찾으므로 서빙 자체엔 영향 없음)
    """
    content_hash = hashlib.md5(html.encode("utf-8")).hexdigest()[:8]
    return f"{base_url}?v={content_hash}"


def _markers_by_type(police: pd.DataFrame) -> dict:
    """지구대/파출소 DataFrame을 종류별 {name, lat, lng} 리스트로 묶는다. 두 지도(시설/길찾기)가 같이 쓴다."""
    return {
        type_name: group.rename(columns={"위도": "lat", "경도": "lng", "이름": "name"})[
            ["name", "lat", "lng"]
        ].to_dict(orient="records")
        for type_name, group in police.groupby("종류")
    }


def render_naver_map(
    client_id: str,
    police: pd.DataFrame,
    street_lights: pd.DataFrame,
    height: int = 550,
) -> str:
    """지구대/파출소/가로등을 종류별 색상 마커 + on/off 체크박스로 표시하는 HTML을 반환한다."""
    markers_by_type = _markers_by_type(police)
    street_light_points = street_lights.rename(columns={"위도": "lat", "경도": "lng"})[
        ["lat", "lng"]
    ].to_dict(orient="records")

    counts = {type_name: len(rows) for type_name, rows in markers_by_type.items()}
    counts["가로등"] = len(street_light_points)

    template = Template(FACILITY_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        client_id=client_id,
        height=height,
        filter_controls_html=_build_filter_controls(counts),
        type_styles_json=json.dumps(FACILITY_TYPE_STYLES, ensure_ascii=False),
        markers_by_type_json=json.dumps(markers_by_type, ensure_ascii=False),
        street_lights_json=json.dumps(street_light_points, ensure_ascii=False),
    )


def write_static_map(client_id: str, police: pd.DataFrame, street_lights: pd.DataFrame) -> str:
    """네이버 지도(시설 위치 탭) HTML을 STATIC_DIR에 저장하고, st.iframe에 넘길 URL 경로를 반환한다."""
    STATIC_DIR.mkdir(exist_ok=True)
    ROOT_STATIC_DIR.mkdir(exist_ok=True)
    html = render_naver_map(client_id, police, street_lights)
    (STATIC_DIR / FACILITY_STATIC_FILENAME).write_text(html, encoding="utf-8")
    (ROOT_STATIC_DIR / FACILITY_STATIC_FILENAME).write_text(html, encoding="utf-8")
    return _versioned_url(FACILITY_STATIC_URL_PATH, html)


def render_route_map(
    client_id: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
    height: int = 560,
) -> str:
    """
    지구대/파출소 마커(목적지는 강조) + 내 위치 + 경로 폴리라인을 그리는 HTML을 반환한다.
    my_location, route는 Streamlit(Python)에서 이미 구한 값을 그대로 데이터로 꽂아 넣는다
    (TMAP 호출은 route_finder.py가 서버 쪽에서 하고, 여기서는 좌표만 그린다).
    """
    template = Template(ROUTE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        client_id=client_id,
        height=height,
        type_styles_json=json.dumps(FACILITY_TYPE_STYLES, ensure_ascii=False),
        markers_by_type_json=json.dumps(_markers_by_type(police), ensure_ascii=False),
        destination_name_json=json.dumps(destination_name, ensure_ascii=False),
        my_location_json=json.dumps(
            {"lat": my_location[0], "lng": my_location[1]} if my_location else None
        ),
        route_json=json.dumps(
            [{"lat": lat, "lng": lng} for lat, lng in (route or [])], ensure_ascii=False
        ),
    )


def write_route_map(
    client_id: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
) -> str:
    """길찾기 탭용 지도 HTML을 저장한다. 시설 위치 탭(naver_map.html)과 파일을 분리해서 서로 덮어쓰지 않게 한다."""
    STATIC_DIR.mkdir(exist_ok=True)
    ROOT_STATIC_DIR.mkdir(exist_ok=True)
    html = render_route_map(client_id, police, my_location, destination_name, route)
    (STATIC_DIR / ROUTE_STATIC_FILENAME).write_text(html, encoding="utf-8")
    (ROOT_STATIC_DIR / ROUTE_STATIC_FILENAME).write_text(html, encoding="utf-8")
    return _versioned_url(ROUTE_STATIC_URL_PATH, html)
