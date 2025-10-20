from typing import Dict, Any, List
import re
import json

class AgentSpecializationValidator:
    """
    Валидатор специализации агентов, обеспечивающий строгое соответствие задач и специализаций
    """
    
    def __init__(self):
        # Словарь ключевых терминов для каждой специализации
        # Значения будут обновляться динамически
        self.specialization_keywords = {
            'researcher': ['research', 'study', 'analyze', 'examine', 'investigate', 'evaluate', 'gather information', 'best practices', 'find', 'explore'],
            'backend_dev': ['backend', 'server', 'api', 'flask', 'django', 'programming', 'code', 'implementation', 'backend', 'server-side'],
            'frontend_dev': ['frontend', 'ui', 'react', 'vue', 'html', 'css', 'client-side', 'interface', 'frontend'],
            'doc_writer': ['document', 'documentation', 'write', 'manual', 'guide', 'readme', 'usage', 'describe', 'explain'],
            'tester': ['test', 'testing', 'unit test', 'integration test', 'quality', 'checker', 'verify', 'validate', 'coverage'],
            'devops': ['docker', 'deploy', 'pipeline', 'ci/cd', 'infrastructure', 'kubernetes', 'dockerfile', 'install', 'setup', 'monitoring']
        }
    
    def set_specialization_keywords(self, new_keywords: Dict[str, List[str]]):
        """
        Обновление ключевых слов для специализаций (универсальный метод)
        """
        self.specialization_keywords = new_keywords
    
    def validate_task_assignment(self, agent_type: str, task_description: str) -> bool:
        """
        Валидация, соответствует ли задача специализации агента
        """
        if agent_type not in self.specialization_keywords:
            return False
        
        task_lower = task_description.lower()
        keywords = self.specialization_keywords[agent_type]
        
        # Проверяем наличие хотя бы одного ключевого слова в описании задачи
        for keyword in keywords:
            if keyword.lower() in task_lower:
                return True
        
        return False
    
    def find_appropriate_agent(self, task_description: str, available_agents: List[str], already_assigned: List[str] = None) -> str:
        """
        Найти наиболее подходящего агента для задачи с улучшенным алгоритмом
        """
        if already_assigned is None:
            already_assigned = []
        
        task_lower = task_description.lower()
        
        best_agent = None
        best_score = 0
        
        for agent_type in available_agents:
            if agent_type not in self.specialization_keywords or agent_type in already_assigned:
                continue
                
            score = 0
            # Подсчет очков на основе ключевых слов
            for keyword in self.specialization_keywords[agent_type]:
                keyword_lower = keyword.lower()
                # Учет вхождений ключевого слова (чем больше вхождений, тем выше оценка)
                count = task_lower.count(keyword_lower)
                if count > 0:
                    # Добавляем вес, зависящий от длины ключевого слова (более конкретные термины имеют больший вес)
                    score += count * len(keyword_lower)
            
            # Проверяем совпадение по фразам (а не только отдельным словам)
            phrase_matches = self._calculate_phrase_match_score(task_lower, self.specialization_keywords[agent_type])
            score += phrase_matches
            
            if score > best_score:
                best_score = score
                best_agent = agent_type
        
        # Если не найден подходящий агент, который не занят, то возвращаем первого доступного
        if best_agent is None and already_assigned:
            for agent_type in available_agents:
                if agent_type not in already_assigned:
                    return agent_type
        
        return best_agent or available_agents[0] if available_agents else None  # возврат запасного варианта

    def _calculate_phrase_match_score(self, task_lower: str, keywords: List[str]) -> int:
        """
        Вычисляет дополнительные баллы за совпадение по фразам
        """
        score = 0
        for keyword in keywords:
            # Проверяем, является ли ключевое слово частью фразы в задаче
            if len(keyword.split()) > 1:  # Это фраза, а не одиночное слово
                if keyword.lower() in task_lower:
                    score += len(keyword) * 2  # Более высокий вес для фраз
        return score

# Глобальный экземпляр валидатора
validator = AgentSpecializationValidator()