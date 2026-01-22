# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse, RedirectResponse, Response
# import qrcode
# import io

# app = FastAPI(title="QR Redirect Service")

# # =========================================================
# # CONFIG
# # =========================================================
# TARGET_URL = "https://digital-links.vercel.app"
# BASE_URL = "https://social-media-vmfr.onrender.com"  # replace with domain/ngrok in real use

# # simple in-memory counter (DB later)
# SCAN_COUNT = 0

# # =========================================================
# # QR IMAGE ENDPOINT (STATIC CONTENT)
# # =========================================================
# @app.get("/qr-image")
# async def qr_image():
#     """
#     This QR is STATIC.
#     It always points to /redirect so we can track scans.
#     """
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_Q,
#         box_size=8,
#         border=4,
#     )

#     # 🔑 QR ALWAYS POINTS TO REDIRECT
#     qr.add_data(f"{BASE_URL}/redirect?source=qr")
#     qr.make(fit=True)

#     img = qr.make_image(fill_color="black", back_color="white")

#     buffer = io.BytesIO()
#     img.save(buffer, format="PNG")
#     buffer.seek(0)

#     return Response(content=buffer.getvalue(), media_type="image/png")

# # =========================================================
# # QR PREVIEW PAGE
# # =========================================================
# @app.get("/", response_class=HTMLResponse)
# async def qr_page():
#     return f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>QR Code Document Manager</title>
#         <meta name="viewport" content="width=device-width, initial-scale=1">
#         <style>
#             body {{
#                 font-family: Arial, sans-serif;
#                 background: #f4f6fb;
#                 margin: 0;
#                 padding: 30px;
#             }}
#             .container {{
#                 max-width: 800px;
#                 margin: auto;
#             }}
#             h1 {{
#                 margin-bottom: 20px;
#             }}
#             .card {{
#                 background: #fff;
#                 border-radius: 12px;
#                 padding: 30px;
#                 box-shadow: 0 10px 25px rgba(0,0,0,.1);
#             }}
#             .section-title {{
#                 font-size: 22px;
#                 font-weight: bold;
#                 margin-bottom: 15px;
#                 text-align: center;
#             }}
#             .label {{
#                 font-weight: bold;
#                 margin-top: 15px;
#             }}
#             .url-box {{
#                 background: #eef1f4;
#                 padding: 12px;
#                 border-radius: 6px;
#                 font-family: monospace;
#                 margin: 10px 0 25px;
#                 word-break: break-all;
#                 text-align: center;
#             }}
#             .qr-wrapper {{
#                 text-align: center;
#             }}
#             .qr-wrapper img {{
#                 width: 300px;
#                 margin: 20px 0;
#                 border-radius: 8px;
#                 box-shadow: 0 5px 15px rgba(0,0,0,.15);
#             }}
#             .note {{
#                 text-align: center;
#                 font-size: 14px;
#                 color: #555;
#             }}
#             .info-box {{
#                 margin-top: 30px;
#                 background: #dff1f5;
#                 padding: 15px;
#                 border-radius: 8px;
#                 font-size: 14px;
#             }}
#             .redirect {{
#                 font-size: 13px;
#                 margin-top: 10px;
#                 text-align: center;
#             }}
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>QR Code Document Manager</h1>

#             <div class="card">
#                 <div class="section-title">Social Media Accounts</div>

#                 <div class="label">Current Document URL:</div>
#                 <div class="url-box">{TARGET_URL}</div>

#                 <div class="qr-wrapper">
#                     <img src="/qr-image" alt="QR Code">
#                 </div>

#                 <div class="note">Scan this QR code to access your document</div>

#                 <div class="redirect">
#                     <strong>Redirect URL:</strong><br>
#                     {BASE_URL}/redirect?source=qr
#                 </div>
#             </div>

#             <div class="info-box">
#                 <strong>How it works:</strong><br>
#                 The QR code always points to the same redirect URL on your server.
#                 When someone scans it, they get redirected to whatever document URL
#                 you have set above. This allows you to change the target document
#                 without regenerating or reprinting the QR code.
#             </div>
#         </div>
#     </body>
#     </html>
#     """

# # =========================================================
# # REDIRECT + TRACKING
# # =========================================================
# from urllib.parse import urlencode

# @app.get("/redirect")
# async def redirect_to_target(request: Request):
#     global SCAN_COUNT
#     SCAN_COUNT += 1

#     params = dict(request.query_params)

#     print("QR accessed")
#     print("Params:", params)
#     print("Total scans:", SCAN_COUNT)

#     # ✅ build final URL safely
#     if params:
#         final_url = f"{TARGET_URL}?{urlencode(params)}"
#     else:
#         final_url = TARGET_URL

#     print("Redirecting to:", final_url)

#     return RedirectResponse(url=final_url, status_code=302)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth,public,qr

app = FastAPI(
    title="QR Code Manager",
    description="QR code management system with analytics",
    version="1.0.0"
)

# CORS middleware (allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(qr.router)

@app.get("/")
async def root():
    return {
        "message": "QR Code Manager API",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)