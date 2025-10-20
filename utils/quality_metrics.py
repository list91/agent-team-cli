from typing import Dict, List, Any, Tuple
from datetime import datetime
import statistics
import math

class QualityMetricsSystem:
    """
    Система измерения и оценки качества артефактов
    """
    
    def __init__(self):
        self.metric_definitions = {}
        self.historical_data = {}
        self.benchmarks = {}
        
        # Инициализируем систему метрик
        self._initialize_metric_definitions()
    
    def _initialize_metric_definitions(self):
        """
        Инициализировать определения метрик качества
        """
        self.metric_definitions = {
            'code_quality': {
                'metrics': {
                    'lines_of_code': {
                        'type': 'count',
                        'range': (10, 1000),
                        'weight': 0.15,
                        'description': 'Number of lines of code'
                    },
                    'function_count': {
                        'type': 'count',
                        'range': (1, 50),
                        'weight': 0.2,
                        'description': 'Number of functions/methods'
                    },
                    'comment_ratio': {
                        'type': 'ratio',
                        'range': (0.1, 0.5),
                        'weight': 0.15,
                        'description': 'Ratio of comments to code'
                    },
                    'cyclomatic_complexity': {
                        'type': 'complexity',
                        'range': (1, 10),
                        'weight': 0.25,
                        'description': 'Average cyclomatic complexity'
                    },
                    'duplication_ratio': {
                        'type': 'ratio',
                        'range': (0.0, 0.2),
                        'weight': 0.25,
                        'description': 'Code duplication ratio'
                    }
                },
                'artifact_types': ['python', 'javascript', 'java', 'cpp']
            },
            'documentation_quality': {
                'metrics': {
                    'section_count': {
                        'type': 'count',
                        'range': (3, 20),
                        'weight': 0.2,
                        'description': 'Number of sections'
                    },
                    'word_count': {
                        'type': 'count',
                        'range': (100, 2000),
                        'weight': 0.15,
                        'description': 'Total word count'
                    },
                    'link_count': {
                        'type': 'count',
                        'range': (0, 20),
                        'weight': 0.1,
                        'description': 'Number of external links'
                    },
                    'example_count': {
                        'type': 'count',
                        'range': (1, 10),
                        'weight': 0.25,
                        'description': 'Number of code examples'
                    },
                    'readability_score': {
                        'type': 'score',
                        'range': (0.5, 1.0),
                        'weight': 0.3,
                        'description': 'Text readability score'
                    }
                },
                'artifact_types': ['markdown', 'rst', 'txt']
            },
            'test_quality': {
                'metrics': {
                    'test_count': {
                        'type': 'count',
                        'range': (2, 100),
                        'weight': 0.25,
                        'description': 'Number of test functions'
                    },
                    'assertion_count': {
                        'type': 'count',
                        'range': (5, 500),
                        'weight': 0.3,
                        'description': 'Total number of assertions'
                    },
                    'coverage_percentage': {
                        'type': 'percentage',
                        'range': (70, 100),
                        'weight': 0.25,
                        'description': 'Code coverage percentage'
                    },
                    'test_depth': {
                        'type': 'score',
                        'range': (0.5, 1.0),
                        'weight': 0.2,
                        'description': 'Test depth and edge case coverage'
                    }
                },
                'artifact_types': ['test_file', 'test_suite']
            },
            'research_quality': {
                'metrics': {
                    'source_count': {
                        'type': 'count',
                        'range': (3, 50),
                        'weight': 0.25,
                        'description': 'Number of cited sources'
                    },
                    'analysis_depth': {
                        'type': 'score',
                        'range': (0.5, 1.0),
                        'weight': 0.3,
                        'description': 'Depth of analysis'
                    },
                    'recommendation_quality': {
                        'type': 'score',
                        'range': (0.6, 1.0),
                        'weight': 0.25,
                        'description': 'Quality of recommendations'
                    },
                    'citation_accuracy': {
                        'type': 'score',
                        'range': (0.8, 1.0),
                        'weight': 0.2,
                        'description': 'Accuracy of citations'
                    }
                },
                'artifact_types': ['research_paper', 'analysis_report']
            },
            'devops_quality': {
                'metrics': {
                    'config_completeness': {
                        'type': 'score',
                        'range': (0.7, 1.0),
                        'weight': 0.3,
                        'description': 'Completeness of configuration'
                    },
                    'security_checks': {
                        'type': 'count',
                        'range': (3, 20),
                        'weight': 0.25,
                        'description': 'Number of security checks'
                    },
                    'error_handling': {
                        'type': 'score',
                        'range': (0.6, 1.0),
                        'weight': 0.25,
                        'description': 'Quality of error handling'
                    },
                    'documentation_clarity': {
                        'type': 'score',
                        'range': (0.7, 1.0),
                        'weight': 0.2,
                        'description': 'Clarity of documentation'
                    }
                },
                'artifact_types': ['dockerfile', 'yaml', 'yml', 'sh']
            }
        }
    
    def calculate_quality_metrics(self, artifact_content: str, 
                                 artifact_type: str, 
                                 artifact_path: str = None) -> Dict[str, Any]:
        """
        Рассчитать метрики качества для артефакта
        """
        # Определяем тип артефакта, если не указан
        if not artifact_type and artifact_path:
            artifact_type = self._detect_artifact_type(artifact_path)
        
        # Получаем подходящие метрики для типа артефакта
        relevant_metrics = self._get_relevant_metrics(artifact_type)
        
        if not relevant_metrics:
            return {
                'overall_score': 0.0,
                'metrics': {},
                'issues': [f'No quality metrics defined for artifact type: {artifact_type}'],
                'suggestions': ['Define quality metrics for this artifact type']
            }
        
        # Рассчитываем метрики
        calculated_metrics = {}
        metric_scores = {}
        
        for metric_name, metric_definition in relevant_metrics.items():
            metric_value = self._calculate_single_metric(
                metric_name, 
                metric_definition, 
                artifact_content, 
                artifact_type
            )
            
            calculated_metrics[metric_name] = metric_value
            
            # Оцениваем качество метрики
            metric_score = self._score_metric(
                metric_name, 
                metric_value, 
                metric_definition
            )
            metric_scores[metric_name] = metric_score
        
        # Рассчитываем общий балл
        overall_score = self._calculate_overall_score(metric_scores, relevant_metrics)
        
        # Генерируем предложения по улучшению
        suggestions = self._generate_improvement_suggestions(
            calculated_metrics, 
            metric_scores, 
            relevant_metrics
        )
        
        return {
            'overall_score': overall_score,
            'metrics': calculated_metrics,
            'metric_scores': metric_scores,
            'suggestions': suggestions,
            'artifact_type': artifact_type
        }
    
    def _detect_artifact_type(self, artifact_path: str) -> str:
        """
        Определить тип артефакта по пути к файлу
        """
        if not artifact_path:
            return 'unknown'
        
        # Извлекаем расширение
        if '.' in artifact_path:
            extension = artifact_path.split('.')[-1].lower()
        else:
            extension = 'unknown'
        
        # Определяем тип по расширению
        extension_mapping = {
            'py': 'python',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'md': 'markdown',
            'rst': 'rst',
            'txt': 'txt',
            'yml': 'yaml',
            'yaml': 'yaml',
            'json': 'json',
            'dockerfile': 'dockerfile',
            'sh': 'shell'
        }
        
        return extension_mapping.get(extension, 'unknown')
    
    def _get_relevant_metrics(self, artifact_type: str) -> Dict[str, Any]:
        """
        Получить релевантные метрики для типа артефакта
        """
        for category, definition in self.metric_definitions.items():
            if artifact_type in definition['artifact_types']:
                return definition['metrics']
        
        # Если не найдено, возвращаем метрики по умолчанию
        return self.metric_definitions.get('documentation_quality', {}).get('metrics', {})
    
    def _calculate_single_metric(self, metric_name: str, 
                                 metric_definition: Dict[str, Any], 
                                 artifact_content: str, 
                                 artifact_type: str) -> float:
        """
        Рассчитать значение одной метрики
        """
        try:
            if metric_name == 'lines_of_code':
                return self._count_lines(artifact_content)
            elif metric_name == 'function_count':
                return self._count_functions(artifact_content, artifact_type)
            elif metric_name == 'comment_ratio':
                return self._calculate_comment_ratio(artifact_content, artifact_type)
            elif metric_name == 'cyclomatic_complexity':
                return self._estimate_cyclomatic_complexity(artifact_content, artifact_type)
            elif metric_name == 'duplication_ratio':
                return self._estimate_duplication_ratio(artifact_content)
            elif metric_name == 'section_count':
                return self._count_sections(artifact_content)
            elif metric_name == 'word_count':
                return self._count_words(artifact_content)
            elif metric_name == 'link_count':
                return self._count_links(artifact_content)
            elif metric_name == 'example_count':
                return self._count_examples(artifact_content)
            elif metric_name == 'readability_score':
                return self._calculate_readability_score(artifact_content)
            elif metric_name == 'test_count':
                return self._count_tests(artifact_content, artifact_type)
            elif metric_name == 'assertion_count':
                return self._count_assertions(artifact_content, artifact_type)
            elif metric_name == 'coverage_percentage':
                return self._estimate_coverage_percentage(artifact_content)
            elif metric_name == 'test_depth':
                return self._estimate_test_depth(artifact_content)
            elif metric_name == 'source_count':
                return self._count_sources(artifact_content)
            elif metric_name == 'analysis_depth':
                return self._estimate_analysis_depth(artifact_content)
            elif metric_name == 'recommendation_quality':
                return self._estimate_recommendation_quality(artifact_content)
            elif metric_name == 'citation_accuracy':
                return self._estimate_citation_accuracy(artifact_content)
            elif metric_name == 'config_completeness':
                return self._estimate_config_completeness(artifact_content)
            elif metric_name == 'security_checks':
                return self._count_security_checks(artifact_content)
            elif metric_name == 'error_handling':
                return self._estimate_error_handling_quality(artifact_content)
            elif metric_name == 'documentation_clarity':
                return self._estimate_documentation_clarity(artifact_content)
            else:
                # По умолчанию возвращаем 0.5
                return 0.5
                
        except Exception as e:
            # В случае ошибки возвращаем 0.0
            return 0.0
    
    def _count_lines(self, content: str) -> int:
        """Посчитать количество строк"""
        return len(content.split('\n'))
    
    def _count_functions(self, content: str, artifact_type: str) -> int:
        """Посчитать количество функций"""
        if artifact_type == 'python':
            return len([line for line in content.split('\n') if line.strip().startswith('def ')])
        elif artifact_type in ['javascript', 'typescript']:
            return len([line for line in content.split('\n') if 'function' in line or '=>' in line])
        else:
            return 0
    
    def _calculate_comment_ratio(self, content: str, artifact_type: str) -> float:
        """Рассчитать отношение комментариев к коду"""
        lines = content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return 0.0
        
        comment_lines = 0
        if artifact_type == 'python':
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
        elif artifact_type in ['javascript', 'typescript']:
            comment_lines = len([line for line in lines if '//' in line or '/*' in line])
        
        return comment_lines / total_lines if total_lines > 0 else 0.0
    
    def _estimate_cyclomatic_complexity(self, content: str, artifact_type: str) -> float:
        """Оценить цикломатическую сложность"""
        # Простая эвристика: считаем ветвления
        branching_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch']
        complexity = 1  # Базовая сложность
        
        for keyword in branching_keywords:
            complexity += content.count(keyword)
        
        # Нормализуем (простая эвристика)
        return min(1.0, complexity / 20.0)
    
    def _estimate_duplication_ratio(self, content: str) -> float:
        """Оценить отношение дублирования"""
        # Простая эвристика: ищем повторяющиеся строки
        lines = content.split('\n')
        unique_lines = set(lines)
        
        if len(lines) == 0:
            return 0.0
        
        duplication_ratio = (len(lines) - len(unique_lines)) / len(lines)
        return min(1.0, duplication_ratio)
    
    def _count_sections(self, content: str) -> int:
        """Посчитать количество секций (заголовков)"""
        import re
        # Ищем заголовки в формате Markdown (#, ##, ###, etc.)
        headers = re.findall(r'^#+\s+.*$', content, re.MULTILINE)
        return len(headers)
    
    def _count_words(self, content: str) -> int:
        """Посчитать количество слов"""
        import re
        words = re.findall(r'\b\w+\b', content)
        return len(words)
    
    def _count_links(self, content: str) -> int:
        """Посчитать количество ссылок"""
        import re
        # Ищем URL-ссылки
        urls = re.findall(r'https?://[^\s]+', content)
        # Ищем markdown ссылки
        md_links = re.findall(r'\[.*?\]\(.*?\)', content)
        return len(urls) + len(md_links)
    
    def _count_examples(self, content: str) -> int:
        """Посчитать количество примеров кода"""
        import re
        # Ищем блоки кода в markdown
        code_blocks = re.findall(r'```.*?```', content, re.DOTALL)
        return len(code_blocks)
    
    def _calculate_readability_score(self, content: str) -> float:
        """Рассчитать оценку читаемости"""
        # Простая эвристика: средняя длина предложений
        import re
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) == 0:
            return 0.5
        
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
        
        # Чем короче предложения, тем выше читаемость (обратная шкала)
        readability = max(0.0, min(1.0, 1.0 - (avg_sentence_length / 50.0)))
        return readability
    
    def _count_tests(self, content: str, artifact_type: str) -> int:
        """Посчитать количество тестов"""
        if artifact_type == 'python':
            return len([line for line in content.split('\n') if line.strip().startswith('def test_')])
        elif artifact_type in ['javascript', 'typescript']:
            return len([line for line in content.split('\n') if 'test(' in line or 'it(' in line])
        else:
            return 0
    
    def _count_assertions(self, content: str, artifact_type: str) -> int:
        """Посчитать количество утверждений"""
        if artifact_type == 'python':
            return content.count('assert') + content.count('self.assertEqual')
        elif artifact_type in ['javascript', 'typescript']:
            return content.count('expect(') + content.count('assert.')
        else:
            return 0
    
    def _estimate_coverage_percentage(self, content: str) -> float:
        """Оценить процент покрытия"""
        # Простая эвристика: отношение строк тестов к строкам кода
        code_lines = len(content.split('\n'))
        test_lines = len([line for line in content.split('\n') if 'test_' in line or 'assert' in line])
        
        if code_lines == 0:
            return 0.5  # По умолчанию
        
        coverage = (test_lines / code_lines) * 100
        return min(1.0, coverage / 100.0)
    
    def _estimate_test_depth(self, content: str) -> float:
        """Оценить глубину тестирования"""
        # Ищем признаки тестирования граничных условий
        depth_indicators = [
            'boundary', 'edge case', 'exception', 'error', 'invalid',
            'null', 'empty', 'zero', 'negative', 'positive'
        ]
        
        depth_score = 0
        content_lower = content.lower()
        
        for indicator in depth_indicators:
            if indicator in content_lower:
                depth_score += 1
        
        # Нормализуем (простая эвристика)
        return min(1.0, depth_score / 5.0)
    
    def _count_sources(self, content: str) -> int:
        """Посчитать количество источников"""
        import re
        # Ищем ссылки и цитаты
        urls = re.findall(r'https?://[^\s]+', content)
        citations = re.findall(r'\[[^\]]+\]', content)  # Markdown-style ссылки
        return len(urls) + len(citations)
    
    def _estimate_analysis_depth(self, content: str) -> float:
        """Оценить глубину анализа"""
        # Ищем индикаторы глубокого анализа
        depth_indicators = [
            'analysis', 'investigation', 'study', 'research', 'examination',
            'evaluation', 'assessment', 'review'
        ]
        
        depth_score = 0
        content_lower = content.lower()
        
        for indicator in depth_indicators:
            depth_score += content_lower.count(indicator)
        
        # Нормализуем
        return min(1.0, depth_score / 10.0)
    
    def _estimate_recommendation_quality(self, content: str) -> float:
        """Оценить качество рекомендаций"""
        # Ищем признаки хороших рекомендаций
        quality_indicators = [
            'recommended', 'suggestion', 'advantage', 'benefit', 'improvement',
            'best practice', 'consider', 'should', 'could'
        ]
        
        quality_score = 0
        content_lower = content.lower()
        
        for indicator in quality_indicators:
            quality_score += content_lower.count(indicator)
        
        # Нормализуем
        return min(1.0, quality_score / 15.0)
    
    def _estimate_citation_accuracy(self, content: str) -> float:
        """Оценить точность цитирования"""
        # Простая эвристика: предполагаем хорошую точность по умолчанию
        return 0.9  # Высокая оценка по умолчанию
    
    def _estimate_config_completeness(self, content: str) -> float:
        """Оценить полноту конфигурации"""
        # Ищем основные элементы конфигурации
        config_elements = [
            'FROM', 'RUN', 'COPY', 'EXPOSE', 'CMD', 'ENTRYPOINT',  # Dockerfile
            'version:', 'services:', 'image:', 'ports:', 'volumes:'  # Docker Compose/YAML
        ]
        
        completeness_score = 0
        for element in config_elements:
            if element in content:
                completeness_score += 1
        
        # Нормализуем
        return min(1.0, completeness_score / len(config_elements))
    
    def _count_security_checks(self, content: str) -> int:
        """Посчитать количество проверок безопасности"""
        security_keywords = [
            'security', 'encrypt', 'decrypt', 'password', 'secret',
            'validate', 'sanitize', 'permission', 'auth', 'certificate'
        ]
        
        count = 0
        content_lower = content.lower()
        
        for keyword in security_keywords:
            count += content_lower.count(keyword)
        
        return count
    
    def _estimate_error_handling_quality(self, content: str) -> float:
        """Оценить качество обработки ошибок"""
        # Ищем признаки обработки ошибок
        error_handling_indicators = [
            'try:', 'except:', 'finally:',  # Python
            'try {', 'catch(', 'finally {',  # JavaScript
            'error', 'handle', 'recover', 'fallback'
        ]
        
        quality_score = 0
        content_lower = content.lower()
        
        for indicator in error_handling_indicators:
            quality_score += content_lower.count(indicator)
        
        # Нормализуем
        return min(1.0, quality_score / 10.0)
    
    def _estimate_documentation_clarity(self, content: str) -> float:
        """Оценить ясность документации"""
        # Простая эвристика: наличие структуры и объяснений
        structure_indicators = ['#', '##', '###', '1.', '2.', '-', '*']
        clarity_score = 0
        
        for indicator in structure_indicators:
            if indicator in content:
                clarity_score += 1
        
        # Нормализуем
        return min(1.0, clarity_score / len(structure_indicators))
    
    def _score_metric(self, metric_name: str, 
                     metric_value: float, 
                     metric_definition: Dict[str, Any]) -> float:
        """
        Оценить качество отдельной метрики
        """
        optimal_range = metric_definition['range']
        min_value, max_value = optimal_range
        
        if min_value <= metric_value <= max_value:
            # Значение в оптимальном диапазоне
            return 1.0
        elif metric_value < min_value:
            # Значение ниже оптимального
            if min_value == 0:
                return max(0.0, 1.0 - (min_value - metric_value) / (min_value + 1))
            else:
                return max(0.0, metric_value / min_value)
        else:
            # Значение выше оптимального
            return max(0.0, 1.0 - (metric_value - max_value) / max_value)
    
    def _calculate_overall_score(self, metric_scores: Dict[str, float], 
                                 metrics_definition: Dict[str, Any]) -> float:
        """
        Рассчитать общий балл качества
        """
        if not metric_scores:
            return 0.0
        
        # Взвешенное среднее
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_name, score in metric_scores.items():
            if metric_name in metrics_definition:
                weight = metrics_definition[metric_name]['weight']
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight == 0:
            # Если веса не определены, используем простое среднее
            return sum(metric_scores.values()) / len(metric_scores)
        
        return weighted_sum / total_weight
    
    def _generate_improvement_suggestions(self, calculated_metrics: Dict[str, float], 
                                         metric_scores: Dict[str, float], 
                                         metrics_definition: Dict[str, Any]) -> List[str]:
        """
        Сгенерировать предложения по улучшению
        """
        suggestions = []
        
        for metric_name, score in metric_scores.items():
            if score < 0.7:  # Низкая оценка
                metric_info = metrics_definition.get(metric_name, {})
                description = metric_info.get('description', metric_name)
                suggestions.append(f'Improve {description} (current score: {score:.2f})')
            elif score < 0.9:  # Средняя оценка
                metric_info = metrics_definition.get(metric_name, {})
                description = metric_info.get('description', metric_name)
                suggestions.append(f'Consider enhancing {description} for better quality')
        
        return suggestions
    
    def get_benchmark_comparison(self, current_metrics: Dict[str, Any], 
                               artifact_type: str) -> Dict[str, Any]:
        """
        Сравнить метрики с эталонными значениями
        """
        benchmarks = self.benchmarks.get(artifact_type, {})
        
        if not benchmarks:
            return {
                'comparison_available': False,
                'message': f'No benchmarks available for artifact type: {artifact_type}'
            }
        
        comparison_results = {}
        better_metrics = []
        worse_metrics = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name in benchmarks:
                benchmark_value = benchmarks[metric_name]
                
                if current_value >= benchmark_value:
                    comparison_results[metric_name] = 'better_or_equal'
                    better_metrics.append(metric_name)
                else:
                    comparison_results[metric_name] = 'worse'
                    worse_metrics.append(metric_name)
        
        return {
            'comparison_available': True,
            'results': comparison_results,
            'better_metrics': better_metrics,
            'worse_metrics': worse_metrics,
            'improvement_needed': len(worse_metrics) > 0
        }
    
    def update_benchmarks(self, artifact_type: str, new_benchmarks: Dict[str, float]):
        """
        Обновить эталонные значения для типа артефакта
        """
        if artifact_type not in self.benchmarks:
            self.benchmarks[artifact_type] = {}
        
        self.benchmarks[artifact_type].update(new_benchmarks)
    
    def get_quality_report(self, artifact_content: str, 
                          artifact_type: str, 
                          artifact_path: str = None) -> Dict[str, Any]:
        """
        Получить полный отчет по качеству артефакта
        """
        # Рассчитываем метрики
        quality_metrics = self.calculate_quality_metrics(
            artifact_content, 
            artifact_type, 
            artifact_path
        )
        
        # Получаем сравнение с эталонами
        benchmark_comparison = self.get_benchmark_comparison(
            quality_metrics.get('metrics', {}), 
            artifact_type
        )
        
        return {
            'artifact_info': {
                'type': artifact_type,
                'path': artifact_path
            },
            'quality_metrics': quality_metrics,
            'benchmark_comparison': benchmark_comparison,
            'timestamp': datetime.now().isoformat(),
            'quality_assessment': self._assess_overall_quality(quality_metrics['overall_score'])
        }
    
    def _assess_overall_quality(self, overall_score: float) -> str:
        """
        Оценить общее качество
        """
        if overall_score >= 0.9:
            return 'excellent'
        elif overall_score >= 0.7:
            return 'good'
        elif overall_score >= 0.5:
            return 'acceptable'
        else:
            return 'needs_improvement'

# Глобальная система метрик качества
quality_metrics = QualityMetricsSystem()