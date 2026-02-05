from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from database import get_db
from models import QRCode, QRScan
from utils import parse_device_info, get_location_from_ip, get_location_from_gps
from config import settings

router = APIRouter(tags=["Public"])
logger = logging.getLogger(__name__)


# ============================================
# PUBLIC QR CODE REDIRECT (WITH GPS)
# ============================================
@router.get("/r/{code}")
async def redirect_qr(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Instantly redirect to target URL and log scan in background.
    No GPS, no permission UI.
    """
    try:
        result = await db.execute(
            select(QRCode.id, QRCode.target_url, QRCode.is_active)
            .where(QRCode.code == code)
        )
        qr_data = result.one_or_none()
        
        if not qr_data:
            raise HTTPException(status_code=404, detail=f"QR code '{code}' not found")
        
        qr_id, target_url, is_active = qr_data
        
        if not is_active:
            raise HTTPException(status_code=410, detail="This QR code has been deactivated")

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url={target_url}">
    <script>
        // Fire-and-forget logging
        fetch("{settings.BASE_URL}/api/scan-log", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
                qr_code_id: {qr_id},
                user_agent: navigator.userAgent
            }})
        }}).catch(() => {{}});

        // Fallback redirect if meta refresh fails
        window.location.href = "{target_url}";
    </script>
</head>
<body>
    Redirecting...
</body>
</html>
"""
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in redirect_qr: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



# ============================================
# LOG SCAN WITH GPS DATA
# ============================================
@router.post("/api/scan-log")
async def log_scan(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Log QR scan with GPS coordinates.
    """
    try:
        data = await request.json()
        qr_code_id = data.get("qr_code_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        user_agent = data.get("user_agent", "")
        
        # Get IP from request
        ip_address = request.client.host if request.client else None
        
        # Parse device info
        device_info = parse_device_info(user_agent)
        
        # Get location - GPS if available, else IP
        location_data = None
        if latitude and longitude:
            logger.info(f"Using GPS: lat={latitude}, lon={longitude}, accuracy={accuracy}m")
            location_data = await get_location_from_gps(latitude, longitude)
            logger.info(f"GPS location result: {location_data}")
        else:
            logger.info(f"GPS not available, using IP: {ip_address}")
            location_data = await get_location_from_ip(ip_address)
            logger.info(f"IP location result: {location_data}")
        
        # Create scan record
        scan = QRScan(
            qr_code_id=qr_code_id,
            device_type=device_info["device_type"],
            device_name=device_info["device_name"],
            browser=device_info["browser"],
            os=device_info["os"],
            ip_address=ip_address,
            country=location_data.get("country") if location_data else None,
            city=location_data.get("city") if location_data else None,
            region=location_data.get("region") if location_data else None,
            user_agent=user_agent
        )
        
        db.add(scan)
        await db.commit()
        
        logger.info(f"Scan logged: QR {qr_code_id}, Location: {scan.city}, {scan.country}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error logging scan: {str(e)}", exc_info=True)
        return {"status": "error"}