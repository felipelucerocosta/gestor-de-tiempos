import sqlite3
import os
from datetime import datetime
import sys

# Make DB portable: save in the same dir as the executable
if getattr(sys, 'frozen', False):
    # Running as PyInstaller exe
    db_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    db_dir = os.path.dirname(__file__)

DB_PATH = os.path.join(db_dir, "projects.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        deadline TEXT NOT NULL
    )
    ''')
    
    # Logs table
    # progress_score: 0 (None), 1 (Minor), 5 (Major) - configurable values for graphing
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        timestamp TEXT NOT NULL,
        description TEXT NOT NULL,
        progress_score INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    ''')
    
    # Stages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    ''')

    # Tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        description TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_project(name, deadline):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO projects (name, created_at, deadline) VALUES (?, ?, ?)", (name, created_at, deadline))
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id

def add_log(project_id, description, progress_score):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs (project_id, timestamp, description, progress_score) VALUES (?, ?, ?, ?)", 
                   (project_id, timestamp, description, progress_score))
    conn.commit()
    conn.close()

def get_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    conn.close()
    return projects

def get_logs(project_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs WHERE project_id = ? ORDER BY timestamp ASC", (project_id,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def add_stage(project_id, name, due_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stages (project_id, name, due_date) VALUES (?, ?, ?)", (project_id, name, due_date))
    conn.commit()
    conn.close()

def get_stages(project_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stages WHERE project_id = ? ORDER BY due_date ASC", (project_id,))
    stages = cursor.fetchall()
    conn.close()
    return stages

def add_task(project_id, description):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (project_id, description) VALUES (?, ?)", (project_id, description))
    conn.commit()
    conn.close()

def get_tasks(project_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE project_id = ?", (project_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def toggle_task(task_id, completed):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (completed, task_id))
    conn.commit()
    conn.close()

def update_project_deadline(project_id, new_deadline):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET deadline = ? WHERE id = ?", (new_deadline, project_id))
    conn.commit()
    conn.close()
