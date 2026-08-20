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

# app.py도 load_dotenv()를 호출하지만, 이 모듈이 app.py보다 먼저 import되면 그때는 아직
# .env가 안 읽힌 상태라 TMAP_APP_KEY가 항상 비어버린다. import 순서에 기대지 않도록 여기서도 직접 읽는다.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
TMAP_APP_KEY = os.getenv("TMAP_APP_KEY")

TMAP_PEDESTRIAN_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
TMAP_CAR_URL = "https://apis.openapi.sk.com/tmap/routes?version=1"


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


def fetch_route(start: tuple, end: tuple, mode: str = "pedestrian") -> Optional[dict]:
    """
    TMAP 경로안내 API를 호출해 다음 형태의 dict를 반환한다.
      coords: [(위도, 경도), ...] 경로 좌표 (지도에 폴리라인으로 그릴 때 씀)
      distance_km, time_min: 총 거리/예상 소요시간 (출발지점 Point feature의
        totalDistance(m)/totalTime(초)에서 변환)
    mode: "pedestrian"(도보) 또는 "car"(자동차). TMAP_APP_KEY가 없거나 호출에 실패하면 None을 반환한다.
    """
    if not TMAP_APP_KEY:
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
            headers={"appKey": TMAP_APP_KEY, "Content-Type": "application/json"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        # 설정(.env 키 없음)이 아니라 실제 호출이 실패한 경우라서, "설정 필요" 경고(st.warning)와
        # 구분되게 st.error로 띄운다. 설정 관련 메시지는 app.py의 _warn_missing_env가 담당한다.
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
