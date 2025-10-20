from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
import pickle
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib

class SelfLearningArchitecture:
    """
    Самообучающаяся архитектура системы агентов
    """
    
    def __init__(self):
        self.learning_history = []
        self.pattern_recognition = PatternRecognitionEngine()
        self.adaptation_engine = AdaptationEngine()
        self.performance_analyzer = PerformanceAnalyzer()
        self.knowledge_base = KnowledgeBase()
        
        # Инициализируем компоненты
        self._initialize_components()
    
    def _initialize_components(self):
        """
        Инициализировать компоненты самообучения
        """
        # Инициализируем историю обучения
        self.learning_history = []
        
        # Инициализируем базу знаний
        self.knowledge_base.initialize_knowledge()
    
    def learn_from_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обучиться на основе взаимодействия
        """
        # Записываем взаимодействие в историю
        interaction_record = {
            'interaction_id': self._generate_interaction_id(interaction_data),
            'timestamp': datetime.now().isoformat(),
            'data': interaction_data,
            'learning_outcome': None
        }
        
        self.learning_history.append(interaction_record)
        
        # Анализируем взаимодействие
        analysis_result = self.performance_analyzer.analyze_interaction(interaction_data)
        
        # Распознаем паттерны
        patterns = self.pattern_recognition.recognize_patterns(interaction_data)
        
        # Применяем обучение
        learning_outcome = self.adaptation_engine.apply_learning(
            interaction_data, 
            analysis_result, 
            patterns
        )
        
        # Обновляем запись взаимодействия
        interaction_record['learning_outcome'] = learning_outcome
        
        # Обновляем базу знаний
        self.knowledge_base.update_knowledge(interaction_data, learning_outcome)
        
        return {
            'interaction_id': interaction_record['interaction_id'],
            'analysis_result': analysis_result,
            'recognized_patterns': patterns,
            'learning_outcome': learning_outcome,
            'timestamp': interaction_record['timestamp']
        }
    
    def _generate_interaction_id(self, interaction_data: Dict[str, Any]) -> str:
        """
        Сгенерировать уникальный ID взаимодействия
        """
        # Создаем хэш из данных взаимодействия
        hash_input = f"{json.dumps(interaction_data, sort_keys=True)}_{datetime.now().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def adapt_system_behavior(self, adaptation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Адаптировать поведение системы
        """
        # Получаем текущие знания
        current_knowledge = self.knowledge_base.get_current_knowledge()
        
        # Анализируем контекст адаптации
        context_analysis = self.performance_analyzer.analyze_context(adaptation_context)
        
        # Определяем необходимые изменения
        adaptation_plan = self.adaptation_engine.generate_adaptation_plan(
            current_knowledge, 
            context_analysis
        )
        
        # Применяем изменения
        adaptation_result = self.adaptation_engine.implement_changes(adaptation_plan)
        
        return {
            'adaptation_plan': adaptation_plan,
            'adaptation_result': adaptation_result,
            'context_analysis': context_analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Получить инсайты обучения
        """
        if not self.learning_history:
            return {
                'insights_available': False,
                'message': 'No learning history available'
            }
        
        # Анализируем историю обучения
        insights = self.performance_analyzer.generate_learning_insights(
            self.learning_history
        )
        
        # Получаем текущие знания
        current_knowledge = self.knowledge_base.get_current_knowledge()
        
        return {
            'learning_insights': insights,
            'current_knowledge': current_knowledge,
            'history_length': len(self.learning_history),
            'last_updated': datetime.now().isoformat()
        }
    
    def optimize_agent_performance(self, agent_type: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оптимизировать производительность агента
        """
        # Анализируем производительность
        performance_analysis = self.performance_analyzer.analyze_agent_performance(
            agent_type, 
            performance_data
        )
        
        # Определяем области для улучшения
        improvement_areas = self.performance_analyzer.identify_improvement_areas(
            performance_analysis
        )
        
        # Генерируем рекомендации по оптимизации
        optimization_recommendations = self.adaptation_engine.generate_optimization_recommendations(
            agent_type, 
            improvement_areas
        )
        
        # Применяем оптимизации
        optimization_result = self.adaptation_engine.apply_optimizations(
            agent_type, 
            optimization_recommendations
        )
        
        return {
            'agent_type': agent_type,
            'performance_analysis': performance_analysis,
            'improvement_areas': improvement_areas,
            'optimization_recommendations': optimization_recommendations,
            'optimization_result': optimization_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_system_behavior(self, input_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предсказать поведение системы
        """
        # Получаем текущие знания
        current_knowledge = self.knowledge_base.get_current_knowledge()
        
        # Анализируем контекст
        context_analysis = self.pattern_recognition.analyze_context(input_context)
        
        # Предсказываем поведение
        behavior_prediction = self.pattern_recognition.predict_behavior(
            current_knowledge, 
            context_analysis
        )
        
        # Оцениваем уверенность предсказания
        confidence_score = self.pattern_recognition.estimate_prediction_confidence(
            behavior_prediction
        )
        
        return {
            'behavior_prediction': behavior_prediction,
            'confidence_score': confidence_score,
            'context_analysis': context_analysis,
            'knowledge_used': len(current_knowledge.get('patterns', [])),
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_learning_effectiveness(self) -> Dict[str, Any]:
        """
        Оценить эффективность обучения
        """
        if not self.learning_history:
            return {
                'effectiveness_evaluated': False,
                'message': 'No learning history to evaluate'
            }
        
        # Оцениваем эффективность обучения
        effectiveness_evaluation = self.performance_analyzer.evaluate_learning_effectiveness(
            self.learning_history
        )
        
        # Получаем статистику
        learning_statistics = self.performance_analyzer.get_learning_statistics(
            self.learning_history
        )
        
        return {
            'effectiveness_evaluation': effectiveness_evaluation,
            'learning_statistics': learning_statistics,
            'total_interactions_learned': len(self.learning_history),
            'evaluation_timestamp': datetime.now().isoformat()
        }
    
    def continuous_improvement_loop(self) -> Dict[str, Any]:
        """
        Цикл непрерывного улучшения
        """
        # Получаем последние взаимодействия для обучения
        recent_interactions = self._get_recent_interactions()
        
        improvements_made = []
        
        for interaction in recent_interactions:
            # Обучаемся на взаимодействии
            learning_result = self.learn_from_interaction(interaction)
            improvements_made.append(learning_result)
        
        # Адаптируем систему на основе обучения
        adaptation_result = self.adapt_system_behavior({
            'recent_learning': improvements_made,
            'timestamp': datetime.now().isoformat()
        })
        
        # Оптимизируем производительность агентов
        agent_optimizations = self._optimize_all_agents()
        
        return {
            'loop_executed_at': datetime.now().isoformat(),
            'interactions_learned': len(improvements_made),
            'adaptation_result': adaptation_result,
            'agent_optimizations': agent_optimizations,
            'total_improvements': len(improvements_made)
        }
    
    def _get_recent_interactions(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Получить недавние взаимодействия для обучения
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_interactions = []
        
        for interaction in self.learning_history:
            interaction_time = datetime.fromisoformat(interaction['timestamp'])
            if interaction_time > cutoff_time:
                recent_interactions.append(interaction['data'])
        
        return recent_interactions
    
    def _optimize_all_agents(self) -> List[Dict[str, Any]]:
        """
        Оптимизировать всех агентов
        """
        # В реальной системе здесь будет оптимизация всех агентов
        # Сейчас используем заглушку
        return [
            {
                'agent_type': 'generic',
                'optimization_applied': 'performance_tuning',
                'timestamp': datetime.now().isoformat()
            }
        ]

class PatternRecognitionEngine:
    """
    Движок распознавания паттернов
    """
    
    def __init__(self):
        self.pattern_vectors = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.clustering_model = KMeans(n_clusters=10)
        
        # Инициализируем модели
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Инициализировать модели машинного обучения
        """
        # В реальной системе здесь будут обученные модели
        pass
    
    def recognize_patterns(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Распознать паттерны во взаимодействии
        """
        patterns_found = []
        
        # Анализируем тип задачи
        task_type = self._analyze_task_type(interaction_data)
        if task_type:
            patterns_found.append({
                'pattern_type': 'task_type',
                'value': task_type,
                'confidence': 0.9
            })
        
        # Анализируем сложность задачи
        complexity_level = self._analyze_complexity_level(interaction_data)
        if complexity_level:
            patterns_found.append({
                'pattern_type': 'complexity_level',
                'value': complexity_level,
                'confidence': 0.85
            })
        
        # Анализируем используемые технологии
        technologies_used = self._analyze_technologies_used(interaction_data)
        if technologies_used:
            patterns_found.extend([
                {
                    'pattern_type': 'technology_used',
                    'value': tech,
                    'confidence': 0.8
                }
                for tech in technologies_used
            ])
        
        # Анализируем структуру запроса
        request_structure = self._analyze_request_structure(interaction_data)
        if request_structure:
            patterns_found.append({
                'pattern_type': 'request_structure',
                'value': request_structure,
                'confidence': 0.75
            })
        
        return {
            'patterns_found': patterns_found,
            'total_patterns': len(patterns_found),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_task_type(self, interaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Проанализировать тип задачи
        """
        task_description = interaction_data.get('task_description', '').lower()
        
        # Определяем тип задачи на основе ключевых слов
        task_keywords = {
            'code_generation': ['implement', 'create', 'write', 'develop', 'build', 'program'],
            'documentation': ['document', 'write', 'manual', 'guide', 'readme', 'explain'],
            'testing': ['test', 'testing', 'unit test', 'integration test', 'quality', 'verify'],
            'research': ['research', 'study', 'analyze', 'investigate', 'examine', 'evaluate'],
            'deployment': ['deploy', 'docker', 'pipeline', 'ci/cd', 'infrastructure'],
            'refactoring': ['refactor', 'improve', 'optimize', 'clean', 'restructure']
        }
        
        best_match = None
        best_score = 0
        
        for task_type, keywords in task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_description)
            if score > best_score:
                best_score = score
                best_match = task_type
        
        return best_match if best_score > 0 else None
    
    def _analyze_complexity_level(self, interaction_data: Dict[str, Any]) -> str:
        """
        Проанализировать уровень сложности задачи
        """
        task_description = interaction_data.get('task_description', '')
        word_count = len(task_description.split())
        
        if word_count < 20:
            return 'simple'
        elif word_count < 50:
            return 'medium'
        else:
            return 'complex'
    
    def _analyze_technologies_used(self, interaction_data: Dict[str, Any]) -> List[str]:
        """
        Проанализировать используемые технологии
        """
        task_description = interaction_data.get('task_description', '').lower()
        
        # Список технологий
        technologies = [
            'python', 'javascript', 'react', 'vue', 'angular', 'node.js', 'django', 'flask',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'postgresql', 'mongodb', 'redis',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib'
        ]
        
        found_technologies = []
        for tech in technologies:
            if tech in task_description:
                found_technologies.append(tech)
        
        return found_technologies
    
    def _analyze_request_structure(self, interaction_data: Dict[str, Any]) -> str:
        """
        Проанализировать структуру запроса
        """
        task_description = interaction_data.get('task_description', '')
        
        # Считаем количество предложений
        sentences = [s.strip() for s in task_description.split('.') if s.strip()]
        
        if len(sentences) == 1:
            return 'single_sentence'
        elif len(sentences) <= 3:
            return 'short_request'
        else:
            return 'detailed_request'
    
    def analyze_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проанализировать контекст
        """
        return {
            'context_type': 'general',
            'context_complexity': 'medium',
            'key_elements': list(context_data.keys()),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def predict_behavior(self, knowledge_base: Dict[str, Any], 
                         context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предсказать поведение системы
        """
        # Простое предсказание на основе текущих знаний
        return {
            'predicted_behavior': 'adaptive_response',
            'expected_outcome': 'successful_completion',
            'confidence_level': 0.85,
            'reasoning': 'Based on historical patterns and current context'
        }
    
    def estimate_prediction_confidence(self, prediction: Dict[str, Any]) -> float:
        """
        Оценить уверенность предсказания
        """
        # Простая оценка уверенности
        return prediction.get('confidence_level', 0.5)

class AdaptationEngine:
    """
    Движок адаптации системы
    """
    
    def __init__(self):
        self.adaptation_history = []
        self.optimization_strategies = {}
        
        # Инициализируем стратегии оптимизации
        self._initialize_optimization_strategies()
    
    def _initialize_optimization_strategies(self):
        """
        Инициализировать стратегии оптимизации
        """
        self.optimization_strategies = {
            'agent_routing': {
                'strategy': 'dynamic_routing',
                'parameters': {
                    'load_balancing': True,
                    'skill_matching': True,
                    'performance_weighting': 0.7
                }
            },
            'task_decomposition': {
                'strategy': 'intelligent_splitting',
                'parameters': {
                    'complexity_threshold': 0.6,
                    'dependency_analysis': True
                }
            },
            'resource_allocation': {
                'strategy': 'efficient_distribution',
                'parameters': {
                    'cpu_optimization': True,
                    'memory_management': True,
                    'parallel_processing': True
                }
            }
        }
    
    def apply_learning(self, interaction_data: Dict[str, Any], 
                      analysis_result: Dict[str, Any], 
                      patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применить обучение
        """
        adaptation_applied = []
        
        # Адаптируем маршрутизацию агентов
        routing_adaptation = self._adapt_agent_routing(interaction_data, patterns)
        if routing_adaptation:
            adaptation_applied.append(routing_adaptation)
        
        # Адаптируем декомпозицию задач
        decomposition_adaptation = self._adapt_task_decomposition(interaction_data)
        if decomposition_adaptation:
            adaptation_applied.append(decomposition_adaptation)
        
        # Адаптируем распределение ресурсов
        resource_adaptation = self._adapt_resource_allocation(interaction_data)
        if resource_adaptation:
            adaptation_applied.append(resource_adaptation)
        
        return {
            'adaptations_applied': adaptation_applied,
            'total_adaptations': len(adaptation_applied),
            'learning_timestamp': datetime.now().isoformat()
        }
    
    def _adapt_agent_routing(self, interaction_data: Dict[str, Any], 
                           patterns: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Адаптировать маршрутизацию агентов
        """
        # Простая адаптация маршрутизации
        return {
            'adaptation_type': 'agent_routing',
            'change_made': 'routing_optimization',
            'timestamp': datetime.now().isoformat()
        }
    
    def _adapt_task_decomposition(self, interaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Адаптировать декомпозицию задач
        """
        # Простая адаптация декомпозиции
        return {
            'adaptation_type': 'task_decomposition',
            'change_made': 'decomposition_refinement',
            'timestamp': datetime.now().isoformat()
        }
    
    def _adapt_resource_allocation(self, interaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Адаптировать распределение ресурсов
        """
        # Простая адаптация распределения ресурсов
        return {
            'adaptation_type': 'resource_allocation',
            'change_made': 'allocation_optimization',
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_adaptation_plan(self, current_knowledge: Dict[str, Any], 
                               context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сгенерировать план адаптации
        """
        return {
            'plan_id': str(hash(datetime.now().isoformat()))[:8],
            'strategies_selected': list(self.optimization_strategies.keys()),
            'implementation_order': ['agent_routing', 'task_decomposition', 'resource_allocation'],
            'estimated_timeline': '2 hours',
            'required_resources': ['computing_power', 'memory', 'storage'],
            'generation_timestamp': datetime.now().isoformat()
        }
    
    def implement_changes(self, adaptation_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Реализовать изменения
        """
        changes_implemented = []
        
        for strategy_name in adaptation_plan.get('implementation_order', []):
            if strategy_name in self.optimization_strategies:
                strategy = self.optimization_strategies[strategy_name]
                change_result = self._implement_strategy(strategy_name, strategy)
                changes_implemented.append(change_result)
        
        return {
            'changes_implemented': changes_implemented,
            'total_changes': len(changes_implemented),
            'implementation_timestamp': datetime.now().isoformat()
        }
    
    def _implement_strategy(self, strategy_name: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Реализовать конкретную стратегию
        """
        return {
            'strategy_name': strategy_name,
            'implementation_status': 'completed',
            'result': f'Strategy {strategy_name} implemented successfully',
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_optimization_recommendations(self, agent_type: str, 
                                            improvement_areas: List[str]) -> List[Dict[str, Any]]:
        """
        Сгенерировать рекомендации по оптимизации
        """
        recommendations = []
        
        for area in improvement_areas:
            recommendation = {
                'area': area,
                'agent_type': agent_type,
                'recommendation': f'Optimize {area} for {agent_type}',
                'priority': 'medium',
                'estimated_impact': 0.7,
                'implementation_guide': f'Steps to optimize {area}'
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def apply_optimizations(self, agent_type: str, 
                          recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Применить оптимизации
        """
        optimizations_applied = []
        
        for recommendation in recommendations:
            optimization_result = {
                'optimization_area': recommendation['area'],
                'agent_type': agent_type,
                'result': f'Applied optimization for {recommendation["area"]}',
                'impact_achieved': recommendation['estimated_impact'] * 0.9,
                'timestamp': datetime.now().isoformat()
            }
            optimizations_applied.append(optimization_result)
        
        return {
            'optimizations_applied': optimizations_applied,
            'total_optimizations': len(optimizations_applied),
            'overall_improvement': sum(o['impact_achieved'] for o in optimizations_applied) / len(optimizations_applied) if optimizations_applied else 0,
            'application_timestamp': datetime.now().isoformat()
        }

class PerformanceAnalyzer:
    """
    Анализатор производительности
    """
    
    def __init__(self):
        self.performance_metrics = {}
        self.analysis_history = []
        
        # Инициализируем метрики
        self._initialize_performance_metrics()
    
    def _initialize_performance_metrics(self):
        """
        Инициализировать метрики производительности
        """
        self.performance_metrics = {
            'response_time': {
                'unit': 'seconds',
                'optimal_range': (0.1, 2.0),
                'weight': 0.3
            },
            'accuracy': {
                'unit': 'percentage',
                'optimal_range': (0.8, 1.0),
                'weight': 0.4
            },
            'resource_utilization': {
                'unit': 'percentage',
                'optimal_range': (0.3, 0.8),
                'weight': 0.2
            },
            'error_rate': {
                'unit': 'percentage',
                'optimal_range': (0.0, 0.05),
                'weight': 0.1
            }
        }
    
    def analyze_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проанализировать взаимодействие
        """
        # Простой анализ взаимодействия
        return {
            'interaction_type': interaction_data.get('interaction_type', 'unknown'),
            'complexity_level': self._assess_complexity(interaction_data),
            'estimated_duration': self._estimate_duration(interaction_data),
            'resource_requirements': self._assess_resource_requirements(interaction_data),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _assess_complexity(self, interaction_data: Dict[str, Any]) -> str:
        """
        Оценить сложность взаимодействия
        """
        task_description = interaction_data.get('task_description', '')
        word_count = len(task_description.split())
        
        if word_count < 30:
            return 'low'
        elif word_count < 100:
            return 'medium'
        else:
            return 'high'
    
    def _estimate_duration(self, interaction_data: Dict[str, Any]) -> float:
        """
        Оценить продолжительность выполнения
        """
        # Простая эвристика
        task_description = interaction_data.get('task_description', '')
        word_count = len(task_description.split())
        
        # Предполагаем, что на каждые 10 слов требуется 1 секунда
        return max(1.0, word_count / 10.0)
    
    def _assess_resource_requirements(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценить требования к ресурсам
        """
        return {
            'cpu': 'medium',
            'memory': 'low',
            'storage': 'minimal',
            'network': 'low'
        }
    
    def analyze_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проанализировать контекст
        """
        return {
            'context_complexity': 'medium',
            'key_factors': list(context_data.keys()),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def generate_learning_insights(self, learning_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Сгенерировать инсайты обучения
        """
        if not learning_history:
            return {
                'insights_available': False,
                'message': 'No learning history to analyze'
            }
        
        # Простой анализ истории обучения
        total_interactions = len(learning_history)
        recent_interactions = self._get_recent_interactions(learning_history, hours=24)
        
        return {
            'total_interactions_analyzed': total_interactions,
            'recent_interactions': len(recent_interactions),
            'learning_trend': 'positive' if total_interactions > 10 else 'building',
            'most_common_patterns': self._identify_common_patterns(learning_history),
            'insight_generation_timestamp': datetime.now().isoformat()
        }
    
    def _get_recent_interactions(self, learning_history: List[Dict[str, Any]], 
                               hours: int = 24) -> List[Dict[str, Any]]:
        """
        Получить недавние взаимодействия
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for interaction in learning_history:
            interaction_time = datetime.fromisoformat(interaction['timestamp'])
            if interaction_time > cutoff_time:
                recent.append(interaction)
        
        return recent
    
    def _identify_common_patterns(self, learning_history: List[Dict[str, Any]]) -> List[str]:
        """
        Идентифицировать общие паттерны
        """
        # Простая эвристика для идентификации паттернов
        return ['task_completion', 'pattern_recognition', 'adaptation_response']
    
    def analyze_agent_performance(self, agent_type: str, 
                                 performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проанализировать производительность агента
        """
        return {
            'agent_type': agent_type,
            'performance_metrics': self._calculate_performance_metrics(performance_data),
            'efficiency_score': self._calculate_efficiency_score(performance_data),
            'areas_for_improvement': self._identify_improvement_areas(performance_data),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_performance_metrics(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитать метрики производительности
        """
        # Простые метрики
        return {
            'response_time': performance_data.get('response_time', 1.0),
            'accuracy': performance_data.get('accuracy', 0.9),
            'throughput': performance_data.get('tasks_completed', 1) / max(performance_data.get('time_spent', 1), 1),
            'error_rate': performance_data.get('errors', 0) / max(performance_data.get('tasks_attempted', 1), 1)
        }
    
    def _calculate_efficiency_score(self, performance_data: Dict[str, Any]) -> float:
        """
        Рассчитать оценку эффективности
        """
        # Простая формула эффективности
        accuracy = performance_data.get('accuracy', 0.9)
        response_time = performance_data.get('response_time', 1.0)
        throughput = performance_data.get('tasks_completed', 1) / max(performance_data.get('time_spent', 1), 1)
        
        # Взвешенная оценка (чем быстрее и точнее, тем выше эффективность)
        efficiency = (accuracy * 0.5 + (1.0 / max(response_time, 0.1)) * 0.3 + throughput * 0.2)
        return min(1.0, efficiency)
    
    def _identify_improvement_areas(self, performance_data: Dict[str, Any]) -> List[str]:
        """
        Идентифицировать области для улучшения
        """
        areas = []
        
        if performance_data.get('response_time', 1.0) > 2.0:
            areas.append('response_time')
        
        if performance_data.get('accuracy', 0.9) < 0.85:
            areas.append('accuracy')
        
        if performance_data.get('error_rate', 0) > 0.1:
            areas.append('error_reduction')
        
        return areas if areas else ['general_optimization']
    
    def identify_improvement_areas(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """
        Идентифицировать области для улучшения
        """
        return performance_analysis.get('areas_for_improvement', ['general_optimization'])
    
    def evaluate_learning_effectiveness(self, learning_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Оценить эффективность обучения
        """
        if not learning_history:
            return {
                'effectiveness_evaluated': False,
                'message': 'No learning history to evaluate'
            }
        
        # Простая оценка эффективности обучения
        total_interactions = len(learning_history)
        
        # Считаем количество уникальных паттернов
        unique_patterns = set()
        for interaction in learning_history:
            learning_outcome = interaction.get('learning_outcome', {})
            patterns = learning_outcome.get('recognized_patterns', {}).get('patterns_found', [])
            for pattern in patterns:
                unique_patterns.add(pattern.get('pattern_type', 'unknown'))
        
        return {
            'learning_effectiveness_score': min(1.0, len(unique_patterns) / 20.0),
            'total_interactions_learned': total_interactions,
            'unique_patterns_identified': len(unique_patterns),
            'pattern_diversity': list(unique_patterns)[:10],  # Показываем первые 10
            'evaluation_timestamp': datetime.now().isoformat()
        }
    
    def get_learning_statistics(self, learning_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Получить статистику обучения
        """
        if not learning_history:
            return {
                'statistics_available': False,
                'message': 'No learning history available'
            }
        
        # Простая статистика
        total_interactions = len(learning_history)
        interaction_types = {}
        
        for interaction in learning_history:
            interaction_type = interaction.get('data', {}).get('interaction_type', 'unknown')
            interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
        
        return {
            'total_interactions': total_interactions,
            'interaction_types_distribution': interaction_types,
            'average_learning_per_day': total_interactions / max(1, len(set(
                datetime.fromisoformat(i['timestamp']).date() 
                for i in learning_history
            ))),
            'statistics_timestamp': datetime.now().isoformat()
        }

class KnowledgeBase:
    """
    База знаний системы
    """
    
    def __init__(self):
        self.knowledge_store = {}
        self.pattern_library = {}
        self.best_practices = {}
        self.failure_cases = {}
        
        # Инициализируем базу знаний
        self.initialize_knowledge()
    
    def initialize_knowledge(self):
        """
        Инициализировать базу знаний
        """
        self.knowledge_store = {
            'system_configuration': {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'components': ['pattern_recognition', 'adaptation_engine', 'performance_analyzer']
            },
            'learning_history': [],
            'patterns': {},
            'best_practices': {},
            'failure_cases': {}
        }
    
    def update_knowledge(self, interaction_data: Dict[str, Any], learning_outcome: Dict[str, Any]):
        """
        Обновить знания на основе взаимодействия
        """
        # Добавляем взаимодействие в историю
        self.knowledge_store['learning_history'].append({
            'interaction_data': interaction_data,
            'learning_outcome': learning_outcome,
            'timestamp': datetime.now().isoformat()
        })
        
        # Обновляем паттерны
        patterns = learning_outcome.get('recognized_patterns', {}).get('patterns_found', [])
        for pattern in patterns:
            pattern_type = pattern.get('pattern_type')
            if pattern_type:
                if pattern_type not in self.knowledge_store['patterns']:
                    self.knowledge_store['patterns'][pattern_type] = []
                self.knowledge_store['patterns'][pattern_type].append(pattern)
    
    def get_current_knowledge(self) -> Dict[str, Any]:
        """
        Получить текущие знания
        """
        return {
            'knowledge_version': self.knowledge_store['system_configuration']['version'],
            'total_interactions_learned': len(self.knowledge_store['learning_history']),
            'patterns_identified': len(self.knowledge_store['patterns']),
            'last_updated': self.knowledge_store['system_configuration']['last_updated'],
            'knowledge_summary': self._generate_knowledge_summary()
        }
    
    def _generate_knowledge_summary(self) -> Dict[str, Any]:
        """
        Сгенерировать краткое содержание знаний
        """
        return {
            'interaction_history_length': len(self.knowledge_store['learning_history']),
            'pattern_types_count': len(self.knowledge_store['patterns']),
            'best_practices_count': len(self.knowledge_store['best_practices']),
            'failure_cases_count': len(self.knowledge_store['failure_cases'])
        }

# Глобальная самообучающаяся архитектура
self_learning_system = SelfLearningArchitecture()