import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    """Primary tracking entity representing an cataloged asset item across target nodes."""
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)  # e.g., "iphone-15-pro"
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)            # e.g., "amazon", "mock-store"
    category = Column(String, nullable=True, default="Electronics")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    """Historical ledger capturing point-in-time pricing telemetry and anomaly tracking metrics."""
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    is_anomaly = Column(Boolean, default=False)
    anomaly_confidence = Column(Float, nullable=True) 

    product = relationship("Product", back_populates="prices")