"""
자치구별 치안 안전 지수 계산 스크립트

실행: python data/build_safety_index.py
출력: data/processed/seoul_safety_index.json

컬럼 계약 (frontend/data_access.py 의 get_district_scores() docstring과 일치해야 함):
  구, 안심지수, CCTV_점수, 귀갓길_점수, 파출소_접근성

지표 정의(가중치/방향/출력 컬럼명)는 INDICATORS 하나에만 있다.
지표를 추가/삭제/가중치 조정할 때 이 리스트만 고치면 되고,
WEIGHTS·POSITIVE_COLS·NEGATIVE_COLS·RENAME_MAP을 따로따로 맞출 필요가 없다.
"""

import json
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).resolve().parent
GEOJSON_PATH = DATA_DIR / "seoul_districts.geojson"
OUTPUT_PATH = DATA_DIR / "processed" / "seoul_safety_index.json"

DISTRICT_COL = "자치구"
OUTPUT_DISTRICT_COL = "구"
INDEX_COL = "치안안전지수"
OUTPUT_INDEX_COL = "안심지수"

# 가중치 설계: 범죄율 50% : (CCTV+파출소) 30% : (안심귀갓길+가로등) 20%
# direction: "positive"면 값이 클수록 안전(그대로 점수화), "negative"면 값이 클수록 위험(뒤집어서 점수화)
# output_col: 최종 JSON에 별도 점수로 노출할 컬럼명. None이면 종합 지수 계산에만 쓰이고 따로 노출하지 않음.
INDICATORS = [
    {"col": "범죄율", "weight": 0.50, "direction": "negative", "output_col": None},
    {"col": "CCTV", "weight": 0.15, "direction": "positive", "output_col": "CCTV_점수"},
    {"col": "파출소", "weight": 0.15, "direction": "positive", "output_col": "파출소_접근성"},
    {"col": "안심귀갓길", "weight": 0.10, "direction": "positive", "output_col": "귀갓길_점수"},
    {"col": "가로등", "weight": 0.10, "direction": "positive", "output_col": None},
]
assert abs(sum(ind["weight"] for ind in INDICATORS) - 1.0) < 1e-9, "가중치 합이 1.0이 아닙니다"


def load_raw_data() -> pd.DataFrame:
    """
    자치구별 원본 지표를 반환한다.
    지금: 더미 값 (5개 구). 나중: 수집한 CSV를 자치구 기준 merge 한 결과로 교체.
    """
    dummy_data = {
        "자치구": ["강남구", "관악구", "종로구", "노원구", "마포구"],
        "범죄율": [3.5, 4.2, 2.1, 1.8, 2.9],
        "CCTV": [1200, 850, 600, 950, 1100],
        "파출소": [15, 12, 8, 10, 11],
        "안심귀갓길": [40, 35, 20, 25, 30],
        "가로등": [3500, 2800, 1500, 2100, 3100],
    }
    return pd.DataFrame(dummy_data)


def load_official_district_names() -> set:
    """data/seoul_districts.geojson 의 25개 자치구 공식 이름 집합을 반환한다."""
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geo = json.load(f)
    return {feat["properties"]["name"] for feat in geo["features"]}


def _scale_to_score(series: pd.Series, direction: str) -> pd.Series:
    """지표 값을 0~100 점수로 정규화한다. negative면 값이 클수록 점수가 낮아지도록 뒤집는다."""
    scaled = MinMaxScaler().fit_transform(series.to_frame()).flatten() * 100
    if direction == "negative":
        scaled = 100 - scaled
    return pd.Series(scaled, index=series.index)


def compute_safety_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for ind in INDICATORS:
        df[ind["col"]] = _scale_to_score(df[ind["col"]], ind["direction"])

    df[INDEX_COL] = sum(df[ind["col"]] * ind["weight"] for ind in INDICATORS).round(2)

    return df.sort_values(INDEX_COL, ascending=False).reset_index(drop=True)


def save_output(df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    output_columns = {DISTRICT_COL: OUTPUT_DISTRICT_COL, INDEX_COL: OUTPUT_INDEX_COL}
    output_columns.update(
        {ind["col"]: ind["output_col"] for ind in INDICATORS if ind["output_col"]}
    )

    df_out = df.rename(columns=output_columns)[list(output_columns.values())]
    df_out.to_json(OUTPUT_PATH, orient="records", force_ascii=False, indent=2)


def main() -> None:
    df = load_raw_data()

    try:
        official_names = load_official_district_names()
        missing = set(df[DISTRICT_COL]) - official_names
        if missing:
            print(f"경고: geojson에 없는 구 이름 발견 (표기 확인 필요): {missing}")
    except FileNotFoundError:
        print(f"경고: {GEOJSON_PATH} 를 찾을 수 없어 구 이름 검증을 건너뜁니다.")

    df_scored = compute_safety_index(df)
    save_output(df_scored)

    print(f"완료: {len(df_scored)}개 구 → {OUTPUT_PATH}")
    print(df_scored[[DISTRICT_COL, INDEX_COL]].to_string(index=False))


if __name__ == "__main__":
    main()
