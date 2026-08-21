"""
서울시 자치구별 CCTV 설치현황 정제 스크립트
- 원본: 서울시 자치구 (목적별) CCTV 설치현황 (서울 열린데이터광장, XLSX)
- 구조: 0~3행 제목/단위/2단 헤더, 4행 합계(총계), 5~29행 25개 자치구, 30행 각주
- 처리: 헤더/합계/각주 제거 -> 자치구명 정규화("구" 누락분 보정) -> 검증 -> 저장
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent  # data_police_cctv 폴더
RAW_PATH = BASE_DIR / "raw" / "cctv_raw.xlsx"
OUT_DIR = BASE_DIR / "processed"
OUT_PATH = OUT_DIR / "cctv_seoul.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not RAW_PATH.exists():
    raise FileNotFoundError(
        f"원본 파일을 찾을 수 없습니다: {RAW_PATH}\n"
        f"서울 열린데이터광장에서 받은 XLSX를 raw/cctv_raw.xlsx 로 저장해주세요."
    )

# 1. 원본 로드 (헤더가 병합되어 있어서 header=None으로 읽고 직접 자른다)
raw = pd.read_excel(RAW_PATH, sheet_name=0, header=None, engine="openpyxl")
print(f"[로그] 원본 로드 완료: {raw.shape[0]}행 x {raw.shape[1]}열")

# 2. 실제 데이터 구간만 자르기
#    0~1행: 제목/단위, 2~3행: 2단 헤더, 4행: 합계(총계) 행, 5~29행: 25개 자치구, 30행: 각주
TOTAL_ROW = 4
DATA_START, DATA_END = 5, 30  # 30은 제외(각주 행)

data = raw.iloc[DATA_START:DATA_END, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]].copy()
data.columns = [
    "자치구", "CCTV수량", "범죄예방수사_소계", "방범", "어린이보호구역",
    "공원놀이터", "쓰레기무단투기", "시설안전화재예방", "교통단속",
    "교통정보수집분석", "기타다른법령",
]
print(f"[로그] 데이터 구간 추출 완료: {len(data)}행")

# 3. 자치구명 정규화: "구"로 안 끝나면 붙이기 (예: '동대문' -> '동대문구')
def normalize_gu(name: str) -> str:
    name = str(name).strip()
    return name if name.endswith("구") else name + "구"

before = data["자치구"].tolist()
data["자치구"] = data["자치구"].apply(normalize_gu)
fixed = [(b, a) for b, a in zip(before, data["자치구"]) if b != a]
if fixed:
    print(f"[로그] 자치구명 보정된 행 {len(fixed)}건: {fixed}")

# 4. 검증 1: 25개 자치구 전수 확인
TARGET_GU = {
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구",
    "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구",
    "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
}
found_gu = set(data["자치구"])
missing = TARGET_GU - found_gu
extra = found_gu - TARGET_GU
if missing:
    print(f"[경고] 25개 자치구 중 누락: {missing}")
else:
    print("[로그] 25개 자치구 전수 확인 완료")
if extra:
    print(f"[경고] 목표 25개 자치구에 없는 이상값: {extra}")

# 5. 검증 2: 결측치 확인 (필수 컬럼: 자치구, CCTV수량)
n_missing = data[["자치구", "CCTV수량"]].isna().sum().sum()
print(f"[체크] 필수 컬럼(자치구, CCTV수량) 결측치: {n_missing}건")

# 6. 검증 3: 합계 검산 (25개 구 총계 합 == 원본 4행 '합계' 값)
official_total = raw.iloc[TOTAL_ROW, 2]
computed_total = data["CCTV수량"].sum()
print(f"[체크] 원본 합계행 값: {official_total} / 25개 구 합산값: {computed_total} "
      f"-> {'일치 (정상)' if official_total == computed_total else '불일치! 확인 필요'}")

# 7. 검증 4: 중복 자치구 확인
dup = data[data.duplicated(subset=["자치구"], keep=False)]
if len(dup) > 0:
    print(f"[경고] 자치구 중복 {len(dup)}건:\n{dup}")
else:
    print("[로그] 자치구 중복 없음 (정상)")

# 8. 저장
data.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
print(f"[로그] 저장 완료: {OUT_PATH} (총 {len(data)}행)")