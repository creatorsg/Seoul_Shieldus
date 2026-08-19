from pathlib import Path

import pandas as pd
from sklearn.preprocessing import MinMaxScaler


DATA_DIR = Path(__file__).resolve().parent
GEOJSON_PATH = DATA_DIR / "seoul_districts.geojson"
OUTPUT_PATH = DATA_DIR / "processed" / "seoul_safety_index.json"

# 가중치: 계산식에 박아두지 않고 상수로 분리

WEIGHTS = {
    "범죄율": 0.50,
    "CCTV": 0.15,
    "파출소": 0.15,
    "안심귀갓길": 0.10,
    "가로등": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "가중치 합이 1.0이 아닙니다"

POSITIVE_COLS = ["CCTV", "파출소", "안심귀갓길", "가로등"]  # 높을수록 안전
NEGATIVE_COLS = ["범죄율"]  # 높을수록 위험

RENAME_MAP = {
    "자치구": "구",
    "치안안전지수": "안심지수",
    "CCTV": "CCTV_점수",
    "파출소": "파출소_접근성",
    "안심귀갓길": "귀갓길_점수",
}


# 데이터 로딩 - 지금은 더미, 나중엔 이 함수 안만 실제 수집 데이터로 교체해야 합니다.
def load_raw_data() -> pd.DataFrame:
    """
    자치구별 원본 지표를 반환.

    지금  : 팀원 데이터 수집 전까지 쓰는 더미 값 (5개 구만)
    나중  : 각자 수집한 CSV를 자치구 기준으로 merge 한 결과로 교체
            예) pd.read_csv(BASE_DIR / "data" / "raw" / "seoul_infra.csv")
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

    import json

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geo = json.load(f)
    return {feat["properties"]["name"] for feat in geo["features"]}


# 정규화 + 가중합 계산
def compute_safety_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    positive_scaler = MinMaxScaler()
    df[POSITIVE_COLS] = positive_scaler.fit_transform(df[POSITIVE_COLS]) * 100

    negative_scaler = MinMaxScaler()
    df[NEGATIVE_COLS] = (1 - negative_scaler.fit_transform(df[NEGATIVE_COLS])) * 100

    df["치안안전지수"] = sum(df[col] * weight for col, weight in WEIGHTS.items())
    df["치안안전지수"] = df["치안안전지수"].round(2)

    return df.sort_values("치안안전지수", ascending=False).reset_index(drop=True)


# 결과값 저장
def save_output(df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df_out = df.rename(columns=RENAME_MAP)[
        ["구", "안심지수", "CCTV_점수", "귀갓길_점수", "파출소_접근성"]
    ]
    df_out.to_json(OUTPUT_PATH, orient="records", force_ascii=False, indent=2)


def main() -> None:
    df = load_raw_data()

    try:
        official_names = load_official_district_names()
        missing = set(df["자치구"]) - official_names
        if missing:
            print(f"geojson에 없는 구 이름 발견 (표기 확인 필요): {missing}")
    except FileNotFoundError:
        print(f"{GEOJSON_PATH} 를 찾을 수 없어 구 이름 검증을 건너뜁니다.")

    df_scored = compute_safety_index(df)
    save_output(df_scored)

    print(f"완료: {len(df_scored)}개 구 → {OUTPUT_PATH}")
    print(df_scored[["자치구", "치안안전지수"]].to_string(index=False))


if __name__ == "__main__":
    main()
