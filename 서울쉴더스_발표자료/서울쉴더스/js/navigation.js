/**
 * 서울-쉴더스 (Seoul-Shielders) Presentation Engine
 * navigation.js - 툴바, 플로팅 네비게이션 독, 썸네일 드로어 및 모달 자동 생성
 */

document.addEventListener('DOMContentLoaded', () => {
    const engine = window.presentation;
    if (!engine) return;

    const currentSlide = engine.slides.find(s => s.id === engine.currentSlideId) || engine.slides[0];
    const totalSlides = engine.slides.length;

    // 1. Build and Inject Floating Navigation Dock if missing
    if (!document.getElementById('presentationDock')) {
        const dock = document.createElement('nav');
        dock.id = 'presentationDock';
        dock.className = 'presentation-dock';
        dock.setAttribute('aria-label', '프레젠테이션 탐색바');
        
        dock.innerHTML = `
            <button class="dock-btn" onclick="presentation.prevSlide()" title="이전 슬라이드 (← / Backspace)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                <span>이전</span>
            </button>
            <span class="dock-page-indicator" onclick="presentation.toggleDrawer()" title="전체 슬라이드 보기 (T)">
                ${String(currentSlide.id).padStart(2, '0')} / ${String(totalSlides).padStart(2, '0')}
            </span>
            <button class="dock-btn" onclick="presentation.nextSlide()" title="다음 슬라이드 (→ / Space)">
                <span>다음</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
            <div style="width: 1px; height: 14px; background: rgba(255,255,255,0.15); margin: 0 2px;"></div>
            <button class="dock-btn" onclick="presentation.toggleDrawer()" title="슬라이드 목록 드로어 (T)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                <span>목록</span>
            </button>
            <button class="dock-btn" onclick="presentation.toggleFullScreen()" title="전체화면 (F)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
            </button>
            <button class="dock-btn" onclick="presentation.toggleHelp()" title="단축키 안내 (?)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </button>
        `;
        document.body.appendChild(dock);
    }

    // 2. Build and Inject Thumbnail Drawer Overview Modal
    if (!document.getElementById('thumbnailDrawer')) {
        const drawerBackdrop = document.createElement('div');
        drawerBackdrop.id = 'thumbnailDrawer';
        drawerBackdrop.className = 'drawer-backdrop';
        drawerBackdrop.onclick = (e) => {
            if (e.target === drawerBackdrop) {
                engine.toggleDrawer();
            }
        };

        const cardsHtml = engine.slides.map(slide => `
            <div class="thumbnail-card ${slide.id === engine.currentSlideId ? 'active' : ''}" onclick="presentation.goToSlide(${slide.id})">
                <div class="flex items-center justify-between">
                    <span class="thumbnail-num">SLIDE ${String(slide.id).padStart(2, '0')}</span>
                    <span class="badge badge-primary" style="font-size: 0.6rem; padding: 1px 5px;">${slide.category || 'PAGE'}</span>
                </div>
                <div class="thumbnail-title">${slide.title}</div>
                <div class="thumbnail-desc">${slide.sub}</div>
            </div>
        `).join('');

        drawerBackdrop.innerHTML = `
            <div class="drawer-content">
                <div class="drawer-header">
                    <div>
                        <h3 class="text-xl font-bold text-white">전체 슬라이드 목차 (Overview)</h3>
                        <p class="text-xs text-muted">이동하고자 하는 슬라이드를 클릭하거나 키보드 번호를 누르세요.</p>
                    </div>
                    <button class="btn-toolbar" onclick="presentation.toggleDrawer()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        <span>닫기 (Esc)</span>
                    </button>
                </div>
                <div class="drawer-grid">
                    ${cardsHtml}
                </div>
            </div>
        `;
        document.body.appendChild(drawerBackdrop);
    }

    // 3. Build and Inject Shortcuts Guide Modal
    if (!document.getElementById('shortcutsModal')) {
        const shortcutsModal = document.createElement('div');
        shortcutsModal.id = 'shortcutsModal';
        shortcutsModal.className = 'shortcuts-modal';
        shortcutsModal.innerHTML = `
            <div class="flex items-center justify-between" style="border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 12px;">
                <h4 class="text-base font-bold text-white flex items-center gap-2">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h.001M10 8h.001M14 8h.001M18 8h.001M8 12h.001M12 12h.001M16 12h.001M7 16h10"/></svg>
                    프레젠테이션 키보드 단축키
                </h4>
                <button class="btn-toolbar" onclick="presentation.toggleHelp()">닫기</button>
            </div>
            <div class="space-y-1">
                <div class="shortcut-row">
                    <span class="text-sub">다음 슬라이드</span>
                    <div><span class="kbd">→</span> <span class="kbd">Space</span> <span class="kbd">PageDown</span></div>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">이전 슬라이드</span>
                    <div><span class="kbd">←</span> <span class="kbd">Backspace</span> <span class="kbd">PageUp</span></div>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">첫 / 마지막 슬라이드</span>
                    <div><span class="kbd">Home</span> / <span class="kbd">End</span></div>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">전체화면 토글</span>
                    <span class="kbd">F</span>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">슬라이드 목록 (드로어)</span>
                    <span class="kbd">T</span>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">다크/라이트 테마 전환</span>
                    <span class="kbd">M</span>
                </div>
                <div class="shortcut-row">
                    <span class="text-sub">단축키 도움말</span>
                    <div><span class="kbd">?</span> <span class="kbd">H</span></div>
                </div>
            </div>
        `;
        document.body.appendChild(shortcutsModal);
    }
});
