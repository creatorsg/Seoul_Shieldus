"""
길찾기(TMAP) 데이터 계층.

TMAP 경로안내는 appKey를 헤더에 담아 보내는 서버 대 서버 API라서, 네이버 지도(ncpKeyId)처럼
브라우저 JS에 키를 노출하면 안 된다. 그래서 이 모듈의 fetch_route()는 Streamlit(Python) 쪽에서만
호출하고, 결과 좌표만 지도 HTML에 데이터로 넘겨서 그린다 (naver_map.py의 route 인자).

내 위치는 지도 iframe 안이 아니라 Streamlit 쪽(streamlit-js-eval)에서 직접 구한다.
iframe은 Streamlit과 값을 주고받는 통로가 없어서, iframe 안 JS가 구한 위치는 Python이 알 수 없기 때문이다.
"""

import math
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

TMAP_PEDESTRIAN_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
TMAP_CAR_URL = "https://apis.openapi.sk.com/tmap/routes?version=1"


def get_tmap_app_key() -> Optional[str]:
    """
    .env를 매번 다시 읽어서 TMAP_APP_KEY를 가져온다 - 모듈 최상단에서 딱 한 번만 os.getenv()로
    읽어서 상수로 박아두면 안 되는 이유가 있다.

    이 모듈(route_finder.py)은 Streamlit 서버 프로세스가 켜져 있는 동안 딱 한 번만 import되고,
    그 이후 리런에서는 이미 import된 모듈을 재사용할 뿐 최상단 코드를 다시 실행하지 않는다
    (app.py는 매 리런마다 통째로 다시 실행되지만 - 그래서 화면이 매번 새로 그려짐 - import된
    모듈은 파이썬이 캐싱해서 재사용할 뿐 다시 실행하지 않는다는 게 기본 동작이다). 그래서 상수로
    한 번만 읽어두면, 서버를 처음 켰을 때 .env에 키가 없었거나 잘못돼 있었을 경우 나중에 .env를
    고쳐도 서버를 완전히 재시작(Ctrl+C 후 다시 실행)하기 전까지는 예전 값(None 등)이 계속
    쓰인다 - "방금 고쳤는데 왜 계속 401/키 누락이 나지" 하는 혼란의 직접적인 원인이 된다.

    호출될 때마다 .env를 다시 읽고, override=True로 이미 프로세스에 들어있는 값도 최신 파일
    내용으로 덮어써서, 서버를 다시 켜지 않고 .env만 고쳐도 바로 반영되게 한다.
    """
    load_dotenv(ENV_PATH, override=True)
    return os.getenv("TMAP_APP_KEY")


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 직선 거리(km)를 반환한다. TMAP을 부르기 전에 '가장 가까운 시설'을 빠르게 추릴 때 쓴다."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_facility(lat: float, lng: float, facilities: pd.DataFrame) -> pd.Series:
    """facilities(이름/위도/경도 컬럼 포함)에서 (lat, lng)와 가장 가까운 행을 반환한다."""
    distances = facilities.apply(lambda row: haversine_km(lat, lng, row["위도"], row["경도"]), axis=1)
    return facilities.loc[distances.idxmin()]


def get_current_location() -> Optional[tuple]:
    """
    브라우저 GPS 권한을 요청하고 (위도, 경도)를 반환한다.
    권한 응답을 기다리는 중이거나 사용자가 거부하면 None을 반환한다.
    """
    location = get_geolocation()
    if not location or "coords" not in location:
        return None
    return location["coords"]["latitude"], location["coords"]["longitude"]


def _tmap_error_message(e: requests.HTTPError) -> str:
    """
    TMAP 에러 응답 본문(JSON)에서 실제 code/message를 뽑아 사람이 읽을 문자열로 만든다.

    requests의 HTTPError를 그냥 str()로 찍으면 "429 Client Error: Too Many Requests for
    url: ..."처럼 HTTP 상태 텍스트만 나온다. 그런데 TMAP은 같은 429여도 응답 본문의
    error.code로 두 가지를 구분해서 내려준다 - THROTTLED(초당 호출 건수 초과, 몇 초 뒤
    재시도하면 바로 풀림)와 QUOTA_EXCEEDED(SLA/하루 할당량 초과, 리셋 전까진 답이 없음).
    이 필드를 안 읽으면 매번 "429니까 할당량 문제겠지"라고 추측만 하게 되는데, 실제로는
    무한 리런 버그처럼 짧은 시간에 몰아서 호출했을 때도 429가 뜨고 그건 THROTTLED이지
    QUOTA_EXCEEDED가 아니다. 403(INVALID_API_KEY/ACCESS_DENIED/MISSING_AUTHENTICATION_TOKEN)
    등 다른 에러도 마찬가지로 code를 봐야 정확한 원인을 알 수 있다.
    """
    try:
        body = e.response.json().get("error", {})
    except (ValueError, AttributeError):
        body = {}
    code, message = body.get("code"), body.get("message")
    if code:
        return f"[{code}] {message}"
    return str(e)


def fetch_route(start: tuple, end: tuple, mode: str = "pedestrian") -> Optional[dict]:
    """
    TMAP 경로안내 API를 호출해 다음 형태의 dict를 반환한다.
      coords: [(위도, 경도), ...] 경로 좌표 (지도에 폴리라인으로 그릴 때 씀)
      distance_km, time_min: 총 거리/예상 소요시간 (출발지점 Point feature의
        totalDistance(m)/totalTime(초)에서 변환)
    mode: "pedestrian"(도보) 또는 "car"(자동차). TMAP_APP_KEY가 없거나 호출에 실패하면 None을 반환한다.
    """
    tmap_app_key = get_tmap_app_key()
    if not tmap_app_key:
        return None

    url = TMAP_PEDESTRIAN_URL if mode == "pedestrian" else TMAP_CAR_URL
    payload = {
        "startX": start[1],
        "startY": start[0],
        "endX": end[1],
        "endY": end[0],
        "startName": "출발",
        "endName": "도착",
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }
    if mode == "car":
        payload["carType"] = 0

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"appKey": tmap_app_key, "Content-Type": "application/json"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        # 설정(.env 키 없음)이 아니라 실제 호출이 실패한 경우라서, "설정 필요" 경고(st.warning)와
        # 구분되게 st.error로 띄운다. 설정 관련 메시지는 app.py의 _warn_missing_env가 담당한다.
        # HTTPError(4xx/5xx 응답을 받긴 받은 경우)는 응답 본문에 TMAP이 내려주는 진짜 원인
        # (code/message)이 있어서, RequestException보다 먼저 잡아 _tmap_error_message로 풀어준다.
        st.error(f"TMAP 경로 조회에 실패했습니다: {_tmap_error_message(e)}")
        return None
    except requests.RequestException as e:
        # 타임아웃, 연결 실패 등 응답 자체를 못 받은 경우 - 본문이 없으니 그냥 예외 메시지를 보여준다.
        st.error(f"TMAP 경로 조회에 실패했습니다: {e}")
        return None

    coords = []
    distance_m = None
    time_sec = None
    for feature in response.json().get("features", []):
        properties = feature.get("properties", {})
        # 총 거리/시간은 출발지점(Point) feature에 한 번만 들어있다. 처음 만난 값을 그대로 쓴다.
        if distance_m is None and "totalDistance" in properties:
            distance_m = properties["totalDistance"]
            time_sec = properties["totalTime"]
        if feature["geometry"]["type"] == "LineString":
            coords.extend((lat, lng) for lng, lat in feature["geometry"]["coordinates"])

    if not coords:
        return None

    return {
        "coords": coords,
        "distance_km": round(distance_m / 1000, 2) if distance_m is not None else None,
        "time_min": round(time_sec / 60, 1) if time_sec is not None else None,
    }
