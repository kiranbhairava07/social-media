from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from database import get_db
from models import QRCode, QRScan
from utils import parse_device_info, get_location_from_ip
from config import settings

router = APIRouter(tags=["Public"])
logger = logging.getLogger(__name__)

# OPTIMIZED: Background task for location lookup
async def update_location_async(scan_id: int, ip_address: str, db_session: AsyncSession):
    """
    Update scan location data in background.
    This prevents blocking the redirect response.
    """
    try:
        location_data = await get_location_from_ip(ip_address)
        
        if location_data:
            async with db_session.begin():
                scan = await db_session.get(QRScan, scan_id)
                if scan:
                    scan.country = location_data.get("country")
                    scan.city = location_data.get("city")
                    scan.region = location_data.get("region")
                    await db_session.commit()
                    logger.info(f"Updated location for scan {scan_id}")
    except Exception as e:
        logger.error(f"Failed to update location for scan {scan_id}: {str(e)}")


# ============================================
# PUBLIC QR CODE REDIRECT (OPTIMIZED)
# ============================================
@router.get("/r/{code}")
async def redirect_qr(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint that redirects to the target URL and logs the scan.
    OPTIMIZED: Location lookup happens in background to not block redirect.
    
    Example: https://yourdomain.com/r/demo-2024
    """
    try:
        # OPTIMIZED: Single query with specific columns only
        result = await db.execute(
            select(QRCode.id, QRCode.target_url, QRCode.is_active, QRCode.code)
            .where(QRCode.code == code)
        )
        qr_data = result.one_or_none()
        
        if not qr_data:
            logger.warning(f"QR code not found: {code}")
            raise HTTPException(
                status_code=404,
                detail=f"QR code '{code}' not found"
            )
        
        qr_id, target_url, is_active, qr_code = qr_data
        
        if not is_active:
            logger.warning(f"Inactive QR code accessed: {code}")
            raise HTTPException(
                status_code=410,
                detail="This QR code has been deactivated"
            )
        
        # Get user agent and IP
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else None
        
        # Parse device info (fast, synchronous)
        device_info = parse_device_info(user_agent)
        
        # OPTIMIZED: Log scan WITHOUT location data first (fast)
        scan = QRScan(
            qr_code_id=qr_id,
            device_type=device_info["device_type"],
            device_name=device_info["device_name"],
            browser=device_info["browser"],
            os=device_info["os"],
            ip_address=ip_address,
            # Location will be filled by background task
            country=None,
            city=None,
            region=None,
            user_agent=user_agent
        )
        
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        
        logger.info(f"QR scan recorded: code={code}, device={device_info['device_type']}, ip={ip_address}")
        
        # OPTIMIZED: Update location in background (doesn't block redirect)
        if settings.LOCATION_LOOKUP_ASYNC and ip_address:
            background_tasks.add_task(update_location_async, scan.id, ip_address, db)
        else:
            # If background tasks disabled, do it synchronously
            location_data = await get_location_from_ip(ip_address)
            if location_data:
                scan.country = location_data["country"]
                scan.city = location_data["city"]
                scan.region = location_data["region"]
                await db.commit()
        
        # Redirect to target URL immediately
        return RedirectResponse(url=target_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in redirect_qr for code {code}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )