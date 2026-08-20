import os
import re
import requests
import json
from datetime import datetime

# 1) 스크립트 파일 기준 절대경로로 저장 위치 고정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # data_accident_list/scripts
SAVE_DIR = os.path.join(BASE_DIR, "..", "raw")          # data_accident_list/raw
os.makedirs(SAVE_DIR, exist_ok=True)

# 2) 세션 생성 (JSESSIONID 쿠키 확보용)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
})
session.get("https://safecity.seoul.go.kr/main.do")

# 3) 사고 목록 API 호출
resp = session.post(
    "https://safecity.seoul.go.kr/news/acdnt/getAcdntList.do",
    headers={
        "Referer": "https://safecity.seoul.go.kr/",
        "Origin": "https://safecity.seoul.go.kr",
        "X-Requested-With": "XMLHttpRequest",
    },
)
resp.raise_for_status()
data = resp.json()

print(len(data.get("timeList", [])), "건 수집")

# 오늘 날짜 기준으로 이미 저장된 파일 중 가장 큰 순번 찾기
today = datetime.now().strftime("%Y%m%d")
pattern = re.compile(rf"accident_list_{today}_(\d+)\.json")

existing_nums = [
    int(m.group(1))
    for fname in os.listdir(SAVE_DIR)
    if (m := pattern.match(fname))
]
next_num = max(existing_nums, default=0) + 1

filename = f"accident_list_{today}_{next_num}.json"
save_path = os.path.join(SAVE_DIR, filename)
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


print("저장 완료:", save_path)