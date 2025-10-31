# Personal Task Manager - PRD

## Overview
A simple task management application for personal productivity. Users can create, view, edit, and delete tasks.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React
- **Database**: SQLite
- **Styling**: Basic CSS (no frameworks)

## Features

### Core Features
1. **Create Task**
   - Task title (required, max 100 chars)
   - Task description (optional, max 500 chars)
   - Due date (optional)
   - Priority level: Low, Medium, High

2. **View Tasks**
   - List all tasks
   - Show task details (title, description, due date, priority)
   - Sort by due date or priority

3. **Edit Task**
   - Update all task fields
   - Mark task as completed

4. **Delete Task**
   - Remove task from list

### Data Model
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    due_date DATE,
    priority VARCHAR(10) DEFAULT 'Medium',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints
- `GET /tasks` - List all tasks
- `POST /tasks` - Create new task
- `GET /tasks/{id}` - Get task details
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

## User Interface
1. **Task List Page** (`/`)
   - Display all tasks
   - Button to create new task
   - Each task shows title, due date, priority
   - Edit/Delete buttons for each task

2. **Task Form** (modal or separate page)
   - Input fields for title, description, due date, priority
   - Save/Cancel buttons

## Success Criteria
- Users can perform all CRUD operations on tasks
- Tasks persist in SQLite database
- Simple, clean interface
- No user authentication required (single-user app)

## Non-Requirements
- No user accounts/authentication
- No task categories/tags
- No search functionality
- No notifications
- No mobile responsiveness (basic desktop only)