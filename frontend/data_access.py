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
  범죄율(인구 1만명당) : float, 원본 범죄율(정규화 전). 한글(alt) 스키마 파일에만 있는 원본
                  데이터라, 영문 스키마 파일이나 더미 데이터일 땐 NaN.

get_facility_markers()가 반환하는 df 컬럼 고정:
  이름(str), 구(str), 주소(str), 종류(str), 위도(float), 경도(float)

get_cctv_stats()가 반환하는 df 컬럼 고정:
  구(str), 총_CCTV(int), 방범_합계(int),
  방범용/어린이보호용/공원놀이터용/무단투기단속용/화재감시용/교통단속용/교통정보용/기타용(int)
  - 위치 정보가 없는 자치구 단위 집계라 지도가 아니라 상세 패널용이다.
"""

import json
import random
import sys
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

# 데이터팀이 인구/면적 기반으로 다시 계산한 버전(seoul_safety_index(1).json 계열)은 컬럼명 체계가
# 아예 다르다 - 영문 스네이크케이스가 아니라 한글이고, 밑줄도 없다(예: cctv_score -> CCTV점수).
# 원본에 인구수/면적/인구당_범죄율 같은 원시 지표까지 같이 들어있는 걸 보면 이쪽이 더 최신/상세
# 버전으로 보인다. 두 스키마 중 뭐가 "진짜" 정식 출처인지 confirm 전까지는 둘 다 인식하도록 해서,
# 어느 쪽 파일이 _resolve_data_path에 걸리든 앱이 죽지 않게 한다.
SAFETY_INDEX_RENAME_ALT = {
    "자치구": "구",
    "치안안전지수": "안심지수",
    "CCTV점수": "CCTV_점수",
    "안심길점수": "귀갓길_점수",
    "경찰서점수": "파출소_접근성",
    "가로등점수": "가로등_점수",
    "범죄안전점수": "범죄안전_점수",
}
SAFETY_INDEX_COLUMNS = [
    "구", "안심지수", "CCTV_점수", "귀갓길_점수", "파출소_접근성", "가로등_점수", "범죄안전_점수",
]

# 한글(alt) 스키마 파일에만 들어있는 원본 범죄율 컬럼. "범죄안전_점수"는 0~100으로 정규화(민맥스)한
# 값이라 "0점"만 보면 왜 0점인지 감이 안 오는데, 이 원본 비율을 같이 보여주면 근거가 바로 보인다.
# 영문 스키마 파일에는 이 원본 데이터가 아예 없어서(계산된 점수만 있음), 그 경우엔 그냥 없는 채로
# 둔다 - get_district_scores()가 컬럼 자체를 NaN으로 채워서 돌려준다.
CRIME_RATE_RAW_COLUMN = "인구당_범죄율"
CRIME_RATE_COLUMN = "범죄율(인구 1만명당)"

JIGUDAE_RENAME = {
    "station_name": "이름",
    "lat": "위도",
    "lng": "경도",
    "type": "종류",
    "district": "구",
    "address": "주소",
}
JIGUDAE_COLUMNS = ["이름", "구", "주소", "종류", "위도", "경도"]

STREET_LIGHT_RENAME = {"management_id": "이름", "lat": "위도", "lng": "경도"}
STREET_LIGHT_COLUMNS = ["이름", "위도", "경도"]

CCTV_STATS_COLUMNS = [
    "구", "총_CCTV", "방범_합계",
    "방범용", "어린이보호용", "공원놀이터용", "무단투기단속용",
    "화재감시용", "교통단속용", "교통정보용", "기타용",
]

# --- backend DB(백엔드 팀 SQLAlchemy 파이프라인) 조회용 컬럼 매핑 -------------------------
# backend/models.py의 ORM 컬럼명 -> 이 모듈의 화면 표시용 한글 컬럼명. JSON 쪽
# SAFETY_INDEX_RENAME/JIGUDAE_RENAME과는 원본 키 이름 체계가 달라서(예: JSON 영문 스키마는
# "safepath_score", DB 컬럼은 "safe_road_score") 별도로 둔다.
SAFETY_INDEX_DB_RENAME = {
    "district": "구",
    "safety_index": "안심지수",
    "cctv_score": "CCTV_점수",
    "safe_road_score": "귀갓길_점수",
    "police_score": "파출소_접근성",
    "street_light_score": "가로등_점수",
    "crime_safety_score": "범죄안전_점수",
    "crime_rate_per_pop": CRIME_RATE_COLUMN,
}
CCTV_STATS_DB_RENAME = {
    "district": "구",
    "total_cctv": "총_CCTV",
    "crime_prevention_total": "방범_합계",
    "purpose_crime": "방범용",
    "purpose_child_protection": "어린이보호용",
    "purpose_park_playground": "공원놀이터용",
    "purpose_illegal_dumping": "무단투기단속용",
    "purpose_fire_safety": "화재감시용",
    "purpose_traffic_crackdown": "교통단속용",
    "purpose_traffic_info": "교통정보용",
    "purpose_others": "기타용",
}
# PoliceStation/StreetLight 테이블은 컬럼명이 JIGUDAE_RENAME/STREET_LIGHT_RENAME과
# 이미 같은 영문 이름 체계(station_name/lat/lng/type/district/address, management_id)라
# 그대로 재사용한다.

# backend/ 아래 SQLAlchemy 파이프라인을 import할 수 있으면 DB에서 읽고, 그게 안 되면(예:
# sqlalchemy 미설치, backend 폴더 없음) 아래 각 get_* 함수가 기존처럼 JSON 파일로 대체한다.
# _resolve_data_path()의 mtime 캐싱과 별개로, DB 연결/시딩 자체는 앱 프로세스당 한 번만
# 시도한다 - 매 리런마다 재시도하면 실패 케이스에서 느려지기만 하고 얻는 게 없다.
_BACKEND_DIR = BASE_DIR / "backend"
_db_engine = None
_db_init = None
if _BACKEND_DIR.is_dir():
    if str(_BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(_BACKEND_DIR))
    try:
        import database as _db_database  # backend/database.py
        import init_db as _db_init  # backend/init_db.py

        _db_engine = _db_database.engine
    except Exception:
        # sqlalchemy가 없거나 backend 쪽 코드에 문제가 있어도 앱 자체는 JSON 폴백으로
        # 계속 돌아가야 하므로, 여기서 죽이지 않고 조용히 DB 비활성 상태로 남겨둔다.
        _db_engine = None
        _db_init = None

_db_seed_attempted = False
_db_seed_ok = False


def _ensure_db_ready() -> bool:
    """DB가 준비돼 있으면 True. 처음 호출될 때만 실제로 시딩을 시도하고, 그 뒤로는
    성공/실패 결과를 그대로 재사용한다(매번 재시도하지 않음)."""
    global _db_seed_attempted, _db_seed_ok
    if _db_engine is None or _db_init is None:
        return False
    if _db_seed_attempted:
        return _db_seed_ok
    _db_seed_attempted = True
    try:
        _db_init.initialize_database()
        _db_seed_ok = True
    except Exception as e:
        st.warning(f"백엔드 DB 초기화에 실패해 JSON 파일로 대체합니다: {e}")
        _db_seed_ok = False
    return _db_seed_ok


def _read_db_table(table_name: str, rename: dict, columns: list) -> Optional[pd.DataFrame]:
    """DB 테이블 하나를 읽어 화면 표시용 컬럼으로 정리한다. DB가 준비 안 됐거나 테이블이
    비어있거나 조회 자체가 실패하면 None을 반환해서 호출부가 JSON 폴백으로 넘어가게 한다."""
    if not _ensure_db_ready():
        return None
    try:
        df = pd.read_sql_table(table_name, _db_engine)
    except Exception as e:
        st.warning(f"DB 테이블 '{table_name}' 조회 실패, JSON 파일로 대체합니다: {e}")
        return None
    if df.empty:
        return None
    return df.rename(columns=rename)[columns]


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
            # 더미 데이터엔 원본 범죄율이 없다 - 실제 파일에 CRIME_RATE_RAW_COLUMN이 있을 때만
            # 값이 채워지는 컬럼이라, 여기선 다운스트림(facility 표 등)이 이 컬럼이 없어서
            # KeyError 나지 않도록 NaN으로라도 채워둔다.
            CRIME_RATE_COLUMN: [float("nan") for _ in districts],
        }
    )


def get_district_scores(geo: dict) -> pd.DataFrame:

    districts = _district_names(geo)

    db_df = _read_db_table(
        "seoul_safety_index", SAFETY_INDEX_DB_RENAME, SAFETY_INDEX_COLUMNS + [CRIME_RATE_COLUMN]
    )
    if db_df is not None:
        missing = set(districts) - set(db_df["구"])
        if missing:
            st.warning(f"DB(seoul_safety_index)에 없는 구: {missing}")
        return db_df

    raw = _try_load_json(SAFETY_INDEX_FILE)
    if raw is None:
        return _dummy_district_scores(districts)

    raw_df = pd.DataFrame(raw)
    df = raw_df.rename(columns=SAFETY_INDEX_RENAME)
    missing_cols = [c for c in SAFETY_INDEX_COLUMNS if c not in df.columns]

    if missing_cols:
        # 기본(영문 키) 스키마로 안 맞으면, 데이터팀이 인구/면적 기반으로 다시 낸 버전(한글 키,
        # 밑줄 없음 - 예: CCTV점수)일 수 있으니 그 매핑으로 한 번 더 시도한다.
        alt_df = raw_df.rename(columns=SAFETY_INDEX_RENAME_ALT)
        alt_missing = [c for c in SAFETY_INDEX_COLUMNS if c not in alt_df.columns]
        if not alt_missing:
            df, missing_cols = alt_df, []

    if missing_cols:
        # 두 스키마(영문 스네이크케이스 / 한글 무밑줄) 중 어느 쪽으로도 필요한 컬럼을 다 못 찾은
        # 경우다. SAFETY_INDEX_FILE 자체는 있지만 컬럼 구성이 완전히 다른 파일(예: 5개 구짜리
        # 더미 데이터, 혹은 또 다른 스키마 변형)일 가능성이 높다. 이걸 그냥 df[SAFETY_INDEX_COLUMNS]로
        # select하면 pandas KeyError가 그대로 튀어나와 앱 전체가 죽는데(사용자가 실제로 겪은 상황),
        # 원인을 전혀 알 수 없는 스택트레이스만 보여주는 셈이라 여기서 먼저 걸러서 알려준다.
        st.error(
            f"{SAFETY_INDEX_FILE} 형식이 예상과 다릅니다 (누락된 컬럼: {missing_cols}). "
            "현재 코드가 인식하는 두 스키마(영문 snake_case, 또는 자치구/CCTV점수 식 한글) 중 "
            "어느 쪽과도 맞지 않습니다. data/processed/ 안에 실제 25개 구 데이터 파일이 맞는지, "
            "혹시 또 다른 컬럼 체계의 파일인지 확인해주세요. "
            "지금은 화면이 안 죽게 임시로 더미 값을 표시합니다."
        )
        return _dummy_district_scores(districts)

    # 원본 범죄율(있으면)을 최종 select 전에 따로 빼둔다 - SAFETY_INDEX_COLUMNS엔 없는 컬럼이라
    # df[SAFETY_INDEX_COLUMNS]에서 걸러지기 전에 챙겨야 한다.
    crime_rate = (
        df[CRIME_RATE_RAW_COLUMN] if CRIME_RATE_RAW_COLUMN in df.columns
        else pd.Series(float("nan"), index=df.index)
    )

    df = df[SAFETY_INDEX_COLUMNS]
    df[CRIME_RATE_COLUMN] = crime_rate
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
        rows.append(
            {
                "이름": f"{name} 대표지점(더미)",
                "구": name,
                "주소": "-",
                "종류": "더미",
                "위도": lat,
                "경도": lng,
            }
        )
    return pd.DataFrame(rows)


def get_facility_markers(geo: dict) -> pd.DataFrame:
    """
    지도에 마커로 찍을 지구대/파출소 위치를 반환한다. "종류" 컬럼에 지구대/파출소가 섞여 있다.
    1) backend DB(police_stations 테이블)가 준비돼 있으면 그걸 우선 읽는다.
    2) 없으면 JIGUDAE_FILE(JSON)을 읽는다.
    3) 그것도 없으면 각 자치구 geojson 경계의 중심점을 더미 위치로 대체한다.
    (get_district_scores와 같은 이유로 @st.cache_data를 여기 대신 _load_json_cached에 둔다.)
    """
    db_df = _read_db_table("police_stations", JIGUDAE_RENAME, JIGUDAE_COLUMNS)
    if db_df is not None:
        return db_df

    raw = _try_load_json(JIGUDAE_FILE)
    if raw is None:
        return _dummy_facility_markers(geo)

    return pd.DataFrame(raw).rename(columns=JIGUDAE_RENAME)[JIGUDAE_COLUMNS]


def get_street_light_markers() -> pd.DataFrame:
    """
    가로등 위치를 반환한다. 19,000여 개로 개수가 많아 지도에는 클러스터링해서 그려야 한다.
    1) backend DB(street_lights 테이블)가 준비돼 있으면 그걸 우선 읽는다.
    2) 없으면 STREET_LIGHT_FILE(JSON)을 읽는다.
    3) 그것도 없으면 빈 DataFrame을 반환한다 (더미로 채우기엔 개수가 의미 없이 많음).
    (인자가 아예 없는 함수라 @st.cache_data를 직접 붙이면 서버가 켜져 있는 동안은 파일을
    통째로 갈아끼워도 절대 다시 안 읽는, 가장 심한 형태의 캐시 문제가 생긴다. 여기도
    _load_json_cached 쪽 mtime 캐싱에 맡긴다.)
    """
    db_df = _read_db_table("street_lights", STREET_LIGHT_RENAME, STREET_LIGHT_COLUMNS)
    if db_df is not None:
        return db_df

    raw = _try_load_json(STREET_LIGHT_FILE)
    if raw is None:
        return pd.DataFrame(columns=STREET_LIGHT_COLUMNS)

    return pd.DataFrame(raw).rename(columns=STREET_LIGHT_RENAME)[STREET_LIGHT_COLUMNS]


def get_cctv_stats() -> pd.DataFrame:

    db_df = _read_db_table("district_cctv_stats", CCTV_STATS_DB_RENAME, CCTV_STATS_COLUMNS)
    if db_df is not None:
        return db_df

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
