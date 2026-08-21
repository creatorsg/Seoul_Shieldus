"""
데이터 로딩 계층 - Streamlit 화면 코드와 분리된 순수 데이터 함수 모음.

app.py는 이 모듈의 함수만 호출해서 데이터를 얻는다. 이렇게 분리해두면:
  - 화면(streamlit) 없이도 이 함수들만 따로 import해서 pytest로 테스트할 수 있다.
  - 데이터 소스가 바뀌어도(예: DB 연결로 교체) app.py는 건드릴 필요가 없다.

데이터 계약 - get_district_scores()가 반환하는 df 컬럼 고정:
  구            : str, 자치구 이름 (seoul_districts.geojson 의
                  feature.properties.name 값과 정확히 일치해야 함)
  안심지수       : int/float, 0~100
  CCTV_점수      : int/float, 0~100
  귀갓길_점수     : int/float, 0~100
  파출소_접근성   : int/float, 0~100

get_facility_markers()가 반환하는 df 컬럼 고정:
  이름(str), 위도(float), 경도(float), 종류(str)
"""

import json
import random
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
GEOJSON_PATH = BASE_DIR / "data" / "seoul_districts.geojson"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SAFETY_INDEX_PATH = PROCESSED_DIR / "seoul_safety_index.json"
JIGUDAE_PATH = PROCESSED_DIR / "seoul_jigudae.json"

# data/processed/*.json 은 영문 키(district, safety_index, cctv_score ...)를 쓰는데
# 화면 표시용 계약은 한글 컬럼명이라 여기서 한 번 매핑해준다.
SAFETY_INDEX_RENAME = {
    "district": "구",
    "safety_index": "안심지수",
    "cctv_score": "CCTV_점수",
    "safepath_score": "귀갓길_점수",
    "police_score": "파출소_접근성",
    "street_light_score": "가로등_점수",
}
SAFETY_INDEX_COLUMNS = ["구", "안심지수", "CCTV_점수", "귀갓길_점수", "파출소_접근성", "가로등_점수"]

JIGUDAE_RENAME = {"station_name": "이름", "lat": "위도", "lng": "경도", "type": "종류"}
JIGUDAE_COLUMNS = ["이름", "위도", "경도", "종류"]

STREET_LIGHT_PATH = PROCESSED_DIR / "seoul_street_lights.json"
STREET_LIGHT_RENAME = {"management_id": "이름", "lat": "위도", "lng": "경도"}
STREET_LIGHT_COLUMNS = ["이름", "위도", "경도"]


def _try_load_json(path: Path) -> Optional[list]:
    """
    path가 있으면 JSON을 읽어 리스트로 반환하고, 없으면 None을 반환한다.
    실제 파일 읽기/파싱은 _load_json_cached가 맡고, 여기서는 최신 mtime을 확인해서 넘겨주기만
    한다 - 이유는 아래 _load_json_cached 설명 참고.
    """
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return None
    return _load_json_cached(str(path), mtime)


@st.cache_data
def _load_json_cached(path_str: str, _mtime: float) -> list:
    """
    JSON 파일을 읽어서 파싱한다. (경로, mtime) 조합을 캐시 키로 쓴다.

    st.cache_data는 "함수 인자"만 보고 캐시를 재사용할지 정하지, 인자로 넘어온 경로가 가리키는
    파일이 디스크에서 바뀌었는지는 전혀 모른다. 예전엔 get_district_scores(geo)처럼 절대 안
    바뀌는 geo(자치구 경계)만 인자로 받았어서, 개발 중 data/processed/*.json을 새 버전으로
    교체해도(가짜→진짜 데이터, 4지표→5지표 등) 캐시가 무효화되지 않고 스트림릿 서버를 껐다
    켜기 전까지 계속 예전 결과(심지어 파일이 아예 없던 시절의 더미 데이터)를 돌려주는 문제가
    있었다. mtime을 인자에 포함시키면 파일이 바뀔 때마다 인자 조합이 달라져서 자동으로 다시
    읽는다 - 서버 재시작 없이 파일 교체만으로 최신 데이터가 반영된다.
    """
    with open(path_str, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_geojson():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _district_names(geo: dict) -> list:
    return [feat["properties"]["name"] for feat in geo["features"]]


def _dummy_district_scores(districts: list) -> pd.DataFrame:
    random.seed(42)
    return pd.DataFrame(
        {
            "구": districts,
            "안심지수": [random.randint(40, 100) for _ in districts],
            "CCTV_점수": [random.randint(0, 100) for _ in districts],
            "귀갓길_점수": [random.randint(0, 100) for _ in districts],
            "파출소_접근성": [random.randint(0, 100) for _ in districts],
            "가로등_점수": [random.randint(0, 100) for _ in districts],
        }
    )


def get_district_scores(geo: dict) -> pd.DataFrame:
    """
    자치구별 안심 지수를 반환한다.
    SAFETY_INDEX_PATH가 있으면 그걸 읽고, 없으면 랜덤 더미로 대체한다.
    (파일 읽기 자체의 캐싱은 _try_load_json -> _load_json_cached가 mtime 기준으로 담당하므로,
    여기엔 @st.cache_data를 안 붙인다. geo만 인자로 캐싱하면 파일이 바뀌어도 예전 결과가
    계속 캐시에 남는 문제가 있었다.)
    """
    districts = _district_names(geo)
    raw = _try_load_json(SAFETY_INDEX_PATH)
    if raw is None:
        return _dummy_district_scores(districts)

    df = pd.DataFrame(raw).rename(columns=SAFETY_INDEX_RENAME)[SAFETY_INDEX_COLUMNS]
    missing = set(districts) - set(df["구"])
    if missing:
        st.warning(f"seoul_safety_index.json에 없는 구: {missing}")
    return df


def _polygon_centroid(geometry: dict) -> tuple:
    """geojson geometry(Polygon/MultiPolygon) 좌표를 평균 낸 근사 중심점을 반환한다."""
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


def _dummy_facility_markers(geo: dict) -> pd.DataFrame:
    rows = []
    for feat in geo["features"]:
        name = feat["properties"]["name"]
        lat, lng = _polygon_centroid(feat["geometry"])
        rows.append({"이름": f"{name} 대표지점(더미)", "위도": lat, "경도": lng, "종류": "더미"})
    return pd.DataFrame(rows)


def get_facility_markers(geo: dict) -> pd.DataFrame:
    """
    지도에 마커로 찍을 지구대/파출소 위치를 반환한다. "종류" 컬럼에 지구대/파출소가 섞여 있다.
    JIGUDAE_PATH(지구대/파출소 실제 좌표)가 있으면 그걸 읽고,
    없으면 각 자치구 geojson 경계의 중심점을 더미 위치로 대체한다.
    (get_district_scores와 같은 이유로 @st.cache_data를 여기 대신 _load_json_cached에 둔다.)
    """
    raw = _try_load_json(JIGUDAE_PATH)
    if raw is None:
        return _dummy_facility_markers(geo)

    return pd.DataFrame(raw).rename(columns=JIGUDAE_RENAME)[JIGUDAE_COLUMNS]


def get_street_light_markers() -> pd.DataFrame:
    """
    가로등 위치를 반환한다. 19,000여 개로 개수가 많아 지도에는 클러스터링해서 그려야 한다.
    STREET_LIGHT_PATH가 없으면 빈 DataFrame을 반환한다 (더미로 채우기엔 개수가 의미 없이 많음).
    (인자가 아예 없는 함수라 @st.cache_data를 직접 붙이면 서버가 켜져 있는 동안은 파일을
    통째로 갈아끼워도 절대 다시 안 읽는, 가장 심한 형태의 캐시 문제가 생긴다. 여기도
    _load_json_cached 쪽 mtime 캐싱에 맡긴다.)
    """
    raw = _try_load_json(STREET_LIGHT_PATH)
    if raw is None:
        return pd.DataFrame(columns=STREET_LIGHT_COLUMNS)

    return pd.DataFrame(raw).rename(columns=STREET_LIGHT_RENAME)[STREET_LIGHT_COLUMNS]
