import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

class CompetencyMatrix:
    """
    Динамическая матрица компетенций для оценки соответствия задач агентам
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
            max_features=1000
        )
        self.agent_profiles = {}  # Профили компетенций агентов
        self.task_vectors = {}     # Векторы задач
        self.fit_initialized = False
    
    def add_agent_profile(self, agent_type: str, competencies: List[str]):
        """
        Добавить профиль компетенций агента
        """
        # Объединяем все компетенции в одно текстовое описание
        competency_text = " ".join(competencies)
        self.agent_profiles[agent_type] = {
            'competencies': competencies,
            'text': competency_text,
            'tasks_completed': []  # Для обучения
        }
    
    def fit_vectorizer(self):
        """
        Обучить векторизатор на доступных данных
        """
        if not self.agent_profiles:
            return
            
        # Собираем все тексты для обучения
        texts = [profile['text'] for profile in self.agent_profiles.values()]
        
        # Добавляем примеры задач для лучшего обучения
        task_texts = list(self.task_vectors.values())
        texts.extend(task_texts)
        
        if texts:
            self.vectorizer.fit(texts)
            self.fit_initialized = True
    
    def get_agent_competency_vector(self, agent_type: str) -> np.ndarray:
        """
        Получить вектор компетенций агента
        """
        if not self.fit_initialized:
            self.fit_vectorizer()
            
        if agent_type not in self.agent_profiles:
            # Создаем временный профиль
            dummy_profile = "general task processing"
            if not self.fit_initialized:
                return np.zeros((1, 1000))  # Размер по умолчанию
            return self.vectorizer.transform([dummy_profile])
            
        profile = self.agent_profiles[agent_type]
        if not self.fit_initialized:
            return np.zeros((1, 1000))
        return self.vectorizer.transform([profile['text']])
    
    def get_task_similarity_scores(self, task_description: str, available_agents: List[str]) -> Dict[str, float]:
        """
        Получить оценки схожести задачи с компетенциями агентов
        """
        if not self.fit_initialized:
            self.fit_vectorizer()
            
        # Векторизуем задачу
        task_vector = self.vectorizer.transform([task_description])
        
        scores = {}
        for agent_type in available_agents:
            if agent_type in self.agent_profiles:
                agent_vector = self.get_agent_competency_vector(agent_type)
                similarity = cosine_similarity(task_vector, agent_vector)[0][0]
                scores[agent_type] = float(similarity)
            else:
                # Для неизвестных агентов используем минимальную оценку
                scores[agent_type] = 0.0
                
        return scores
    
    def find_best_agent(self, task_description: str, available_agents: List[str], 
                       already_assigned: List[str] = None) -> Tuple[str, float]:
        """
        Найти лучшего агента для задачи с оценкой уверенности
        """
        if already_assigned is None:
            already_assigned = []
            
        scores = self.get_task_similarity_scores(task_description, available_agents)
        
        # Фильтруем уже назначенные агенты
        filtered_scores = {agent: score for agent, score in scores.items() 
                          if agent not in already_assigned}
        
        if not filtered_scores:
            # Если все агенты заняты, возвращаем первого доступного
            for agent in available_agents:
                if agent not in already_assigned:
                    return agent, 0.0
            return available_agents[0] if available_agents else ('backend_dev', 0.0)
        
        # Находим агента с наивысшей оценкой
        best_agent = max(filtered_scores, key=filtered_scores.get)
        best_score = filtered_scores[best_agent]
        
        return best_agent, best_score
    
    def update_agent_performance(self, agent_type: str, task_description: str, success: bool):
        """
        Обновить профиль агента на основе выполнения задачи
        """
        if agent_type in self.agent_profiles:
            self.agent_profiles[agent_type]['tasks_completed'].append({
                'task': task_description,
                'success': success
            })
            
            # Переобучаем векторизатор при необходимости
            if len(self.agent_profiles[agent_type]['tasks_completed']) % 10 == 0:
                self.fit_vectorizer()

# Глобальная матрица компетенций
competency_matrix = CompetencyMatrix()

# Инициализируем базовые профили компетенций
initial_profiles = {
    'researcher': [
        'research', 'study', 'analyze', 'examine', 'investigate', 'evaluate', 
        'gather information', 'best practices', 'find', 'explore', 'literature review',
        'data collection', 'survey', 'market analysis', 'competitive analysis'
    ],
    'backend_dev': [
        'backend', 'server', 'api', 'flask', 'django', 'programming', 'code', 
        'implementation', 'server-side', 'database', 'rest api', 'microservices',
        'sql', 'nosql', 'authentication', 'authorization', 'performance optimization'
    ],
    'frontend_dev': [
        'frontend', 'ui', 'react', 'vue', 'html', 'css', 'client-side', 
        'interface', 'javascript', 'typescript', 'responsive design', 'user experience',
        'component library', 'state management', 'styling', 'accessibility'
    ],
    'doc_writer': [
        'document', 'documentation', 'write', 'manual', 'guide', 'readme', 
        'usage', 'describe', 'explain', 'technical writing', 'user manual',
        'api documentation', 'tutorial', 'getting started', 'faq'
    ],
    'tester': [
        'test', 'testing', 'unit test', 'integration test', 'quality', 
        'checker', 'verify', 'validate', 'automation', 'regression testing',
        'performance testing', 'security testing', 'test coverage', 'bug report'
    ],
    'devops': [
        'docker', 'deploy', 'pipeline', 'ci/cd', 'infrastructure', 'kubernetes', 
        'dockerfile', 'install', 'setup', 'monitoring', 'logging', 'containerization',
        'orchestration', 'cloud deployment', 'scaling', 'backup'
    ]
}

# Загружаем начальные профили
for agent_type, competencies in initial_profiles.items():
    competency_matrix.add_agent_profile(agent_type, competencies)

# Обучаем векторизатор
competency_matrix.fit_vectorizer()