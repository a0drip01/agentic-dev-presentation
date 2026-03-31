# Project Planning: Django Web App for Room Assignment & Timers

## Overview
Build a simple Django web app to manage users (doctors, nurses, patients), assign them to rooms, and track timers for each room. Initial data will be loaded from a CSV file. The app will print notifications when a room timer expires.

---

## Phase 1: Project Setup & Scaffolding

1. Create a folder for the Django web app (e.g., `webapp/`).
2. Ensure the correct Python version is available (recommend Python 3.10+).
3. Set up a Python virtual environment inside the webapp folder.
4. Create a Makefile for managing the virtual environment and common tasks (install, run, etc.).
5. Initialize a new Django project inside the webapp folder.

---

## Phase 2: Planning & Design

1. Create a `planning/` folder for documentation, task lists, and design notes.
2. Write a refined planning document (this file).
3. Design the data model:
    - User model (with roles: doctor, nurse, patient)
    - Room model (with assigned users and timer)
4. Plan CSV import structure and sample data.

---

## Phase 3: Core Functionality

1. Implement models for User and Room.
2. Implement CSV import logic to populate the database.
3. Create views to display users and rooms.
4. Implement timer logic for each room.
5. Print notification messages when a room timer expires.

---

## Phase 4: Testing & Validation

1. Write basic tests for models and CSV import.
2. Test timer and notification logic.

---

## Phase 5: Next Steps (Future Work)

1. Set up PostgreSQL database.
2. Add user authentication and web UI improvements.
3. Add real-time notifications (optional).

---

## Task List

- [x] Create `webapp/` folder and set up virtual environment
- [x] Create Makefile for environment management
- [x] Initialize Django project
- [x] Create `planning/` folder and add planning docs
- [x] Design models and CSV structure
- [ ] Implement models and CSV import
- [ ] Implement timer and notification logic
- [ ] Add basic tests
