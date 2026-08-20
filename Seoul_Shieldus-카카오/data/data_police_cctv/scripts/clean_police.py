"""
서울시 지구대/파출소 데이터 정제 스크립트 (수정본)
- 원본: 경찰청_전국 지구대 파출소 주소 현황 (공공데이터포털, cp949 인코딩)
- 처리: 인코딩 변환(메모리상에서만) -> 서울특별시만 필터 -> 자치구 컬럼 추출
        -> 관서명 통일 -> 검증 -> 저장

"""

import re
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------
# 1. 경로 설정
#    이 스크립트는 data_police_cctv/scripts/clean_police.py 에 있다고 가정.
#    __file__ 기준 상대경로로 잡아서, 터미널에서 어느 위치에서 실행하든
#    (VS Code Run 버튼이든 터미널 cd 상태든) 항상 같은 파일을 가리키게 함.
#
#    C:\rookies6\Seoul_Shieldus\Seoul_Shieldus\data_police_cctv
#    ├── raw/police_raw.csv              <- 원본 (절대 덮어쓰지 않음)
#    ├── scripts/clean_police.py         <- 이 파일
#    └── processed/
#         ├── jigudae_seoul.csv          <- 최종 결과
#         └── jigudae_seoul_unmatched.csv <- 자치구 추출 실패 행(디버깅용)
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent  # data_police_cctv 폴더
RAW_PATH = BASE_DIR / "raw" / "police_raw.csv"
OUT_DIR = BASE_DIR / "processed"
OUT_PATH = OUT_DIR / "jigudae_seoul.csv"
UNMATCHED_PATH = OUT_DIR / "jigudae_seoul_unmatched.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)  # processed 폴더 없으면 자동 생성

if not RAW_PATH.exists():
    raise FileNotFoundError(
        f"원본 파일을 찾을 수 없습니다: {RAW_PATH}\n"
    )

# ------------------------------------------------------------------
# 2. 인코딩 판별 (원본 파일은 절대 덮어쓰지 않고, 메모리에서만 처리)
# ------------------------------------------------------------------
try:
    df = pd.read_csv(RAW_PATH, encoding="cp949")
    print("[로그] cp949로 읽기 성공")
except UnicodeDecodeError:
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    print("[로그] cp949 디코딩 실패 -> utf-8-sig로 읽기 성공")

print(f"[로그] 원본 로드 완료: 총 {len(df)}행, 컬럼: {list(df.columns)}")

required_cols = {"시도청", "관서명", "구분", "주소"}
missing_cols = required_cols - set(df.columns)
if missing_cols:
    raise KeyError(
        f"원본에 필요한 컬럼이 없습니다: {missing_cols}\n"
        f"실제 컬럼: {list(df.columns)}\n"
        f"공공데이터포털에서 컬럼명이 바뀌었을 수 있으니 확인해주세요."
    )

# ------------------------------------------------------------------
# 3. 서울특별시(서울청) 데이터만 필터링
# ------------------------------------------------------------------
seoul = df[df["시도청"] == "서울청"].copy()
print(f"[로그] 서울청 필터링 완료: {len(seoul)}행")

if len(seoul) == 0:
    unique_vals = df["시도청"].dropna().unique().tolist()
    raise ValueError(
        "서울청으로 필터링된 행이 0건입니다. '시도청' 컬럼의 표기가 "
        "다를 수 있습니다.\n"
        f"'시도청' 컬럼에 실제로 들어있는 값들: {unique_vals}\n"
        "위 목록에서 서울에 해당하는 값을 찾아 필터 조건을 맞춰주세요."
    )

# ------------------------------------------------------------------
# 4. 주소에서 자치구 추출
#    주소 표기가 '서울특별시'/'서울시'/'서울' 등으로 일관되지 않아서
#    시도명 접두사에 의존하지 않고, 25개 자치구 이름 자체를 직접 매칭한다.
# ------------------------------------------------------------------
TARGET_GU = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구",
    "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구",
    "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
]
# '중구'가 '중랑구'의 부분문자열로 먼저 매칭되지 않도록 긴 이름부터 검사
GU_PATTERN = re.compile("|".join(sorted(TARGET_GU, key=len, reverse=True)))


def extract_gu(addr: str):
    m = GU_PATTERN.search(str(addr))
    return m.group(0) if m else None


seoul["자치구"] = seoul["주소"].apply(extract_gu)

# ------------------------------------------------------------------
# 5. 관서명 통일: '관서명' + '구분' 합쳐서 정식 명칭 생성
#    (예: 신림 + 파출소 -> 신림파출소)
#    단, 원본 '관서명'에 이미 '지구대'/'파출소'가 포함돼 있으면
#    중복으로 붙이지 않는다 (예: '역삼지구대' + '지구대' -> '역삼지구대지구대' 방지)
# ------------------------------------------------------------------
name = seoul["관서명"].astype(str).str.strip()
suffix = seoul["구분"].astype(str).str.strip()

already_has_suffix = pd.Series(
    [n.endswith(s) for n, s in zip(name, suffix)], index=seoul.index
)
seoul["관서명_전체"] = name.where(already_has_suffix, name + suffix)

n_dedup = already_has_suffix.sum()
if n_dedup > 0:
    print(f"[로그] 관서명에 구분 접미사가 이미 포함된 행 {n_dedup}건은 중복 결합하지 않음")

# ------------------------------------------------------------------
# 6. 팀 스펙에 맞는 최종 컬럼만 선택
# ------------------------------------------------------------------
result = seoul[["자치구", "관서명_전체", "구분", "주소"]].rename(
    columns={"관서명_전체": "관서명"}
)

# ------------------------------------------------------------------
# 7. 검증 1: 자치구 추출 실패 행은 별도로 분리 저장하고, 최종 결과에서는 제외
# ------------------------------------------------------------------
missing_gu_mask = result["자치구"].isna()
missing_gu_rows = result[missing_gu_mask]

if len(missing_gu_rows) > 0:
    print(f"[경고] 자치구 추출 실패한 행 {len(missing_gu_rows)}건 -> {UNMATCHED_PATH.name} 로 분리 저장")
    missing_gu_rows.to_csv(UNMATCHED_PATH, index=False, encoding="utf-8-sig")
    result = result[~missing_gu_mask].copy()
else:
    print("[로그] 자치구 추출 실패 행 없음 (정상)")

# ------------------------------------------------------------------
# 8. 검증 2: 25개 자치구가 모두 존재하는지 확인
# ------------------------------------------------------------------
target_gu = set(TARGET_GU)
found_gu = set(result["자치구"].dropna().unique())
missing = target_gu - found_gu
if missing:
    print(f"[경고] 25개 자치구 중 누락: {missing}")
else:
    print("[로그] 25개 자치구 전수 확인 완료")

print(f"[로그] 자치구별 관서 수:\n{result['자치구'].value_counts().sort_index()}")

# ------------------------------------------------------------------
# 9. 검증 3: 완전히 동일한 행(주소+관서명 중복)이 있는지 확인
# ------------------------------------------------------------------
dup_mask = result.duplicated(subset=["관서명", "주소"], keep=False)
if dup_mask.any():
    print(f"[경고] 관서명+주소가 동일한 중복 행 {dup_mask.sum()}건 발견 (제거하지 않고 남겨둠, 필요 시 직접 확인)")
    print(result[dup_mask].sort_values(["관서명", "주소"]))
else:
    print("[로그] 중복 행 없음 (정상)")

# ------------------------------------------------------------------
# 10. 위도/경도는 원본에 없으므로 빈 컬럼으로 남겨둠 (추후 카카오 지오코딩)
# ------------------------------------------------------------------
result["위도"] = None
result["경도"] = None

# ------------------------------------------------------------------
# 11. 저장 (UTF-8-SIG로 저장해야 엑셀에서 열어도 한글이 안 깨짐)
# ------------------------------------------------------------------
result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
print(f"[로그] 저장 완료: {OUT_PATH} (총 {len(result)}행)")