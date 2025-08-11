from sqlalchemy import Column, Integer, String
from database import Base
import jdatetime, datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    name = Column(String(50), unique=False, index=True)
    family = Column(String(50), unique=False, index=True)
    email = Column(String(100), unique=True, index=True)
    role = Column(String(50), default="Advisor",)
    hashed_password = Column(String(100))
    status = Column(String(50), default="active",)
    phone = Column(String(13), unique=False)

class Owner(Base):
    __tablename__ = "owner"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=False, nullable=False)
    Family = Column(String(50), unique=False, nullable=False)
    phone = Column(String(15), unique=False, nullable=False)
    DISC_test = Column(String(2), unique=False, nullable=True)

class Property(Base):
    __tablename__ = "Property"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), unique=False, nullable=False)
    size = Column(Integer, unique=False, nullable=False)
    price = Column(Integer, unique=False, nullable=False)
    pricePerMeter = Column(Integer, unique=False, nullable=False)
    bedrooms = Column(Integer, unique=False, nullable=True)
    width = Column(Integer, unique=False, nullable=False)
    length = Column(Integer, unique=False, nullable=False)
    floorNumber = Column(Integer, unique=False, nullable=False)
    facade_status = Column(String(50), unique=False, nullable=False)
    builtYear = Column(Integer, unique=False, nullable=False)
    locationOnMap = Column(String(100), unique=False, nullable=False)
    detailed_address = Column(String(500), unique=False, nullable=False)
    neighborhood = Column(String(50), unique=False, nullable=False)
    description = Column(String(500), unique=False, nullable=True)
    amenities = Column(String(500), unique=False, nullable=True)
    units_in_building = Column(Integer, unique=False, nullable=True)
    property_type = Column(String(50), unique=False, nullable=False)
    latitude = Column(String(50), unique=False, nullable=False)
    longitude = Column(String(50), unique=False, nullable=False)

    status = Column(String(10), unique=False, nullable=False, default="active")
    RegisterDatePersian = Column(String(200), unique=False, nullable=False, default=str(jdatetime.datetime.today()))
    today = str(datetime.datetime.today().date())
    RegisterDateNational = Column(String(200), unique=False, nullable=False, default=str(today))
    adviosor_id = Column(Integer, unique=False, nullable=True, default=0)
    owner_id = Column(Integer, unique=False, nullable=True)

class deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String(50), unique=False, nullable=False)
    user_id = Column(Integer, unique=False, nullable=False)

