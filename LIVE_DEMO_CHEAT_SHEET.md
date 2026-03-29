# 🏥 LIVE DEMO CHEAT SHEET - Hospital Notification System
## Observer Pattern Implementation with iPhone App Integration

### 🚀 PRE-DEMO SETUP (5 minutes before demo)

```bash
# 1. Navigate to project and activate virtual environment
cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp
source .venv/bin/activate

# 2. Setup demo data
python manage.py setup_demo --clean

# 3. Start the server
python manage.py runserver 8000
```

---

## 📊 DASHBOARD URLs (Open these in browser tabs)

- **Observer Dashboard**: http://localhost:8000/dashboard/observers/
- **Room Grid Dashboard**: http://localhost:8000/dashboard/
- **Admin Interface**: http://localhost:8000/admin/ (admin/demo123)

---

## 🎯 LIVE DEMO FLOW (15-20 minutes)

### **1. Show the Problem** (2 mins)
"The old observer pattern was broken because it used in-memory storage..."
- Explain how observers were lost on server restart
- Show the fixed database-persisted approach

### **2. Show Observer Dashboard** (3 mins)
Open: http://localhost:8000/dashboard/observers/
- Real-time updates every 10 seconds
- Shows active observers and consumers
- Demonstrates proper observer pattern implementation

### **3. Register iPhone App Observer via API** (5 mins)

```bash
# Copy/paste this curl command during demo:
curl -X POST http://localhost:8000/api/observers/register/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "LIVE-iPhone-Demo-App",
    "observer_type": "mobile_app",
    "room_name": "DEMO-ICU-1",
    "callback_url": "https://httpbin.org/post",
    "callback_headers": {
      "Authorization": "Bearer live_demo_token"
    },
    "metadata": {
      "device_id": "iPhone_Live_Demo",
      "user": "Dr. Demo",
      "presentation": true
    }
  }'
```

**Expected Response:**
```json
{
  "observer_id": "uuid-here",
  "name": "LIVE-iPhone-Demo-App",
  "observer_type": "mobile_app",
  "room": "DEMO-ICU-1",
  "status": "active",
  "created_at": "timestamp"
}
```

**Watch for**: Green notification popup on dashboard saying "New observer registered"

### **4. Trigger Notification** (3 mins)

```bash
# Option A: Manual notification trigger
python manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers(event_type='demo', reason='Live presentation demo')"

# Option B: Start timer (more realistic)
python manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').start_timer(60)"
```

**Show**: 
- Webhook request sent to httpbin.org
- Observer success/failure tracking
- Real-time dashboard updates

### **5. Demonstrate Failure Handling** (3 mins)

```bash
# Register observer with bad URL to show failure handling
curl -X POST http://localhost:8000/api/observers/register/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "LIVE-Bad-Observer",
    "observer_type": "mobile_app", 
    "room_name": "DEMO-ICU-1",
    "callback_url": "https://this-will-fail.invalid"
  }'

# Trigger notification to show failure
python manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers(reason='Testing failure handling')"
```

**Watch for**: Red notification popup showing observer failure

### **6. Show Observer Status** (2 mins)

```bash
# Get observer status via API
curl http://localhost:8000/api/rooms/DEMO-ICU-1/observers/
```

**Highlight**:
- Success/failure statistics
- Retry mechanisms
- Database persistence

---

## 📱 STANDARD TEST DATA FOR iPhone CONSUMER

### Room Tags Available:
- `room`: `DEMO-ICU-1`, `DEMO-ICU-2`, `DEMO-ER-1`, `DEMO-OR-1`
- `provider`: `demo_doctor1`, `demo_doctor2`

### iPhone App Registration Template:
```json
{
  "name": "iPhone App - [Doctor Name]",
  "consumer_type": "mobile",
  "subscriptions": [
    {"tag_type": "room", "tag_value": "DEMO-ICU-1"},
    {"tag_type": "provider", "tag_value": "demo_doctor1"}
  ],
  "metadata": {
    "device_id": "iPhone_[unique_id]",
    "user_id": "[doctor_username]",
    "app_version": "1.0.0"
  }
}
```

### Observer Registration Template:
```json
{
  "name": "iPhone Push - [Doctor Name]",
  "observer_type": "mobile_app",
  "room_name": "DEMO-ICU-1",
  "callback_url": "https://your-push-server.com/notify",
  "callback_headers": {
    "Authorization": "Bearer [device_token]",
    "X-Device-ID": "[device_id]"
  },
  "metadata": {
    "device_token": "[push_token]",
    "user_id": "[doctor_id]"
  }
}
```

---

## 🛠️ TROUBLESHOOTING COMMANDS

```bash
# Check observer status
python manage.py shell -c "from core.models import ObserverSubscription; [print(f'{o.name}: {o.status} (failures: {o.failure_count})') for o in ObserverSubscription.objects.all()]"

# Check recent notifications
python manage.py shell -c "from core.models import Notification; [print(f'{n.timestamp}: {n.room.name} - {n.message[:50]}') for n in Notification.objects.order_by('-timestamp')[:5]]"

# Restart demo data if needed
python manage.py setup_demo --clean
```

---

## 🎤 KEY TALKING POINTS

1. **"Before Fix"**: "The old system used in-memory storage that was lost on restart"
2. **"After Fix"**: "Database-persisted observers with retry logic and failure tracking"
3. **"iPhone Integration"**: "Your iPhone app registers once and receives push notifications reliably"
4. **"Scalability"**: "Works across multiple servers, handles failures gracefully"
5. **"Monitoring"**: "Real-time dashboard shows observer health and statistics"

---

## 📋 DEMO CHECKLIST

- [ ] Server running on port 8000
- [ ] Demo data populated
- [ ] Browser tabs open (observer dashboard, room grid)
- [ ] Terminal ready for commands
- [ ] httpbin.org tab open to show webhook delivery
- [ ] Curl commands copied and ready
- [ ] Backup commands prepared

---

## 🚨 IF THINGS GO WRONG

### Server won't start:
```bash
python manage.py check
python manage.py migrate
```

### No demo data:
```bash
python manage.py setup_demo --clean
```

### Observer registration fails:
- Check room name exists: `DEMO-ICU-1`, `DEMO-ICU-2`, `DEMO-ER-1`, `DEMO-OR-1`
- Verify JSON format in curl command
- Check server logs for errors

---

**🎯 Total Demo Time: 15-20 minutes**
**🎉 You're ready for an awesome presentation!**