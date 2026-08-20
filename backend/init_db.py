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
        district_name = item.get("자치구") or item.get("district")
        record = db.query(SeoulSafetyIndex).filter_by(district=district_name).first()
        record_data = {
            "district": district_name,
            "population": item.get("인구수") or item.get("population"),
            "area": item.get("면적") or item.get("area"),
            "crime_count_2024": item.get("2024") or item.get("crime_count_2024"),
            "route_count": item.get("노선수") or item.get("route_count"),
            "total_length": item.get("총길이") or item.get("total_length"),
            "police_station_count": item.get("지구대파출소수")
            or item.get("police_station_count"),
            "cctv_count": item.get("CCTV수량") or item.get("cctv_count"),
            "street_light_count": item.get("가로등_개수")
            or item.get("street_light_count"),
            "crime_rate_per_pop": item.get("인구당_범죄율")
            or item.get("crime_rate_per_pop"),
            "cctv_per_pop": item.get("인구당_CCTV") or item.get("cctv_per_pop"),
            "police_per_area": item.get("면적당_경찰서") or item.get("police_per_area"),
            "safe_road_per_area": item.get("면적당_안심길")
            or item.get("safe_road_per_area"),
            "street_light_per_area": item.get("면적당_가로등")
            or item.get("street_light_per_area"),
            "cctv_score": item.get("CCTV점수") or item.get("cctv_score"),
            "police_score": item.get("경찰서점수") or item.get("police_score"),
            "safe_road_score": item.get("안심길점수") or item.get("safe_road_score"),
            "street_light_score": item.get("가로등점수")
            or item.get("street_light_score"),
            "crime_safety_score": item.get("범죄안전점수")
            or item.get("crime_safety_score"),
            "safety_index": item.get("치안안전지수") or item.get("safety_index"),
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
        district_name = item.get("district") or item.get("자치구")
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
        station_name = (
            item.get("station_name") or item.get("지구대파출소명") or item.get("관서명")
        )
        district_name = item.get("district") or item.get("자치구")
        record = (
            db.query(PoliceStation)
            .filter_by(district=district_name, station_name=station_name)
            .first()
        )
        record_data = {
            "district": district_name,
            "station_name": station_name,
            "type": item.get("type") or item.get("구분"),
            "address": item.get("address") or item.get("주소"),
            "lat": item.get("lat") or item.get("위도"),
            "lng": item.get("lng") or item.get("경도"),
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
