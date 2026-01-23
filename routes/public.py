from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from database import get_db
from models import QRCode, QRScan
from utils import parse_device_info, get_location_from_gps
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
    Show GPS permission page, then redirect to target URL.
    """
    try:
        result = await db.execute(
            select(QRCode.id, QRCode.target_url, QRCode.is_active, QRCode.code)
            .where(QRCode.code == code)
        )
        qr_data = result.one_or_none()
        
        if not qr_data:
            raise HTTPException(status_code=404, detail=f"QR code '{code}' not found")
        
        qr_id, target_url, is_active, qr_code = qr_data
        
        if not is_active:
            raise HTTPException(status_code=410, detail="This QR code has been deactivated")
        
        # Return GPS permission page
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .icon {{ font-size: 48px; margin-bottom: 16px; }}
        h1 {{ color: #1a202c; margin-bottom: 8px; font-size: 20px; }}
        p {{ color: #718096; font-size: 14px; margin-bottom: 20px; }}
        .spinner {{
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📍</div>
        <h1>Redirecting...</h1>
        <p id="status">Detecting your location...</p>
        <div class="spinner"></div>
    </div>
    
    <script>
        const QR_ID = {qr_id};
        const TARGET_URL = "{target_url}";
        const API = "{settings.BASE_URL}";
        
        async function logScan(lat, lon, accuracy) {{
            const userAgent = navigator.userAgent;
            
            try {{
                await fetch(`${{API}}/api/scan-log`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        qr_code_id: QR_ID,
                        latitude: lat,
                        longitude: lon,
                        accuracy: accuracy,
                        user_agent: userAgent
                    }})
                }});
            }} catch (e) {{
                console.log('Log failed:', e);
            }}
            
            // Redirect to target
            window.location.href = TARGET_URL;
        }}
        
        // Try GPS first
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    // GPS success - use coordinates
                    logScan(
                        position.coords.latitude,
                        position.coords.longitude,
                        position.coords.accuracy
                    );
                }},
                (error) => {{
                    // GPS denied/failed - use IP fallback
                    document.getElementById('status').textContent = 'Redirecting...';
                    logScan(null, null, null);
                }},
                {{ timeout: 5000 }}
            );
        }} else {{
            // No GPS support - redirect immediately
            logScan(null, null, null);
        }}
    </script>
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
            location_data = await get_location_from_gps(latitude, longitude)
            logger.info(f"GPS location: {location_data}")
        else:
            location_data = await get_location_from_gps(ip_address)
            logger.info(f"IP location: {location_data}")
        
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