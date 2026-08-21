"""
서울시 치안 안전 지수 대시보드 - 다크 스타일 모듈

보안/관제 센터 컨셉의 고급 다크모드 스타일과 커스텀 UI 컴포넌트 렌더링 헬퍼를 정의한다.
"""

import streamlit as st
from colors import score_to_color

DARK_THEME_CSS = """
<style>
/* 1. 전체 배경 및 기본 폰트 */
html, body, [data-testid="stAppViewContainer"], .main {
    background-color: #0B1120 !important;
    color: #F8FAFC !important;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* 2. 크롬 요소 숨기기 (푸터, 장식바, 햄버거 메뉴 등) */
footer { visibility: hidden !important; display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
#MainMenu { visibility: hidden !important; }

/* 3. 사이드바 / 네비게이션 다크모드 */
[data-testid="stSidebar"], section[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #263449 !important;
}

[data-testid="stSidebarNav"] {
    background-color: #111827 !important;
    padding-top: 1rem;
}

[data-testid="stSidebarNav"] a {
    color: #94A3B8 !important;
    border-radius: 6px !important;
    margin: 2px 8px !important;
    padding: 10px 14px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarNav"] a:hover {
    background-color: #172033 !important;
    color: #06B6D4 !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #172033 !important;
    color: #06B6D4 !important;
    border-left: 3px solid #06B6D4 !important;
    font-weight: 700 !important;
}

/* 4. 카드 / 컨테이너 박스 */
.dark-card {
    background-color: #111827;
    border: 1px solid #263449;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.dark-card-title {
    font-size: 15px;
    font-weight: 600;
    color: #06B6D4;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 5. 타이포그래피 */
h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
    font-weight: 700 !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #94A3B8 !important;
}

p, span, label {
    color: #F8FAFC;
}

/* 6. Form 입력 요소 (Selectbox, Radio, Button 등) */
div[data-baseweb="select"] > div {
    background-color: #172033 !important;
    border-color: #263449 !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
}

div[data-baseweb="select"] * {
    color: #F8FAFC !important;
}

div[data-baseweb="popover"] div {
    background-color: #172033 !important;
    color: #F8FAFC !important;
}

/* Radio 버튼 */
div[role="radiogroup"] {
    background-color: #172033 !important;
    padding: 4px !important;
    border-radius: 8px !important;
    border: 1px solid #263449 !important;
}

div[role="radiogroup"] label {
    padding: 6px 14px !important;
    border-radius: 6px !important;
    transition: background-color 0.2s ease !important;
}

div[role="radiogroup"] label:hover {
    background-color: #111827 !important;
}

/* 7. Dataframe / 테이블 다크 스타일 */
[data-testid="stDataFrame"], div[data-testid="stTable"] {
    background-color: #111827 !important;
    border: 1px solid #263449 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

div[data-testid="stDataFrame"] iframe {
    border-radius: 8px !important;
}

/* 8. Metric 박스 */
div[data-testid="stMetric"] {
    background-color: #172033 !important;
    border: 1px solid #263449 !important;
    border-radius: 8px !important;
    padding: 14px 18px !important;
}

div[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 13px !important;
}

div[data-testid="stMetricValue"] {
    color: #06B6D4 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* 9. iframe (지도) 테두리 & 배경 스타일 */
iframe {
    border: 1px solid #263449 !important;
    border-radius: 8px !important;
    background-color: #0B1120 !important;
}

/* 10. 경고/알림 박스 다크 스타일 */
div[data-testid="stNotification"] {
    background-color: #172033 !important;
    border: 1px solid #263449 !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

/* 11. 스크롤바 커스텀 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #0B1120;
}
::-webkit-scrollbar-thumb {
    background: #263449;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #06B6D4;
}
</style>
"""


def apply_dark_theme() -> None:
    """Streamlit 앱 전체에 다크모드 CSS를 적용한다."""
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def render_dashboard_header(title: str, subtitle: str = "") -> None:
    """관제 센터 느낌의 고급 다크모드 대시보드 헤더를 그린다."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; border-bottom: 1px solid #263449; padding-bottom: 16px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom: 6px;">
                <span style="background:#06B6D4; width:4px; height:24px; border-radius:2px; display:inline-block;"></span>
                <h1 style="margin:0; font-size:24px; font-weight:700; color:#F8FAFC; letter-spacing:-0.5px;">{title}</h1>
                <span style="background:#172033; border:1px solid #263449; color:#06B6D4; font-size:11px; font-weight:600; padding:3px 8px; border-radius:4px; margin-left:auto;">
                    LIVE CONTROL CENTER
                </span>
            </div>
            {f'<p style="margin:0; color:#94A3B8; font-size:13px; padding-left:16px;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_bar_html(label: str, score: float) -> str:
    """점수에 알맞은 다크모드 프로그레스 바 HTML을 생성한다."""
    color = score_to_color(score)
    width = max(0, min(100, score))
    return f"""
    <div style="margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px;">
        <span style="color:#94A3B8; font-weight:500;">{label}</span>
        <span style="color:{color}; font-weight:700;">{score:.1f}점</span>
      </div>
      <div style="background:#172033; border:1px solid #263449; border-radius:4px; height:8px; width:100%; overflow:hidden;">
        <div style="width:{width}%; background:{color}; height:100%; border-radius:4px; transition: width 0.4s ease;"></div>
      </div>
    </div>
    """


def render_route_summary_card(destination_name: str, mode_label: str, distance_km: float, time_min: float) -> None:
    """길찾기 경로 결과를 강조 카드 형태로 렌더링한다."""
    st.markdown(
        f"""
        <div class="dark-card" style="border-left: 4px solid #06B6D4;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="color:#94A3B8; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">
                        목적지 경로 안내 ({mode_label})
                    </div>
                    <div style="color:#F8FAFC; font-size:18px; font-weight:700;">
                        내 위치 <span style="color:#06B6D4;">➔</span> {destination_name}
                    </div>
                </div>
                <div style="display:flex; gap:24px; background:#172033; padding:10px 18px; border-radius:6px; border:1px solid #263449;">
                    <div>
                        <div style="color:#94A3B8; font-size:11px;">예상 거리</div>
                        <div style="color:#22C55E; font-size:20px; font-weight:700;">약 {distance_km} <span style="font-size:13px;">km</span></div>
                    </div>
                    <div style="width:1px; background:#263449;"></div>
                    <div>
                        <div style="color:#94A3B8; font-size:11px;">예상 소요 시간</div>
                        <div style="color:#06B6D4; font-size:20px; font-weight:700;">약 {time_min} <span style="font-size:13px;">분</span></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
