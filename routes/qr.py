# from fastapi import APIRouter, Depends, HTTPException, status, Response
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func, and_
# from typing import List
# from datetime import datetime, timedelta
# import qrcode
# import io

# from database import get_db
# from auth import get_current_user
# from models import User, QRCode, QRScan
# from schemas import QRCodeCreate, QRCodeUpdate, QRCodeResponse, QRAnalytics, QRScanResponse
# from config import settings

# router = APIRouter(prefix="/api/qr", tags=["QR Codes"])

# # ============================================
# # LIST ALL QR CODES
# # ============================================
# @router.get("", response_model=List[QRCodeResponse])
# async def list_qr_codes(
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get all QR codes with scan counts.
#     """
#     # Get all QR codes for current user
#     result = await db.execute(
#         select(QRCode).where(QRCode.created_by == current_user.id).order_by(QRCode.created_at.desc())
#     )
#     qr_codes = result.scalars().all()
    
#     # Get scan counts for each QR code
#     response_list = []
#     for qr in qr_codes:
#         scan_count_result = await db.execute(
#             select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr.id)
#         )
#         scan_count = scan_count_result.scalar()
        
#         qr_dict = {
#             "id": qr.id,
#             "code": qr.code,
#             "target_url": qr.target_url,
#             "is_active": qr.is_active,
#             "created_at": qr.created_at,
#             "updated_at": qr.updated_at,
#             "created_by": qr.created_by,
#             "scan_count": scan_count
#         }
#         response_list.append(qr_dict)
    
#     return response_list


# # ============================================
# # CREATE QR CODE
# # ============================================
# @router.post("", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
# async def create_qr_code(
#     qr_data: QRCodeCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Create a new QR code.
#     """
#     # Check if code already exists
#     result = await db.execute(
#         select(QRCode).where(QRCode.code == qr_data.code)
#     )
#     existing_qr = result.scalar_one_or_none()
    
#     if existing_qr:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"QR code with code '{qr_data.code}' already exists"
#         )
    
#     # Create new QR code
#     new_qr = QRCode(
#         code=qr_data.code,
#         target_url=qr_data.target_url,
#         created_by=current_user.id,
#         is_active=True
#     )
    
#     db.add(new_qr)
#     await db.commit()
#     await db.refresh(new_qr)
    
#     return {
#         **new_qr.__dict__,
#         "scan_count": 0
#     }


# # ============================================
# # GET SINGLE QR CODE
# # ============================================
# @router.get("/{qr_id}", response_model=QRCodeResponse)
# async def get_qr_code(
#     qr_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get a single QR code by ID.
#     """
#     result = await db.execute(
#         select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
#     )
#     qr_code = result.scalar_one_or_none()
    
#     if not qr_code:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="QR code not found"
#         )
    
#     # Get scan count
#     scan_count_result = await db.execute(
#         select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_code.id)
#     )
#     scan_count = scan_count_result.scalar()
    
#     return {
#         **qr_code.__dict__,
#         "scan_count": scan_count
#     }


# # ============================================
# # UPDATE QR CODE
# # ============================================
# @router.put("/{qr_id}", response_model=QRCodeResponse)
# async def update_qr_code(
#     qr_id: int,
#     qr_update: QRCodeUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update a QR code's target URL or active status.
#     """
#     result = await db.execute(
#         select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
#     )
#     qr_code = result.scalar_one_or_none()
    
#     if not qr_code:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="QR code not found"
#         )
    
#     # Update fields
#     if qr_update.target_url is not None:
#         qr_code.target_url = qr_update.target_url
    
#     if qr_update.is_active is not None:
#         qr_code.is_active = qr_update.is_active
    
#     qr_code.updated_at = datetime.utcnow()
    
#     await db.commit()
#     await db.refresh(qr_code)
    
#     # Get scan count
#     scan_count_result = await db.execute(
#         select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_code.id)
#     )
#     scan_count = scan_count_result.scalar()
    
#     return {
#         **qr_code.__dict__,
#         "scan_count": scan_count
#     }


# # ============================================
# # DELETE QR CODE
# # ============================================
# @router.delete("/{qr_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_qr_code(
#     qr_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Delete a QR code (also deletes all associated scans due to cascade).
#     """
#     result = await db.execute(
#         select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
#     )
#     qr_code = result.scalar_one_or_none()
    
#     if not qr_code:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="QR code not found"
#         )
    
#     await db.delete(qr_code)
#     await db.commit()
    
#     return None


# # ============================================
# # GET QR CODE IMAGE (PNG)
# # ============================================
# @router.get("/{qr_id}/image")
# async def get_qr_image(
#     qr_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Generate and download QR code image as PNG.
#     """
#     result = await db.execute(
#         select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
#     )
#     qr_code = result.scalar_one_or_none()
    
#     if not qr_code:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="QR code not found"
#         )
    
#     # Generate QR code image
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
    
#     # QR points to the redirect URL
#     redirect_url = f"{settings.BASE_URL}/r/{qr_code.code}"
#     qr.add_data(redirect_url)
#     qr.make(fit=True)
    
#     img = qr.make_image(fill_color="black", back_color="white")
    
#     # Save to buffer
#     buffer = io.BytesIO()
#     img.save(buffer, format="PNG")
#     buffer.seek(0)
    
#     return Response(
#         content=buffer.getvalue(),
#         media_type="image/png",
#         headers={
#             "Content-Disposition": f"attachment; filename=qr-{qr_code.code}.png"
#         }
#     )


# # ============================================
# # GET QR CODE ANALYTICS
# # ============================================
# @router.get("/{qr_id}/analytics", response_model=QRAnalytics)
# async def get_qr_analytics(
#     qr_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get detailed analytics for a QR code.
#     """
#     result = await db.execute(
#         select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
#     )
#     qr_code = result.scalar_one_or_none()
    
#     if not qr_code:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="QR code not found"
#         )
    
#     now = datetime.utcnow()
#     today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
#     week_start = now - timedelta(days=7)
#     month_start = now - timedelta(days=30)
    
#     # Total scans
#     total_result = await db.execute(
#         select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_id)
#     )
#     total_scans = total_result.scalar()
    
#     # Scans today
#     today_result = await db.execute(
#         select(func.count(QRScan.id)).where(
#             and_(
#                 QRScan.qr_code_id == qr_id,
#                 QRScan.scanned_at >= today_start
#             )
#         )
#     )
#     scans_today = today_result.scalar()
    
#     # Scans this week
#     week_result = await db.execute(
#         select(func.count(QRScan.id)).where(
#             and_(
#                 QRScan.qr_code_id == qr_id,
#                 QRScan.scanned_at >= week_start
#             )
#         )
#     )
#     scans_this_week = week_result.scalar()
    
#     # Scans this month
#     month_result = await db.execute(
#         select(func.count(QRScan.id)).where(
#             and_(
#                 QRScan.qr_code_id == qr_id,
#                 QRScan.scanned_at >= month_start
#             )
#         )
#     )
#     scans_this_month = month_result.scalar()
    
#     # Recent scans (last 10)
#     recent_result = await db.execute(
#         select(QRScan)
#         .where(QRScan.qr_code_id == qr_id)
#         .order_by(QRScan.scanned_at.desc())
#         .limit(10)
#     )
#     recent_scans = recent_result.scalars().all()
    
#     return {
#         "qr_code_id": qr_id,
#         "total_scans": total_scans,
#         "scans_today": scans_today,
#         "scans_this_week": scans_this_week,
#         "scans_this_month": scans_this_month,
#         "recent_scans": recent_scans
#     }

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta
import qrcode
import io

from database import get_db
from auth import get_current_user
from models import User, QRCode, QRScan
from schemas import QRCodeCreate, QRCodeUpdate, QRCodeResponse, QRAnalytics, QRScanResponse
from config import settings

router = APIRouter(prefix="/api/qr", tags=["QR Codes"])

# ============================================
# LIST ALL QR CODES
# ============================================
@router.get("", response_model=List[QRCodeResponse])
async def list_qr_codes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all QR codes with scan counts.
    """
    # Get all QR codes for current user
    result = await db.execute(
        select(QRCode).where(QRCode.created_by == current_user.id).order_by(QRCode.created_at.desc())
    )
    qr_codes = result.scalars().all()
    
    # Get scan counts for each QR code
    response_list = []
    for qr in qr_codes:
        scan_count_result = await db.execute(
            select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr.id)
        )
        scan_count = scan_count_result.scalar()
        
        qr_dict = {
            "id": qr.id,
            "code": qr.code,
            "target_url": qr.target_url,
            "is_active": qr.is_active,
            "created_at": qr.created_at,
            "updated_at": qr.updated_at,
            "created_by": qr.created_by,
            "scan_count": scan_count
        }
        response_list.append(qr_dict)
    
    return response_list


# ============================================
# CREATE QR CODE
# ============================================
@router.post("", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_qr_code(
    qr_data: QRCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new QR code.
    """
    # Check if code already exists
    result = await db.execute(
        select(QRCode).where(QRCode.code == qr_data.code)
    )
    existing_qr = result.scalar_one_or_none()
    
    if existing_qr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QR code with code '{qr_data.code}' already exists"
        )
    
    # Create new QR code
    new_qr = QRCode(
        code=qr_data.code,
        target_url=qr_data.target_url,
        created_by=current_user.id,
        is_active=True
    )
    
    db.add(new_qr)
    await db.commit()
    await db.refresh(new_qr)
    
    return {
        **new_qr.__dict__,
        "scan_count": 0
    }


# ============================================
# GET SINGLE QR CODE
# ============================================
@router.get("/{qr_id}", response_model=QRCodeResponse)
async def get_qr_code(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single QR code by ID.
    """
    result = await db.execute(
        select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    # Get scan count
    scan_count_result = await db.execute(
        select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_code.id)
    )
    scan_count = scan_count_result.scalar()
    
    return {
        **qr_code.__dict__,
        "scan_count": scan_count
    }


# ============================================
# UPDATE QR CODE
# ============================================
@router.put("/{qr_id}", response_model=QRCodeResponse)
async def update_qr_code(
    qr_id: int,
    qr_update: QRCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a QR code's target URL or active status.
    """
    result = await db.execute(
        select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    # Update fields
    if qr_update.target_url is not None:
        qr_code.target_url = qr_update.target_url
    
    if qr_update.is_active is not None:
        qr_code.is_active = qr_update.is_active
    
    qr_code.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(qr_code)
    
    # Get scan count
    scan_count_result = await db.execute(
        select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_code.id)
    )
    scan_count = scan_count_result.scalar()
    
    return {
        **qr_code.__dict__,
        "scan_count": scan_count
    }


# ============================================
# DELETE QR CODE
# ============================================
@router.delete("/{qr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qr_code(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a QR code (also deletes all associated scans due to cascade).
    """
    result = await db.execute(
        select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    await db.delete(qr_code)
    await db.commit()
    
    return None


# ============================================
# GET QR CODE IMAGE (PNG)
# ============================================
@router.get("/{qr_id}/image")
async def get_qr_image(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and download QR code image as PNG.
    """
    result = await db.execute(
        select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # QR points to the redirect URL
    redirect_url = f"{settings.BASE_URL}/r/{qr_code.code}"
    qr.add_data(redirect_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=qr-{qr_code.code}.png"
        }
    )


# ============================================
# GET QR CODE ANALYTICS
# ============================================
@router.get("/{qr_id}/analytics", response_model=QRAnalytics)
async def get_qr_analytics(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed analytics for a QR code with device breakdown, location data, and time analysis.
    """
    result = await db.execute(
        select(QRCode).where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # === BASIC COUNTS ===
    # Total scans
    total_result = await db.execute(
        select(func.count(QRScan.id)).where(QRScan.qr_code_id == qr_id)
    )
    total_scans = total_result.scalar() or 0
    
    # Scans today
    today_result = await db.execute(
        select(func.count(QRScan.id)).where(
            and_(QRScan.qr_code_id == qr_id, QRScan.scanned_at >= today_start)
        )
    )
    scans_today = today_result.scalar() or 0
    
    # Scans this week
    week_result = await db.execute(
        select(func.count(QRScan.id)).where(
            and_(QRScan.qr_code_id == qr_id, QRScan.scanned_at >= week_start)
        )
    )
    scans_this_week = week_result.scalar() or 0
    
    # Scans this month
    month_result = await db.execute(
        select(func.count(QRScan.id)).where(
            and_(QRScan.qr_code_id == qr_id, QRScan.scanned_at >= month_start)
        )
    )
    scans_this_month = month_result.scalar() or 0
    
    # === DEVICE BREAKDOWN ===
    device_result = await db.execute(
        select(QRScan.device_type, func.count(QRScan.id))
        .where(QRScan.qr_code_id == qr_id)
        .group_by(QRScan.device_type)
    )
    device_counts = dict(device_result.all())
    
    mobile_count = device_counts.get("Mobile", 0)
    desktop_count = device_counts.get("Desktop", 0)
    tablet_count = device_counts.get("Tablet", 0)
    
    device_breakdown = {
        "mobile": mobile_count,
        "desktop": desktop_count,
        "tablet": tablet_count
    }
    
    mobile_percentage = round((mobile_count / total_scans * 100) if total_scans > 0 else 0, 1)
    
    # === LOCATION DATA ===
    # Top countries
    country_result = await db.execute(
        select(QRScan.country, func.count(QRScan.id))
        .where(and_(QRScan.qr_code_id == qr_id, QRScan.country.isnot(None)))
        .group_by(QRScan.country)
        .order_by(func.count(QRScan.id).desc())
        .limit(5)
    )
    top_countries = [
        {"country": country, "city": "", "count": count}
        for country, count in country_result.all()
    ]
    
    # Top cities
    city_result = await db.execute(
        select(QRScan.city, QRScan.country, func.count(QRScan.id))
        .where(and_(QRScan.qr_code_id == qr_id, QRScan.city.isnot(None)))
        .group_by(QRScan.city, QRScan.country)
        .order_by(func.count(QRScan.id).desc())
        .limit(5)
    )
    top_cities = [
        {"country": country, "city": city, "count": count}
        for city, country, count in city_result.all()
    ]
    
    # === TIME ANALYSIS ===
    # Hourly breakdown (last 24 hours)
    hourly_result = await db.execute(
        select(
            func.extract('hour', QRScan.scanned_at).label('hour'),
            func.count(QRScan.id)
        )
        .where(and_(QRScan.qr_code_id == qr_id, QRScan.scanned_at >= now - timedelta(hours=24)))
        .group_by('hour')
        .order_by('hour')
    )
    hourly_data = {int(hour): count for hour, count in hourly_result.all()}
    hourly_breakdown = [
        {"hour": i, "count": hourly_data.get(i, 0)}
        for i in range(24)
    ]
    
    # Peak hour
    peak_hour = max(hourly_data.items(), key=lambda x: x[1])[0] if hourly_data else None
    
    # === RECENT SCANS ===
    recent_result = await db.execute(
        select(QRScan)
        .where(QRScan.qr_code_id == qr_id)
        .order_by(QRScan.scanned_at.desc())
        .limit(10)
    )
    recent_scans = recent_result.scalars().all()
    
    return {
        "qr_code_id": qr_id,
        "total_scans": total_scans,
        "scans_today": scans_today,
        "scans_this_week": scans_this_week,
        "scans_this_month": scans_this_month,
        "device_breakdown": device_breakdown,
        "mobile_percentage": mobile_percentage,
        "top_countries": top_countries,
        "top_cities": top_cities,
        "peak_hour": peak_hour,
        "hourly_breakdown": hourly_breakdown,
        "recent_scans": recent_scans
    }