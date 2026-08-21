/**
 * 서울-쉴더스 (Seoul-Shielders) Presentation Engine
 * presentation.js - 슬라이드 목록 정의, 페이지 전환, 키보드 단축키, 전체화면
 */

/**
 * ==============================================================================
 * 1. SLIDE LIST CONFIGURATION (슬라이드 단일 진실 공급원)
 * 슬라이드 추가/삭제/순서 변경 시 아래 배열만 수정하면 시스템 전체에 즉시 반영됩니다.
 * ==============================================================================
 */
const slides = [
    {
        id: 1,
        file: "pages/01-intro.html",
        title: "프로젝트 소개",
        sub: "서울-쉴더스 비전 및 4단계 파이프라인",
        category: "INTRO"
    },
    {
        id: 2,
        file: "pages/02-problem.html",
        title: "문제 정의 & 배경",
        sub: "치안 인프라 분산 및 절대건수 착시 문제",
        category: "PROBLEM"
    },
    {
        id: 3,
        file: "pages/03-data.html",
        title: "공공데이터 수집",
        sub: "5대 범죄, 인구, 가로등·CCTV 데이터",
        category: "DATA"
    },
    {
        id: 4,
        file: "pages/04-analysis.html",
        title: "전처리 및 방법론",
        sub: "데이터 품질 검토 및 인구 보정 지표",
        category: "METHOD"
    },
    {
        id: 5,
        file: "pages/05-map.html",
        title: "치안 공간 매핑",
        sub: "서울 25개 자치구 보안 레이어 시각화",
        category: "SPATIAL"
    },
    {
        id: 6,
        file: "pages/06-infrastructure.html",
        title: "인프라 상관성 분석",
        sub: "가로등·CCTV 상관성 및 인과 해석 엄밀성",
        category: "ANALYSIS"
    },
    {
        id: 7,
        file: "pages/07-safety.html",
        title: "자치구별 지표 비교",
        sub: "강남 vs 중구 대조 및 범죄 유형별 분포",
        category: "INSIGHT"
    },
    {
        id: 8,
        file: "pages/08-service.html",
        title: "안전지도 서비스",
        sub: "Streamlit 대시보드 및 시스템 아키텍처",
        category: "SERVICE"
    },
    {
        id: 9,
        file: "pages/09-result.html",
        title: "프로젝트 수행 회고",
        sub: "4대 핵심 과제 해결 및 레슨런",
        category: "RETRO"
    },
    {
        id: 10,
        file: "pages/10-closing.html",
        title: "시연 시나리오 & Q&A",
        sub: "7단계 라이브 시연 및 질의응답",
        category: "DEMO & QA"
    }
];

/**
 * ==============================================================================
 * 2. SLIDE NAVIGATION CONTROLLER
 * ==============================================================================
 */
class PresentationEngine {
    constructor() {
        this.slides = slides;
        this.currentSlideId = this.detectCurrentSlideId();
        this.basePath = this.detectBasePath();
        this.init();
    }

    /**
     * 현재 파일 경로를 분석하여 활성 슬라이드 ID 감지
     */
    detectCurrentSlideId() {
        const path = window.location.pathname;
        const filename = path.substring(path.lastIndexOf('/') + 1);
        
        for (let i = 0; i < this.slides.length; i++) {
            if (this.slides[i].file.endsWith(filename)) {
                return this.slides[i].id;
            }
        }
        return 1; // Default to slide 1
    }

    /**
     * index.html과 pages/ 하위 경로 차이를 보정하는 Base Path 반환
     */
    detectBasePath() {
        const path = window.location.pathname;
        if (path.includes('/pages/')) {
            return '../';
        }
        return './';
    }

    init() {
        this.bindKeyboardShortcuts();
        this.applyStoredTheme();
        console.log(`[Presentation Engine] Loaded Slide ${this.currentSlideId} of ${this.slides.length}`);
    }

    /**
     * 특정 슬라이드 ID로 이동
     */
    goToSlide(slideId) {
        if (slideId < 1 || slideId > this.slides.length) return;
        const targetSlide = this.slides.find(s => s.id === slideId);
        if (!targetSlide) return;

        const targetUrl = this.basePath + targetSlide.file;
        window.location.href = targetUrl;
    }

    nextSlide() {
        if (this.currentSlideId < this.slides.length) {
            this.goToSlide(this.currentSlideId + 1);
        }
    }

    prevSlide() {
        if (this.currentSlideId > 1) {
            this.goToSlide(this.currentSlideId - 1);
        }
    }

    firstSlide() {
        this.goToSlide(1);
    }

    lastSlide() {
        this.goToSlide(this.slides.length);
    }

    /**
     * 전체화면 토글
     */
    toggleFullScreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn(`Fullscreen request failed: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    /**
     * 다크 / 라이트 모드 전환 및 로컬 스토리지 저장
     */
    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme') || 'dark';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-theme', nextTheme);
        localStorage.setItem('seoul_shielders_theme', nextTheme);

        const themeLabel = document.getElementById('themeLabel');
        if (themeLabel) {
            themeLabel.textContent = nextTheme === 'dark' ? '라이트 모드' : '다크 모드';
        }
    }

    applyStoredTheme() {
        const savedTheme = localStorage.getItem('seoul_shielders_theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        const themeLabel = document.getElementById('themeLabel');
        if (themeLabel) {
            themeLabel.textContent = savedTheme === 'dark' ? '라이트 모드' : '다크 모드';
        }
    }

    /**
     * 썸네일 드로어 토글
     */
    toggleDrawer() {
        const drawer = document.getElementById('thumbnailDrawer');
        if (drawer) {
            drawer.classList.toggle('active');
        }
    }

    /**
     * 단축키 안내 모달 토글
     */
    toggleHelp() {
        const modal = document.getElementById('shortcutsModal');
        if (modal) {
            modal.classList.toggle('active');
        }
    }

    /**
     * 키보드 단축키 리스너 바인딩
     */
    bindKeyboardShortcuts() {
        window.addEventListener('keydown', (e) => {
            // 모달이 열려있을 때 ESC 키 누르면 모달 닫기
            if (e.key === 'Escape') {
                const drawer = document.getElementById('thumbnailDrawer');
                const modal = document.getElementById('shortcutsModal');
                if (drawer && drawer.classList.contains('active')) {
                    drawer.classList.remove('active');
                    return;
                }
                if (modal && modal.classList.contains('active')) {
                    modal.classList.remove('active');
                    return;
                }
            }

            // Input / Textarea 입력 중에는 단축키 비활성화
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
                return;
            }

            switch (e.key) {
                case 'ArrowRight':
                case 'PageDown':
                case ' ':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                case 'PageUp':
                case 'Backspace':
                    e.preventDefault();
                    this.prevSlide();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.firstSlide();
                    break;
                case 'End':
                    e.preventDefault();
                    this.lastSlide();
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullScreen();
                    break;
                case 't':
                case 'T':
                    e.preventDefault();
                    this.toggleDrawer();
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    this.toggleTheme();
                    break;
                case '?':
                case 'h':
                case 'H':
                    e.preventDefault();
                    this.toggleHelp();
                    break;
            }
        });
    }
}

// Global Presentation Instance
window.presentation = new PresentationEngine();
