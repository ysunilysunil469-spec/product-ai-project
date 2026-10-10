from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False, index=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    material = Column(String(160), nullable=False)
    color = Column(String(60), nullable=False)
    fit = Column(String(80), nullable=False)
    style = Column(String(100), nullable=False)
    occasions = Column(String(240), nullable=False)
    description = Column(Text, nullable=False)
    care = Column(String(240), nullable=False)
    manufactured_in = Column(String(100), nullable=True)
    origin_verified = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=4.2, nullable=False)
    review_summary = Column(Text, nullable=False)
    image_emoji = Column(String(12), default="👕", nullable=False)
    accent = Column(String(20), default="#dce9ff", nullable=False)
