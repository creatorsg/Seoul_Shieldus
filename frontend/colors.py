

# 점수 구간별 (채우기 색, 그 위에 얹을 글자 색). 낮은 점수(위험)일수록 빨강, 높은 점수(안전)일수록
# 초록. 글자 색은 각 배경색 위에서 대비가 잘 나오는 쪽으로 골랐다(노랑 배경엔 흰 글자가 잘 안 보여서
# 검정으로, 나머지는 배경이 충분히 진해서 흰 글자로).
SCORE_COLOR_BANDS = [
    (40, "#D32F2F", "#FFFFFF"),  # 40점 미만: 위험
    (50, "#F57C00", "#FFFFFF"),  # 40~50점: 주의
    (60, "#FBC02D", "#1B1B1B"),  # 50~60점: 보통
    (101, "#2E7D32", "#FFFFFF"),  # 75점 이상: 안전
]


def score_to_color(score: float) -> str:
    """0~100 점수를 안전도 색상(hex)으로 변환한다."""
    for threshold, color, _ in SCORE_COLOR_BANDS:
        if score < threshold:
            return color
    return SCORE_COLOR_BANDS[-1][1]


def score_to_text_color(score: float) -> str:
    """score_to_color()가 반환하는 배경색 위에 글자를 얹을 때 쓸, 대비가 좋은 글자색을 반환한다."""
    for threshold, _, text_color in SCORE_COLOR_BANDS:
        if score < threshold:
            return text_color
    return SCORE_COLOR_BANDS[-1][2]
