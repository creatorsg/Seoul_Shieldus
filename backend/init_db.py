import json
import os

# database 및 models 모듈 불러오기
from database import engine, SessionLocal, Base
from models import (
    SeoulSafetyIndex,
    DistrictCctvStat,
    PoliceStation,
    SafeRouteDistrict,
    SafeRoute,
    StreetLight,
)


def _first_present(item, *keys):
    """item에서 keys 순서대로 실제로 "존재하는" 첫 값을 반환한다 (없으면 None).

    기존 코드 전반에 `item.get(a) or item.get(b)` 패턴이 쓰였는데, 이러면 a쪽 값이 0이나
    0.0처럼 "있지만 falsy한" 값일 때 엉뚱하게 b를 찾으러 가버린다. 실제로 이 데이터엔
    범죄안전점수가 정확히 0.0인 구(중구)가 있는데, `or`를 쓰면 0.0이 버려지고 존재하지도
    않는 영문 키(crime_safety_score)를 찾다가 None이 되어 DB에 NULL로 저장되는 버그가
    있었다 - 다른 4개 구도 CCTV/경찰서/안심길/가로등 점수 중 하나가 정확히 0인 경우가 있어서
    같은 문제를 겪는다. 이 헬퍼는 값의 참/거짓이 아니라 "키가 있는지"로 판단해서 0/0.0도
    정상적으로 살아남는다.
    """
    for key in keys:
        if key in item:
            return item[key]
    return None


# -------------------------------------------------------------
# 1. DB 테이블 전체 생성 함수
# -------------------------------------------------------------
def create_all_tables():
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------
# 2. JSON 데이터 자동 적재 함수들 (Seed Data Loading)
# -------------------------------------------------------------
# 1) 치안안전지수 적재
def seed_safety_index(db, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    for item in data_list:
        district_name = _first_present(item, "자치구", "district")
        record = db.query(SeoulSafetyIndex).filter_by(district=district_name).first()
        record_data = {
            "district": district_name,
            "population": _first_present(item, "인구수", "population"),
            "area": _first_present(item, "면적", "area"),
            "crime_count_2024": _first_present(item, "2024", "crime_count_2024"),
            "route_count": _first_present(item, "노선수", "route_count"),
            "total_length": _first_present(item, "총길이", "total_length"),
            "police_station_count": _first_present(
                item, "지구대파출소수", "police_station_count"
            ),
            "cctv_count": _first_present(item, "CCTV수량", "cctv_count"),
            "street_light_count": _first_present(
                item, "가로등_개수", "street_light_count"
            ),
            "crime_rate_per_pop": _first_present(
                item, "인구당_범죄율", "crime_rate_per_pop"
            ),
            "cctv_per_pop": _first_present(item, "인구당_CCTV", "cctv_per_pop"),
            "police_per_area": _first_present(item, "면적당_경찰서", "police_per_area"),
            "safe_road_per_area": _first_present(
                item, "면적당_안심길", "safe_road_per_area"
            ),
            "street_light_per_area": _first_present(
                item, "면적당_가로등", "street_light_per_area"
            ),
            "cctv_score": _first_present(item, "CCTV점수", "cctv_score"),
            "police_score": _first_present(item, "경찰서점수", "police_score"),
            "safe_road_score": _first_present(item, "안심길점수", "safe_road_score"),
            "street_light_score": _first_present(
                item, "가로등점수", "street_light_score"
            ),
            "crime_safety_score": _first_present(
                item, "범죄안전점수", "crime_safety_score"
            ),
            "safety_index": _first_present(item, "치안안전지수", "safety_index"),
        }
        if record:
            for k, v in record_data.items():
                setattr(record, k, v)
        else:
            db.add(SeoulSafetyIndex(**record_data))
    db.commit()


# 2) 안심귀갓길 및 노선 적재 (SafeRouteDistrict, SafeRoute)
def seed_safe_routes(db, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    for item in data_list:
        district_name = item.get("district")
        if not district_name:
            continue

        # 1) 자치구 요약 정보 적재 (SafeRouteDistrict)
        dist_record = (
            db.query(SafeRouteDistrict).filter_by(district=district_name).first()
        )
        dist_data = {
            "district": district_name,
            "route_count": item.get("route_count"),
            "total_length": item.get("total_length"),
        }
        if dist_record:
            for k, v in dist_data.items():
                if v is not None:
                    setattr(dist_record, k, v)
        else:
            db.add(SafeRouteDistrict(**dist_data))
            db.flush()

        # 2) 노선 상세 정보 적재 (SafeRoute)
        routes_list = item.get("routes", [])
        for r in routes_list:
            route_id = r.get("route_id")
            if not route_id:
                continue

            facilities = r.get("facilities", {})

            route_record = db.query(SafeRoute).filter_by(route_id=route_id).first()
            route_data = {
                "route_id": route_id,
                "district_name": district_name,
                "route_name": r.get("route_name"),
                "dong": r.get("dong"),
                "link_length": r.get("link_length"),
                "location_desc": r.get("location_desc"),
                "security_bell": facilities.get("security_bell", 0),
                "cctv": facilities.get("cctv", 0),
                "security_light": facilities.get("security_light", 0),
                "signage": facilities.get("signage", 0),
                "road_marking": facilities.get("road_marking", 0),
                "police_report_board": facilities.get("police_report_board", 0),
            }
            if route_record:
                for k, v in route_data.items():
                    setattr(route_record, k, v)
            else:
                db.add(SafeRoute(**route_data))

    db.commit()


# 3) 가로등 위치 적재 (StreetLight)
def seed_street_lights(db, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    for item in data_list:
        mgmt_id = item.get("management_id")
        if not mgmt_id:
            continue

        lat = item.get("lat")
        lng = item.get("lng")

        record = db.query(StreetLight).filter_by(management_id=mgmt_id).first()
        record_data = {
            "management_id": mgmt_id,
            "lat": lat,
            "lng": lng,
        }
        if record:
            for k, v in record_data.items():
                setattr(record, k, v)
        else:
            db.add(StreetLight(**record_data))
    db.commit()


# 4) CCTV 통계 적재 (DistrictCctvStat)
def seed_cctv_stats(db, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    for item in data_list:
        district_name = _first_present(item, "district", "자치구")
        purpose = item.get("purpose", {})
        record = db.query(DistrictCctvStat).filter_by(district=district_name).first()
        record_data = {
            "district": district_name,
            "total_cctv": item.get("total_cctv", 0),
            "crime_prevention_total": item.get("crime_prevention_total", 0),
            "purpose_crime": purpose.get("crime", 0),
            "purpose_child_protection": purpose.get("child_protection", 0),
            "purpose_park_playground": purpose.get("park_playground", 0),
            "purpose_illegal_dumping": purpose.get("illegal_dumping", 0),
            "purpose_fire_safety": purpose.get("fire_safety", 0),
            "purpose_traffic_crackdown": purpose.get("traffic_crackdown", 0),
            "purpose_traffic_info": purpose.get("traffic_info", 0),
            "purpose_others": purpose.get("others", 0),
        }
        if record:
            for k, v in record_data.items():
                setattr(record, k, v)
        else:
            db.add(DistrictCctvStat(**record_data))
    db.commit()


# 5) 경찰서/지구대 위치 적재 (PoliceStation)
def seed_police_stations(db, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    for item in data_list:
        station_name = _first_present(item, "station_name", "지구대파출소명", "관서명")
        district_name = _first_present(item, "district", "자치구")
        record = (
            db.query(PoliceStation)
            .filter_by(district=district_name, station_name=station_name)
            .first()
        )
        record_data = {
            "district": district_name,
            "station_name": station_name,
            "type": _first_present(item, "type", "구분"),
            "address": _first_present(item, "address", "주소"),
            "lat": _first_present(item, "lat", "위도"),
            "lng": _first_present(item, "lng", "경도"),
        }
        if record:
            for k, v in record_data.items():
                setattr(record, k, v)
        else:
            db.add(PoliceStation(**record_data))
    db.commit()


# -------------------------------------------------------------
# 3. 메인 실행 함수
# -------------------------------------------------------------
def initialize_database():
    # 1) 테이블 생성
    create_all_tables()

    # 2) JSON 초기 데이터 적재 실행
    db = SessionLocal()
    try:
        # 데이터 폴더 기본 경로 (프로젝트 root 기준 data/processed/)
        base_data_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed"
        )

        # 5개 데이터 세트 초기화 및 데이터 적재
        seed_safety_index(db, os.path.join(base_data_dir, "seoul_safety_index(1).json"))
        seed_safe_routes(db, os.path.join(base_data_dir, "seoul_safe_paths(2).json"))
        seed_street_lights(
            db, os.path.join(base_data_dir, "seoul_street_lights(3).json")
        )
        seed_cctv_stats(db, os.path.join(base_data_dir, "seoul_cctv_stats(4).json"))
        seed_police_stations(db, os.path.join(base_data_dir, "seoul_jigudae(5).json"))

        print("\n🎉 [완료] 데이터베이스 초기화 및 데이터 적재가 모두 끝났습니다!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ [오류] 데이터 적재 실패: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
