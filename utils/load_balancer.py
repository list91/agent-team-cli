from typing import Dict, List, Any, Tuple
from collections import defaultdict
import time
from datetime import datetime, timedelta

class LoadBalancer:
    """
    Система балансировки нагрузки для распределения задач между агентами
    """
    
    def __init__(self):
        self.agent_workloads = defaultdict(list)  # Список задач для каждого агента
        self.agent_performance = defaultdict(list)  # История производительности агентов
        self.task_complexity = {}  # Оценка сложности задач
        self.agent_capabilities = {}  # Способности агентов
        
        # Инициализируем базовые способности агентов
        self._initialize_agent_capabilities()
    
    def _initialize_agent_capabilities(self):
        """
        Инициализировать базовые способности агентов
        """
        self.agent_capabilities = {
            'researcher': {
                'task_types': ['research', 'analysis', 'study', 'investigation'],
                'max_concurrent': 5,
                'complexity_preference': 'high',
                'processing_speed': 0.8  # Относительная скорость обработки
            },
            'backend_dev': {
                'task_types': ['coding', 'implementation', 'backend', 'api'],
                'max_concurrent': 3,
                'complexity_preference': 'medium',
                'processing_speed': 1.0
            },
            'frontend_dev': {
                'task_types': ['ui', 'frontend', 'design', 'interface'],
                'max_concurrent': 3,
                'complexity_preference': 'medium',
                'processing_speed': 1.0
            },
            'doc_writer': {
                'task_types': ['documentation', 'writing', 'manual', 'guide'],
                'max_concurrent': 4,
                'complexity_preference': 'low',
                'processing_speed': 1.2
            },
            'tester': {
                'task_types': ['testing', 'quality', 'verification', 'validation'],
                'max_concurrent': 4,
                'complexity_preference': 'medium',
                'processing_speed': 0.9
            },
            'devops': {
                'task_types': ['deployment', 'infrastructure', 'docker', 'ci/cd'],
                'max_concurrent': 2,
                'complexity_preference': 'high',
                'processing_speed': 0.7
            }
        }
    
    def assign_task_to_agent(self, task_description: str, available_agents: List[str],
                           session_id: str) -> str:
        """
        Назначить задачу агенту с учетом балансировки нагрузки
        """
        # Оцениваем сложность задачи
        task_complexity = self._assess_task_complexity(task_description)
        
        # Получаем текущую нагрузку на агентов
        current_workloads = self._get_current_workloads(available_agents)
        
        # Оцениваем пригодность каждого агента
        suitability_scores = {}
        
        for agent_type in available_agents:
            suitability = self._calculate_agent_suitability(
                agent_type, task_description, task_complexity, 
                current_workloads.get(agent_type, 0)
            )
            suitability_scores[agent_type] = suitability
        
        # Выбираем агента с наивысшей оценкой пригодности
        if suitability_scores:
            best_agent = max(suitability_scores, key=suitability_scores.get)
            
            # Регистрируем назначение задачи
            self._register_task_assignment(best_agent, task_description, task_complexity, session_id)
            
            return best_agent
        else:
            # Если нет подходящих агентов, выбираем первого доступного
            return available_agents[0] if available_agents else 'backend_dev'
    
    def _assess_task_complexity(self, task_description: str) -> float:
        """
        Оценить сложность задачи (0.0 - простая, 1.0 - сложная)
        """
        # Хэшируем описание задачи для кэширования
        task_hash = hash(task_description)
        if task_hash in self.task_complexity:
            return self.task_complexity[task_hash]
        
        # Анализируем сложность на основе ключевых слов
        complexity_indicators = {
            'high': ['complex', 'advanced', 'sophisticated', 'distributed', 'scalable', 
                    'concurrent', 'parallel', 'machine learning', 'neural network',
                    'algorithm', 'optimization', 'architecture'],
            'medium': ['implement', 'create', 'develop', 'build', 'integrate',
                      'configure', 'setup', 'deploy', 'automate'],
            'low': ['document', 'write', 'describe', 'explain', 'summarize',
                   'generate', 'list', 'compile', 'organize']
        }
        
        task_lower = task_description.lower()
        high_count = sum(1 for word in complexity_indicators['high'] if word in task_lower)
        medium_count = sum(1 for word in complexity_indicators['medium'] if word in task_lower)
        low_count = sum(1 for word in complexity_indicators['low'] if word in task_lower)
        
        # Вычисляем относительную сложность
        total_indicators = high_count + medium_count + low_count
        if total_indicators == 0:
            complexity = 0.5  # Средняя сложность по умолчанию
        else:
            # Взвешенная оценка сложности
            weighted_complexity = (
                high_count * 1.0 + 
                medium_count * 0.5 + 
                low_count * 0.2
            ) / total_indicators
            
            complexity = min(1.0, weighted_complexity)
        
        # Кэшируем оценку
        self.task_complexity[task_hash] = complexity
        return complexity
    
    def _get_current_workloads(self, available_agents: List[str]) -> Dict[str, int]:
        """
        Получить текущую нагрузку на доступных агентов
        """
        workloads = {}
        
        for agent_type in available_agents:
            # Считаем активные задачи (начатые в последние 24 часа)
            cutoff_time = datetime.now() - timedelta(hours=24)
            active_tasks = [
                task for task in self.agent_workloads[agent_type]
                if datetime.fromisoformat(task['assigned_at']) > cutoff_time
            ]
            workloads[agent_type] = len(active_tasks)
        
        return workloads
    
    def _calculate_agent_suitability(self, agent_type: str, task_description: str,
                                   task_complexity: float, current_workload: int) -> float:
        """
        Вычислить пригодность агента для задачи
        """
        # Получаем способности агента
        capabilities = self.agent_capabilities.get(agent_type, {})
        
        # Оцениваем совпадение по типу задачи
        task_type_match = self._assess_task_type_match(agent_type, task_description)
        
        # Оцениваем соответствие сложности
        complexity_match = self._assess_complexity_match(agent_type, task_complexity)
        
        # Оцениваем текущую нагрузку
        workload_factor = self._assess_workload_factor(agent_type, current_workload)
        
        # Оцениваем историческую производительность
        performance_factor = self._assess_performance_factor(agent_type)
        
        # Комбинируем все факторы (веса можно настраивать)
        suitability = (
            task_type_match * 0.4 +
            complexity_match * 0.3 +
            workload_factor * 0.2 +
            performance_factor * 0.1
        )
        
        return suitability
    
    def _assess_task_type_match(self, agent_type: str, task_description: str) -> float:
        """
        Оценить совпадение типа задачи с возможностями агента
        """
        capabilities = self.agent_capabilities.get(agent_type, {})
        task_types = capabilities.get('task_types', [])
        
        if not task_types:
            return 0.5  # Нейтральная оценка
        
        task_lower = task_description.lower()
        match_count = sum(1 for task_type in task_types if task_type in task_lower)
        
        return min(1.0, match_count / len(task_types))
    
    def _assess_complexity_match(self, agent_type: str, task_complexity: float) -> float:
        """
        Оценить соответствие сложности задачи предпочтениям агента
        """
        capabilities = self.agent_capabilities.get(agent_type, {})
        preference = capabilities.get('complexity_preference', 'medium')
        
        # Преобразуем предпочтение в числовую шкалу
        preference_map = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        preferred_complexity = preference_map.get(preference, 0.5)
        
        # Чем ближе сложность задачи к предпочтениям агента, тем лучше
        match_score = 1.0 - abs(task_complexity - preferred_complexity)
        return max(0.0, match_score)
    
    def _assess_workload_factor(self, agent_type: str, current_workload: int) -> float:
        """
        Оценить фактор текущей нагрузки
        """
        capabilities = self.agent_capabilities.get(agent_type, {})
        max_concurrent = capabilities.get('max_concurrent', 3)
        
        # Чем меньше текущая нагрузка по сравнению с максимальной, тем лучше
        if max_concurrent == 0:
            return 1.0
        
        workload_ratio = current_workload / max_concurrent
        workload_factor = max(0.0, 1.0 - workload_ratio)
        return workload_factor
    
    def _assess_performance_factor(self, agent_type: str) -> float:
        """
        Оценить историческую производительность агента
        """
        performance_history = self.agent_performance.get(agent_type, [])
        
        if not performance_history:
            return 1.0  # Нет данных - нейтральная оценка
        
        # Вычисляем среднюю производительность
        total_performance = sum(record['performance_score'] for record in performance_history)
        average_performance = total_performance / len(performance_history)
        
        # Нормализуем до шкалы 0-1
        return min(1.0, max(0.0, average_performance))
    
    def _register_task_assignment(self, agent_type: str, task_description: str,
                                 task_complexity: float, session_id: str):
        """
        Зарегистрировать назначение задачи агенту
        """
        task_record = {
            'task': task_description,
            'complexity': task_complexity,
            'assigned_at': datetime.now().isoformat(),
            'session_id': session_id,
            'status': 'assigned'
        }
        
        self.agent_workloads[agent_type].append(task_record)
    
    def update_agent_performance(self, agent_type: str, task_description: str,
                               performance_score: float, completion_time: float):
        """
        Обновить историю производительности агента
        """
        performance_record = {
            'task': task_description,
            'performance_score': performance_score,
            'completion_time': completion_time,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.agent_performance[agent_type].append(performance_record)
        
        # Ограничиваем историю последними 100 записями для каждого агента
        if len(self.agent_performance[agent_type]) > 100:
            self.agent_performance[agent_type] = self.agent_performance[agent_type][-100:]
    
    def rebalance_workloads(self, available_agents: List[str]) -> Dict[str, List[str]]:
        """
        Перебалансировать нагрузку между агентами
        """
        # Получаем текущие нагрузки
        current_workloads = self._get_current_workloads(available_agents)
        
        # Находим агентов с наименьшей и наибольшей нагрузкой
        if not current_workloads:
            return {}
        
        min_load_agent = min(current_workloads, key=current_workloads.get)
        max_load_agent = max(current_workloads, key=current_workloads.get)
        
        min_load = current_workloads[min_load_agent]
        max_load = current_workloads[max_load_agent]
        
        # Если разница в нагрузке значительная, переназначаем задачи
        if max_load - min_load > 2:
            # Переназначаем одну задачу от перегруженного агента к свободному
            if self.agent_workloads[max_load_agent]:
                # Берем самую простую задачу для переназначения
                task_to_reassign = min(
                    self.agent_workloads[max_load_agent],
                    key=lambda x: x.get('complexity', 0.5)
                )
                
                # Удаляем задачу из перегруженного агента
                self.agent_workloads[max_load_agent].remove(task_to_reassign)
                
                # Назначаем задачу свободному агенту
                self.agent_workloads[min_load_agent].append(task_to_reassign)
                
                return {
                    'reassigned': [task_to_reassign['task']],
                    'from_agent': max_load_agent,
                    'to_agent': min_load_agent
                }
        
        return {'reassigned': [], 'from_agent': None, 'to_agent': None}
    
    def get_load_balancing_report(self) -> Dict[str, Any]:
        """
        Получить отчет о балансировке нагрузки
        """
        current_workloads = self._get_current_workloads(list(self.agent_capabilities.keys()))
        
        total_tasks = sum(current_workloads.values())
        agent_count = len(current_workloads)
        
        if agent_count == 0:
            avg_load = 0
        else:
            avg_load = total_tasks / agent_count
        
        # Вычисляем дисбаланс (стандартное отклонение от среднего)
        if total_tasks > 0:
            variance = sum((load - avg_load) ** 2 for load in current_workloads.values()) / agent_count
            imbalance = variance ** 0.5
        else:
            imbalance = 0
        
        return {
            'current_workloads': dict(current_workloads),
            'total_tasks': total_tasks,
            'average_load_per_agent': avg_load,
            'imbalance_measure': imbalance,
            'needs_rebalancing': imbalance > 1.5,  # Порог для перебалансировки
            'agent_count': agent_count
        }

# Глобальная система балансировки нагрузки
load_balancer = LoadBalancer()