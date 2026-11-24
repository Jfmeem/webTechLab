from sqlalchemy import Column, ForeignKey, Integer, Numeric, String

from database import Base


class ServiceListing(Base):
    __tablename__ = "service_listings"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    delivery_days = Column(Integer, nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hash_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="customer")
