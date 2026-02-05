import requests
import json

BASE_URL = "https://social-media-vmfr.onrender.com"

def test_complete_flow():
    print("🔍 Testing Complete QR Redirect Flow\n")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "marketing@company.com",
        "password": "marketing123"
    })
    
    if response.status_code != 200:
        print("❌ Login failed!")
        print(response.text)
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(" Login successful")
    
    # Step 2: Create test QR code
    print("\n2️⃣ Creating test QR code...")
    test_code = "vercel-test-2024"
    test_target = "https://digital-links.vercel.app"
    
    response = requests.post(
        f"{BASE_URL}/api/qr",
        json={
            "code": test_code,
            "target_url": test_target
        },
        headers=headers
    )
    
    if response.status_code == 201:
        print(f" QR code created: {test_code}")
        qr_data = response.json()
        print(f"   Target URL: {test_target}")
        print(f"   QR ID: {qr_data['id']}")
    elif response.status_code == 400:
        print(f"⚠️  QR code already exists (using existing)")
    else:
        print(f"❌ Failed to create QR: {response.text}")
        return
    
    # Step 3: Test the redirect endpoint (DON'T FOLLOW REDIRECTS)
    print("\n3️⃣ Testing redirect endpoint...")
    print(f"   Hitting: {BASE_URL}/r/{test_code}")
    
    response = requests.get(
        f"{BASE_URL}/r/{test_code}",
        allow_redirects=False  # Important: don't follow the redirect
    )
    
    print(f"\n   Response Status: {response.status_code}")
    print(f"   Location Header: {response.headers.get('location', 'NOT FOUND')}")
    
    # Step 4: Verify the redirect
    expected_location = test_target
    actual_location = response.headers.get('location')
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if response.status_code == 302:
        print(" Status code is correct (302 redirect)")
    else:
        print(f"❌ Wrong status code: {response.status_code} (expected 302)")
    
    if actual_location == expected_location:
        print(f" Redirect target is correct")
        print(f"   Expected: {expected_location}")
        print(f"   Got:      {actual_location}")
    else:
        print(f"❌ Redirect target is WRONG!")
        print(f"   Expected: {expected_location}")
        print(f"   Got:      {actual_location}")
    
    # Step 5: Check if scan was logged
    print("\n4️⃣ Checking analytics...")
    response = requests.get(
        f"{BASE_URL}/api/qr",
        headers=headers
    )
    
    if response.status_code == 200:
        qr_codes = response.json()
        for qr in qr_codes:
            if qr['code'] == test_code:
                print(f" Scan was logged! Total scans: {qr['scan_count']}")
                break
    
    print("\n" + "=" * 60)
    print("🎉 TEST COMPLETE")
    print("=" * 60)
    
    # Step 6: What the QR code should contain
    print("\n📱 QR CODE INFORMATION")
    print("=" * 60)
    print(f"QR Code should contain this URL:")
    print(f"   {BASE_URL}/r/{test_code}")
    print(f"\nWhen scanned, it redirects to:")
    print(f"   {test_target}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()