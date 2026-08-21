/**
 * 서울-쉴더스 (Seoul-Shielders) Presentation Engine
 * data.js - 서울시 치안·보안 인프라 데이터 모듈 및 통계 헬퍼
 */

class SeoulShieldersDataService {
    constructor() {
        this.districts = [];
        this.policeStations = [];
        this.cctvData = [];
        this.safePaths = [];
        this.initialized = false;
    }

    /**
     * 비동기 데이터 로더 (JSON 파일 로드 또는 내장 폴백 데이터셋 사용)
     */
    async init() {
        if (this.initialized) return;

        try {
            const basePath = window.location.pathname.includes('/pages/') ? '../' : './';
            const [distRes, polRes, cctvRes, pathRes] = await Promise.all([
                fetch(`${basePath}data/seoul-districts.json`),
                fetch(`${basePath}data/police.json`),
                fetch(`${basePath}data/cctv.json`),
                fetch(`${basePath}data/safe-path.json`)
            ]);

            this.districts = await distRes.json();
            this.policeStations = await polRes.json();
            this.cctvData = await cctvRes.json();
            this.safePaths = await pathRes.json();
            this.initialized = true;
            console.log('[Data Service] All 4 JSON datasets loaded successfully.');
        } catch (error) {
            console.warn('[Data Service] Fetch fallback to embedded data:', error.message);
            this.districts = this.getEmbeddedDistricts();
            this.initialized = true;
        }
    }

    /**
     * 25개 자치구 데이터 반환
     */
    getDistricts() {
        return this.districts.length ? this.districts : this.getEmbeddedDistricts();
    }

    /**
     * 5대 범죄 서울 전체 종합 통계 KPI 산출
     */
    getCitySummary() {
        const list = this.getDistricts();
        return list.reduce((acc, cur) => {
            acc.totalPopulation += cur.population;
            acc.totalCrime += cur.totalCrime;
            acc.violence += cur.violence;
            acc.theft += cur.theft;
            acc.sexCrime += cur.sexCrime;
            acc.murderRobbery += cur.murderRobbery;
            acc.totalStreetlights += cur.streetlights;
            acc.totalCCTV += cur.cctv;
            acc.totalSafePaths += cur.safePaths;
            return acc;
        }, {
            totalPopulation: 0,
            totalCrime: 0,
            violence: 0,
            theft: 0,
            sexCrime: 0,
            murderRobbery: 0,
            totalStreetlights: 0,
            totalCCTV: 0,
            totalSafePaths: 0
        });
    }

    /**
     * 상관관계 분석 수치 반환
     */
    getCorrelationStats() {
        return {
            rawPearson: 0.561, // 가로등수 ↔ 범죄 절대건수
            adjustedPearson: 0.120, // 가로등/인구 ↔ 범죄/인구 (보정 후)
            spearman: 0.492,
            regressionFormula: "y = 0.8415x + 2583.4",
            rSquared: 0.315
        };
    }

    /**
     * 오프라인 또는 직접 실행 시 사용할 내장 데이터셋
     */
    getEmbeddedDistricts() {
        return [
            { id: "11110", name: "종로구", population: 139417, totalCrime: 2735, crimePer10k: 196.17, violence: 1340, theft: 1195, sexCrime: 182, murderRobbery: 18, streetlights: 892, cctv: 2150, safePaths: 42 },
            { id: "11140", name: "중구", population: 121349, totalCrime: 2963, crimePer10k: 244.17, violence: 1388, theft: 1380, sexCrime: 178, murderRobbery: 17, streetlights: 745, cctv: 2480, safePaths: 38 },
            { id: "11170", name: "용산구", population: 213039, totalCrime: 2596, crimePer10k: 121.86, violence: 1285, theft: 1140, sexCrime: 158, murderRobbery: 13, streetlights: 810, cctv: 2950, safePaths: 46 },
            { id: "11200", name: "성동구", population: 278696, totalCrime: 2112, crimePer10k: 75.78, violence: 1020, theft: 955, sexCrime: 128, murderRobbery: 9, streetlights: 732, cctv: 3820, safePaths: 51 },
            { id: "11215", name: "광진구", population: 336024, totalCrime: 3120, crimePer10k: 92.85, violence: 1540, theft: 1370, sexCrime: 198, murderRobbery: 12, streetlights: 845, cctv: 3450, safePaths: 48 },
            { id: "11230", name: "동대문구", population: 341887, totalCrime: 3180, crimePer10k: 93.01, violence: 1580, theft: 1410, sexCrime: 175, murderRobbery: 15, streetlights: 912, cctv: 3180, safePaths: 53 },
            { id: "11260", name: "중랑구", population: 384274, totalCrime: 3420, crimePer10k: 89.00, violence: 1750, theft: 1460, sexCrime: 195, murderRobbery: 15, streetlights: 0, cctv: 3950, safePaths: 55 },
            { id: "11290", name: "성북구", population: 427278, totalCrime: 2460, crimePer10k: 57.57, violence: 1180, theft: 1120, sexCrime: 150, murderRobbery: 10, streetlights: 810, cctv: 4520, safePaths: 62 },
            { id: "11305", "name": "강북구", population: 291384, totalCrime: 2680, crimePer10k: 91.97, violence: 1420, theft: 1100, sexCrime: 148, murderRobbery: 12, streetlights: 740, cctv: 3120, safePaths: 44 },
            { id: "11320", "name": "도봉구", population: 309494, totalCrime: 1980, crimePer10k: 63.98, violence: 980, theft: 870, sexCrime: 122, murderRobbery: 8, streetlights: 680, cctv: 2890, safePaths: 39 },
            { id: "11350", "name": "노원구", population: 498305, totalCrime: 3620, crimePer10k: 72.65, violence: 1820, theft: 1580, sexCrime: 205, murderRobbery: 15, streetlights: 1120, cctv: 3280, safePaths: 68 },
            { id: "11380", "name": "은평구", population: 465223, totalCrime: 3390, crimePer10k: 72.87, violence: 1690, theft: 1490, sexCrime: 195, murderRobbery: 15, streetlights: 960, cctv: 4250, safePaths: 59 },
            { id: "11410", "name": "서대문구", population: 306079, totalCrime: 2280, crimePer10k: 74.49, violence: 1090, theft: 1030, sexCrime: 150, murderRobbery: 10, streetlights: 740, cctv: 3580, safePaths: 45 },
            { id: "11440", "name": "마포구", population: 364657, totalCrime: 3850, crimePer10k: 105.58, violence: 1860, theft: 1690, sexCrime: 285, murderRobbery: 15, streetlights: 890, cctv: 3240, safePaths: 56 },
            { id: "11470", "name": "양천구", population: 438354, totalCrime: 2980, crimePer10k: 67.98, violence: 1480, theft: 1340, sexCrime: 150, murderRobbery: 10, streetlights: 830, cctv: 3890, safePaths: 52 },
            { id: "11500", "name": "강서구", population: 564972, totalCrime: 4350, crimePer10k: 76.99, violence: 2180, theft: 1910, sexCrime: 240, murderRobbery: 20, streetlights: 1250, cctv: 3350, safePaths: 74 },
            { id: "11530", "name": "구로구", population: 393792, totalCrime: 3650, crimePer10k: 92.69, violence: 1860, theft: 1570, sexCrime: 205, murderRobbery: 15, streetlights: 910, cctv: 4480, safePaths: 58 },
            { id: "11545", "name": "금천구", population: 228945, totalCrime: 2680, crimePer10k: 117.06, violence: 1410, theft: 1120, sexCrime: 138, murderRobbery: 12, streetlights: 680, cctv: 2950, safePaths: 41 },
            { id: "11560", "name": "영등포구", population: 376282, totalCrime: 4820, crimePer10k: 128.09, violence: 2430, theft: 2080, sexCrime: 290, murderRobbery: 20, streetlights: 1040, cctv: 4680, safePaths: 64 },
            { id: "11590", "name": "동작구", population: 380486, totalCrime: 2790, crimePer10k: 73.33, violence: 1350, theft: 1260, sexCrime: 170, murderRobbery: 10, streetlights: 790, cctv: 2860, safePaths: 50 },
            { id: "11620", "name": "관악구", population: 486744, totalCrime: 4580, crimePer10k: 94.09, violence: 2340, theft: 1980, sexCrime: 240, murderRobbery: 20, streetlights: 1150, cctv: 5420, safePaths: 72 },
            { id: "11650", "name": "서초구", population: 406604, totalCrime: 3950, crimePer10k: 97.15, violence: 1820, theft: 1850, sexCrime: 265, murderRobbery: 15, streetlights: 1210, cctv: 4890, safePaths: 61 },
            { id: "11680", "name": "강남구", population: 550282, totalCrime: 6107, crimePer10k: 110.98, violence: 2890, theft: 2790, sexCrime: 405, murderRobbery: 22, streetlights: 1420, cctv: 7240, safePaths: 86 },
            { id: "11710", "name": "송파구", population: 654166, totalCrime: 5120, crimePer10k: 78.27, violence: 2510, theft: 2320, sexCrime: 270, murderRobbery: 20, streetlights: 1390, cctv: 3680, safePaths: 78 },
            { id: "11740", "name": "강동구", population: 458694, totalCrime: 3480, crimePer10k: 75.87, violence: 1720, theft: 1580, sexCrime: 168, murderRobbery: 12, streetlights: 980, cctv: 3390, safePaths: 60 }
        ];
    }
}

// Global Data Service Instance
window.seoulData = new SeoulShieldersDataService();
window.seoulData.init();
