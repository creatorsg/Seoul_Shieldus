"""
점수(0~100)를 안전도 색상으로 바꾸는 단일 기준점.

사이드바 점수 막대, 자치구 랭킹 표, 안심지수 히트맵까지 점수를 색으로 표현하는 모든 곳이
이 함수만 같이 쓴다. 색 기준이나 임계값을 바꿔야 하면 여기 한 곳만 고치면 된다.

⚠ 예전엔 히트맵 지도만 folium.Choropleth의 fill_color="RdYlGn"을 따로 썼었다. 이게 이름만
비슷한 배색이지 실제로는 25개 구의 안심지수 "분포"를 6구간으로 자동으로 나눠서 칠하는
상대적 색칠(데이터가 바뀌면 같은 점수도 다른 색이 될 수 있음)이라, 여기 이 파일의 고정
임계값(40/60/75) 기준과는 전혀 다른 기준으로 색이 매겨졌었다 - 그래서 지도에서는 초록인데
랭킹 표나 상세 페이지에서는 주황으로 보이는 등 화면마다 "무슨 색이 무슨 뜻인지"가 어긋났다.
지금은 지도도 이 파일의 score_to_color()를 직접 호출해서 칠하도록 고쳐서, 어느 화면에서
보든 같은 점수는 항상 같은 색이다.
"""

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
