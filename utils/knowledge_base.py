from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import sqlite3
import os

class KnowledgeBase:
    """
    База знаний системы с использованием SQLite для хранения знаний агентов
    """
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """
        Инициализировать базу данных знаний
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицы для хранения знаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_type TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                embedding BLOB  -- Для хранения векторных представлений знаний
            )
        ''')
        
        # Создаем таблицу для хранения паттернов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                last_seen TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Создаем таблицу для хранения метрик производительности
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Создаем индексы для быстрого поиска
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_knowledge_agent_session 
            ON knowledge_entries (agent_type, session_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patterns_agent_type 
            ON pattern_entries (agent_type, pattern_type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_performance_agent_metric 
            ON performance_metrics (agent_type, metric_name)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_knowledge(self, knowledge_type: str, agent_type: str, 
                     session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Добавить знание в базу знаний
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO knowledge_entries 
                (knowledge_type, agent_type, session_id, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_type,
                agent_type,
                session_id,
                content,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error adding knowledge to database: {e}")
        finally:
            conn.close()
    
    def get_knowledge(self, knowledge_type: str, agent_type: str, 
                     session_id: str) -> List[Dict[str, Any]]:
        """
        Получить знания из базы знаний
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT knowledge_type, agent_type, session_id, content, timestamp, metadata
                FROM knowledge_entries
                WHERE knowledge_type = ? AND agent_type = ? AND session_id = ?
                ORDER BY timestamp DESC
            ''', (knowledge_type, agent_type, session_id))
            
            rows = cursor.fetchall()
            knowledge_entries = []
            
            for row in rows:
                knowledge_entries.append({
                    'knowledge_type': row[0],
                    'agent_type': row[1],
                    'session_id': row[2],
                    'content': row[3],
                    'timestamp': row[4],
                    'metadata': json.loads(row[5]) if row[5] else None
                })
            
            return knowledge_entries
        except Exception as e:
            print(f"Error getting knowledge from database: {e}")
            return []
        finally:
            conn.close()
    
    def add_pattern(self, pattern_type: str, pattern_description: str, 
                   agent_type: str, success: bool = True, 
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Добавить паттерн в базу паттернов
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Проверяем, существует ли уже такой паттерн
            cursor.execute('''
                SELECT id, frequency, success_rate FROM pattern_entries
                WHERE pattern_type = ? AND pattern_description = ? AND agent_type = ?
            ''', (pattern_type, pattern_description, agent_type))
            
            existing_pattern = cursor.fetchone()
            
            if existing_pattern:
                # Обновляем существующий паттерн
                pattern_id, frequency, success_rate = existing_pattern
                new_frequency = frequency + 1
                new_success_rate = ((success_rate * frequency) + (1 if success else 0)) / new_frequency
                
                cursor.execute('''
                    UPDATE pattern_entries
                    SET frequency = ?, success_rate = ?, last_seen = ?
                    WHERE id = ?
                ''', (new_frequency, new_success_rate, datetime.now().isoformat(), pattern_id))
            else:
                # Создаем новый паттерн
                success_rate = 1.0 if success else 0.0
                cursor.execute('''
                    INSERT INTO pattern_entries 
                    (pattern_type, pattern_description, agent_type, frequency, success_rate, last_seen, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern_type,
                    pattern_description,
                    agent_type,
                    1,
                    success_rate,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None
                ))
            
            conn.commit()
        except Exception as e:
            print(f"Error adding pattern to database: {e}")
        finally:
            conn.close()
    
    def get_patterns(self, pattern_type: str = None, agent_type: str = None) -> List[Dict[str, Any]]:
        """
        Получить паттерны из базы паттернов
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Формируем запрос с учетом фильтров
            query = "SELECT pattern_type, pattern_description, agent_type, frequency, success_rate, last_seen, metadata FROM pattern_entries"
            params = []
            
            if pattern_type or agent_type:
                query += " WHERE"
                conditions = []
                
                if pattern_type:
                    conditions.append("pattern_type = ?")
                    params.append(pattern_type)
                
                if agent_type:
                    conditions.append("agent_type = ?")
                    params.append(agent_type)
                
                query += " AND ".join(conditions)
            
            query += " ORDER BY success_rate DESC, frequency DESC"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            pattern_entries = []
            
            for row in rows:
                pattern_entries.append({
                    'pattern_type': row[0],
                    'pattern_description': row[1],
                    'agent_type': row[2],
                    'frequency': row[3],
                    'success_rate': row[4],
                    'last_seen': row[5],
                    'metadata': json.loads(row[6]) if row[6] else None
                })
            
            return pattern_entries
        except Exception as e:
            print(f"Error getting patterns from database: {e}")
            return []
        finally:
            conn.close()
    
    def add_performance_metric(self, agent_type: str, session_id: str, 
                             metric_name: str, metric_value: float, 
                             metadata: Optional[Dict[str, Any]] = None):
        """
        Добавить метрику производительности в базу метрик
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO performance_metrics 
                (agent_type, session_id, metric_name, metric_value, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                agent_type,
                session_id,
                metric_name,
                metric_value,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error adding performance metric to database: {e}")
        finally:
            conn.close()
    
    def get_performance_metrics(self, agent_type: str = None, 
                              metric_name: str = None) -> List[Dict[str, Any]]:
        """
        Получить метрики производительности из базы метрик
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Формируем запрос с учетом фильтров
            query = "SELECT agent_type, session_id, metric_name, metric_value, timestamp, metadata FROM performance_metrics"
            params = []
            
            if agent_type or metric_name:
                query += " WHERE"
                conditions = []
                
                if agent_type:
                    conditions.append("agent_type = ?")
                    params.append(agent_type)
                
                if metric_name:
                    conditions.append("metric_name = ?")
                    params.append(metric_name)
                
                query += " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            metric_entries = []
            
            for row in rows:
                metric_entries.append({
                    'agent_type': row[0],
                    'session_id': row[1],
                    'metric_name': row[2],
                    'metric_value': row[3],
                    'timestamp': row[4],
                    'metadata': json.loads(row[5]) if row[5] else None
                })
            
            return metric_entries
        except Exception as e:
            print(f"Error getting performance metrics from database: {e}")
            return []
        finally:
            conn.close()
    
    def get_agent_performance_summary(self, agent_type: str) -> Dict[str, Any]:
        """
        Получить сводку по производительности агента
        """
        metrics = self.get_performance_metrics(agent_type=agent_type)
        
        if not metrics:
            return {
                'agent_type': agent_type,
                'total_metrics': 0,
                'average_performance': 0.0,
                'best_metric': None,
                'worst_metric': None
            }
        
        # Группируем метрики по имени
        metric_groups = {}
        for metric in metrics:
            name = metric['metric_name']
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(metric['metric_value'])
        
        # Вычисляем средние значения для каждой метрики
        averages = {}
        for name, values in metric_groups.items():
            averages[name] = sum(values) / len(values)
        
        # Находим лучшую и худшую метрики
        best_metric = max(averages.items(), key=lambda x: x[1]) if averages else None
        worst_metric = min(averages.items(), key=lambda x: x[1]) if averages else None
        
        # Вычисляем общую среднюю производительность
        overall_average = sum(averages.values()) / len(averages) if averages else 0.0
        
        return {
            'agent_type': agent_type,
            'total_metrics': len(metrics),
            'average_performance': overall_average,
            'best_metric': best_metric,
            'worst_metric': worst_metric,
            'metric_averages': averages
        }
    
    def get_pattern_recommendations(self, agent_type: str, task_description: str) -> List[Dict[str, Any]]:
        """
        Получить рекомендации паттернов для агента и задачи
        """
        # Получаем все паттерны для данного типа агента
        patterns = self.get_patterns(agent_type=agent_type)
        
        # Фильтруем паттерны по релевантности задаче
        relevant_patterns = []
        task_lower = task_description.lower()
        
        for pattern in patterns:
            pattern_desc = pattern['pattern_description'].lower()
            # Простая проверка на релевантность
            if any(word in task_lower for word in pattern_desc.split()):
                relevant_patterns.append(pattern)
        
        # Сортируем по успешности и частоте
        relevant_patterns.sort(key=lambda x: (x['success_rate'], x['frequency']), reverse=True)
        
        return relevant_patterns[:5]  # Возвращаем топ-5 паттернов
    
    def initialize_knowledge(self):
        """
        Инициализировать базу знаний начальными данными
        """
        # Добавляем базовые паттерны
        base_patterns = [
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'research task delegation',
                'agent_type': 'researcher',
                'success': True
            },
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'backend development task delegation',
                'agent_type': 'backend_dev',
                'success': True
            },
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'frontend development task delegation',
                'agent_type': 'frontend_dev',
                'success': True
            },
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'documentation task delegation',
                'agent_type': 'doc_writer',
                'success': True
            },
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'testing task delegation',
                'agent_type': 'tester',
                'success': True
            },
            {
                'pattern_type': 'task_delegation',
                'pattern_description': 'devops task delegation',
                'agent_type': 'devops',
                'success': True
            }
        ]
        
        for pattern in base_patterns:
            self.add_pattern(
                pattern['pattern_type'],
                pattern['pattern_description'],
                pattern['agent_type'],
                pattern['success']
            )
    
    def update_knowledge(self, interaction_data: Dict[str, Any], 
                        learning_outcome: Dict[str, Any]):
        """
        Обновить знания на основе взаимодействия
        """
        # Добавляем знания о взаимодействии
        self.add_knowledge(
            'interaction',
            'system',
            interaction_data.get('session_id', 'unknown'),
            json.dumps(interaction_data),
            {
                'outcome': learning_outcome,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Добавляем паттерны из результата обучения
        if 'patterns_found' in learning_outcome:
            for pattern in learning_outcome['patterns_found']:
                self.add_pattern(
                    pattern.get('pattern_type', 'unknown'),
                    pattern.get('value', 'unknown'),
                    pattern.get('agent_type', 'system'),
                    pattern.get('success', True),
                    pattern.get('metadata', {})
                )
        
        # Добавляем метрики производительности
        if 'performance_metrics' in learning_outcome:
            for metric in learning_outcome['performance_metrics']:
                self.add_performance_metric(
                    metric.get('agent_type', 'system'),
                    metric.get('session_id', 'unknown'),
                    metric.get('metric_name', 'unknown'),
                    metric.get('metric_value', 0.0),
                    metric.get('metadata', {})
                )

# Глобальная база знаний
knowledge_base = KnowledgeBase()