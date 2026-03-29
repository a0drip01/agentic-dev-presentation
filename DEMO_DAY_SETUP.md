# 🎯 DEMO DAY - 30 Second Setup

## **FASTEST SETUP** (Run this and you're done!)

```bash
cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp
source .venv/bin/activate  
make demo
```

**That's it!** Server will start, demo data will be loaded, and you're ready to present.

---

## **OR USE THE ULTIMATE SCRIPT**

```bash
cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp
./start_demo.sh
```

---

## **BROWSER TABS TO OPEN**

1. http://localhost:8000/dashboard/observers/ (Main demo dashboard)
2. http://localhost:8000/dashboard/ (Room timers)
3. http://localhost:8000/admin/ (admin/demo123)

---

## **DEMO TALKING POINTS**

1. **"The Problem"** - Old observer pattern lost data on restart
2. **"The Fix"** - Database-persisted observers with monitoring
3. **"iPhone Demo"** - Open iPhone app, show registration popup
4. **"Trigger Notification"** - Use room timer or: `make test-notification`
5. **"Show Results"** - iPhone gets notification, dashboard updates

---

## **BACKUP COMMANDS**

```bash
# Test notification
make test-notification

# Manual iPhone registration (if app fails)
curl -X POST http://localhost:8000/api/observers/register/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"LIVE-iPhone-Demo","observer_type":"mobile_app","room_name":"DEMO-ICU-1","callback_url":"https://httpbin.org/post","metadata":{"demo":true}}'

# Check status
curl http://localhost:8000/api/rooms/DEMO-ICU-1/observers/
```

**🎉 You're ready to rock this demo!**