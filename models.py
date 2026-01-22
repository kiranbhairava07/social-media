# from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from database import Base

# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String(255), unique=True, nullable=False, index=True)
#     hashed_password = Column(String(255), nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     # Relationships
#     qr_codes = relationship("QRCode", back_populates="creator")

#     def __repr__(self):
#         return f"<User(id={self.id}, email='{self.email}')>"


# class QRCode(Base):
#     __tablename__ = "qr_codes"

#     id = Column(Integer, primary_key=True, index=True)
#     code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "promo-2024"
#     target_url = Column(Text, nullable=False)  # Where the QR redirects
#     created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
#     is_active = Column(Boolean, default=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())

#     # Relationships
#     creator = relationship("User", back_populates="qr_codes")
#     scans = relationship("QRScan", back_populates="qr_code", cascade="all, delete-orphan")

#     def __repr__(self):
#         return f"<QRCode(id={self.id}, code='{self.code}')>"


# class QRScan(Base):
#     __tablename__ = "qr_scans"

#     id = Column(Integer, primary_key=True, index=True)
#     qr_code_id = Column(Integer, ForeignKey("qr_codes.id"), nullable=False)
#     scanned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
#     source = Column(String(50))  # e.g., "mobile", "desktop", "qr"
#     ip_address = Column(String(45))  # IPv4 or IPv6
#     user_agent = Column(Text)  # Browser/device info

#     # Relationships
#     qr_code = relationship("QRCode", back_populates="scans")

#     def __repr__(self):
#         return f"<QRScan(id={self.id}, qr_code_id={self.qr_code_id})>"


from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
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
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "promo-2024"
    target_url = Column(Text, nullable=False)  # Where the QR redirects
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="qr_codes")
    scans = relationship("QRScan", back_populates="qr_code", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QRCode(id={self.id}, code='{self.code}')>"


class QRScan(Base):
    __tablename__ = "qr_scans"

    id = Column(Integer, primary_key=True, index=True)
    qr_code_id = Column(Integer, ForeignKey("qr_codes.id"), nullable=False)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Device info (user-friendly)
    device_type = Column(String(20))  # "Mobile", "Desktop", "Tablet"
    device_name = Column(String(100))  # "iPhone 15", "Samsung Galaxy", "Windows PC"
    browser = Column(String(50))  # "Chrome", "Safari", "Firefox"
    os = Column(String(50))  # "iOS 17", "Android 14", "Windows 11"
    
    # Location info
    ip_address = Column(String(45))
    country = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))
    
    # Raw data (for debugging)
    user_agent = Column(Text)

    # Relationships
    qr_code = relationship("QRCode", back_populates="scans")

    def __repr__(self):
        return f"<QRScan(id={self.id}, qr_code_id={self.qr_code_id})>"