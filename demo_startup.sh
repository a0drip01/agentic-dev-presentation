#!/bin/bash

# Demo Startup Script for Hospital Notification System
# Live Demo Commands for Easy Presentation

set -e  # Exit on any error

echo "🏥 Hospital Notification System - Live Demo Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the webapp directory!"
    echo "Usage: cd webapp && bash ../demo_startup.sh"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not activated. Activating..."
    if [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found at ../.venv/bin/activate"
        echo "Please create and activate your virtual environment first:"
        echo "  python -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
fi

print_step "Step 1: Checking system health..."
python manage.py check
print_success "Django system check passed"

print_step "Step 2: Applying database migrations..."
python manage.py migrate --no-input
print_success "Database migrations applied"

print_step "Step 3: Setting up demo data..."
python manage.py setup_demo --clean
print_success "Demo data populated"

print_step "Step 4: Creating superuser for admin access..."
echo "Creating admin user (username: admin, password: demo123)"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@demo.com', 'demo123')
    print('Superuser created: admin / demo123')
else:
    print('Superuser already exists')
"

print_success "Admin user ready"

echo ""
echo "🚀 Starting Django Development Server..."
echo "=================================================="

# Start the server in background
python manage.py runserver 8000 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    print_success "Server started on http://localhost:8000"
else
    print_error "Failed to start server"
    exit 1
fi

echo ""
echo "🎯 LIVE DEMO READY!"
echo "=================================================="
echo ""
echo "📊 Dashboard URLs:"
echo "  🏠 Main Dashboard:     http://localhost:8000/dashboard/"
echo "  🔔 Observer Dashboard: http://localhost:8000/dashboard/observers/"
echo "  👨‍💼 Admin Interface:    http://localhost:8000/admin/ (admin/demo123)"
echo ""
echo "🔧 API Endpoints for Testing:"
echo "  📱 Register Observer:  POST http://localhost:8000/api/observers/register/"
echo "  📋 List Room Observers: GET http://localhost:8000/api/rooms/DEMO-ICU-1/observers/"
echo "  🔔 Observer Status:    GET http://localhost:8000/api/observers/{id}/status/"
echo ""
echo "💡 Quick Demo Commands:"
echo "  # Test notification (new terminal):"
echo "  python manage.py shell -c \"from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers()\""
echo ""
echo "  # Start room timer (new terminal):"
echo "  python manage.py shell -c \"from core.models import Room; Room.objects.get(name='DEMO-ICU-1').start_timer(60)\""
echo ""
echo "  # Register iPhone app observer:"
echo "  curl -X POST http://localhost:8000/api/observers/register/ \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{"
echo "      \"name\": \"iPhone Demo App\","
echo "      \"observer_type\": \"mobile_app\","
echo "      \"room_name\": \"DEMO-ICU-1\","
echo "      \"callback_url\": \"https://httpbin.org/post\","
echo "      \"metadata\": {\"demo\": true}"
echo "    }'"
echo ""
echo "📋 Demo Data Available:"
echo "  🏥 Rooms: DEMO-ICU-1, DEMO-ICU-2, DEMO-ER-1, DEMO-OR-1"
echo "  👨‍⚕️ Users: Dr. Sarah Johnson, Dr. Michael Chen, Nurses, Patients"
echo "  📱 Pre-registered Observers: iPhone Push, Slack Integration, External Monitor"
echo "  📊 Pre-registered Consumers: iPhone App, Android App, Monitoring Script"
echo ""
echo "🎪 Live Demo Flow:"
echo "  1. Show observer dashboard with real-time updates"
echo "  2. Register new iPhone app observer via API"
echo "  3. Watch notification popup appear on dashboard"
echo "  4. Start room timer to trigger notifications"
echo "  5. Show webhook delivery to httpbin.org"
echo "  6. Demonstrate observer failure handling"
echo ""
echo "⏹️  To stop the demo server: kill $SERVER_PID"
echo ""
print_success "Demo environment is ready for your presentation! 🎉"

# Keep script running to maintain server
wait $SERVER_PID