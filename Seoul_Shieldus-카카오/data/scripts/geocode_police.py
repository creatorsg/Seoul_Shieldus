"""
지구대/파출소 위도/경도 채우기 (카카오 로컬 API 지오코딩)

준비물:
  1) pip install requests python-dotenv
  2) data_police_cctv/scripts/.env 파일 만들고 아래처럼 한 줄 작성
     KAKAO_API_KEY=발급받은_REST_API_키
  3) .env는 절대 깃허브에 올리지 말 것 (.gitignore에 .env 추가)

동작 순서:
  1) processed/jigudae_seoul.csv 읽기
  2) 각 행의 '주소'로 카카오 "주소 검색 API" 호출
  3) 실패하면(도로명 주소가 애매하거나 괄호 설명 등으로 매칭 안 되는 경우)
     '관서명 + 자치구'로 "키워드 검색 API" 재시도 (경찰서/파출소는 보통 장소로 등록돼 있음)
  4) 그래도 실패하면 위도/경도 비워두고 로그에 남김 (수동 확인용)
  5) 같은 파일에 위도/경도 채워서 저장
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()  # scripts/.env 에서 KAKAO_API_KEY 로드

KAKAO_API_KEY = os.getenv("KAKAO_REST_API_KEY") or os.getenv("KAKAO_API_KEY")
if not KAKAO_API_KEY:
    raise RuntimeError(
        "KAKAO_REST_API_KEY가 없습니다. .env 파일에 KAKAO_REST_API_KEY=발급받은키 형태로 추가하세요."
    )

HEADERS = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

BASE_DIR = Path(__file__).resolve().parent.parent  # data_police_cctv 폴더
IN_PATH = BASE_DIR / "processed" / "jigudae_seoul.csv"
OUT_PATH = BASE_DIR / "processed" / "jigudae_seoul.csv"  # 같은 파일에 덮어씀


def geocode_by_address(addr: str):
    """주소 검색 API. 성공하면 (위도, 경도) 반환, 실패하면 None."""
    res = requests.get(ADDRESS_URL, headers=HEADERS, params={"query": addr}, timeout=5)
    res.raise_for_status()
    docs = res.json().get("documents", [])
    if not docs:
        return None
    # 카카오 응답은 x=경도, y=위도 (헷갈리기 쉬우니 주의)
    return float(docs[0]["y"]), float(docs[0]["x"])


def geocode_by_keyword(keyword: str):
    """키워드(장소) 검색 API. 주소 검색 실패 시 보조 수단."""
    res = requests.get(KEYWORD_URL, headers=HEADERS, params={"query": keyword}, timeout=5)
    res.raise_for_status()
    docs = res.json().get("documents", [])
    if not docs:
        return None
    return float(docs[0]["y"]), float(docs[0]["x"])


def main():
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig")
    print(f"[로그] 대상 {len(df)}행 로드 완료")

    lat_list, lng_list = [], []
    failed_rows = []

    for i, row in df.iterrows():
        addr = str(row["주소"])
        lat, lng = None, None

        try:
            result = geocode_by_address(addr)
            if result:
                lat, lng = result
                source = "주소검색"
            else:
                # 주소 검색 실패 -> 관서명 + 자치구로 키워드 검색 재시도
                keyword = f"{row['자치구']} {row['관서명']}"
                result = geocode_by_keyword(keyword)
                if result:
                    lat, lng = result
                    source = "키워드검색(재시도)"
                else:
                    source = "실패"
                    failed_rows.append((i, row["관서명"], addr))
        except requests.exceptions.RequestException as e:
            source = "API오류"
            failed_rows.append((i, row["관서명"], f"{addr} (오류: {e})"))

        lat_list.append(lat)
        lng_list.append(lng)

        print(f"[{i+1}/{len(df)}] {row['자치구']} {row['관서명']} -> {source} "
              f"({lat}, {lng})")

        time.sleep(0.05)  # 과도한 요청 방지용 짧은 대기

    df["위도"] = lat_list
    df["경도"] = lng_list

    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[로그] 저장 완료: {OUT_PATH}")

    if failed_rows:
        print(f"\n[경고] 좌표 변환 실패 {len(failed_rows)}건 (수동 확인 필요):")
        for idx, name, addr in failed_rows:
            print(f"  - ({idx}) {name}: {addr}")
    else:
        print("\n[로그] 전체 좌표 변환 성공")


if __name__ == "__main__":
    main()