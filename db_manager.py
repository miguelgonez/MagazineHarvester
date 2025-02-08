import sqlite3
from typing import Dict, List, Tuple
import os

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume INTEGER NOT NULL,
                issue INTEGER NOT NULL,
                filepath TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_path TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                pdf_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def add_download(self, volume: int, issue: int, filepath: str, status: str = 'success'):
        """Record a new download in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO downloads (volume, issue, filepath, status)
            VALUES (?, ?, ?, ?)
        ''', (volume, issue, filepath, status))
        
        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        """Get download statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM downloads')
        total_downloads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT volume) FROM downloads')
        total_volumes = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT 
                ROUND(CAST(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS FLOAT) / 
                COUNT(*) * 100, 1)
            FROM downloads
        ''')
        success_rate = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'total_downloads': total_downloads,
            'total_volumes': total_volumes,
            'success_rate': success_rate
        }

    def get_download_history(self, limit: int = 10) -> List[Tuple]:
        """Get recent download history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT volume, issue, status, timestamp
            FROM downloads
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        
        return history

    def add_chat_history(self, pdf_path: str, user_message: str, assistant_response: str):
        """Record a new chat interaction in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history (pdf_path, user_message, assistant_response)
            VALUES (?, ?, ?)
        ''', (pdf_path, user_message, assistant_response))
        
        conn.commit()
        conn.close()

    def get_chat_history(self, pdf_path: str, limit: int = 10) -> List[Tuple]:
        """Get chat history for a specific PDF."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, assistant_response, timestamp
            FROM chat_history
            WHERE pdf_path = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (pdf_path, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        return history

    def add_todo(self, title: str, description: str = None, pdf_path: str = None):
        """Add a new todo item."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO todos (title, description, pdf_path)
            VALUES (?, ?, ?)
        ''', (title, description, pdf_path))

        conn.commit()
        conn.close()

    def get_todos(self, status: str = None) -> List[Tuple]:
        """Get todo items, optionally filtered by status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT id, title, description, pdf_path, status, created_at, completed_at
                FROM todos
                WHERE status = ?
                ORDER BY created_at DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT id, title, description, pdf_path, status, created_at, completed_at
                FROM todos
                ORDER BY created_at DESC
            ''')

        todos = cursor.fetchall()
        conn.close()
        return todos

    def update_todo_status(self, todo_id: int, status: str):
        """Update the status of a todo item."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status == 'completed':
            cursor.execute('''
                UPDATE todos
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, todo_id))
        else:
            cursor.execute('''
                UPDATE todos
                SET status = ?, completed_at = NULL
                WHERE id = ?
            ''', (status, todo_id))

        conn.commit()
        conn.close()