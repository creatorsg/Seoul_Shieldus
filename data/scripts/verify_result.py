"""
최종 결과물(jigudae_seoul.csv) 검증 스크립트
- 스펙 체크: 25개 자치구 전수, 위도/경도 결측 없음, 좌표 범위 정상, 중복 없음
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent  # data_police_cctv 폴더
PATH = BASE_DIR / "processed" / "jigudae_seoul.csv"

df = pd.read_csv(PATH, encoding="utf-8-sig")
print(f"[체크] 총 행 수: {len(df)}")

TARGET_GU = {
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구",
    "도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구",
    "양천구","영등포구","용산구","은평구","종로구","중구","중랑구",
}

# 1. 25개 자치구 전수 확인
missing_gu = TARGET_GU - set(df["자치구"])
print(f"[체크] 자치구 누락: {missing_gu if missing_gu else '없음 (정상)'}")

# 2. 필수 컬럼 결측치 확인
required_cols = ["자치구", "관서명", "위도", "경도"]
for col in required_cols:
    n_missing = df[col].isna().sum()
    print(f"[체크] '{col}' 결측치: {n_missing}건 {'(정상)' if n_missing == 0 else '(확인 필요!)'}")

# 3. 위도/경도가 서울 범위 안에 있는지 (서울은 대략 위도 37.4~37.7, 경도 126.7~127.3)
out_of_range = df[
    ~df["위도"].between(37.3, 37.8) | ~df["경도"].between(126.6, 127.4)
]
print(f"[체크] 서울 범위를 벗어난 좌표: {len(out_of_range)}건")
if len(out_of_range) > 0:
    print(out_of_range[["자치구", "관서명", "위도", "경도"]])

# 4. 중복 확인 (같은 관서명이 같은 자치구에 두 번 있는지)
dup = df[df.duplicated(subset=["자치구", "관서명"], keep=False)]
print(f"[체크] 중복 행: {len(dup)}건")
if len(dup) > 0:
    print(dup[["자치구", "관서명", "주소"]])

# 5. 최종 판정
all_ok = (
    not missing_gu
    and df[required_cols].isna().sum().sum() == 0
    and len(out_of_range) == 0
    and len(dup) == 0
)
print("\n" + ("✅ 모든 검증 통과 — 1번 데이터 완료" if all_ok else "⚠️ 위 항목 확인 후 수정 필요"))