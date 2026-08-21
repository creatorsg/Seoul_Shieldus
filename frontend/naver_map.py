"""
네이버 지도 JS SDK 렌더링 - HTML/JS는 templates/에 분리해두고, 여기서는 그 HTML을 실제
URL로 서빙하는 역할을 한다.

st.iframe()에 HTML 문자열을 바로 넘기면 안 된다 (srcdoc 방식이라 iframe의 출처가
about:srcdoc이 되어 네이버의 도메인 인증이 항상 실패한다). 반드시 정적 파일로 저장한 뒤,
/app/static/ 경로로 st.iframe에 넘겨서 실제 URL로 서빙해야 한다.
인증 파라미터는 ncpKeyId이며, NCP 콘솔에 Web 서비스 URL을 등록해야 인증이 통과된다.

가로등처럼 마커 개수가 아주 많은 데이터는 낱개로 찍으면 브라우저가 버벅여서,
NAVER가 공식 제공하는 MarkerClustering.js(static/vendor/)로 묶어서 그린다.

** 2026-08 "지도 무한로딩" 버그 이후로 시설찾기/길찾기 지도가 파일을 다루는 방식이 다르다 **
(자세한 진단 과정은 배포 후 실제로 겪은 문제를 그대로 옮긴 것 - 아래 두 함수 문서 참고):

Streamlit Community Cloud는 "앱이 실행되는 도중에" 새로 쓴 static 파일의 서빙을 보장하지
않는다(공식 문서: https://docs.streamlit.io/develop/concepts/configuration/serving-static-files
- "Any files generated while the app is running... are not guaranteed to persist across user
sessions."). 실제로 겪은 증상이 정확히 이거였다: 네트워크 탭엔 200이 뜨는데, 응답 내용이 우리
지도 HTML이 아니라 Streamlit 자체 앱 셸이라 지도가 영원히 로딩 스피너에 머물렀다.
(.gitignore가 frontend/static/*.html을 통째로 무시하고 있어서, 런타임에 쓴 파일이 배포
저장소에는 애초에 존재하지 않았던 것도 원인 중 하나 - 지금은 아래 두 고정 파일만 예외로 뒀다.)

  - 시설찾기 지도: 지구대/파출소/가로등/안심귀갓길 데이터가 사용자 입력과 무관하게 항상 같다.
    그래서 scripts/build_static_maps.py로 배포 전에 딱 한 번 구워서 저장소에 커밋해두고
    (FACILITY_PREBUILT_PATH), write_static_map()은 그 고정 파일을 그대로 가리키기만 한다.

  - 길찾기 지도: 내 위치/목적지/경로는 매 요청 달라져서 미리 구울 수 없다. 그래서 HTML
    파일 자체(templates/route_map.html, static/route_map.html에 그대로 커밋)는 고정해두고,
    달라지는 데이터만 URL 해시(#...)에 실어 보낸다 - 해시는 브라우저가 서버로 아예 안 보내는
    순수 클라이언트 값이라, 이 경로는 파일을 새로 쓸 필요 자체가 없다(render_route_map 참고).
"""

import json
import hashlib
import os
import tempfile
from pathlib import Path
from string import Template
from urllib.parse import quote

import pandas as pd

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

FACILITY_TEMPLATE_PATH = TEMPLATE_DIR / "naver_map.html"
FACILITY_STATIC_STEM = "naver_map"
# 배포 전에 scripts/build_static_maps.py로 미리 구워서 저장소에 커밋해두는 고정 파일.
# 이게 있으면 write_static_map()은 런타임에 아무것도 안 쓰고 이 파일만 가리킨다.
FACILITY_PREBUILT_FILENAME = "naver_map_prebuilt.html"
FACILITY_PREBUILT_PATH = STATIC_DIR / FACILITY_PREBUILT_FILENAME

ROUTE_TEMPLATE_PATH = TEMPLATE_DIR / "route_map.html"
# 길찾기 지도는 이제 데이터를 안 굽는다 - 이 파일은 templates/route_map.html을 그대로 복사한
# "껍데기"만 저장소에 커밋돼 있고(scripts/build_static_maps.py), 실제 데이터는 render_route_map()이
# URL 해시로 매 요청 실어 보낸다.
ROUTE_STATIC_FILENAME = "route_map.html"

# 지도 위 종류별 색상(마커든 폴리라인이든). 여러 종류를 동시에 켜도 구분되도록 색을 다르게 준다.
FACILITY_TYPE_STYLES = {
    "지구대": "#1565C0",
    "파출소": "#2E7D32",
    "가로등": "#F9A825",
    "귀갓길": "#8E24AA",
}

# 기본으로 꺼둔 채 시작하는 종류. 가로등(19,000여개)과 귀갓길(360여개 노선)은 한꺼번에 다 켜면
# 지도가 복잡해서, 필요할 때 사용자가 직접 켜도록 기본은 꺼둔다.
DEFAULT_OFF_TYPES = {"가로등", "귀갓길"}


def _build_filter_controls(counts: dict) -> str:
    """
    종류별 on/off 체크박스 HTML을 만든다. DEFAULT_OFF_TYPES는 기본으로 꺼둔다.

    각 <label>을 inline-flex + white-space:nowrap으로 묶어서 "체크박스+색점+이름+개수"가
    하나의 덩어리로 줄바꿈되게 한다 (모바일 폭에서 확인해보니, 이렇게 안 묶으면 브라우저가
    일반 inline 요소 취급해서 "가로등"과 "(19,316)" 사이처럼 라벨 중간에서 줄이 끊겨 지저분했다).
    줄이 넘치면 라벨 전체 단위로만 다음 줄로 내려간다.
    """
    labels = []
    for type_name, color in FACILITY_TYPE_STYLES.items():
        count = counts.get(type_name, 0)
        checked = "" if type_name in DEFAULT_OFF_TYPES else "checked"
        labels.append(
            '<label style="display:inline-flex;align-items:center;white-space:nowrap;'
            'font-size:14px;">'
            f'<input type="checkbox" value="{type_name}" {checked}> '
            f'<span style="display:inline-block;width:10px;height:10px;background:{color};'
            'border-radius:50%;margin:0 4px;"></span>'
            f"{type_name} ({count:,})</label>"
        )
    return "".join(labels)


def _atomic_write_text(path: Path, content: str) -> None:
    """
    같은 디렉터리에 임시 파일로 먼저 다 쓴 다음 os.replace()로 한 번에 원래 이름으로 바꿔치기한다.
    이 함수는 대상 path에 "아무도 손대고 있지 않을 때"만 쓴다 (호출하는 쪽에서 항상 새 파일
    이름에만 쓰도록 보장 - _write_versioned_html 참고). 그래도 파일을 "열기 → 쓰기 → 닫기"
    사이에 잠깐이라도 빈 상태로 노출되는 것보단, 임시 파일에 다 쓴 뒤 한 번에 바꿔치기하는 게
    항상 더 안전하다.
    """
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _write_versioned_html(stem: str, html: str) -> str:
    """
    내용 해시를 "쿼리스트링"이 아니라 "파일 이름 자체"에 넣어서 매번 새 파일로 저장하고,
    그 파일의 URL 경로를 반환한다. 절대 기존 파일을 덮어쓰지 않는다.

    처음엔 파일 이름은 고정해두고(naver_map.html) 내용 해시를 쿼리스트링(?v=...)으로만 붙였는데,
    그러면 브라우저가 새 요청을 보내긴 해도 "쓰는 파일"과 "읽히는 파일"이 여전히 같은 이름이라
    문제가 있었다: Streamlit 정적 서버가 이 파일(지도 HTML이라 1MB가 넘음)을 브라우저에 내려주는
    도중에 우리가 같은 이름으로 파일을 다시 쓰려고 하면, 윈도우에서는 그 파일이 아직 다른
    프로세스에 열려있다는 이유로 쓰기/이름바꾸기 자체가 거부된다(PermissionError: WinError 5).
    리눅스는 열려있는 파일도 자유롭게 지우고 이름을 바꿀 수 있어서 샌드박스에서는 이 문제가
    안 보였다 - 그래서 실제 윈도우 환경에서만 "지도가 몇 번 새로고침해야 뜨는" 것처럼 보였던 것.

    해결책은 "같은 파일을 절대 두 번 쓰지 않는 것"이다. 내용이 다르면 파일 이름도 통째로 다르게
    만들면, 우리가 새 파일을 쓰는 동작과 웹 서버가 예전 파일을 읽는 동작이 같은 파일을 두고
    부딪힐 일 자체가 없어진다. 같은 내용이면(= 같은 해시면) 이미 있는 파일을 그대로 재사용해서
    불필요한 디스크 쓰기도 줄인다.
    """
    content_hash = hashlib.md5(html.encode("utf-8")).hexdigest()[:8]
    filename = f"{stem}.{content_hash}.html"
    path = STATIC_DIR / filename
    if not path.exists():
        _atomic_write_text(path, html)
    _cleanup_old_versions(stem, keep_filename=filename)
    return f"/app/static/{filename}"


def _cleanup_old_versions(stem: str, keep_filename: str) -> None:
    """
    같은 stem(naver_map/route_map)의 이전 버전 파일들을 정리한다. 못 지워도(다른 요청이 아직
    읽고 있어서 등) 그냥 넘어간다 - 다음 호출 때 다시 시도되고, 못 지운다고 앱이 깨지진 않는다
    (그냥 안 쓰는 파일 하나가 잠깐 더 남아있을 뿐). static 폴더가 개발 세션 내내 무한정
    쌓이는 걸 막는 용도라 실패해도 치명적이지 않다.
    """
    for old in STATIC_DIR.glob(f"{stem}.*.html"):
        if old.name != keep_filename:
            try:
                old.unlink()
            except OSError:
                pass


def _markers_by_type(police: pd.DataFrame) -> dict:
    """
    지구대/파출소 DataFrame을 종류별 {name, lat, lng, address} 리스트로 묶는다.
    두 지도(시설/길찾기)가 같이 쓴다. address는 마커를 클릭했을 때 주소를 복사해주는
    기능(templates의 copyAddressToClipboard)에 쓰인다.
    """
    return {
        type_name: group.rename(
            columns={"위도": "lat", "경도": "lng", "이름": "name", "주소": "address"}
        )[["name", "lat", "lng", "address"]].to_dict(orient="records")
        for type_name, group in police.groupby("종류")
    }


def render_naver_map(
    client_id: str,
    police: pd.DataFrame,
    street_lights: pd.DataFrame,
    safe_paths: list,
    height: int = 550,
) -> str:
    """
    지구대/파출소/가로등을 종류별 색상 마커로, 안심귀갓길을 폴리라인으로 표시하는 HTML을 반환한다.
    on/off 체크박스로 네 종류를 각각 켜고 끌 수 있다.
    """
    markers_by_type = _markers_by_type(police)
    street_light_points = street_lights.rename(columns={"위도": "lat", "경도": "lng"})[
        ["lat", "lng"]
    ].to_dict(orient="records")

    counts = {type_name: len(rows) for type_name, rows in markers_by_type.items()}
    counts["가로등"] = len(street_light_points)
    counts["귀갓길"] = len(safe_paths)

    template = Template(FACILITY_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        client_id=client_id,
        height=height,
        filter_controls_html=_build_filter_controls(counts),
        type_styles_json=json.dumps(FACILITY_TYPE_STYLES, ensure_ascii=False),
        markers_by_type_json=json.dumps(markers_by_type, ensure_ascii=False),
        street_lights_json=json.dumps(street_light_points, ensure_ascii=False),
        safe_paths_json=json.dumps(safe_paths, ensure_ascii=False),
    )


def write_static_map(
    client_id: str, police: pd.DataFrame, street_lights: pd.DataFrame, safe_paths: list
) -> str:
    """
    시설 찾기 지도의 URL을 반환한다.

    FACILITY_PREBUILT_PATH(scripts/build_static_maps.py로 미리 구워서 저장소에 커밋해둔 고정
    파일)가 있으면 그걸 그대로 가리킨다 - 런타임에 아무것도 쓰지 않는다. 지구대/파출소/가로등/
    안심귀갓길 데이터는 사용자 입력과 무관하게 항상 같아서, 매 세션 다시 구울 이유가 없다.
    무엇보다 Streamlit Community Cloud는 "실행 도중에" 새로 쓴 static 파일의 서빙을 보장하지
    않기 때문에(모듈 docstring 참고), 배포본에서는 반드시 이 고정 파일 경로를 타야 한다.

    고정 파일이 아직 없으면(빌드 스크립트를 안 돌린 로컬 개발/프리뷰 중) 예전처럼 그 자리에서
    만들어 저장한다 - 이 폴백 경로는 여전히 Windows 파일 잠금 문제 때문에 해시 파일명을 쓴다
    (_write_versioned_html).
    """
    if FACILITY_PREBUILT_PATH.exists():
        return f"/app/static/{FACILITY_PREBUILT_FILENAME}"
    STATIC_DIR.mkdir(exist_ok=True)
    html = render_naver_map(client_id, police, street_lights, safe_paths)
    return _write_versioned_html(FACILITY_STATIC_STEM, html)


def render_route_map(
    client_id: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
) -> str:
    """
    길찾기 지도 URL을 만든다. 지도 HTML 파일 자체(static/route_map.html)는 저장소에 고정으로
    커밋돼 있고, 요청마다 달라지는 데이터(내 위치/목적지/경로/마커)는 파일을 새로 쓰지 않고
    URL 해시(#...)에 실어 보낸다. TMAP 호출은 route_finder.py가 서버 쪽에서 이미 끝내고,
    여기서는 좌표만 그린다.

    해시는 브라우저가 서버로 아예 보내지 않는 순수 클라이언트 값이다. 이 방식이면 요청마다
    파일을 쓸 필요 자체가 없어져서, Streamlit Cloud의 "런타임에 쓴 static 파일은 서빙 보장
    안 됨" 제약을 애초에 만나지 않는다 - 예전에 이 경로에서 겪던 Windows 파일 잠금 문제도
    같이 사라진다.
    """
    payload = {
        "client_id": client_id,
        "type_styles": FACILITY_TYPE_STYLES,
        "markers_by_type": _markers_by_type(police),
        "destination_name": destination_name,
        "my_location": (
            {"lat": my_location[0], "lng": my_location[1]} if my_location else None
        ),
        "route": [{"lat": lat, "lng": lng} for lat, lng in (route or [])],
    }
    # safe="" : 콤마/콜론/한글 등 JSON에 흔한 문자를 전부 이스케이프한다. quote()의 기본
    # safe 값("/")을 그대로 두면 주소 문자열 속 "/"가 인코딩 안 돼 해시 파싱이 깨질 수 있다.
    encoded = quote(json.dumps(payload, ensure_ascii=False), safe="")
    return f"/app/static/{ROUTE_STATIC_FILENAME}#{encoded}"


def write_route_map(
    client_id: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
) -> str:
    """app.py 호출부 이름을 그대로 유지하기 위한 얇은 별칭. render_route_map 참고."""
    return render_route_map(client_id, police, my_location, destination_name, route)
