from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pathlib import Path
import logging

from database import get_db
from models import SocialClick
from utils import parse_device_info, get_location_from_ip

router = APIRouter(tags=["Social Links"])
logger = logging.getLogger(__name__)

# Path to templates directory
TEMPLATES_DIR = Path("templates/social")

@router.get("/social-links", response_class=HTMLResponse)
async def social_links_page(request: Request):
    """
    Serve the social media links page.
    This page can be used as a target URL for QR code campaigns.
    
    Example QR code setup:
    - Code: social-2024
    - Target URL: https://social-media-vmfr.onrender.com/social-links
    """
    try:
        html_path = TEMPLATES_DIR / "index.html"
        
        if not html_path.exists():
            return HTMLResponse(
                content="<h1>Social Links page not found</h1>",
                status_code=404
            )
        
        # Read and serve the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error loading social links page: {str(e)}", exc_info=True)
        return HTMLResponse(
            content=f"<h1>Error loading page: {str(e)}</h1>",
            status_code=500
        )


@router.post("/api/social-click")
async def log_social_click(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Track clicks on social media platform buttons.
    Called from JavaScript when user clicks a social media link.
    """
    try:
        data = await request.json()
        platform = data.get("platform", "unknown")
        user_agent = request.headers.get("user-agent", "")
        
        # Get IP address
        ip_address = request.client.host if request.client else None
        
        # Parse device info
        device_info = parse_device_info(user_agent)
        
        # Get location from IP
        location_data = await get_location_from_ip(ip_address)
        
        # Create click record
        click = SocialClick(
            platform=platform,
            device_type=device_info["device_type"],
            browser=device_info["browser"],
            os=device_info["os"],
            ip_address=ip_address,
            country=location_data.get("country") if location_data else None,
            city=location_data.get("city") if location_data else None,
            user_agent=user_agent
        )
        
        db.add(click)
        await db.commit()
        
        logger.info(f"Social click logged: {platform} from {ip_address}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error logging social click: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get("/api/social-analytics")
async def get_social_analytics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for social media platform clicks.
    Returns total clicks per platform.
    """
    try:
        # Get total clicks per platform
        result = await db.execute(
            select(
                SocialClick.platform,
                func.count(SocialClick.id).label('count')
            )
            .group_by(SocialClick.platform)
            .order_by(func.count(SocialClick.id).desc())
        )
        
        platform_stats = [
            {"platform": row.platform, "count": row.count}
            for row in result.all()
        ]
        
        # Get total clicks
        total_result = await db.execute(
            select(func.count(SocialClick.id))
        )
        total_clicks = total_result.scalar()
        
        return {
            "total_clicks": total_clicks,
            "platforms": platform_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting social analytics: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get analytics"}
        )


@router.get("/social-links/styles.css")
async def social_links_css():
    """Serve the CSS file for social links page"""
    try:
        css_path = TEMPLATES_DIR / "styles.css"
        
        if not css_path.exists():
            return HTMLResponse(content="", status_code=404)
        
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        return HTMLResponse(
            content=css_content,
            media_type="text/css"
        )
    except Exception as e:
        logger.error(f"Error loading CSS: {str(e)}", exc_info=True)
        return HTMLResponse(content="", status_code=500)


@router.get("/social-links/{image_name}")
async def social_links_images(image_name: str):
    """Serve images for social links page"""
    from fastapi.responses import FileResponse
    
    try:
        # Security: only allow specific image files
        allowed_images = [
            'gk.png', 'facebook.png', 'instagram.png', 
            'youtube.png', 'threads.png', 'twitter.png', 'whatsapp.png'
        ]
        
        if image_name not in allowed_images:
            return HTMLResponse(content="Not found", status_code=404)
        
        image_path = TEMPLATES_DIR / image_name
        
        if not image_path.exists():
            return HTMLResponse(content="Image not found", status_code=404)
        
        # Determine content type
        if image_name.endswith('.png'):
            media_type = "image/png"
        elif image_name.endswith('.jpg') or image_name.endswith('.jpeg'):
            media_type = "image/jpeg"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=image_path,
            media_type=media_type
        )
    except Exception as e:
        logger.error(f"Error loading image: {str(e)}", exc_info=True)
        return HTMLResponse(content="Error", status_code=500)