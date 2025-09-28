# 🏥 DEMO QUICK START GUIDE
## Hospital Notification System - Observer Pattern Demo

### ⏱️ **TOTAL SETUP TIME: 3 MINUTES**

---

## 🚀 **STEP-BY-STEP DEMO STARTUP** 

### **Terminal 1: Main Server Setup** (2 minutes)

```bash
# 1. Navigate to project directory
cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp

# 2. Activate virtual environment  
source .venv/bin/activate

# 3. Setup demo data (creates rooms, users, observers)
python manage.py setup_demo --clean

# 4. Start Django server (LEAVE THIS RUNNING)
make runserver
```

**✅ Expected Output:**
- Demo data created (rooms, users, observers, consumers)
- Server starts on `http://127.0.0.1:8000/`
- Message: "Starting development server at http://127.0.0.1:8000/"

**🔄 Notification Bus Status:** ✅ **RUNNING** (automatically starts with Django server)

---

## 🖥️ **BROWSER SETUP** (30 seconds)

Open these URLs in separate browser tabs:

1. **Observer Dashboard**: http://localhost:8000/dashboard/observers/
   - Shows real-time observer registrations
   - Pop-up notifications when iPhone app connects
   
2. **Room Dashboard**: http://localhost:8000/dashboard/
   - Timer controls for triggering notifications
   - Room status monitoring

3. **Admin Panel**: http://localhost:8000/admin/ 
   - Username: `admin`
   - Password: `demo123`

---

## 📱 **DEMO FLOW** (10-15 minutes presentation)

### **Phase 1: Show The Fix** (3 mins)
- Explain old observer pattern was broken (in-memory)
- Show new database-persisted approach
- Point out real-time dashboard

### **Phase 2: iPhone App Registration** (5 mins)
- **iPhone App Task**: Open iPhone app, it should auto-register
- **Watch For**: Green notification popup on Observer Dashboard
- **Backup Plan**: Manual registration via curl (see commands below)

### **Phase 3: Trigger Notifications** (5 mins)

**Terminal 2: Notification Testing** (new terminal window)
```bash
# Navigate to webapp directory
cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp

# Activate virtual environment
source .venv/bin/activate

# Option A: Manual notification trigger
python manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers(reason='Live demo notification')"

# Option B: Start room timer (more realistic)
python manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').start_timer(60)"
```

### **Phase 4: Show Results** (2 mins)
- iPhone app should receive push notification
- Dashboard shows delivery status
- Demonstrate failure handling if needed

---

## 🔧 **MAKEFILE COMMANDS REFERENCE**

```bash
# In webapp directory:
make runserver     # Start Django development server
make shell         # Open Django shell for testing
make install       # Install/update dependencies  
make clean         # Clean environment if needed
make db           # Open database for inspection
```

---

## 📋 **BACKUP COMMANDS** (If iPhone App Fails to Register)

**Manual iPhone Observer Registration:**
```bash
curl -X POST http://localhost:8000/api/observers/register/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "LIVE-iPhone-Demo",
    "observer_type": "mobile_app",
    "room_name": "DEMO-ICU-1", 
    "callback_url": "https://httpbin.org/post",
    "metadata": {"demo": true, "device": "iPhone"}
  }'
```

**Check Observer Status:**
```bash
curl http://localhost:8000/api/rooms/DEMO-ICU-1/observers/
```

---

## 🎯 **PRE-LOADED TEST DATA**

| Type | Name | Purpose |
|------|------|---------|
| **Rooms** | DEMO-ICU-1, DEMO-ICU-2, DEMO-ER-1, DEMO-OR-1 | Demo hospital rooms |
| **Doctors** | Dr. Sarah Johnson, Dr. Michael Chen | Assigned to rooms |
| **Observers** | iPhone Push, Slack Integration, External Monitor | Pre-registered observers |
| **Consumers** | iPhone App, Android App, Monitoring Script | API polling consumers |

---

## ✅ **SUCCESS INDICATORS**

### **Server Running Successfully:**
- ✅ No Django errors in terminal
- ✅ Dashboard URLs load without 404s
- ✅ Demo data populated (see setup_demo output)

### **Observer Pattern Working:**
- ✅ Observer Dashboard shows active observers
- ✅ Real-time updates every 10 seconds  
- ✅ Notification popups appear when observers register

### **iPhone Integration Ready:**
- ✅ API endpoints responding (test with backup curl)
- ✅ Room timers can be set via dashboard
- ✅ Manual notifications trigger successfully

---

## 🚨 **TROUBLESHOOTING**

### **Server Won't Start:**
```bash
# Check for errors
python manage.py check

# Apply any missing migrations  
python manage.py migrate

# Recreate demo data
python manage.py setup_demo --clean
```

### **404 Errors on Dashboards:**
- Ensure server is running on port 8000
- Check URLs: `/dashboard/` and `/dashboard/observers/`
- Restart server if needed

### **No Demo Data:**
```bash
python manage.py setup_demo --clean
```

### **Observer Registration Fails:**
- Verify room names: `DEMO-ICU-1`, `DEMO-ICU-2`, `DEMO-ER-1`, `DEMO-OR-1`
- Check JSON format in API calls
- Look at server logs for detailed errors

---

## 🎪 **DEMO SCRIPT TALKING POINTS**

1. **"The Problem"**: "Old observer pattern used in-memory storage - lost on restart"
2. **"The Solution"**: "Database-persisted observers with retry logic and monitoring"  
3. **"iPhone Integration"**: "Your iPhone app registers once, receives reliable push notifications"
4. **"Real-time Monitoring"**: "Dashboard shows observer health and statistics"
5. **"Enterprise Ready"**: "Handles failures, scales across servers, maintains reliability"

---

## ⚡ **ONE-COMMAND DEMO SETUP**

```bash
# Ultimate shortcut (run from project root):
cd webapp && source .venv/bin/activate && python manage.py setup_demo --clean && make runserver
```

**🎉 That's it! Your demo environment is ready. The notification bus runs automatically with Django - no separate process needed.**

**💡 Expected Demo Duration: 15-20 minutes total**