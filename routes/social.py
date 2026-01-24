from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter(tags=["Social Links"])

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
        return HTMLResponse(
            content=f"<h1>Error loading page: {str(e)}</h1>",
            status_code=500
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
        return HTMLResponse(content="Error", status_code=500)