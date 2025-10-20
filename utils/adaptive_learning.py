from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from utils.knowledge_base import knowledge_base

class AdaptiveLearningSystem:
    """
    Система адаптивного обучения агентов на основе их производительности и взаимодействий
    """
    
    def __init__(self):
        self.learning_history = []
        self.performance_models = {}
        self.scalers = {}
        self.adaptation_strategies = {}
        
        # Инициализируем систему
        self._initialize_system()
    
    def _initialize_system(self):
        """
        Инициализировать систему адаптивного обучения
        """
        # Инициализируем модели производительности для каждого типа агента
        agent_types = ['researcher', 'backend_dev', 'frontend_dev', 'doc_writer', 'tester', 'devops']
        
        for agent_type in agent_types:
            self.performance_models[agent_type] = LinearRegression()
            self.scalers[agent_type] = StandardScaler()
        
        # Инициализируем стратегии адаптации
        self.adaptation_strategies = {
            'performance_improvement': self._improve_performance_strategy,
            'task_optimization': self._optimize_task_assignment_strategy,
            'resource_allocation': self._optimize_resource_allocation_strategy,
            'collaboration_enhancement': self._enhance_collaboration_strategy
        }
    
    def record_interaction(self, agent_type: str, task_description: str, 
                          result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Записать взаимодействие агента для последующего обучения
        """
        interaction_record = {
            'agent_type': agent_type,
            'task_description': task_description,
            'result': result,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': self._calculate_performance_metrics(result, task_description),
            'learning_outcome': None
        }
        
        self.learning_history.append(interaction_record)
        
        # Обновляем базу знаний
        knowledge_base.add_knowledge(
            'agent_interaction',
            agent_type,
            session_id,
            json.dumps(interaction_record),
            {
                'performance_metrics': interaction_record['performance_metrics'],
                'timestamp': interaction_record['timestamp']
            }
        )
        
        return interaction_record
    
    def _calculate_performance_metrics(self, result: Dict[str, Any], 
                                    task_description: str) -> Dict[str, float]:
        """
        Рассчитать метрики производительности для результата
        """
        metrics = {
            'quality_score': 0.0,
            'completeness_score': 0.0,
            'efficiency_score': 0.0,
            'accuracy_score': 0.0,
            'timeliness_score': 0.0
        }
        
        # Рассчитываем оценку качества
        result_content = result.get('result', '')
        if result_content:
            # Оценка качества на основе длины и содержания
            content_length = len(result_content)
            quality_indicators = ['def ', 'class ', 'import ', 'function', 'return', 'docstring']
            quality_score = min(1.0, content_length / 500.0)  # Нормализуем до 500 символов
            
            # Добавляем баллы за наличие индикаторов качества
            for indicator in quality_indicators:
                if indicator in result_content:
                    quality_score += 0.1
            
            metrics['quality_score'] = min(1.0, quality_score)
        
        # Рассчитываем оценку полноты
        artifacts_created = result.get('artifacts_created', [])
        if artifacts_created:
            # Чем больше артефактов, тем выше оценка полноты (до определенного предела)
            completeness_score = min(1.0, len(artifacts_created) / 3.0)
            metrics['completeness_score'] = completeness_score
        else:
            metrics['completeness_score'] = 0.5  # Средняя оценка по умолчанию
        
        # Рассчитываем оценку эффективности
        task_words = len(task_description.split())
        result_words = len(result_content.split()) if result_content else 0
        
        if task_words > 0:
            # Эффективность = отношение слов результата к словам задачи
            efficiency_score = min(1.0, result_words / (task_words * 2.0))
            metrics['efficiency_score'] = efficiency_score
        else:
            metrics['efficiency_score'] = 0.5
        
        # Рассчитываем оценку точности
        forbidden_patterns = ['NEEDS_CLARIFICATION', 'TODO', 'FIXME', 'placeholder']
        forbidden_count = sum(1 for pattern in forbidden_patterns if pattern in result_content)
        
        # Чем меньше запрещенных паттернов, тем выше оценка точности
        accuracy_score = max(0.0, 1.0 - (forbidden_count / 3.0))
        metrics['accuracy_score'] = accuracy_score
        
        # Рассчитываем оценку своевременности (временная заглушка)
        metrics['timeliness_score'] = 0.8  # Предполагаем среднюю своевременность
        
        return metrics
    
    def analyze_performance_trends(self, agent_type: str, 
                                 time_window_days: int = 30) -> Dict[str, Any]:
        """
        Проанализировать тенденции производительности агента за определенный период
        """
        # Получаем историю взаимодействий для агента
        agent_interactions = [
            interaction for interaction in self.learning_history
            if interaction['agent_type'] == agent_type
        ]
        
        if not agent_interactions:
            return {
                'agent_type': agent_type,
                'analysis_available': False,
                'message': 'No interaction history for this agent'
            }
        
        # Фильтруем по временному окну
        cutoff_time = datetime.now() - timedelta(days=time_window_days)
        recent_interactions = [
            interaction for interaction in agent_interactions
            if datetime.fromisoformat(interaction['timestamp']) > cutoff_time
        ]
        
        if not recent_interactions:
            return {
                'agent_type': agent_type,
                'analysis_available': False,
                'message': f'No recent interactions within {time_window_days} days'
            }
        
        # Рассчитываем средние метрики
        metric_sums = {}
        metric_counts = {}
        
        for interaction in recent_interactions:
            metrics = interaction['performance_metrics']
            for metric_name, metric_value in metrics.items():
                if metric_name not in metric_sums:
                    metric_sums[metric_name] = 0.0
                    metric_counts[metric_name] = 0
                
                metric_sums[metric_name] += metric_value
                metric_counts[metric_name] += 1
        
        # Рассчитываем средние значения
        average_metrics = {}
        for metric_name in metric_sums:
            if metric_counts[metric_name] > 0:
                average_metrics[metric_name] = metric_sums[metric_name] / metric_counts[metric_name]
            else:
                average_metrics[metric_name] = 0.0
        
        # Определяем тенденции (улучшение или ухудшение)
        trends = self._calculate_performance_trends(recent_interactions)
        
        return {
            'agent_type': agent_type,
            'time_window_days': time_window_days,
            'total_interactions_analyzed': len(recent_interactions),
            'average_metrics': average_metrics,
            'performance_trends': trends,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_performance_trends(self, interactions: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Рассчитать тенденции производительности на основе взаимодействий
        """
        if len(interactions) < 2:
            return {metric: 'stable' for metric in ['quality_score', 'completeness_score', 'efficiency_score', 'accuracy_score', 'timeliness_score']}
        
        # Сортируем взаимодействия по времени
        sorted_interactions = sorted(interactions, key=lambda x: datetime.fromisoformat(x['timestamp']))
        
        # Разделяем на две половины для сравнения
        midpoint = len(sorted_interactions) // 2
        first_half = sorted_interactions[:midpoint]
        second_half = sorted_interactions[midpoint:]
        
        trends = {}
        
        # Сравниваем средние значения метрик в первой и второй половинах
        for metric in ['quality_score', 'completeness_score', 'efficiency_score', 'accuracy_score', 'timeliness_score']:
            first_avg = sum(interaction['performance_metrics'][metric] for interaction in first_half) / len(first_half)
            second_avg = sum(interaction['performance_metrics'][metric] for interaction in second_half) / len(second_half)
            
            # Определяем тенденцию
            diff = second_avg - first_avg
            if diff > 0.1:
                trends[metric] = 'improving'
            elif diff < -0.1:
                trends[metric] = 'declining'
            else:
                trends[metric] = 'stable'
        
        return trends
    
    def generate_adaptation_recommendations(self, agent_type: str, 
                                          performance_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Сгенерировать рекомендации по адаптации на основе анализа производительности
        """
        recommendations = []
        
        # Получаем тенденции производительности
        trends = performance_analysis.get('performance_trends', {})
        average_metrics = performance_analysis.get('average_metrics', {})
        
        # Генерируем рекомендации на основе тенденций и средних значений
        for metric_name, trend in trends.items():
            if trend == 'declining':
                # Если метрика ухудшается, предлагаем улучшения
                recommendation = self._generate_improvement_recommendation(
                    agent_type, 
                    metric_name, 
                    average_metrics.get(metric_name, 0.0)
                )
                recommendations.append(recommendation)
            elif trend == 'stable':
                # Если метрика стабильна, предлагаем оптимизации
                recommendation = self._generate_optimization_recommendation(
                    agent_type, 
                    metric_name, 
                    average_metrics.get(metric_name, 0.0)
                )
                recommendations.append(recommendation)
            elif trend == 'improving':
                # Если метрика улучшается, предлагаем закрепление успеха
                recommendation = self._generate_success_recommendation(
                    agent_type, 
                    metric_name, 
                    average_metrics.get(metric_name, 0.0)
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_improvement_recommendation(self, agent_type: str, 
                                          metric_name: str, 
                                          current_value: float) -> Dict[str, Any]:
        """
        Сгенерировать рекомендацию по улучшению для ухудшающейся метрики
        """
        improvement_strategies = {
            'quality_score': 'Focus on code quality improvements, add more documentation, and follow best practices',
            'completeness_score': 'Increase artifact creation, add more comprehensive test coverage, and expand documentation',
            'efficiency_score': 'Optimize task processing algorithms, reduce redundant work, and improve resource utilization',
            'accuracy_score': 'Reduce placeholder usage, improve error handling, and enhance validation checks',
            'timeliness_score': 'Streamline workflows, reduce bottlenecks, and optimize task scheduling'
        }
        
        return {
            'type': 'improvement',
            'agent_type': agent_type,
            'metric': metric_name,
            'current_value': current_value,
            'recommendation': improvement_strategies.get(metric_name, 'General performance improvement needed'),
            'priority': 'high',
            'estimated_impact': 0.3,  # Предполагаемый положительный эффект
            'implementation_guide': f'Steps to improve {metric_name} for {agent_type}'
        }
    
    def _generate_optimization_recommendation(self, agent_type: str, 
                                           metric_name: str, 
                                           current_value: float) -> Dict[str, Any]:
        """
        Сгенерировать рекомендацию по оптимизации для стабильной метрики
        """
        optimization_strategies = {
            'quality_score': 'Maintain current quality standards while exploring advanced techniques',
            'completeness_score': 'Enhance artifact variety and depth without sacrificing quality',
            'efficiency_score': 'Fine-tune existing processes for marginal gains',
            'accuracy_score': 'Strengthen validation mechanisms and error prevention',
            'timeliness_score': 'Optimize scheduling for better resource allocation'
        }
        
        return {
            'type': 'optimization',
            'agent_type': agent_type,
            'metric': metric_name,
            'current_value': current_value,
            'recommendation': optimization_strategies.get(metric_name, 'General performance optimization needed'),
            'priority': 'medium',
            'estimated_impact': 0.15,  # Предполагаемый положительный эффект
            'implementation_guide': f'Steps to optimize {metric_name} for {agent_type}'
        }
    
    def _generate_success_recommendation(self, agent_type: str, 
                                      metric_name: str, 
                                      current_value: float) -> Dict[str, Any]:
        """
        Сгенерировать рекомендацию по закреплению успеха для улучшающейся метрики
        """
        success_strategies = {
            'quality_score': 'Continue following current best practices and document successful approaches',
            'completeness_score': 'Maintain comprehensive artifact creation while expanding to new areas',
            'efficiency_score': 'Share efficient workflows with other agents and teams',
            'accuracy_score': 'Codify successful validation techniques and error prevention strategies',
            'timeliness_score': 'Standardize successful scheduling practices across the organization'
        }
        
        return {
            'type': 'success_maintenance',
            'agent_type': agent_type,
            'metric': metric_name,
            'current_value': current_value,
            'recommendation': success_strategies.get(metric_name, 'Continue current successful practices'),
            'priority': 'low',
            'estimated_impact': 0.05,  # Предполагаемый положительный эффект
            'implementation_guide': f'Steps to maintain {metric_name} success for {agent_type}'
        }
    
    def apply_adaptive_learning(self, agent_type: str, 
                             recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Применить адаптивное обучение на основе рекомендаций
        """
        adaptations_applied = []
        
        for recommendation in recommendations:
            adaptation_result = self._apply_recommendation(agent_type, recommendation)
            adaptations_applied.append(adaptation_result)
        
        return {
            'agent_type': agent_type,
            'adaptations_applied': adaptations_applied,
            'total_adaptations': len(adaptations_applied),
            'learning_timestamp': datetime.now().isoformat()
        }
    
    def _apply_recommendation(self, agent_type: str, 
                           recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применить отдельную рекомендацию
        """
        recommendation_type = recommendation['type']
        metric_name = recommendation['metric']
        recommendation_text = recommendation['recommendation']
        
        # Применяем стратегию адаптации в зависимости от типа рекомендации
        if recommendation_type in self.adaptation_strategies:
            adaptation_strategy = self.adaptation_strategies[recommendation_type]
            adaptation_result = adaptation_strategy(agent_type, recommendation)
        else:
            # По умолчанию используем общую стратегию улучшения
            adaptation_result = self._improve_performance_strategy(agent_type, recommendation)
        
        return {
            'recommendation_type': recommendation_type,
            'metric': metric_name,
            'recommendation': recommendation_text,
            'adaptation_result': adaptation_result,
            'application_timestamp': datetime.now().isoformat()
        }
    
    def _improve_performance_strategy(self, agent_type: str, 
                                    recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стратегия улучшения производительности
        """
        return {
            'strategy_applied': 'performance_improvement',
            'result': f'Applied performance improvement strategy for {agent_type} focusing on {recommendation["metric"]}',
            'success': True,
            'details': recommendation['implementation_guide']
        }
    
    def _optimize_task_assignment_strategy(self, agent_type: str, 
                                        recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стратегия оптимизации назначения задач
        """
        return {
            'strategy_applied': 'task_optimization',
            'result': f'Optimized task assignment for {agent_type} based on {recommendation["metric"]} performance',
            'success': True,
            'details': recommendation['implementation_guide']
        }
    
    def _optimize_resource_allocation_strategy(self, agent_type: str, 
                                            recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стратегия оптимизации распределения ресурсов
        """
        return {
            'strategy_applied': 'resource_allocation',
            'result': f'Optimized resource allocation for {agent_type} to improve {recommendation["metric"]}',
            'success': True,
            'details': recommendation['implementation_guide']
        }
    
    def _enhance_collaboration_strategy(self, agent_type: str, 
                                      recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стратегия улучшения сотрудничества
        """
        return {
            'strategy_applied': 'collaboration_enhancement',
            'result': f'Enhanced collaboration for {agent_type} to boost {recommendation["metric"]} performance',
            'success': True,
            'details': recommendation['implementation_guide']
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
        
        # Анализируем общие тенденции
        agent_performance = {}
        
        for interaction in self.learning_history:
            agent_type = interaction['agent_type']
            metrics = interaction['performance_metrics']
            
            if agent_type not in agent_performance:
                agent_performance[agent_type] = {
                    'interactions': [],
                    'total_metrics': {}
                }
            
            agent_performance[agent_type]['interactions'].append(interaction)
            
            # Суммируем метрики
            for metric_name, metric_value in metrics.items():
                if metric_name not in agent_performance[agent_type]['total_metrics']:
                    agent_performance[agent_type]['total_metrics'][metric_name] = 0.0
                agent_performance[agent_type]['total_metrics'][metric_name] += metric_value
        
        # Рассчитываем средние значения
        for agent_type, data in agent_performance.items():
            interaction_count = len(data['interactions'])
            if interaction_count > 0:
                for metric_name in data['total_metrics']:
                    data['total_metrics'][metric_name] /= interaction_count
        
        return {
            'total_interactions': len(self.learning_history),
            'agents_analyzed': list(agent_performance.keys()),
            'agent_performance_averages': {
                agent: data['total_metrics'] for agent, data in agent_performance.items()
            },
            'learning_insights_timestamp': datetime.now().isoformat()
        }
    
    def continuous_learning_loop(self) -> Dict[str, Any]:
        """
        Цикл непрерывного обучения
        """
        # Получаем последние взаимодействия
        recent_interactions = self._get_recent_interactions(hours=24)
        
        learning_outcomes = []
        
        # Для каждого агента анализируем производительность и генерируем рекомендации
        agent_types = set(interaction['agent_type'] for interaction in recent_interactions)
        
        for agent_type in agent_types:
            # Анализируем производительность агента
            performance_analysis = self.analyze_performance_trends(agent_type, time_window_days=7)
            
            if performance_analysis['analysis_available']:
                # Генерируем рекомендации по адаптации
                recommendations = self.generate_adaptation_recommendations(
                    agent_type, 
                    performance_analysis
                )
                
                # Применяем адаптивное обучение
                learning_outcome = self.apply_adaptive_learning(agent_type, recommendations)
                learning_outcomes.append(learning_outcome)
        
        return {
            'loop_executed_at': datetime.now().isoformat(),
            'agents_processed': list(agent_types),
            'learning_outcomes': learning_outcomes,
            'total_learning_actions': len(learning_outcomes)
        }
    
    def _get_recent_interactions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Получить недавние взаимодействия для обучения
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_interactions = []
        
        for interaction in self.learning_history:
            interaction_time = datetime.fromisoformat(interaction['timestamp'])
            if interaction_time > cutoff_time:
                recent_interactions.append(interaction)
        
        return recent_interactions

# Глобальная система адаптивного обучения
adaptive_learning_system = AdaptiveLearningSystem()