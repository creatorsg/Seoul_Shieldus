"""
CSS/HTML 문자열 상수 모음.

app.py의 렌더링 함수들이 st.markdown(..., unsafe_allow_html=True)로 그대로 주입해서 쓴다.
각 상수 아래 주석은 "무엇을 하는지"만 한 줄로 적어둔다 - "왜 이렇게 짜여있는지"(배경/트레이드
오프/버그 히스토리)는 frontend.md의 같은 이름 섹션에 정리되어 있다.
"""

PRETENDARD_CSS_URL = (
    "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@1.3.9/dist/web/static/pretendard.css"
)

# 화면 전체(사이드바/본문/위젯)에 Pretendard 폰트를 적용한다.
PRETENDARD_FONT_CSS = """
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stMarkdownContainer"],
button, input, textarea, select, label {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui,
        'Malgun Gothic', sans-serif !important;
}
code, pre, kbd, samp {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
}
</style>
"""

# 사이드바 글자색/네비 하이라이트를 본문과 분리하고, 로고를 좌측 하단에 고정한다.
SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] a[aria-current="page"] {
    background: rgba(255,255,255,0.14) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] a:hover {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}
.sidebar-brand {
    color: #FFFFFF !important;
}
[data-testid="stSidebarUserContent"] {
    flex: none !important;
    min-height: 0 !important;
    height: 0 !important;
    overflow: visible !important;
}
[data-testid="stSidebar"] {
    position: relative !important;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .sidebar-logo-marker) {
    position: absolute !important;
    left: 16px;
    bottom: 16px;
    width: auto !important;
}
</style>
"""

# 지도(iframe 커스텀 컴포넌트) 카드의 모서리/테두리를 다른 카드들과 통일한다.
MAP_CARD_CSS = """
<style>
[data-testid="stCustomComponentV1"] {
    border-radius: 12px !important;
    border: 1px solid rgba(20,20,20,0.09) !important;
    overflow: hidden !important;
}
</style>
"""

# Streamlit 기본 UI(푸터/장식줄)를 숨기고, 화면에 안 그려지는 컴포넌트들의 높이를 0으로 접는다.
HIDE_STREAMLIT_CHROME_CSS = """
<style>
footer { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
[class*="st-key-head_scripts_inject"],
[class*="st-key-scroll_restore_"],
[class*="st-key-score_bar_replay_"] {
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
div[data-testid="stMainBlockContainer"] {
    padding-top: 64px !important;
}
</style>
"""

# 페이지 전환 시 콘텐츠가 살짝 떠오르며 나타나는 페이드인 애니메이션 (지도 iframe은 제외).
PAGE_TRANSITION_CSS = """
<style>
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
div[data-testid="stMain"] div[data-testid="stElementContainer"]:not(:has(iframe)) {
    animation: fadeSlideIn 0.28s ease-out;
}
</style>
"""

# selectbox 배경을 흰색으로 고정한다 (사이드바 남색을 물려받아 텍스트가 안 보이던 문제).
SELECTBOX_CSS = """
<style>
[data-testid="stSelectbox"] [role="group"] {
    background-color: #FFFFFF !important;
}
</style>
"""

# "보기 방식" 라디오를 세그먼트 버튼(탭)처럼 보이게 한다.
VIEW_TOGGLE_CSS = """
<style>
div[data-testid="stRadio"] > div[role="radiogroup"] { display:flex; gap:8px; }
div[data-testid="stRadio"] label {
    border:1px solid rgba(20,20,20,0.09); border-radius:8px; padding:8px 16px; cursor:pointer;
}
div[data-testid="stRadio"] label:has(input:checked) { background:#262626; }
div[data-testid="stRadio"] label:has(input:checked) p { color:#fff; }
</style>
"""

# GPS 위치를 기다리는 동안 보여줄 스피너 (CSS 애니메이션이라 리런과 무관하게 계속 돈다).
GPS_WAIT_SPINNER_HTML = """
<style>
@keyframes gpsSpin { to { transform: rotate(360deg); } }
</style>
<div style="display:flex;align-items:center;gap:12px;padding:16px;
            background:#F5F7F5;border-radius:8px;margin-bottom:8px;">
  <div style="width:22px;height:22px;border-radius:50%;flex-shrink:0;
              border:3px solid #C8E6C9;border-top-color:#2E7D32;
              animation:gpsSpin 0.8s linear infinite;"></div>
  <span style="font-size:14px;color:#1B1B1B;">
    브라우저가 위치 권한을 물어보면 허용해주세요. 내 위치를 가져오는 중입니다...
  </span>
</div>
"""

# 점수 막대가 0%에서 실제 값까지 좌→우로 차오르는 애니메이션.
SCORE_BAR_CSS = """
<style>
@keyframes scoreBarFill {
    from { width: 0%; }
    to { width: var(--fill-width); }
}
.score-bar-fill {
    animation: scoreBarFill 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
"""

# 자치구 상세 패널의 소제목 3개(구 상세/안심지수/CCTV) 글씨 크기를 24px/굵게로 통일한다.
DISTRICT_DETAIL_CSS = """
<style>
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    font-size: 24px !important;
    font-weight: 600 !important;
}
</style>
"""

# 안심지수/CCTV 섹션을 반투명 유리(glass) 카드로 감싼다 (.glass-card-marker로 대상 컨테이너만 선택).
GLASS_CARD_CSS = """
<style>
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .glass-card-marker) {
    background: rgba(255,255,255,0.55) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.6) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 24px rgba(30,58,95,0.08) !important;
    padding: 20px !important;
}
</style>
"""

# 안심지수 히트맵 페이지의 expander(설명 접기/펼치기) 모서리를 둥글게, 그림자는 없앤다.
EXPANDER_CARD_CSS = """
<style>
div[data-testid="stExpander"] details {
    border-radius: 12px !important;
    box-shadow: none !important;
}
</style>
"""

# 홈 화면 기능 카드 3개의 모서리/호버 효과(뜨는 애니메이션 + accent 색 테두리)를 정의한다.
HOME_CARD_CSS = """
<style>
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stPageLink"]) {
    border-radius: 12px !important;
    box-shadow: none !important;
    transition: transform 0.15s ease-out, border-color 0.15s ease-out;
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stPageLink"]):hover {
    transform: translateY(-4px);
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(1)
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stPageLink"]):hover {
    border-color: #2E7D32 !important;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2)
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stPageLink"]):hover {
    border-color: #D81B60 !important;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(3)
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] [data-testid="stPageLink"]):hover {
    border-color: #1565C0 !important;
}
.home-card-icon-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 44px; height: 44px; border-radius: 12px; font-size: 22px;
    margin-bottom: 8px;
}
</style>
"""
