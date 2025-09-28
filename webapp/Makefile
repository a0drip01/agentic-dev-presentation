VENV_DIR=.venv
PYTHON=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip
DJANGO_ADMIN=$(VENV_DIR)/bin/django-admin

.PHONY: help venv install runserver shell freeze clean db demo setup-demo test-notification

help:
	@echo "Common Makefile commands:"
	@echo "  make venv           # Create virtual environment"
	@echo "  make install        # Install requirements"
	@echo "  make runserver      # Run Django development server"
	@echo "  make shell          # Open Django shell"
	@echo "  make freeze         # Freeze requirements.txt"
	@echo "  make clean          # Remove virtual environment and pyc files"
	@echo "  make db             # Open SQLite database"
	@echo ""
	@echo "Demo-specific commands:"
	@echo "  make demo           # Complete demo setup (setup-demo + runserver)"
	@echo "  make setup-demo     # Setup demo data only"
	@echo "  make test-notification # Send test notification to DEMO-ICU-1"

venv:
	python3 -m venv $(VENV_DIR)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install django

runserver:
	$(PYTHON) manage.py runserver 8000

shell:
	$(PYTHON) manage.py shell

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV_DIR) *.pyc **/*.pyc __pycache__ **/__pycache__

db:
	@echo "Opening SQLite DB (db.sqlite3) with sqlite3 CLI..."
	sqlite3 db.sqlite3

# Demo-specific commands
demo: setup-demo runserver

setup-demo:
	@echo "🚀 Setting up demo data..."
	$(PYTHON) manage.py setup_demo --clean
	@echo "✅ Demo data ready!"

test-notification:
	@echo "🔔 Sending test notification to DEMO-ICU-1..."
	$(PYTHON) manage.py shell -c "from core.models import Room; Room.objects.get(name='DEMO-ICU-1').notify_observers(reason='Makefile test notification')"
	@echo "✅ Test notification sent!"
