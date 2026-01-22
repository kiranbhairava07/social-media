from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import QRCode, QRScan

router = APIRouter(tags=["Public"])

# ============================================
# PUBLIC QR CODE REDIRECT
# ============================================
@router.get("/r/{code}")
async def redirect_qr(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint that redirects to the target URL and logs the scan.
    This is what the QR code actually points to.
    
    Example: https://yourdomain.com/r/demo-2024
    """
    # Get QR code by code
    result = await db.execute(
        select(QRCode).where(QRCode.code == code)
    )
    qr_code = result.scalar_one_or_none()
    
    if not qr_code:
        raise HTTPException(
            status_code=404,
            detail=f"QR code '{code}' not found"
        )
    
    if not qr_code.is_active:
        raise HTTPException(
            status_code=410,
            detail="This QR code has been deactivated"
        )
    
    # Log the scan
    scan = QRScan(
        qr_code_id=qr_code.id,
        source=request.query_params.get("source", "unknown"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    db.add(scan)
    await db.commit()
    
    # Redirect to target URL
    return RedirectResponse(url=qr_code.target_url, status_code=302)