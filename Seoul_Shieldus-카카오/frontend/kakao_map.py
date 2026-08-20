"""
카카오 지도 JS SDK 렌더링.

HTML/JS는 templates/kakao_map.html,
templates/kakao_route_map.html에 분리하고,
여기서는 Python 데이터를 JSON으로 주입하여 완성된 HTML을 만든다.

완성된 HTML은 static/에 저장한 뒤 st.iframe()으로 표시한다.
"""

import hashlib
import json
from pathlib import Path
from string import Template

import pandas as pd


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ROOT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

FACILITY_TEMPLATE_PATH = TEMPLATE_DIR / "kakao_map.html"
FACILITY_STATIC_FILENAME = "kakao_map.html"
FACILITY_STATIC_URL_PATH = f"/app/static/{FACILITY_STATIC_FILENAME}"

ROUTE_TEMPLATE_PATH = TEMPLATE_DIR / "kakao_route_map.html"
ROUTE_STATIC_FILENAME = "kakao_route_map.html"
ROUTE_STATIC_URL_PATH = f"/app/static/{ROUTE_STATIC_FILENAME}"


FACILITY_TYPE_STYLES = {
    "지구대": "#1565C0",
    "파출소": "#2E7D32",
    "가로등": "#F9A825",
}


def _build_filter_controls(counts: dict) -> str:
    """시설 종류별 마커 표시 여부 체크박스."""

    labels = []

    for type_name, color in FACILITY_TYPE_STYLES.items():
        count = counts.get(type_name, 0)

        checked = "" if type_name == "가로등" else "checked"

        labels.append(
            '<label style="margin-right:14px;font-size:14px;">'
            f'<input type="checkbox" value="{type_name}" {checked}> '
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'background:{color};border-radius:50%;margin:0 4px;"></span>'
            f"{type_name} ({count:,})"
            "</label>"
        )

    return "".join(labels)


def _versioned_url(base_url: str, html: str) -> str:
    """HTML 변경 시 iframe URL도 변경하여 캐시 문제를 방지한다."""

    content_hash = hashlib.md5(
        html.encode("utf-8")
    ).hexdigest()[:8]

    return f"{base_url}?v={content_hash}"


def _markers_by_type(police: pd.DataFrame) -> dict:
    """지구대/파출소를 종류별 JSON 데이터로 변환."""

    return {
        type_name: group.rename(
            columns={
                "위도": "lat",
                "경도": "lng",
                "이름": "name",
            }
        )[
            ["name", "lat", "lng"]
        ].to_dict(orient="records")

        for type_name, group in police.groupby("종류")
    }


def render_kakao_map(
    app_key: str,
    police: pd.DataFrame,
    street_lights: pd.DataFrame,
    height: int = 550,
) -> str:
    """시설 찾기용 카카오맵 HTML 생성."""

    markers_by_type = _markers_by_type(police)

    street_light_points = (
        street_lights.rename(
            columns={
                "위도": "lat",
                "경도": "lng",
            }
        )[["lat", "lng"]]
        .to_dict(orient="records")
    )

    counts = {
        type_name: len(rows)
        for type_name, rows in markers_by_type.items()
    }

    counts["가로등"] = len(street_light_points)

    template = Template(
        FACILITY_TEMPLATE_PATH.read_text(
            encoding="utf-8"
        )
    )

    return template.substitute(
        app_key=app_key,
        height=height,
        filter_controls_html=_build_filter_controls(counts),
        type_styles_json=json.dumps(
            FACILITY_TYPE_STYLES,
            ensure_ascii=False,
        ),
        markers_by_type_json=json.dumps(
            markers_by_type,
            ensure_ascii=False,
        ),
        street_lights_json=json.dumps(
            street_light_points,
            ensure_ascii=False,
        ),
    )


def write_static_map(
    app_key: str,
    police: pd.DataFrame,
    street_lights: pd.DataFrame,
) -> str:
    """시설 찾기 지도 HTML을 생성하고 static에 저장."""

    STATIC_DIR.mkdir(exist_ok=True)
    ROOT_STATIC_DIR.mkdir(exist_ok=True)

    html = render_kakao_map(
        app_key,
        police,
        street_lights,
    )

    (STATIC_DIR / FACILITY_STATIC_FILENAME).write_text(html, encoding="utf-8")
    (ROOT_STATIC_DIR / FACILITY_STATIC_FILENAME).write_text(html, encoding="utf-8")

    return _versioned_url(
        FACILITY_STATIC_URL_PATH,
        html,
    )


def render_route_map(
    app_key: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
    height: int = 560,
) -> str:
    """길찾기용 카카오맵 HTML 생성."""

    template = Template(
        ROUTE_TEMPLATE_PATH.read_text(
            encoding="utf-8"
        )
    )

    return template.substitute(
        app_key=app_key,
        height=height,

        type_styles_json=json.dumps(
            FACILITY_TYPE_STYLES,
            ensure_ascii=False,
        ),

        markers_by_type_json=json.dumps(
            _markers_by_type(police),
            ensure_ascii=False,
        ),

        destination_name_json=json.dumps(
            destination_name,
            ensure_ascii=False,
        ),

        my_location_json=json.dumps(
            {
                "lat": my_location[0],
                "lng": my_location[1],
            }
            if my_location
            else None
        ),

        route_json=json.dumps(
            [
                {
                    "lat": lat,
                    "lng": lng,
                }
                for lat, lng in (route or [])
            ],
            ensure_ascii=False,
        ),
    )


def write_route_map(
    app_key: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
) -> str:
    """길찾기 지도 HTML 저장."""

    STATIC_DIR.mkdir(exist_ok=True)
    ROOT_STATIC_DIR.mkdir(exist_ok=True)

    html = render_route_map(
        app_key,
        police,
        my_location,
        destination_name,
        route,
    )

    (STATIC_DIR / ROUTE_STATIC_FILENAME).write_text(html, encoding="utf-8")
    (ROOT_STATIC_DIR / ROUTE_STATIC_FILENAME).write_text(html, encoding="utf-8")

    return _versioned_url(
        ROUTE_STATIC_URL_PATH,
        html,
    )
