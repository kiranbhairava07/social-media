from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    qr_codes = relationship("QRCode", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class QRCode(Base):
    __tablename__ = "qr_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    target_url = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="qr_codes")
    scans = relationship("QRScan", back_populates="qr_code", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_created_by_active', 'created_by', 'is_active'),
        Index('idx_created_by_created_at', 'created_by', 'created_at'),
    )

    def __repr__(self):
        return f"<QRCode(id={self.id}, code='{self.code}')>"


class QRScan(Base):
    __tablename__ = "qr_scans"

    id = Column(Integer, primary_key=True, index=True)
    qr_code_id = Column(Integer, ForeignKey("qr_codes.id"), nullable=False, index=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Device info (user-friendly)
    device_type = Column(String(20), index=True)  # "Mobile", "Desktop", "Tablet"
    device_name = Column(String(100))
    browser = Column(String(50), index=True)
    os = Column(String(50))
    
    # Location info
    ip_address = Column(String(45))
    country = Column(String(100), index=True)
    city = Column(String(100), index=True)
    region = Column(String(100))
    
    # Raw data (for debugging)
    user_agent = Column(Text)

    # Relationships
    qr_code = relationship("QRCode", back_populates="scans")

    # OPTIMIZED: Composite indexes for common query patterns
    __table_args__ = (
        # For analytics queries grouped by QR code and time
        Index('idx_qr_scanned', 'qr_code_id', 'scanned_at'),
        
        # For device analytics
        Index('idx_qr_device', 'qr_code_id', 'device_type'),
        
        # For location analytics
        Index('idx_qr_location', 'qr_code_id', 'country', 'city'),
        
        # For time-based filtering
        Index('idx_scanned_at_qr', 'scanned_at', 'qr_code_id'),
        
        # For hourly breakdown queries
        Index('idx_qr_hour', 'qr_code_id', func.extract('hour', 'scanned_at')),
    )

    def __repr__(self):
        return f"<QRScan(id={self.id}, qr_code_id={self.qr_code_id})>"