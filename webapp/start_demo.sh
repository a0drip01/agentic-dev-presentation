#!/bin/bash

# Ultimate Demo Launcher - Hospital Notification System
# Run this script and your demo will be ready in 30 seconds!

set -e

echo "🏥 Hospital Notification System - Ultimate Demo Launcher"
echo "======================================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this from the webapp directory!"
    echo "   cd /Users/alexdripchak/Projects/agentic-dev-presentation/webapp"
    echo "   ./start_demo.sh"
    exit 1
fi

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please create it first: make venv && make install"
    exit 1
fi

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

echo "🔄 Setting up demo data..."
python manage.py setup_demo --clean

echo "🔄 Creating admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@demo.com', 'demo123')
    print('✅ Admin user created: admin/demo123')
else:
    print('✅ Admin user already exists: admin/demo123')
"

echo ""
echo "🚀 DEMO IS READY!"
echo "================="
echo ""
echo "📊 Open these URLs in your browser:"
echo "   Observer Dashboard: http://localhost:8000/dashboard/observers/"
echo "   Room Dashboard:     http://localhost:8000/dashboard/"
echo "   Admin Panel:        http://localhost:8000/admin/ (admin/demo123)"
echo ""
echo "🎯 Quick Commands for Demo:"
echo "   Test Notification:  make test-notification"
echo "   Django Shell:       make shell"
echo ""
echo "📱 iPhone App should register automatically when opened"
echo "🔔 Notification Bus is running automatically with Django"
echo ""
echo "🎪 Starting Django server on port 8000..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Start the server
python manage.py runserver 8000