## 📋 **Simple RSS Feed Monitoring - 3 Quick Commands**

### **1. Check if Redis is Running**
```bash
redis-cli ping
```
✅ **Redis is running** (PONG response means it's working)

### **2. Check if Celery Beat (60-min scheduler) is Running**
```bash
ps aux | grep "celery.*beat" | grep -v grep
```
✅ **Celery Beat is running** (process ID 56350, started at 10:48 AM)

### **3. Simple Feed Status Check**
```bash
cd backend && python -c "
from app.db.session import SessionLocal
from app.models.job import RSSFeedConfiguration

db = SessionLocal()
feeds = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.source_type == 'rss_app').all()

print('RSS Feed Status:')
working = 0
for feed in feeds:
    status = '✅ Working' if feed.last_job_count and feed.last_job_count > 0 else '❌ Issues'
    jobs = feed.last_job_count or 0
    print(f'{status} | {jobs:2d} jobs | {feed.name}')
    if jobs > 0:
        working += 1

print(f'\\nSummary: {working}/{len(feeds)} feeds working')
db.close()
"
```
## 🎯 **Simple Answers to Your Questions:**

### **1. How to know Redis is initiated?**
**Command:** `redis-cli ping`
**Expected:** `PONG` (means Redis is running)

### **2. How to know 60-minute scheduler is running?**
**Command:** `ps aux | grep "celery.*beat" | grep -v grep`
**Expected:** Shows process with `celery beat` (means scheduler is active)

### **3. How to know which feeds have issues?**
**Command:** Run the Python script above
**Result:** 
- ✅ = Feed working (has jobs)
- ❌ = Feed has issues (0 jobs)

### **4. When does the 60-minute fetch happen?**
Your Celery Beat started at **10:48 AM**, so it fetches every hour at:
- 11:48 AM
- 12:48 PM  
- 1:48 PM
- etc.

## 📊 **Current Status:**
- ✅ Redis: Running
- ✅ Scheduler: Running (every 60 min)
- ✅ Working Feeds: 8 out of 12
- ❌ Problem Feeds: 4 feeds have 0 jobs

**That's it!** These 3 commands tell you everything you need to know about your RSS feed automation system.