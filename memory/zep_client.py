import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Import the sanitizer
from utils.message_sanitizer import sanitize_for_storage

load_dotenv()

class RealZepMemoryManager:
    """
    Реальная система памяти с использованием SQLite для хранения записей.
    Имеет FIFO буфер (ограничение 50 строк) и полную изоляцию между сессиями и агентами.
    """
    
    def __init__(self, db_path: str = "zep_memory.db"):
        self.db_path = db_path
        self.max_entries = 20  # Уменьшаем до 20 для предотвращения переполнения контекста
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу для хранения записей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL,
                message_type TEXT DEFAULT 'general'  -- Тип сообщения: general, task, result, review и т.п.
            )
        ''')
        
        # Создаем индекс для быстрого поиска
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_agent ON memory_entries (session_id, agent_name)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_agent_type ON memory_entries (session_id, agent_name, message_type)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_session_id(self, session_id: str, agent_name: str) -> str:
        """
        Создает изолированный идентификатор сессии для каждого агента внутри сессии
        """
        return f"{session_id}:{agent_name}"
    
    def add_message(self, session_id: str, agent_name: str, message: str, message_type: str = 'general') -> None:
        """
        Добавляет сообщение в память агента в сессии с отметкой времени.
        Ограничивает длину сообщений для предотвращения переполнения контекста.
        """
        formatted_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{agent_name}] -> {message}"
        
        # Ограничиваем длину сообщения до 300 символов для предотвращения переполнения контекста
        if len(formatted_message) > 300:
            formatted_message = formatted_message[:300] + "... [TRUNCATED]"
        
        # Sanitize the message to avoid encoding issues
        sanitized_message = sanitize_for_storage(formatted_message)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Добавляем сообщение в базу
            cursor.execute('''
                INSERT INTO memory_entries (session_id, agent_name, timestamp, message, message_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, agent_name, datetime.now().isoformat(), sanitized_message, message_type))
            
            # Проверяем количество записей и при необходимости удаляем старые (FIFO)
            cursor.execute('''
                SELECT COUNT(*) FROM memory_entries 
                WHERE session_id = ? AND agent_name = ?
            ''', (session_id, agent_name))
            
            count = cursor.fetchone()[0]
            
            if count > self.max_entries:
                # Удаляем самые старые записи, оставляя только max_entries
                cursor.execute('''
                    DELETE FROM memory_entries 
                    WHERE session_id = ? AND agent_name = ? 
                    AND id NOT IN (
                        SELECT id FROM memory_entries 
                        WHERE session_id = ? AND agent_name = ? 
                        ORDER BY id DESC 
                        LIMIT ?
                    )
                ''', (session_id, agent_name, session_id, agent_name, self.max_entries))
            
            conn.commit()
        except Exception as e:
            print(f"Error adding message to memory: {e}")
        finally:
            conn.close()
    
    def get_messages(self, session_id: str, agent_name: str) -> List[str]:
        """
        Получает все сообщения для агента в сессии, отсортированные по времени.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT message FROM memory_entries
                WHERE session_id = ? AND agent_name = ?
                ORDER BY id ASC
            ''', (session_id, agent_name))
            
            rows = cursor.fetchall()
            messages = [row[0] for row in rows]
            return messages
        except Exception as e:
            print(f"Error getting messages from memory: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_agent_messages(self, session_id: str, agent_name: str) -> List[str]:
        """
        Получает все сообщения для конкретного агента в сессии с ограничением FIFO.
        """
        messages = self.get_messages(session_id, agent_name)
        return messages[-self.max_entries:]  # Уже ограничено на уровне базы, но дополнительная гарантия
    
    def ensure_memory_limit(self, session_id: str, agent_name: str) -> None:
        """
        Обеспечивает ограничение на количество записей в памяти для агента.
        """
        # Это происходит автоматически при добавлении сообщений, но можно вызвать явно
        # для принудительной чистки, если нужно.
        pass
    
    def create_user(self, user_id: str, metadata: Optional[dict] = None) -> None:
        """
        Создание пользователя (не используется в текущей реализации, но для совместимости).
        """
        # В данной реализации создание пользователей не требуется
        pass
    
    def get_sessions_for_user(self, user_id: str) -> List[str]:
        """
        Получить все сессии для пользователя (не используется в текущей реализации).
        """
        # В данной реализации это не требуется
        return []


# Алиас для совместимости с существующим кодом
ZepMemoryManager = RealZepMemoryManager