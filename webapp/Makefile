VENV_DIR=.venv
PYTHON=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip
DJANGO_ADMIN=$(VENV_DIR)/bin/django-admin

.PHONY: help venv install runserver shell freeze clean

help:
	@echo "Common Makefile commands:"
	@echo "  make venv      # Create virtual environment"
	@echo "  make install   # Install requirements"
	@echo "  make runserver # Run Django development server"
	@echo "  make shell     # Open Django shell"
	@echo "  make freeze    # Freeze requirements.txt"
	@echo "  make clean     # Remove virtual environment and pyc files"

venv:
	python3 -m venv $(VENV_DIR)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install django

runserver:
	$(PYTHON) manage.py runserver

shell:
	$(PYTHON) manage.py shell

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV_DIR) *.pyc **/*.pyc __pycache__ **/__pycache__
