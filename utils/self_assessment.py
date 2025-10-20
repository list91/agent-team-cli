from typing import Dict, List, Any, Tuple
from utils.competency_matrix import competency_matrix
import json

class SelfAssessmentSystem:
    """
    Система самооценки качества выполнения задач агентами
    """
    
    def __init__(self):
        self.assessment_history = {}
        self.quality_metrics = {
            'completeness': {
                'description': 'Percentage of task requirements fulfilled',
                'weight': 0.3
            },
            'correctness': {
                'description': 'Accuracy of implementation',
                'weight': 0.25
            },
            'efficiency': {
                'description': 'Resource usage and performance',
                'weight': 0.2
            },
            'maintainability': {
                'description': 'Code quality and documentation',
                'weight': 0.15
            },
            'innovation': {
                'description': 'Creative problem-solving approaches',
                'weight': 0.1
            }
        }
    
    def request_self_assessment(self, agent_type: str, task_description: str, 
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запросить самооценку качества выполнения задачи от агента
        """
        # Формируем запрос к агенту на самооценку
        assessment_request = {
            'task': task_description,
            'result_preview': result.get('result', '')[:200],
            'metrics_to_evaluate': list(self.quality_metrics.keys()),
            'evaluation_criteria': self.quality_metrics
        }
        
        return assessment_request
    
    def process_agent_self_assessment(self, agent_type: str, task_description: str,
                                    self_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработать самооценку агента
        """
        if not self_assessment:
            return {
                'assessed': False,
                'issues': ['No self-assessment provided'],
                'suggestions': ['Provide self-assessment for quality evaluation']
            }
        
        # Проверяем структуру самооценки
        scores = self_assessment.get('scores', {})
        explanations = self_assessment.get('explanations', {})
        
        issues = []
        suggestions = []
        
        # Проверка наличия всех метрик
        missing_metrics = set(self.quality_metrics.keys()) - set(scores.keys())
        if missing_metrics:
            issues.append(f'Missing metrics in self-assessment: {missing_metrics}')
            suggestions.append(f'Provide scores for all required metrics: {list(self.quality_metrics.keys())}')
        
        # Проверка диапазонов оценок
        invalid_scores = []
        for metric, score in scores.items():
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                invalid_scores.append(metric)
        
        if invalid_scores:
            issues.append(f'Invalid score ranges for metrics: {invalid_scores}')
            suggestions.append('Scores should be numbers between 0 and 1')
        
        # Проверка наличия объяснений
        missing_explanations = set(scores.keys()) - set(explanations.keys())
        if missing_explanations:
            issues.append(f'Missing explanations for metrics: {missing_explanations}')
            suggestions.append('Provide explanations for all scored metrics')
        
        # Вычисляем общий балл
        if scores:
            weighted_sum = 0
            total_weight = 0
            
            for metric, score in scores.items():
                if metric in self.quality_metrics:
                    weight = self.quality_metrics[metric]['weight']
                    weighted_sum += score * weight
                    total_weight += weight
            
            if total_weight > 0:
                overall_score = weighted_sum / total_weight
            else:
                overall_score = sum(scores.values()) / len(scores)
        else:
            overall_score = 0.0
        
        assessed = len(issues) == 0
        
        return {
            'assessed': assessed,
            'overall_score': overall_score,
            'scores': scores,
            'explanations': explanations,
            'issues': issues,
            'suggestions': suggestions,
            'details': {
                'metrics_evaluated': list(scores.keys()),
                'weighted_calculation': assessed
            }
        }
    
    def cross_validate_assessment(self, agent_type: str, task_description: str,
                                 self_assessment: Dict[str, Any], 
                                 actual_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Перекрестно проверить самооценку агента с реальными результатами
        """
        # Получаем самооценку
        assessment_result = self.process_agent_self_assessment(
            agent_type, task_description, self_assessment
        )
        
        # Сравниваем с реальными метриками качества
        real_metrics = self._calculate_real_metrics(agent_type, task_description, actual_result)
        
        # Сравниваем самооценку с реальными метриками
        comparison_results = {}
        discrepancies = []
        
        if assessment_result['assessed'] and 'scores' in assessment_result:
            self_scores = assessment_result['scores']
            
            for metric, real_score in real_metrics.items():
                if metric in self_scores:
                    self_score = self_scores[metric]
                    difference = abs(real_score - self_score)
                    
                    comparison_results[metric] = {
                        'self_assessed': self_score,
                        'real': real_score,
                        'difference': difference
                    }
                    
                    # Если разница больше 0.2, считаем это значительным расхождением
                    if difference > 0.2:
                        discrepancies.append({
                            'metric': metric,
                            'self_score': self_score,
                            'real_score': real_score,
                            'difference': difference
                        })
        
        # Вычисляем уровень достоверности самооценки
        if discrepancies:
            reliability_score = 1.0 - (len(discrepancies) / len(comparison_results) if comparison_results else 1.0)
        else:
            reliability_score = 1.0
        
        return {
            'self_assessment_result': assessment_result,
            'real_metrics': real_metrics,
            'comparison': comparison_results,
            'discrepancies': discrepancies,
            'reliability_score': reliability_score,
            'needs_calibration': reliability_score < 0.7
        }
    
    def _calculate_real_metrics(self, agent_type: str, task_description: str,
                               result: Dict[str, Any]) -> Dict[str, float]:
        """
        Вычислить реальные метрики качества результата
        """
        metrics = {}
        
        # Получаем результат выполнения
        result_content = result.get('result', '')
        artifacts = result.get('artifacts_created', [])
        
        # 1. Completeness - полнота выполнения
        completeness = self._calculate_completeness(task_description, result_content, artifacts)
        metrics['completeness'] = completeness
        
        # 2. Correctness - правильность выполнения
        correctness = self._calculate_correctness(result_content, agent_type)
        metrics['correctness'] = correctness
        
        # 3. Efficiency - эффективность
        efficiency = self._calculate_efficiency(result_content, artifacts)
        metrics['efficiency'] = efficiency
        
        # 4. Maintainability - поддерживаемость
        maintainability = self._calculate_maintainability(result_content, artifacts)
        metrics['maintainability'] = maintainability
        
        # 5. Innovation - инновационность
        innovation = self._calculate_innovation(result_content)
        metrics['innovation'] = innovation
        
        return metrics
    
    def _calculate_completeness(self, task_description: str, result_content: str, 
                              artifacts: List[str]) -> float:
        """
        Вычислить полноту выполнения задачи
        """
        # Простая эвристика: чем больше содержательного текста и артефактов, тем полнее выполнение
        content_length_score = min(1.0, len(result_content) / 500.0)
        artifacts_count_score = min(1.0, len(artifacts) / 3.0)
        
        # Проверяем наличие ключевых слов из задачи в результате
        task_keywords = set(task_description.lower().split())
        result_words = set(result_content.lower().split())
        keyword_overlap = len(task_keywords.intersection(result_words)) / max(len(task_keywords), 1)
        
        return (content_length_score + artifacts_count_score + keyword_overlap) / 3.0
    
    def _calculate_correctness(self, result_content: str, agent_type: str) -> float:
        """
        Вычислить правильность выполнения
        """
        # Проверяем отсутствие запрещенных паттернов
        forbidden_patterns = ['NEEDS_CLARIFICATION', 'TODO', 'FIXME', 'placeholder']
        forbidden_count = sum(1 for pattern in forbidden_patterns if pattern in result_content)
        
        # Чем меньше запрещенных паттернов, тем лучше
        forbidden_penalty = min(1.0, forbidden_count / 3.0)
        
        # Проверяем соответствие типу агента
        agent_specific_patterns = {
            'backend_dev': ['def ', 'return', 'import'],
            'frontend_dev': ['function', 'const', 'return'],
            'doc_writer': ['#', '##', '###'],
            'tester': ['test_', 'assert', 'mock'],
            'researcher': ['##', '###', 'research'],
            'devops': ['FROM', 'RUN', 'CMD']
        }
        
        patterns = agent_specific_patterns.get(agent_type, [])
        pattern_score = sum(1 for pattern in patterns if pattern in result_content) / max(len(patterns), 1)
        
        return max(0.0, (1.0 - forbidden_penalty + pattern_score) / 2.0)
    
    def _calculate_efficiency(self, result_content: str, artifacts: List[str]) -> float:
        """
        Вычислить эффективность выполнения
        """
        # Оцениваем по длине кода/документации - не слишком длинно, не слишком коротко
        content_length = len(result_content)
        
        if content_length < 50:
            # Слишком коротко
            length_score = content_length / 50.0
        elif content_length > 2000:
            # Слишком длинно
            length_score = max(0.0, 1.0 - (content_length - 2000) / 2000.0)
        else:
            # Оптимальная длина
            length_score = 1.0
        
        # Оцениваем количество артефактов
        artifacts_score = min(1.0, len(artifacts) / 2.0)
        
        return (length_score + artifacts_score) / 2.0
    
    def _calculate_maintainability(self, result_content: str, artifacts: List[str]) -> float:
        """
        Вычислить поддерживаемость результата
        """
        # Проверяем структурированность (наличие заголовков, секций)
        structure_indicators = ['#', '##', '###', '\n\n', '- ', '* ']
        structure_score = sum(1 for indicator in structure_indicators if indicator in result_content) / len(structure_indicators)
        
        # Проверяем наличие комментариев/документации
        comment_indicators = ['"""', "'''", '//', '/*', '<!--']
        comment_score = min(1.0, sum(1 for indicator in comment_indicators if indicator in result_content) / 3.0)
        
        return (structure_score + comment_score) / 2.0
    
    def _calculate_innovation(self, result_content: str) -> float:
        """
        Вычислить инновационность подхода
        """
        # Простая эвристика: наличие уникальных терминов и подходов
        unique_words = set(result_content.lower().split())
        unique_word_ratio = len(unique_words) / max(len(result_content.split()), 1)
        
        # Проверяем наличие технологических терминов
        tech_terms = ['async', 'await', 'decorator', 'generator', 'context', 'lambda', 
                     'comprehension', 'closure', 'mixin', 'metaclass', 'coroutine']
        tech_term_score = min(1.0, sum(1 for term in tech_terms if term in result_content) / 5.0)
        
        return (unique_word_ratio + tech_term_score) / 2.0

# Глобальная система самооценки
self_assessment_system = SelfAssessmentSystem()