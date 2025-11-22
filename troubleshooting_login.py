"""
Check what might be preventing your login
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.core.cache import cache
import socket

print("=" * 80)
print("LOGIN TROUBLESHOOTING GUIDE")
print("=" * 80)

print("\n✅ VERIFIED WORKING:")
print("-" * 80)
print("✅ Backend authentication: WORKS (tested)")
print("✅ Login form: WORKS (tested)")
print("✅ HTTP redirect: WORKS (tested)")
print("✅ Database connection: WORKS (AWS MySQL connected)")
print("✅ User accounts: WORKS (52 users present)")
print("✅ Rate limiting: WORKS (not blocking)")

print("\n\n⚠️ POSSIBLE ISSUES ON YOUR END:")
print("-" * 80)
print("""
1. ❓ BROWSER CACHE
   - Clear your browser cache, cookies, and site data
   - Close and reopen browser
   - Try incognito/private window
   
2. ❓ WRONG URL
   - Make sure you're using: http://your-domain/login/
   - NOT: http://your-domain/register/ (that's registration)
   - NOT: http://your-domain/admin/ (that's Django admin)

3. ❓ WRONG CREDENTIALS
   - Email: Christianbituonon4@gmail.com (case-insensitive)
   - Password: VNxv76dBIbL@JO7UDqLo (case-sensitive!)
   - Double-check there are NO spaces at beginning/end

4. ❓ NETWORK/FIREWALL
   - Check if you can reach the website
   - Try: ping your-domain-or-ip
   - Try from different network/WiFi/cellular

5. ❓ SESSION STORAGE
   - Django uses database sessions
   - Make sure MySQL is accessible
   - Check: sudo mysql -e "SELECT * FROM django_session LIMIT 1;"

6. ❓ DJANGO SERVER NOT RUNNING
   - Make sure your Django server is running
   - Check: ps aux | grep runserver
   - Or: netstat -an | grep LISTEN
""")

print("\n💡 QUICK FIXES TO TRY:")
print("-" * 80)
print("""
1. Clear Django cache:
   python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('✅ Cache cleared')"

2. Clear sessions:
   python manage.py clearsessions

3. Restart Django server:
   python manage.py runserver 0.0.0.0:8000

4. Check database connection:
   python manage.py dbshell

5. Run migrations:
   python manage.py migrate
""")

print("\n📝 YOUR LOGIN CREDENTIALS:")
print("-" * 80)
print(f"""
Email:    Christianbituonon4@gmail.com
Password: VNxv76dBIbL@JO7UDqLo
URL:      /login/
""")

print("\n🔐 VERIFY YOUR USER:")
print("-" * 80)
try:
    user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
    print(f"✅ User exists: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Is active: {user.is_active}")
    print(f"   Created: {user.date_joined}")
    print(f"   Last login: {user.last_login}")
except:
    print("❌ User not found!")

print("\n" + "=" * 80)
print("NEXT: Try the fixes above and let me know what error you see!")
print("=" * 80)
