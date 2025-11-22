"""
Make an actual HTTP request to the running Django server to test login
"""
import requests
import sys

print("=" * 80)
print("TESTING LOGIN VIA HTTP REQUEST TO RUNNING SERVER")
print("=" * 80)

# Get initial session to capture CSRF token
session = requests.Session()

login_url = 'http://127.0.0.1:8000/login/'

print(f"\n1️⃣ GET /login/ to get CSRF token:")
print("-" * 80)
try:
    response = session.get(login_url)
    print(f"Status: {response.status_code}")
    
    # Extract CSRF token
    import re
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
    if match:
        csrf_token = match.group(1)
        print(f"✅ CSRF token found: {csrf_token[:20]}...")
    else:
        print(f"❌ CSRF token NOT found in response")
        csrf_token = None
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print(f"\n2️⃣ POST login with credentials:")
print("-" * 80)

login_data = {
    'email': 'Christianbituonon4@gmail.com',
    'password': 'VNxv76dBIbL@JO7UDqLo',
}

if csrf_token:
    login_data['csrfmiddlewaretoken'] = csrf_token

try:
    response = session.post(login_url, data=login_data, allow_redirects=False)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"✅ Redirect to: {response.headers.get('Location')}")
        print(f"✅ ✅✅ LOGIN SUCCESSFUL! ✅✅✅")
    elif response.status_code == 200:
        print(f"⚠️ Returned to login page (200 OK)")
        if 'Invalid email' in response.text or 'non_field_errors' in response.text:
            print(f"❌ Form has errors - login failed")
            # Try to extract error message
            if 'Incorrect Username or Password' in response.text:
                print(f"   Error: Incorrect Username or Password")
        else:
            print(f"ℹ️ No obvious errors in response")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
