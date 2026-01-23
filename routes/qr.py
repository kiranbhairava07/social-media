from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract
from typing import List, Optional
from datetime import datetime, timedelta
import qrcode
import io
import logging

from database import get_db
from auth import get_current_user
from models import User, QRCode, QRScan
from schemas import QRCodeCreate, QRCodeUpdate, QRCodeResponse, QRAnalytics, QRScanResponse
from config import settings

router = APIRouter(prefix="/api/qr", tags=["QR Codes"])
logger = logging.getLogger(__name__)

# ============================================
# LIST ALL QR CODES (OPTIMIZED)
# ============================================
@router.get("", response_model=List[QRCodeResponse])
async def list_qr_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all QR codes with scan counts (OPTIMIZED - Single Query).
    Supports pagination for better performance.
    """
    try:
        # OPTIMIZED: Single query with LEFT JOIN and GROUP BY
        result = await db.execute(
            select(
                QRCode,
                func.coalesce(func.count(QRScan.id), 0).label('scan_count')
            )
            .outerjoin(QRScan, QRCode.id == QRScan.qr_code_id)
            .where(QRCode.created_by == current_user.id)
            .group_by(QRCode.id)
            .order_by(QRCode.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        rows = result.all()
        
        response_list = []
        for qr, scan_count in rows:
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
        
        logger.info(f"Listed {len(response_list)} QR codes for user {current_user.id}")
        return response_list
        
    except Exception as e:
        logger.error(f"Error listing QR codes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch QR codes")


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
    try:
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
        
        logger.info(f"Created QR code: {qr_data.code} by user {current_user.id}")
        
        return {
            **new_qr.__dict__,
            "scan_count": 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating QR code: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create QR code")


# ============================================
# GET SINGLE QR CODE (OPTIMIZED)
# ============================================
@router.get("/{qr_id}", response_model=QRCodeResponse)
async def get_qr_code(
    qr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single QR code by ID with scan count (OPTIMIZED).
    """
    try:
        # OPTIMIZED: Single query with scan count
        result = await db.execute(
            select(
                QRCode,
                func.coalesce(func.count(QRScan.id), 0).label('scan_count')
            )
            .outerjoin(QRScan, QRCode.id == QRScan.qr_code_id)
            .where(and_(QRCode.id == qr_id, QRCode.created_by == current_user.id))
            .group_by(QRCode.id)
        )
        
        row = result.one_or_none()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code not found"
            )
        
        qr_code, scan_count = row
        
        return {
            **qr_code.__dict__,
            "scan_count": scan_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching QR code {qr_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch QR code")


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
    try:
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
        
        logger.info(f"Updated QR code {qr_id} by user {current_user.id}")
        
        return {
            **qr_code.__dict__,
            "scan_count": scan_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating QR code {qr_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update QR code")


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
    try:
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
        
        logger.info(f"Deleted QR code {qr_id} by user {current_user.id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting QR code {qr_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete QR code")


# ============================================
# GET QR CODE IMAGE (PNG)
# ============================================
@router.get("/{qr_id}/image")
async def get_qr_image(
    qr_id: int,
    download: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate QR code image (view or download).
    """
    try:
        result = await db.execute(
            select(QRCode).where(
                and_(QRCode.id == qr_id, QRCode.created_by == current_user.id)
            )
        )
        qr_code = result.scalar_one_or_none()

        if not qr_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code not found"
            )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        redirect_url = f"{settings.BASE_URL}/r/{qr_code.code}"
        qr.add_data(redirect_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        headers = {}
        if download:
            headers["Content-Disposition"] = (
                f"attachment; filename=qr-{qr_code.code}.png"
            )

        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR image {qr_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate QR image")


# ============================================
# GET QR CODE ANALYTICS (HEAVILY OPTIMIZED)
# ============================================
@router.get("/{qr_id}/analytics", response_model=QRAnalytics)
async def get_qr_analytics(
    qr_id: int,
    time_range: Optional[str] = Query("30days", regex="^(today|7days|30days|90days|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed analytics for a QR code (HEAVILY OPTIMIZED).
    All stats computed in 3-4 queries instead of 10+.
    """
    try:
        # Verify QR code ownership
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
        
        # OPTIMIZED QUERY 1: All counts in single query
        counts_result = await db.execute(
            select(
                func.count(QRScan.id).label('total_scans'),
                func.sum(case((QRScan.scanned_at >= today_start, 1), else_=0)).label('scans_today'),
                func.sum(case((QRScan.scanned_at >= week_start, 1), else_=0)).label('scans_week'),
                func.sum(case((QRScan.scanned_at >= month_start, 1), else_=0)).label('scans_month'),
            )
            .where(QRScan.qr_code_id == qr_id)
        )
        counts = counts_result.one()
        
        total_scans = counts.total_scans or 0
        scans_today = counts.scans_today or 0
        scans_this_week = counts.scans_week or 0
        scans_this_month = counts.scans_month or 0
        
        # OPTIMIZED QUERY 2: Device breakdown in single query
        device_result = await db.execute(
            select(
                QRScan.device_type,
                func.count(QRScan.id).label('count')
            )
            .where(QRScan.qr_code_id == qr_id)
            .group_by(QRScan.device_type)
        )
        device_counts = {row.device_type: row.count for row in device_result.all()}
        
        mobile_count = device_counts.get("Mobile", 0)
        desktop_count = device_counts.get("Desktop", 0)
        tablet_count = device_counts.get("Tablet", 0)
        
        device_breakdown = {
            "mobile": mobile_count,
            "desktop": desktop_count,
            "tablet": tablet_count
        }
        
        mobile_percentage = round((mobile_count / total_scans * 100) if total_scans > 0 else 0, 1)
        
        # OPTIMIZED QUERY 3: Location data (top cities)
        city_result = await db.execute(
            select(
                QRScan.city,
                QRScan.country,
                func.count(QRScan.id).label('count')
            )
            .where(and_(QRScan.qr_code_id == qr_id, QRScan.city.isnot(None)))
            .group_by(QRScan.city, QRScan.country)
            .order_by(func.count(QRScan.id).desc())
            .limit(5)
        )
        top_cities = [
            {"country": row.country, "city": row.city, "count": row.count}
            for row in city_result.all()
        ]
        
        # Top countries
        country_result = await db.execute(
            select(
                QRScan.country,
                func.count(QRScan.id).label('count')
            )
            .where(and_(QRScan.qr_code_id == qr_id, QRScan.country.isnot(None)))
            .group_by(QRScan.country)
            .order_by(func.count(QRScan.id).desc())
            .limit(5)
        )
        top_countries = [
            {"country": row.country, "city": "", "count": row.count}
            for row in country_result.all()
        ]
        
        # OPTIMIZED QUERY 4: Hourly breakdown
        hourly_result = await db.execute(
            select(
                extract('hour', QRScan.scanned_at).label('hour'),
                func.count(QRScan.id).label('count')
            )
            .where(and_(QRScan.qr_code_id == qr_id, QRScan.scanned_at >= now - timedelta(hours=24)))
            .group_by('hour')
            .order_by('hour')
        )
        hourly_data = {int(row.hour): row.count for row in hourly_result.all()}
        hourly_breakdown = [
            {"hour": i, "count": hourly_data.get(i, 0)}
            for i in range(24)
        ]
        
        peak_hour = max(hourly_data.items(), key=lambda x: x[1])[0] if hourly_data else None
        
        # Recent scans
        recent_result = await db.execute(
            select(QRScan)
            .where(QRScan.qr_code_id == qr_id)
            .order_by(QRScan.scanned_at.desc())
            .limit(10)
        )
        recent_scans = recent_result.scalars().all()
        
        logger.info(f"Generated analytics for QR {qr_id}")
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics for QR {qr_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate analytics")