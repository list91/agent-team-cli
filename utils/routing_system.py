from typing import Dict, List, Any, Tuple, Optional
from utils.competency_matrix import competency_matrix
import re

class SpecializedRoutingSystem:
    """
    Система специализированной маршрутизации задач к соответствующим агентам
    """
    
    def __init__(self):
        self.routing_rules = {}
        self.task_classifiers = {}
        self.routing_history = {}
        
        # Инициализируем базовые правила маршрутизации
        self._initialize_routing_rules()
    
    def _initialize_routing_rules(self):
        """
        Инициализировать базовые правила маршрутизации
        """
        self.routing_rules = {
            'code_generation': {
                'patterns': [
                    r'implement', r'create.*code', r'write.*function', 
                    r'develop.*api', r'build.*backend', r'program'
                ],
                'preferred_agents': ['backend_dev', 'frontend_dev'],
                'required_skills': ['programming', 'implementation', 'coding']
            },
            'documentation': {
                'patterns': [
                    r'document', r'write.*manual', r'create.*guide', 
                    r'make.*readme', r'generate.*documentation'
                ],
                'preferred_agents': ['doc_writer'],
                'required_skills': ['writing', 'documentation', 'explanation']
            },
            'testing': {
                'patterns': [
                    r'test', r'create.*test', r'write.*unit.*test',
                    r'verify', r'validate', r'quality.*check'
                ],
                'preferred_agents': ['tester'],
                'required_skills': ['testing', 'verification', 'quality']
            },
            'research': {
                'patterns': [
                    r'research', r'study', r'analyze', r'investigate',
                    r'best.*practices', r'gather.*information'
                ],
                'preferred_agents': ['researcher'],
                'required_skills': ['research', 'analysis', 'investigation']
            },
            'devops': {
                'patterns': [
                    r'docker', r'deploy', r'pipeline', r'ci/cd',
                    r'infrastructure', r'kubernetes', r'container'
                ],
                'preferred_agents': ['devops'],
                'required_skills': ['deployment', 'infrastructure', 'devops']
            },
            'refactoring': {
                'patterns': [
                    r'refactor', r'improve.*code', r'optimize.*performance',
                    r'clean.*code', r'restructure'
                ],
                'preferred_agents': ['backend_dev', 'frontend_dev'],
                'required_skills': ['refactoring', 'optimization', 'improvement']
            },
            'security': {
                'patterns': [
                    r'security', r'encrypt', r'protect', r'vulnerability',
                    r'audit', r'safe'
                ],
                'preferred_agents': ['backend_dev', 'devops'],
                'required_skills': ['security', 'encryption', 'protection']
            }
        }
        
        # Инициализируем классификаторы задач
        self._initialize_task_classifiers()
    
    def _initialize_task_classifiers(self):
        """
        Инициализировать классификаторы задач
        """
        # Классификатор по типу задачи
        self.task_classifiers['task_type'] = {
            'implementation': ['implement', 'create', 'build', 'develop', 'write'],
            'documentation': ['document', 'write', 'create.*guide', 'manual'],
            'testing': ['test', 'verify', 'validate', 'check'],
            'research': ['research', 'study', 'analyze', 'investigate'],
            'deployment': ['deploy', 'setup', 'install', 'configure'],
            'optimization': ['optimize', 'improve', 'refactor', 'enhance'],
            'security': ['secure', 'encrypt', 'protect', 'audit']
        }
        
        # Классификатор по технологии
        self.task_classifiers['technology'] = {
            'python': ['python', 'flask', 'django', 'fastapi'],
            'javascript': ['javascript', 'react', 'vue', 'node'],
            'database': ['database', 'sql', 'postgres', 'mysql'],
            'docker': ['docker', 'container', 'image'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud'],
            'api': ['api', 'rest', 'graphql', 'endpoint']
        }
    
    def classify_task(self, task_description: str) -> Dict[str, Any]:
        """
        Классифицировать задачу по типу и технологиям
        """
        classification = {
            'task_types': [],
            'technologies': [],
            'complexity': 'medium',
            'priority': 'normal'
        }
        
        task_lower = task_description.lower()
        
        # Классификация по типу задачи
        for task_type, patterns in self.task_classifiers['task_type'].items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    classification['task_types'].append(task_type)
        
        # Классификация по технологиям
        for tech, patterns in self.task_classifiers['technology'].items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    classification['technologies'].append(tech)
        
        # Оценка сложности
        classification['complexity'] = self._assess_task_complexity(task_description)
        
        # Оценка приоритета
        classification['priority'] = self._assess_task_priority(task_description)
        
        return classification
    
    def _assess_task_complexity(self, task_description: str) -> str:
        """
        Оценить сложность задачи
        """
        task_lower = task_description.lower()
        
        # Сложные задачи
        complex_indicators = [
            'complex', 'advanced', 'sophisticated', 'distributed', 'scalable',
            'concurrent', 'parallel', 'machine learning', 'neural network',
            'algorithm', 'optimization', 'architecture', 'framework'
        ]
        
        # Простые задачи
        simple_indicators = [
            'document', 'write', 'describe', 'explain', 'summarize',
            'generate', 'list', 'compile', 'organize'
        ]
        
        complex_count = sum(1 for indicator in complex_indicators if indicator in task_lower)
        simple_count = sum(1 for indicator in simple_indicators if indicator in task_lower)
        
        if complex_count > simple_count:
            return 'high'
        elif simple_count > complex_count:
            return 'low'
        else:
            return 'medium'
    
    def _assess_task_priority(self, task_description: str) -> str:
        """
        Оценить приоритет задачи
        """
        task_lower = task_description.lower()
        
        # Высокий приоритет
        high_priority_indicators = [
            'critical', 'urgent', 'asap', 'immediately', 'emergency',
            'blocking', 'essential', 'must have'
        ]
        
        # Низкий приоритет
        low_priority_indicators = [
            'nice to have', 'optional', 'whenever possible', 'low priority',
            'later', 'eventually'
        ]
        
        high_count = sum(1 for indicator in high_priority_indicators if indicator in task_lower)
        low_count = sum(1 for indicator in low_priority_indicators if indicator in task_lower)
        
        if high_count > 0:
            return 'high'
        elif low_count > 0:
            return 'low'
        else:
            return 'normal'
    
    def route_task(self, task_description: str, available_agents: List[str],
                   session_id: str) -> str:
        """
        Маршрутизировать задачу к наиболее подходящему агенту
        """
        # Классифицируем задачу
        classification = self.classify_task(task_description)
        
        # Определяем маршрут
        route = self._determine_route(task_description, classification, available_agents)
        
        # Регистрируем маршрутизацию
        self._register_routing(task_description, route, classification, session_id)
        
        return route['agent']
    
    def _determine_route(self, task_description: str, classification: Dict[str, Any],
                        available_agents: List[str]) -> Dict[str, Any]:
        """
        Определить маршрут задачи
        """
        # Сначала пытаемся найти точное совпадение по правилам маршрутизации
        best_match = self._find_rule_based_match(task_description, available_agents)
        if best_match:
            return best_match
        
        # Если нет точного совпадения, используем классификацию и компетентность
        return self._find_competency_based_match(task_description, classification, available_agents)
    
    def _find_rule_based_match(self, task_description: str, 
                              available_agents: List[str]) -> Optional[Dict[str, Any]]:
        """
        Найти совпадение по правилам маршрутизации
        """
        task_lower = task_description.lower()
        
        best_rule = None
        best_score = 0
        
        # Ищем лучшее правило маршрутизации
        for rule_name, rule in self.routing_rules.items():
            score = 0
            for pattern in rule['patterns']:
                if re.search(pattern, task_lower):
                    score += 1
            
            if score > best_score:
                best_score = score
                best_rule = rule_name
        
        if best_rule and best_rule in self.routing_rules:
            rule = self.routing_rules[best_rule]
            preferred_agents = rule['preferred_agents']
            
            # Ищем доступного предпочтительного агента
            for agent in preferred_agents:
                if agent in available_agents:
                    return {
                        'agent': agent,
                        'route_type': 'rule_based',
                        'rule_used': best_rule,
                        'confidence': min(1.0, best_score / len(rule['patterns']))
                    }
        
        return None
    
    def _find_competency_based_match(self, task_description: str, 
                                   classification: Dict[str, Any],
                                   available_agents: List[str]) -> Dict[str, Any]:
        """
        Найти совпадение на основе компетентности агентов
        """
        # Используем матрицу компетенций для оценки соответствия
        competency_scores = competency_matrix.get_task_similarity_scores(
            task_description, available_agents
        )
        
        if not competency_scores:
            # Если нет оценок, используем первый доступный агент
            return {
                'agent': available_agents[0] if available_agents else 'backend_dev',
                'route_type': 'fallback',
                'confidence': 0.5
            }
        
        # Находим агента с наивысшей оценкой компетентности
        best_agent = max(competency_scores, key=competency_scores.get)
        best_score = competency_scores[best_agent]
        
        return {
            'agent': best_agent,
            'route_type': 'competency_based',
            'confidence': best_score,
            'classification': classification
        }
    
    def _register_routing(self, task_description: str, route: Dict[str, Any],
                         classification: Dict[str, Any], session_id: str):
        """
        Зарегистрировать маршрутизацию задачи
        """
        routing_record = {
            'task': task_description,
            'route': route,
            'classification': classification,
            'session_id': session_id,
            'timestamp': self._get_current_timestamp()
        }
        
        task_hash = hash(task_description)
        self.routing_history[task_hash] = routing_record
    
    def _get_current_timestamp(self) -> str:
        """
        Получить текущую временную метку
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику маршрутизации
        """
        if not self.routing_history:
            return {'total_routed': 0, 'by_route_type': {}, 'agent_distribution': {}}
        
        route_types = {}
        agent_distribution = {}
        
        for record in self.routing_history.values():
            route_info = record['route']
            route_type = route_info.get('route_type', 'unknown')
            agent = route_info.get('agent', 'unknown')
            
            route_types[route_type] = route_types.get(route_type, 0) + 1
            agent_distribution[agent] = agent_distribution.get(agent, 0) + 1
        
        return {
            'total_routed': len(self.routing_history),
            'by_route_type': route_types,
            'agent_distribution': agent_distribution,
            'success_rate_estimation': self._estimate_success_rate()
        }
    
    def _estimate_success_rate(self) -> float:
        """
        Оценить общий уровень успеха маршрутизации (заглушка)
        """
        # В реальной системе это будет основано на обратной связи
        return 0.85  # Предполагаем 85% успешных маршрутов
    
    def update_routing_rules(self, new_rules: Dict[str, Any]):
        """
        Обновить правила маршрутизации
        """
        self.routing_rules.update(new_rules)
        # В реальной системе здесь была бы логика сохранения правил
    
    def get_optimal_agent_for_task(self, task_description: str, 
                                  available_agents: List[str]) -> Tuple[str, float]:
        """
        Получить оптимального агента для задачи с оценкой уверенности
        """
        route = self._determine_route(
            task_description, 
            self.classify_task(task_description), 
            available_agents
        )
        
        return route['agent'], route.get('confidence', 0.5)

# Глобальная система маршрутизации
routing_system = SpecializedRoutingSystem()