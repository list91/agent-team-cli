from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
import json
import os
import re

class QualityControlSystem:
    """
    Система контроля качества выполнения задач
    """
    
    def __init__(self):
        self.quality_standards = {
            'code_generation': {
                'min_lines': 10,
                'required_elements': ['function', 'return', 'docstring'],
                'forbidden_patterns': ['TODO', 'FIXME', 'NEEDS_CLARIFICATION'],
                'complexity_threshold': 2  # Минимальная сложность
            },
            'documentation': {
                'min_sections': 3,
                'required_headers': ['Usage', 'Installation', 'Examples'],
                'min_word_count': 100,
                'forbidden_patterns': ['TBD', 'To be determined']
            },
            'testing': {
                'min_test_functions': 2,
                'required_assertions': True,
                'coverage_indicators': ['assert', 'test', 'mock'],
                'min_lines': 15
            },
            'research': {
                'min_sources': 3,
                'required_structure': ['Introduction', 'Methodology', 'Conclusion'],
                'min_citations': 2,
                'min_word_count': 200
            },
            'devops': {
                'required_configs': ['Dockerfile', 'docker-compose'],
                'min_steps': 3,
                'required_validators': ['syntax check', 'linting'],
                'min_lines': 15
            }
        }
    
    def validate_artifact_quality(self, artifact_path: str, artifact_type: str) -> Dict[str, Any]:
        """
        Проверить качество артефакта
        """
        try:
            path = Path(artifact_path)
            if not path.exists():
                return {
                    'valid': False,
                    'score': 0.0,
                    'issues': ['File does not exist'],
                    'suggestions': ['Create the required file']
                }
            
            # Читаем содержимое файла
            content = path.read_text(encoding='utf-8')
            
            # Определяем тип артефакта, если не указан
            if not artifact_type:
                artifact_type = self._detect_artifact_type(path.suffix, content)
            
            # Получаем стандарты качества для типа артефакта
            standards = self.quality_standards.get(artifact_type, {})
            
            # Проверяем качество
            validation_result = self._perform_validation(content, standards, artifact_type)
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'score': 0.0,
                'issues': [f'Error reading file: {str(e)}'],
                'suggestions': ['Fix file access issues']
            }
    
    def _detect_artifact_type(self, extension: str, content: str) -> str:
        """
        Определить тип артефакта по расширению и содержимому
        """
        extension_map = {
            '.py': 'code_generation',
            '.js': 'code_generation',
            '.jsx': 'code_generation',
            '.ts': 'code_generation',
            '.md': 'documentation',
            '.txt': 'documentation',
            '.yml': 'devops',
            '.yaml': 'devops',
            '.json': 'documentation',
            '.dockerfile': 'devops',
            '.sh': 'devops'
        }
        
        if extension.lower() in extension_map:
            return extension_map[extension.lower()]
        
        # Определяем по содержимому
        if 'def ' in content and 'return' in content:
            return 'code_generation'
        elif '#' in content or '##' in content:
            return 'documentation'
        elif 'FROM' in content and 'RUN' in content:
            return 'devops'
        else:
            return 'documentation'  # По умолчанию
    
    def _perform_validation(self, content: str, standards: Dict[str, Any], 
                          artifact_type: str) -> Dict[str, Any]:
        """
        Выполнить проверку качества контента по стандартам
        """
        issues = []
        suggestions = []
        score_components = []
        
        # Проверка минимального количества строк
        lines = content.strip().split('\n')
        line_count = len(lines)
        
        if 'min_lines' in standards and line_count < standards['min_lines']:
            issues.append(f'Too few lines: {line_count}, minimum required: {standards["min_lines"]}')
            suggestions.append(f'Add more content to reach minimum {standards["min_lines"]} lines')
        else:
            score_components.append(min(1.0, line_count / (standards.get('min_lines', 10) * 2)))
        
        # Проверка запрещенных паттернов
        if 'forbidden_patterns' in standards:
            for pattern in standards['forbidden_patterns']:
                if pattern in content:
                    issues.append(f'Forbidden pattern found: {pattern}')
                    suggestions.append(f'Remove or replace "{pattern}" with actual content')
        
        # Проверка требуемых элементов
        if 'required_elements' in standards:
            missing_elements = []
            for element in standards['required_elements']:
                if element not in content.lower():
                    missing_elements.append(element)
            
            if missing_elements:
                issues.append(f'Missing required elements: {missing_elements}')
                suggestions.append(f'Add the following elements: {missing_elements}')
            else:
                score_components.append(1.0)
        
        # Специфические проверки для разных типов
        if artifact_type == 'code_generation':
            code_issues, code_suggestions, code_score = self._validate_code_quality(content, standards)
            issues.extend(code_issues)
            suggestions.extend(code_suggestions)
            score_components.append(code_score)
        
        elif artifact_type == 'documentation':
            doc_issues, doc_suggestions, doc_score = self._validate_documentation_quality(content, standards)
            issues.extend(doc_issues)
            suggestions.extend(doc_suggestions)
            score_components.append(doc_score)
        
        elif artifact_type == 'testing':
            test_issues, test_suggestions, test_score = self._validate_testing_quality(content, standards)
            issues.extend(test_issues)
            suggestions.extend(test_suggestions)
            score_components.append(test_score)
        
        # Вычисляем общий счет
        if score_components:
            average_score = sum(score_components) / len(score_components)
        else:
            average_score = 0.5  # По умолчанию
        
        return {
            'valid': len(issues) == 0,
            'score': min(1.0, average_score),  # Максимум 1.0
            'issues': issues,
            'suggestions': suggestions,
            'artifact_type': artifact_type
        }
    
    def _validate_code_quality(self, content: str, standards: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """
        Проверить качество кода
        """
        issues = []
        suggestions = []
        scores = []
        
        # Проверка наличия функций
        function_count = len(re.findall(r'def\s+\w+\s*\(', content))
        if function_count < 1:
            issues.append('No functions found')
            suggestions.append('Add at least one function')
        else:
            scores.append(min(1.0, function_count / 3.0))
        
        # Проверка наличия docstring
        if '"""' not in content and "'''" not in content:
            issues.append('No docstrings found')
            suggestions.append('Add docstrings to functions')
        else:
            scores.append(1.0)
        
        # Проверка наличия return
        if 'return' not in content:
            issues.append('No return statements found')
            suggestions.append('Add return statements where appropriate')
        else:
            scores.append(1.0)
        
        # Проверка сложности (упрощенная)
        complexity_score = min(1.0, len(content.split('\n')) / 50.0)
        scores.append(complexity_score)
        
        average_score = sum(scores) / len(scores) if scores else 0.5
        return issues, suggestions, average_score
    
    def _validate_documentation_quality(self, content: str, standards: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """
        Проверить качество документации
        """
        issues = []
        suggestions = []
        scores = []
        
        # Подсчет слов
        words = re.findall(r'\b\w+\b', content)
        word_count = len(words)
        
        if 'min_word_count' in standards and word_count < standards['min_word_count']:
            issues.append(f'Too few words: {word_count}, minimum required: {standards["min_word_count"]}')
            suggestions.append(f'Add more content to reach minimum {standards["min_word_count"]} words')
        else:
            scores.append(min(1.0, word_count / (standards.get('min_word_count', 100) * 2)))
        
        # Проверка заголовков
        headers = re.findall(r'^#{1,6}\s+.+', content, re.MULTILINE)
        header_count = len(headers)
        
        if header_count < 2:
            issues.append('Too few headers')
            suggestions.append('Add more section headers')
        else:
            scores.append(min(1.0, header_count / 5.0))
        
        average_score = sum(scores) / len(scores) if scores else 0.5
        return issues, suggestions, average_score
    
    def _validate_testing_quality(self, content: str, standards: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """
        Проверить качество тестов
        """
        issues = []
        suggestions = []
        scores = []
        
        # Подсчет тестовых функций
        test_functions = len(re.findall(r'def\s+test_\w+|def\s+\w+_test', content))
        
        if test_functions < 1:
            issues.append('No test functions found')
            suggestions.append('Add test functions with names starting with "test_"')
        else:
            scores.append(min(1.0, test_functions / 3.0))
        
        # Проверка наличия assert
        if 'assert' not in content:
            issues.append('No assertions found')
            suggestions.append('Add assert statements to verify behavior')
        else:
            scores.append(1.0)
        
        average_score = sum(scores) / len(scores) if scores else 0.5
        return issues, suggestions, average_score
    
    def validate_result_quality(self, result: Dict[str, Any], 
                              agent_type: str, 
                              task_description: str, 
                              session_id: str) -> Dict[str, Any]:
        """
        Проверить качество результата выполнения задачи
        """
        # Проверяем качество результата
        quality_score = self._calculate_result_quality_score(result, agent_type, task_description)
        
        # Проверяем наличие ошибок
        issues = self._identify_result_issues(result, agent_type, task_description)
        
        # Проверяем соответствие специализации
        specialization_match = self._validate_specialization_match(agent_type, task_description, result)
        
        # Проверяем полноту выполнения
        completeness = self._assess_result_completeness(result, task_description)
        
        # Объединяем все метрики
        overall_valid = (
            quality_score >= 0.6 and  # Минимальный балл качества
            len(issues) == 0 and      # Нет критических проблем
            specialization_match and   # Соответствует специализации
            completeness >= 0.7       # Достаточно полное выполнение
        )
        
        return {
            'valid': overall_valid,
            'quality_score': quality_score,
            'issues': issues,
            'specialization_match': specialization_match,
            'completeness': completeness,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_result_quality_score(self, result: Dict[str, Any], 
                                     agent_type: str, 
                                     task_description: str) -> float:
        """
        Рассчитать балл качества результата
        """
        # Получаем содержание результата
        result_content = result.get('result', '')
        artifacts = result.get('artifacts_created', [])
        
        # Базовый балл
        base_score = 0.5
        
        # Добавляем баллы за объем результата
        content_length_score = min(1.0, len(result_content) / 500.0)
        base_score += content_length_score * 0.2
        
        # Добавляем баллы за количество артефактов
        artifacts_count_score = min(1.0, len(artifacts) / 3.0)
        base_score += artifacts_count_score * 0.15
        
        # Добавляем баллы за отсутствие запрещенных паттернов
        forbidden_patterns = ['NEEDS_CLARIFICATION', 'TODO', 'FIXME', 'placeholder']
        forbidden_count = sum(1 for pattern in forbidden_patterns if pattern in result_content)
        forbidden_penalty = min(1.0, forbidden_count / 3.0)
        base_score -= forbidden_penalty * 0.15
        
        # Ограничиваем диапазон от 0.0 до 1.0
        return max(0.0, min(1.0, base_score))
    
    def _identify_result_issues(self, result: Dict[str, Any], 
                              agent_type: str, 
                              task_description: str) -> List[str]:
        """
        Идентифицировать проблемы в результате
        """
        issues = []
        
        # Проверяем содержание результата
        result_content = result.get('result', '')
        
        # Проверяем на запрещенные паттерны
        forbidden_patterns = ['NEEDS_CLARIFICATION', 'TODO', 'FIXME', 'placeholder']
        for pattern in forbidden_patterns:
            if pattern in result_content:
                issues.append(f'Forbidden pattern found: {pattern}')
        
        # Проверяем длину результата
        if len(result_content) < 20:
            issues.append('Result content is too short')
        
        # Проверяем наличие артефактов
        artifacts = result.get('artifacts_created', [])
        if not artifacts:
            issues.append('No artifacts created')
        
        # Проверяем ошибки выполнения
        if 'error' in result or 'Error' in result_content:
            issues.append('Execution error detected')
        
        return issues
    
    def _validate_specialization_match(self, agent_type: str, 
                                    task_description: str, 
                                    result: Dict[str, Any]) -> bool:
        """
        Проверить соответствие результата специализации агента
        """
        # Простая проверка - результат должен содержать ключевые слова, соответствующие специализации
        specialization_keywords = {
            'researcher': ['research', 'study', 'analyze', 'examine', 'investigate', 'evaluate', 'gather information', 'best practices'],
            'backend_dev': ['backend', 'server', 'api', 'flask', 'django', 'programming', 'code', 'implementation', 'backend', 'server-side'],
            'frontend_dev': ['frontend', 'ui', 'react', 'vue', 'html', 'css', 'client-side', 'interface', 'frontend'],
            'doc_writer': ['document', 'documentation', 'write', 'manual', 'guide', 'readme', 'usage', 'describe', 'explain'],
            'tester': ['test', 'testing', 'unit test', 'integration test', 'quality', 'checker', 'verify', 'validate'],
            'devops': ['docker', 'deploy', 'pipeline', 'ci/cd', 'infrastructure', 'kubernetes', 'dockerfile', 'install', 'setup', 'monitoring']
        }
        
        keywords = specialization_keywords.get(agent_type, [])
        task_lower = task_description.lower()
        result_lower = str(result.get('result', '')).lower()
        
        # Проверяем, что результат соответствует специализации
        keyword_matches = sum(1 for keyword in keywords if keyword in result_lower)
        return keyword_matches > 0
    
    def _assess_result_completeness(self, result: Dict[str, Any], 
                                  task_description: str) -> float:
        """
        Оценить полноту выполнения задачи
        """
        result_content = result.get('result', '')
        artifacts = result.get('artifacts_created', [])
        
        # Проверяем количество ключевых слов из задачи в результате
        task_words = set(task_description.lower().split())
        result_words = set(result_content.lower().split())
        overlap = len(task_words.intersection(result_words))
        
        # Нормализуем оценку
        completeness_score = min(1.0, overlap / max(len(task_words), 1))
        
        # Добавляем баллы за артефакты
        if artifacts:
            completeness_score += 0.2
        
        # Ограничиваем диапазон от 0.0 до 1.0
        return max(0.0, min(1.0, completeness_score))
    
    def enforce_quality_requirements(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принудительно применить требования качества к результату
        """
        # Проверяем качество созданных артефактов
        artifacts = result.get('artifacts_created', [])
        session_id = result.get('session_id', 'unknown')
        
        quality_issues = []
        total_score = 0.0
        artifact_count = 0
        
        for artifact in artifacts:
            if isinstance(artifact, str):
                artifact_path = f"./workspace/{session_id}/{artifact}"
                validation = self.validate_artifact_quality(artifact_path, None)
                
                if not validation['valid']:
                    quality_issues.append({
                        'artifact': artifact,
                        'issues': validation['issues'],
                        'suggestions': validation['suggestions']
                    })
                
                total_score += validation['score']
                artifact_count += 1
        
        # Вычисляем средний балл качества
        average_quality_score = total_score / artifact_count if artifact_count > 0 else 0.0
        
        # Добавляем информацию о качестве в результат
        result['quality_check'] = {
            'average_score': average_quality_score,
            'issues_found': quality_issues,
            'artifacts_checked': artifact_count,
            'requires_improvement': average_quality_score < 0.7
        }
        
        return result

# Глобальная система контроля качества
quality_control = QualityControlSystem()