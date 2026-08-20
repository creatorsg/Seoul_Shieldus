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
  가로등_점수     : int/float, 0~100
  범죄안전_점수   : int/float, 0~100

get_facility_markers()가 반환하는 df 컬럼 고정:
  이름(str), 위도(float), 경도(float), 종류(str)

get_cctv_stats()가 반환하는 df 컬럼 고정:
  구(str), 총_CCTV(int), 방범_합계(int),
  방범용/어린이보호용/공원놀이터용/무단투기단속용/화재감시용/교통단속용/교통정보용/기타용(int)
  - 위치 정보가 없는 자치구 단위 집계라 지도가 아니라 상세 패널용이다.
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

# 파일 "이름"만 여기 적어둔다 (정리된 이름 기준). 실제로 어느 파일을 읽을지는
# _resolve_data_path가 정한다 - 바로 아래 설명 참고.
SAFETY_INDEX_FILE = "seoul_safety_index.json"
JIGUDAE_FILE = "seoul_jigudae.json"
STREET_LIGHT_FILE = "seoul_street_lights.json"
SAFE_PATH_FILE = "seoul_safe_paths.json"
CCTV_STATS_FILE = "seoul_cctv_stats.json"

# data/processed/*.json 은 영문 키(district, safety_index, cctv_score ...)를 쓰는데
# 화면 표시용 계약은 한글 컬럼명이라 여기서 한 번 매핑해준다.
SAFETY_INDEX_RENAME = {
    "district": "구",
    "safety_index": "안심지수",
    "cctv_score": "CCTV_점수",
    "safepath_score": "귀갓길_점수",
    "police_score": "파출소_접근성",
    "street_light_score": "가로등_점수",
    "crime_safety_score": "범죄안전_점수",
}
SAFETY_INDEX_COLUMNS = [
    "구", "안심지수", "CCTV_점수", "귀갓길_점수", "파출소_접근성", "가로등_점수", "범죄안전_점수",
]

JIGUDAE_RENAME = {"station_name": "이름", "lat": "위도", "lng": "경도", "type": "종류"}
JIGUDAE_COLUMNS = ["이름", "위도", "경도", "종류"]

STREET_LIGHT_RENAME = {"management_id": "이름", "lat": "위도", "lng": "경도"}
STREET_LIGHT_COLUMNS = ["이름", "위도", "경도"]

CCTV_STATS_COLUMNS = [
    "구", "총_CCTV", "방범_합계",
    "방범용", "어린이보호용", "공원놀이터용", "무단투기단속용",
    "화재감시용", "교통단속용", "교통정보용", "기타용",
]


def _resolve_data_path(file_name: str) -> Optional[Path]:
    """
    file_name과 정확히 이름이 같은 파일 하나만 찾지 않고, 같은 데이터셋의 파일명 변형
    (예: seoul_safety_index.json, seoul_safety_index(1).json - 브라우저가 재다운로드할 때
    자동으로 붙이는 번호)까지 전부 후보로 놓고 그중 가장 최근에 수정된 파일을 쓴다.

    왜 이렇게 하나: 백엔드(init_db.py)는 원본 파일명("(1)" 붙은 이름)을 그대로 읽고, 프론트는
    정리된 이름을 읽는 이원화 상태다. 팀 중 누군가 한쪽 이름의 파일만 새로 받아서 올리면 다른
    쪽은 계속 예전 데이터를 보게 되는데(실제로 겪었던 "가짜 데이터만 나옴" 버그가 이 패턴이었다),
    파일명이 정리된 이름이든 번호 붙은 원본이든 "가장 최근에 바뀐 파일"을 쓰면 팀 컨벤션이
    통일되기 전까지는 최소한 안전망 역할을 한다.
    """
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    candidates = list(PROCESSED_DIR.glob(f"{stem}*{suffix}"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _try_load_json(file_name: str) -> Optional[list]:
    """
    file_name(정리된 이름 기준)에 해당하는 데이터가 있으면 JSON을 읽어 리스트로 반환하고,
    없으면 None을 반환한다. 실제 파일 읽기/파싱은 _load_json_cached가 맡고, 여기서는
    _resolve_data_path로 찾은 최신 파일의 mtime을 확인해서 넘겨주기만 한다 - 이유는 아래
    _load_json_cached 설명 참고.
    """
    path = _resolve_data_path(file_name)
    if path is None:
        return None
    return _load_json_cached(str(path), path.stat().st_mtime)


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
            "범죄안전_점수": [random.randint(0, 100) for _ in districts],
        }
    )


def get_district_scores(geo: dict) -> pd.DataFrame:
    """
    자치구별 안심 지수를 반환한다.
    SAFETY_INDEX_FILE이 있으면 그걸 읽고, 없으면 랜덤 더미로 대체한다.
    (파일 읽기 자체의 캐싱은 _try_load_json -> _load_json_cached가 mtime 기준으로 담당하므로,
    여기엔 @st.cache_data를 안 붙인다. geo만 인자로 캐싱하면 파일이 바뀌어도 예전 결과가
    계속 캐시에 남는 문제가 있었다.)
    """
    districts = _district_names(geo)
    raw = _try_load_json(SAFETY_INDEX_FILE)
    if raw is None:
        return _dummy_district_scores(districts)

    df = pd.DataFrame(raw).rename(columns=SAFETY_INDEX_RENAME)[SAFETY_INDEX_COLUMNS]
    missing = set(districts) - set(df["구"])
    if missing:
        st.warning(f"{SAFETY_INDEX_FILE}에 없는 구: {missing}")
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
    JIGUDAE_FILE(지구대/파출소 실제 좌표)이 있으면 그걸 읽고,
    없으면 각 자치구 geojson 경계의 중심점을 더미 위치로 대체한다.
    (get_district_scores와 같은 이유로 @st.cache_data를 여기 대신 _load_json_cached에 둔다.)
    """
    raw = _try_load_json(JIGUDAE_FILE)
    if raw is None:
        return _dummy_facility_markers(geo)

    return pd.DataFrame(raw).rename(columns=JIGUDAE_RENAME)[JIGUDAE_COLUMNS]


def get_street_light_markers() -> pd.DataFrame:
    """
    가로등 위치를 반환한다. 19,000여 개로 개수가 많아 지도에는 클러스터링해서 그려야 한다.
    STREET_LIGHT_FILE이 없으면 빈 DataFrame을 반환한다 (더미로 채우기엔 개수가 의미 없이 많음).
    (인자가 아예 없는 함수라 @st.cache_data를 직접 붙이면 서버가 켜져 있는 동안은 파일을
    통째로 갈아끼워도 절대 다시 안 읽는, 가장 심한 형태의 캐시 문제가 생긴다. 여기도
    _load_json_cached 쪽 mtime 캐싱에 맡긴다.)
    """
    raw = _try_load_json(STREET_LIGHT_FILE)
    if raw is None:
        return pd.DataFrame(columns=STREET_LIGHT_COLUMNS)

    return pd.DataFrame(raw).rename(columns=STREET_LIGHT_RENAME)[STREET_LIGHT_COLUMNS]


def get_cctv_stats() -> pd.DataFrame:
    """
    자치구별 CCTV 설치 현황(총량 + 목적별 세부)을 반환한다. 위치 정보가 없는(자치구 단위 집계)
    통계 데이터라 지도 마커가 아니라 자치구 상세 패널의 표/차트용이다.
    CCTV_STATS_FILE이 없으면 빈 DataFrame을 반환한다 (목적별 세부까지 의미 있게 흉내낸
    더미를 만들기는 애매해서 더미 대체는 하지 않는다).
    """
    raw = _try_load_json(CCTV_STATS_FILE)
    if raw is None:
        return pd.DataFrame(columns=CCTV_STATS_COLUMNS)

    rows = []
    for item in raw:
        purpose = item.get("purpose", {})
        rows.append(
            {
                "구": item.get("district"),
                "총_CCTV": item.get("total_cctv", 0),
                "방범_합계": item.get("crime_prevention_total", 0),
                "방범용": purpose.get("crime", 0),
                "어린이보호용": purpose.get("child_protection", 0),
                "공원놀이터용": purpose.get("park_playground", 0),
                "무단투기단속용": purpose.get("illegal_dumping", 0),
                "화재감시용": purpose.get("fire_safety", 0),
                "교통단속용": purpose.get("traffic_crackdown", 0),
                "교통정보용": purpose.get("traffic_info", 0),
                "기타용": purpose.get("others", 0),
            }
        )
    return pd.DataFrame(rows)[CCTV_STATS_COLUMNS]


def get_safe_paths() -> list:
    """
    여성안심귀갓길 노선을 반환한다. 원본은 구 단위로 묶여 있고 그 안에 노선별 좌표가 들어있는데,
    지도에는 노선 하나하나가 폴리라인 한 줄이라서 [{district, route_name, coords}, ...]로 평평하게
    펴서 반환한다. coords는 [{"lat": float, "lng": float}, ...].

    원본 좌표에 바로 앞 점과 완전히 똑같은 점이 섞여 있는데(추출 과정에서 생긴 걸로 보임),
    지도에 그릴 땐 길이 0인 구간이라 그냥 무해하지만 용량만 차지해서 여기서 미리 걸러낸다.

    STREET_LIGHT_FILE처럼 위치 데이터가 아예 없던 시절엔 이 함수가 없었다 - 안심귀갓길에
    좌표가 추가되면서 새로 생긴 함수다. 파일이 없으면(아직 안 받았으면) 빈 리스트를 반환한다.
    """
    raw = _try_load_json(SAFE_PATH_FILE)
    if raw is None:
        return []

    routes = []
    for district in raw:
        district_name = district.get("district", "")
        for route in district.get("routes", []):
            coords = route.get("coordinates") or []
            deduped = [c for i, c in enumerate(coords) if i == 0 or c != coords[i - 1]]
            if len(deduped) < 2:
                continue
            routes.append(
                {
                    "district": district_name,
                    "route_name": route.get("route_name") or route.get("route_id", ""),
                    "coords": deduped,
                }
            )
    return routes
