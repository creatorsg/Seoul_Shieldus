import _frozen_importlib_external
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# pyrefly: ignore [missing-import]
from database import Base


# 1. 자치구별 치안 안전 지수 테이블
class SeoulSafetyIndex(Base):
    __tablename__ = "seoul_safety_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district = Column(
        String(50), nullable=False, unique=True, comment="자치구 (예: 강남구)"
    )
    population = Column(Integer, comment="인구수")
    area = Column(Float, comment="면적 (km²)")
    crime_count_2024 = Column(Integer, comment="2024년 범죄 발생 건수")
    route_count = Column(Integer, comment="안심길 노선수")
    total_length = Column(Float, comment="안심길 총길이 (km)")
    police_station_count = Column(Integer, comment="지구대 및 파출소 수")
    cctv_count = Column(Integer, comment="CCTV 수량")
    street_light_count = Column(Integer, comment="가로등 개수")

    # 단위당 파생 지표
    crime_rate_per_pop = Column(Float, comment="인구당 범죄율")
    cctv_per_pop = Column(Float, comment="인구당 CCTV")
    police_per_area = Column(Float, comment="면적당 경찰서")
    safe_road_per_area = Column(Float, comment="면적당 안심길")
    street_light_per_area = Column(Float, comment="면적당 가로등")

    # 평가 점수 및 지수
    cctv_score = Column(Float, comment="CCTV 점수")
    police_score = Column(Float, comment="경찰서 점수")
    safe_road_score = Column(Float, comment="안심길 점수")
    street_light_score = Column(Float, comment="가로등 점수")
    crime_safety_score = Column(Float, comment="범죄 안전 점수")
    safety_index = Column(Float, comment="치안 안전 지수")

    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 2. 안심귀갓길 상세 데이터
# 2-1. 자치구별 안심귀갓길 요약 테이블 (Parent)
class SafeRouteDistrict(Base):
    __tablename__ = "safe_route_districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district = Column(
        String(50), nullable=False, unique=True, comment="자치구명 (예: 강남구)"
    )
    route_count = Column(Integer, comment="노선수")
    total_length = Column(Float, comment="총길이 (km)")

    # 1:N 관계 설정 (SafeRoute 테이블과 연결)
    routes = relationship(
        "SafeRoute", back_populates="district_rel", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 2-2. 개별 안심귀갓길 노선 상세 테이블 (Child)
class SafeRoute(Base):
    __tablename__ = "safe_routes"

    # route_id("1168010100_01")를 기본키(PK)로 바로 사용
    route_id = Column(String(50), primary_key=True, comment="노선 고유 ID")

    # 외래키(FK): 자치구 요약 테이블의 district(자치구명)와 연결
    district_name = Column(
        String(50), ForeignKey("safe_route_districts.district"), nullable=False
    )

    route_name = Column(String(100), comment="노선명 (예: 강남안심01)")
    dong = Column(String(50), comment="법정동 (예: 역삼동)")
    link_length = Column(Float, comment="구간 길이 (m)")
    location_desc = Column(String(255), comment="위치 설명 (예: 강남대로106길)")

    # facilities (방범 시설물 수량 컬럼들)
    security_bell = Column(Integer, default=0, comment="비상벨 수")
    cctv = Column(Integer, default=0, comment="CCTV 수")
    security_light = Column(Integer, default=0, comment="보안등 수")
    signage = Column(Integer, default=0, comment="안내판 수")
    road_marking = Column(Integer, default=0, comment="노면 표시 수")
    police_report_board = Column(Integer, default=0, comment="112 신고 표지판 수")

    # Parent 관계 역참조
    district_rel = relationship("SafeRouteDistrict", back_populates="routes")

    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 3. 가로등 위치 데이터
class StreetLight(Base):
    __tablename__ = "street_lights"

    # management_id("가락지하차도-01")를 기본키(PK)로 사용
    management_id = Column(String(100), primary_key=True, comment="가로등 관리 번호")
    lat = Column(Float, nullable=False, comment="위도 (Latitude)")
    lng = Column(Float, nullable=False, comment="경도 (Longitude)")

    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 4.  CCTV 상세 통계 데이터
class DistrictCctvStat(Base):
    __tablename__ = "district_cctv_stats"

    # 자치구명을 기본키(PK)로 사용
    district = Column(String(50), primary_key=True, comment="자치구명 (예: 종로구)")
    total_cctv = Column(Integer, default=0, comment="총 CCTV 수량")
    crime_prevention_total = Column(Integer, default=0, comment="범죄예방 총 수량")

    # purpose (목적별 세부 수량 컬럼들)
    purpose_crime = Column(Integer, default=0, comment="생활안전/범죄예방용 수량")
    purpose_child_protection = Column(
        Integer, default=0, comment="어린이 보호 구역용 수량"
    )
    purpose_park_playground = Column(Integer, default=0, comment="공원/놀이터용 수량")
    purpose_illegal_dumping = Column(
        Integer, default=0, comment="쓰레기 무단투기 단속용 수량"
    )
    purpose_fire_safety = Column(Integer, default=0, comment="화재 감시용 수량")
    purpose_traffic_crackdown = Column(Integer, default=0, comment="교통 단속용 수량")
    purpose_traffic_info = Column(Integer, default=0, comment="교통 정보 수집용 수량")
    purpose_others = Column(Integer, default=0, comment="기타 용도 수량")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 5. 지구대 및 파출소 위치 데이터
class PoliceStation(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district = Column(String(50), nullable=False, index=True)
    station_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    address = Column(String(255), nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
