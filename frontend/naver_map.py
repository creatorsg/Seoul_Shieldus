"""
네이버 지도 JS SDK 렌더링 - HTML 파일을 만들어 URL로 서빙하는 대신, window.parent(진짜 배포
도메인 그 자체)에 <script>와 지도 DOM을 직접 심는 JS 코드 문자열을 만든다. app.py가 이 문자열을
streamlit_js_eval로 실행시킨다.

** 2026-08 "지도 무한로딩" 배포 버그의 최종 원인과 결론 **

이전에는 지도를 별도 정적 HTML 파일로 저장해서 st.iframe(url)로 서빙하려 했다. 순서대로 시도한
방법: (1) 런타임에 파일 쓰기 (2) .gitignore 예외로 빌드타임에 미리 구워서 커밋 (3) 요청별
데이터를 URL 해시(#...)로 전달 (4) sessionStorage로 전달 (5) .streamlit/config.toml을 레포
루트로 이동(enableStaticServing이 CWD 기준으로 config를 찾으므로). 전부 문서대로 정확히
고쳤는데도 배포에서는 여전히 무한로딩이었다.

결정적 증거: 브라우저 주소창에 직접 "https://.../app/static/route_map.html"을 쳐서
들어가봐도(즉 iframe이나 st.iframe과 완전히 무관한 순수 GET 요청) 우리가 만든 HTML이 아니라
Streamlit 자체 앱 셸(index 번들, "Manage app" 문구)이 그대로 응답으로 왔다. 이건 요청이 우리
Streamlit 서버 프로세스까지 도달하지도 못하고 있다는 뜻이다 - 그 응답에 heap/segment/Google
Analytics/GTM 같은 Community Cloud 전용 트래킹 스크립트가 주입돼 있었던 게 그 증거다(우리
코드는 저런 걸 넣은 적이 없다). 즉 Streamlit Community Cloud 앞단에는 자체 리버스 프록시/CDN이
있고, 이게 자기가 아는 특정 경로 패턴이 아니면 전부 앱 셸로 폴백시키는 것으로 보인다 -
enableStaticServing을 문서대로 다 맞게 설정해도, 무료 Community Cloud 티어에서는 그 설정이
적용될 서버 프로세스까지 요청이 아예 오지 않으므로 구조적으로 무의미했다.

그렇다고 st.components.v1.html()로 HTML 문자열을 바로 넘기는 것도 답이 아니다 - 그건 내부적으로
iframe의 "srcdoc" 속성을 쓰는데, srcdoc 문서는 document.location.href가 "about:srcdoc"이 되어
네이버 지도 SDK의 도메인 인증(NCP 콘솔에 등록한 Web 서비스 URL과 매치하는 방식)이 항상
실패한다.

그래서 별도 HTTP 요청도, 별도 iframe도 아예 만들지 않는 세 번째 길로 간다. app.py의
_inject_head_scripts, _restore_scroll_position이 이미 하고 있는 것과 똑같은 방식 -
streamlit_js_eval로 window.parent(진짜 배포 도메인)의 document에 직접 <script src=maps.js>와
지도를 그릴 <div>를 심는다. 이러면:
  - 네이버 SDK가 보는 location.href가 실제 서비스 도메인 그대로라 도메인 인증이 정상 통과된다
    (앱 전체가 이미 이 도메인에서 정상 로드되고 있으므로, NCP 콘솔에 이 도메인만 등록돼 있으면
    된다 - 배포용 새 서브도메인을 만들었다면 그 도메인도 등록해야 한다).
  - "/app/static/..." 같은 별도 HTTP 요청 자체가 없으니 위에서 확인한 Community Cloud 정적
    서빙 문제를 아예 거치지 않는다.
  - 가로등 클러스터링에 쓰는 MarkerClustering.js(NAVER 공식, frontend/static/vendor/)도
    <script src=...>로 불러오지 않고, 디스크에서 파일 내용을 그대로 문자열로 읽어서
    <script> 태그 텍스트로 심는다 - 이 파일 자체는 여전히 저장소에 있지만(서빙이 아니라 우리
    Python 프로세스가 로컬 파일로 그냥 읽는 것이므로 Streamlit의 정적 서빙 여부와 무관하다),
    브라우저가 별도로 GET 요청을 하지 않는다.

시설찾기/길찾기 지도 각각 build_facility_map_js() / build_route_map_js()가 "이 문자열을
streamlit_js_eval로 실행시켜라"만 하면 되는 완성된 JS 코드를 반환한다. 실제 지도 렌더링 로직은
templates/naver_map.html, templates/route_map.html에 있다 - 파일 이름은 .html이지만 내용은
순수 JS(window.parent 안에서 실행될 코드 조각)다. 마커/내 위치/목적지/경로 같은 요청별 데이터는
build_route_map_js() 호출 시점에 이미 JS 코드 문자열 안에 값으로 그대로 박혀 들어가므로,
예전처럼 sessionStorage 같은 별도 채널로 전달할 필요가 없다.
"""

import json
from pathlib import Path
from string import Template

import pandas as pd

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

FACILITY_TEMPLATE_PATH = TEMPLATE_DIR / "naver_map.html"
ROUTE_TEMPLATE_PATH = TEMPLATE_DIR / "route_map.html"
# NAVER 공식 MarkerClustering.js(Apache-2.0) - 여전히 저장소에 존재하지만, 더 이상 브라우저가
# 별도로 GET 요청하지 않는다(위 모듈 docstring 참고). Python이 그냥 로컬 파일로 읽는다.
MARKER_CLUSTERING_PATH = STATIC_DIR / "vendor" / "MarkerClustering.js"

# app.py가 st.markdown(unsafe_allow_html=True)으로 미리 만들어두는 mount div id와
# 반드시 일치해야 한다.
FACILITY_MOUNT_ID = "shieldus-facility-map"
FACILITY_FILTERS_MOUNT_ID = "shieldus-facility-filters"
ROUTE_MOUNT_ID = "shieldus-route-map"

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

_marker_clustering_js_cache = None


def _marker_clustering_js() -> str:
    """
    MarkerClustering.js 파일 내용을 읽어서 프로세스 안에 캐싱해둔다. 세션/요청마다 안 바뀌는
    고정 파일이라 지도를 그릴 때마다 디스크에서 다시 읽을 이유가 없다.
    """
    global _marker_clustering_js_cache
    if _marker_clustering_js_cache is None:
        _marker_clustering_js_cache = MARKER_CLUSTERING_PATH.read_text(encoding="utf-8")
    return _marker_clustering_js_cache


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


def _run_when_naver_ready(client_id: str, body_js: str, need_clustering: bool = False) -> str:
    """
    window.parent에 네이버 지도 SDK를 "딱 한 번만" 로드하고 나서 body_js를 실행하는 JS 전체를
    만든다. 이미 로드가 끝났으면 바로 실행하고, 로드가 진행 중이면 콜백 큐에 쌓아뒀다가 로드
    완료 시 한꺼번에 실행한다 - 시설찾기/길찾기 페이지를 오가며 <script> 태그를 매번 새로
    만들지 않기 위함이다(중복 로드는 에러는 안 나지만 낭비고, 신경 쓰지 않는 게 더 깔끔하다).
    """
    clustering_src_json = json.dumps(_marker_clustering_js()) if need_clustering else "null"
    # client_id는 실제로는 NCP가 발급하는 영숫자 값이라 따옴표가 섞일 일이 없지만, 문자열
    # 리터럴 안에 그대로 꽂아 넣으면(f"...{client_id}...") 혹시라도 따옴표가 섞였을 때 JS
    # 구문이 깨진다. json.dumps로 안전하게 이스케이프해서 넣는다.
    client_id_json = json.dumps(client_id)
    return f"""
    (function () {{
        var w = window.parent;

        function ensureClustering() {{
            var src = {clustering_src_json};
            if (src && !w.MarkerClustering) {{
                var mc = w.document.createElement('script');
                mc.text = src;
                w.document.head.appendChild(mc);
            }}
        }}

        function runBody() {{
            ensureClustering();
            {body_js}
        }}

        if (w.naver && w.naver.maps) {{
            runBody();
            return;
        }}

        w.__shieldusNaverCallbacks = w.__shieldusNaverCallbacks || [];
        w.__shieldusNaverCallbacks.push(runBody);
        if (w.__shieldusNaverLoading) {{
            return;
        }}
        w.__shieldusNaverLoading = true;

        var s = w.document.createElement('script');
        s.src = 'https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=' + {client_id_json};
        s.onload = function () {{
            var callbacks = w.__shieldusNaverCallbacks;
            w.__shieldusNaverCallbacks = [];
            callbacks.forEach(function (fn) {{ fn(); }});
        }};
        w.document.head.appendChild(s);
    }})();
    """


def build_facility_map_js(
    client_id: str, police: pd.DataFrame, street_lights: pd.DataFrame, safe_paths: list
) -> str:
    """
    시설찾기 지도를 window.parent 안에 그리는 JS 전체를 반환한다.

    호출 전에 app.py가 st.markdown(unsafe_allow_html=True)으로
    '#shieldus-facility-filters' + '#shieldus-facility-map' div를 먼저 만들어둬야 하고,
    이 함수가 반환한 문자열은 streamlit_js_eval(js_expressions=..., want_output=False)로
    실행시키면 된다.
    """
    markers_by_type = _markers_by_type(police)
    street_light_points = street_lights.rename(columns={"위도": "lat", "경도": "lng"})[
        ["lat", "lng"]
    ].to_dict(orient="records")

    counts = {type_name: len(rows) for type_name, rows in markers_by_type.items()}
    counts["가로등"] = len(street_light_points)
    counts["귀갓길"] = len(safe_paths)

    template = Template(FACILITY_TEMPLATE_PATH.read_text(encoding="utf-8"))
    body_js = template.substitute(
        filter_controls_html_json=json.dumps(_build_filter_controls(counts), ensure_ascii=False),
        type_styles_json=json.dumps(FACILITY_TYPE_STYLES, ensure_ascii=False),
        markers_by_type_json=json.dumps(markers_by_type, ensure_ascii=False),
        street_lights_json=json.dumps(street_light_points, ensure_ascii=False),
        safe_paths_json=json.dumps(safe_paths, ensure_ascii=False),
    )
    return _run_when_naver_ready(client_id, body_js, need_clustering=True)


def build_route_map_js(
    client_id: str,
    police: pd.DataFrame,
    my_location: tuple,
    destination_name: str,
    route: list,
) -> str:
    """
    길찾기 지도를 window.parent 안에 그리는 JS 전체를 반환한다.

    호출 전에 app.py가 st.markdown(unsafe_allow_html=True)으로 '#shieldus-route-map' div를
    먼저 만들어둬야 하고, 이 함수가 반환한 문자열은
    streamlit_js_eval(js_expressions=..., want_output=False)로 실행시키면 된다. 내 위치/목적지/
    경로 같은 요청별 데이터는 이 함수가 호출되는 시점에 이미 JS 코드 문자열 안에 값으로 그대로
    박혀 들어가므로, 매 요청 최신 상태를 그대로 그린다. TMAP 호출은 route_finder.py가 서버
    쪽에서 이미 끝내고, 여기서는 좌표만 그린다.
    """
    template = Template(ROUTE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    body_js = template.substitute(
        type_styles_json=json.dumps(FACILITY_TYPE_STYLES, ensure_ascii=False),
        markers_by_type_json=json.dumps(_markers_by_type(police), ensure_ascii=False),
        destination_name_json=json.dumps(destination_name, ensure_ascii=False),
        my_location_json=json.dumps(
            {"lat": my_location[0], "lng": my_location[1]} if my_location else None
        ),
        route_json=json.dumps([{"lat": lat, "lng": lng} for lat, lng in (route or [])]),
    )
    return _run_when_naver_ready(client_id, body_js, need_clustering=False)
