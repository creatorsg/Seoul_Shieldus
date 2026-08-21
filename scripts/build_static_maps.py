"""
배포 전에 정적 지도 파일들을 미리 만들어서 frontend/static/에 저장하는 빌드 스크립트.

왜 필요한가:
Streamlit Community Cloud는 "앱이 실행되는 도중에" 새로 쓴 static 파일의 서빙을 보장하지
않는다 (공식 문서: https://docs.streamlit.io/develop/concepts/configuration/serving-static-files
- "Any files generated while the app is running... are not guaranteed to persist across user
sessions."). 예전 방식(naver_map.py가 페이지 열릴 때마다 지도 HTML을 새로 써서 저장)이 배포
후 "지도 무한로딩" 버그의 원인이었다 - 네트워크 요청은 200인데 실제로는 우리 HTML이 아니라
Streamlit 자체 앱 셸이 응답으로 와서 지도가 영원히 로딩 스피너에 머물렀다. 게다가
.gitignore가 frontend/static/*.html을 통째로 무시하고 있어서, 런타임에 쓴 파일이 배포
저장소에는 애초에 존재하지도 않았다.

이 스크립트가 만드는 파일 두 개(둘 다 .gitignore에서 예외로 빼뒀으니 git에 커밋해야 한다):
  - frontend/static/naver_map_prebuilt.html : 시설찾기 지도. 지구대/파출소/가로등/안심귀갓길
    데이터를 그대로 구워 넣는다. 이 데이터는 사용자 입력과 무관하게 항상 같으므로 배포 전에
    한 번만 만들면 된다.
  - frontend/static/route_map.html : 길찾기 지도. 마커/내 위치/목적지/경로 같은 요청별
    데이터는 구워 넣지 않는다(sessionStorage로 매 요청 따로 전달 - naver_map.py의
    build_route_payload/route_map_url, app.py의 _send_route_payload 참고) - 대신
    ncpKeyId(client_id)만 templates/route_map.html의 ${client_id} 자리에 채워 넣는다. 이건
    세션마다 안 바뀌는 값이라 파일에 고정으로 구워도 된다.
    (처음엔 요청별 데이터까지 전부 URL 해시(#...)로 실어 보내려 했는데, 로컬에서 바로 "네이버
    오픈API 인증 실패"가 났다 - 데이터를 통째로 욱여넣은 해시 때문에 location.href가 너무
    커져서 네이버 쪽 도메인 인증이 깨진 것으로 보였다. sessionStorage 방식이 그 문제를 피한다.)

사용법 (프로젝트 루트에서, 최초 1회 + 데이터가 바뀔 때마다):
    python scripts/build_static_maps.py

실행 후 할 일:
    git add frontend/static/naver_map_prebuilt.html frontend/static/route_map.html
    git commit -m "지도 정적 파일 빌드"
    git push
"""

import os
import sys
from pathlib import Path
from string import Template

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
sys.path.insert(0, str(FRONTEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BASE_DIR / ".env", override=True)

from data_access import (  # noqa: E402
    get_facility_markers,
    get_safe_paths,
    get_street_light_markers,
    load_geojson,
)
from naver_map import (  # noqa: E402
    FACILITY_PREBUILT_PATH,
    ROUTE_STATIC_FILENAME,
    ROUTE_TEMPLATE_PATH,
    STATIC_DIR,
    render_naver_map,
)


def build_facility_map(client_id: str) -> None:
    geo = load_geojson()
    facilities = get_facility_markers(geo)
    street_lights = get_street_light_markers()
    safe_paths = get_safe_paths()

    html = render_naver_map(client_id, facilities, street_lights, safe_paths)
    STATIC_DIR.mkdir(exist_ok=True)
    FACILITY_PREBUILT_PATH.write_text(html, encoding="utf-8")
    print(f"생성 완료: {FACILITY_PREBUILT_PATH} ({len(html):,} bytes)")


def build_route_map_shell(client_id: str) -> None:
    """
    route_map.html은 요청별 데이터(마커/내 위치/목적지/경로)는 안 굽지만, ncpKeyId(client_id)는
    시설찾기와 마찬가지로 고정으로 채워 넣는다 - templates/route_map.html의 ${client_id} 자리
    딱 하나만 채우는 Template 치환이다. newline="" : Python의 기본 텍스트 모드는 \\r\\n을 읽을 때
    \\n으로, 쓸 때 다시 OS 기본 줄바꿈으로 바꾸는 "universal newlines" 변환을 하는데, 그걸 끄지
    않으면 원본의 CRLF가 조용히 LF로 바뀐다(그러면 git diff가 파일 전체를 바꾼 것처럼 보인다).
    Path.read_text/write_text는 이 버전(3.11)에서 newline 인자를 못 받아서 open()을 직접 쓴다.
    """
    STATIC_DIR.mkdir(exist_ok=True)
    with open(ROUTE_TEMPLATE_PATH, encoding="utf-8", newline="") as f:
        template = Template(f.read())
    html = template.substitute(client_id=client_id)
    dest = STATIC_DIR / ROUTE_STATIC_FILENAME
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    print(f"생성 완료: {dest} ({len(html):,} bytes)")


def main() -> None:
    client_id = os.getenv("NAVER_MAPS_CLIENT_ID")
    if not client_id:
        raise SystemExit(
            "NAVER_MAPS_CLIENT_ID가 없습니다. 프로젝트 루트의 .env에 값이 있는지 확인하세요."
        )
    build_facility_map(client_id)
    build_route_map_shell(client_id)
    print(
        "\n완료! 아래 두 파일을 git에 커밋 + push하세요:\n"
        "  frontend/static/naver_map_prebuilt.html\n"
        "  frontend/static/route_map.html"
    )


if __name__ == "__main__":
    main()
