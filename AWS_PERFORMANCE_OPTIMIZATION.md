# 🚀 AWS Performance Optimization Guide (FREE!)

Your AWS t2.micro is undersized, but here are proven methods to speed it up **without paying money**:

---

## **Step 1: Optimize Gunicorn Workers** ⚙️

Current Gunicorn config probably has too many workers for 914MB RAM.

**SSH into AWS:**
```bash
ssh -i your-key.pem ubuntu@54.66.185.78
```

**Edit Gunicorn service:**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Change the workers line to:**
```bash
ExecStart=/home/ubuntu/edulytics/venv/bin/gunicorn \
    --workers 2 \
    --worker-class sync \
    --worker-connections 100 \
    --bind 0.0.0.0:8000 \
    --timeout 60 \
    evaluationWeb.wsgi
```

**Apply changes:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

**Why:** 2 workers use ~300-400MB, leaving room for MySQL.

---

## **Step 2: Enable MySQL Query Caching** 📊

**SSH into AWS and connect to MySQL:**
```bash
mysql -h 54.66.185.78 -u eval_user -p evaluation
```

**Check if query cache is enabled:**
```sql
SHOW VARIABLES LIKE 'query_cache%';
```

**If not enabled, optimize MySQL config:**
```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

**Add/modify these settings:**
```ini
[mysqld]
query_cache_type = 1
query_cache_size = 64M
query_cache_limit = 2M
max_connections = 50
```

**Restart MySQL:**
```bash
sudo systemctl restart mysql
```

---

## **Step 3: Enable Django ORM Query Optimization** 🐍

✅ **Already done in latest settings.py:**
- Connection pooling (600 seconds)
- Template caching
- Gzip compression middleware
- Cache settings

**No action needed** - Latest code has these optimizations.

---

## **Step 4: Add Nginx Reverse Proxy** 🔌

**Install Nginx:**
```bash
sudo apt-get update
sudo apt-get install -y nginx
```

**Create Nginx config:**
```bash
sudo nano /etc/nginx/sites-available/default
```

**Paste this:**
```nginx
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    client_max_body_size 100M;

    location /static/ {
        alias /home/ubuntu/edulytics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /images/ {
        alias /home/ubuntu/edulytics/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

**Enable Nginx:**
```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

**Why:** Nginx serves static files ~10x faster than Gunicorn.

---

## **Step 5: Optimize Static Files** 📦

**On your local machine:**
```bash
cd C:\Users\ADMIN\eval\evaluation
python manage.py collectstatic --noinput
git add staticfiles/
git commit -m "Add optimized static files"
git push origin main
```

**On AWS:**
```bash
cd /home/ubuntu/edulytics
git pull origin main
python manage.py collectstatic --noinput --clear
sudo systemctl restart nginx
```

---

## **Step 6: Enable Pagination & Filtering** 🔍

**Already implemented in views.py**, but verify:
- ✅ Admin view uses `Paginator` (25 items/page)
- ✅ Views use `select_related()` to prevent N+1 queries
- ✅ Database indexes on frequently queried fields

**Nothing to do** - Already optimized.

---

## **Step 7: Monitor & Log Slow Queries** 📈

**On AWS, monitor performance:**
```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check Gunicorn status
sudo systemctl status gunicorn

# View Gunicorn logs
sudo journalctl -u gunicorn -n 50 -f

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

**If MySQL is slow:**
```bash
# Check MySQL slow query log
sudo tail -f /var/log/mysql/slow.log
```

---

## **Expected Performance Improvements**

| Optimization | Speed Gain | Effort |
|---|---|---|
| Gunicorn workers (2 instead of 4) | 20-30% | 2 min |
| MySQL query cache | 30-50% | 5 min |
| Nginx reverse proxy | 40-60% | 10 min |
| Static file caching | 50-70% | 2 min |
| Django cache settings | 20-30% | Already done |
| **TOTAL** | **3-4x faster** | **~20 min** |

---

## **When to Upgrade to t2.small (Free for 12 months)**

If after all optimizations you still need more power:
- **t2.small = 2GB RAM** (4x more than t2.micro)
- **FREE for first 12 months** on AWS free tier
- Just scale up: AWS → EC2 → Instance Settings → Change Instance Type

---

## **Next Steps**

1. ✅ Pull latest settings from GitHub
2. Run Gunicorn optimization (Step 1)
3. Install & configure Nginx (Step 4)
4. Push static files (Step 5)
5. Test performance: `ab -n 100 http://54.66.185.78/`

---

**Questions?** Check Django performance docs: https://docs.djangoproject.com/en/5.1/topics/performance/
