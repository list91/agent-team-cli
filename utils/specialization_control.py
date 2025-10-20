from typing import Dict, List, Any, Tuple, Set
from utils.competency_matrix import competency_matrix
import re

class SpecializationControlSystem:
    """
    Система контроля соответствия задач специализациям агентов
    """
    
    def __init__(self):
        self.specialization_rules = {}
        self.violation_history = {}
        self.agent_specializations = {}
        
        # Инициализируем базовые правила специализаций
        self._initialize_specialization_rules()
    
    def _initialize_specialization_rules(self):
        """
        Инициализировать базовые правила специализаций
        """
        self.specialization_rules = {
            'researcher': {
                'allowed_tasks': [
                    'research', 'study', 'analyze', 'examine', 'investigate',
                    'evaluate', 'gather information', 'best practices', 'find',
                    'explore', 'literature review', 'data collection'
                ],
                'forbidden_tasks': [
                    'implement', 'code', 'programming', 'write.*function',
                    'create.*api', 'build.*backend', 'docker', 'deploy'
                ],
                'required_skills': ['research', 'analysis', 'investigation']
            },
            'backend_dev': {
                'allowed_tasks': [
                    'backend', 'server', 'api', 'flask', 'django', 'programming',
                    'code', 'implementation', 'server-side', 'database',
                    'rest api', 'microservices'
                ],
                'forbidden_tasks': [
                    'document', 'write.*manual', 'create.*guide',
                    'test', 'testing', 'unit test', 'quality.*check'
                ],
                'required_skills': ['programming', 'backend', 'api']
            },
            'frontend_dev': {
                'allowed_tasks': [
                    'frontend', 'ui', 'react', 'vue', 'html', 'css',
                    'client-side', 'interface', 'javascript', 'typescript'
                ],
                'forbidden_tasks': [
                    'research', 'study', 'analyze.*data', 'gather.*information',
                    'document', 'write.*manual'
                ],
                'required_skills': ['frontend', 'ui', 'javascript']
            },
            'doc_writer': {
                'allowed_tasks': [
                    'document', 'documentation', 'write', 'manual', 'guide',
                    'readme', 'usage', 'describe', 'explain', 'technical writing'
                ],
                'forbidden_tasks': [
                    'implement', 'code', 'programming', 'test', 'testing',
                    'docker', 'deploy', 'pipeline'
                ],
                'required_skills': ['writing', 'documentation', 'explanation']
            },
            'tester': {
                'allowed_tasks': [
                    'test', 'testing', 'unit test', 'integration test',
                    'quality', 'checker', 'verify', 'validate', 'automation'
                ],
                'forbidden_tasks': [
                    'implement', 'code', 'programming', 'document',
                    'research', 'study'
                ],
                'required_skills': ['testing', 'quality', 'verification']
            },
            'devops': {
                'allowed_tasks': [
                    'docker', 'deploy', 'pipeline', 'ci/cd', 'infrastructure',
                    'kubernetes', 'dockerfile', 'install', 'setup', 'monitoring'
                ],
                'forbidden_tasks': [
                    'implement', 'code', 'programming', 'document',
                    'research', 'study'
                ],
                'required_skills': ['devops', 'deployment', 'infrastructure']
            }
        }
    
    def validate_task_assignment(self, agent_type: str, task_description: str) -> Dict[str, Any]:
        """
        Проверить соответствует ли задача специализации агента
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'suggestions': [],
            'confidence': 1.0
        }
        
        # Проверяем существование правил для агента
        if agent_type not in self.specialization_rules:
            validation_result.update({
                'valid': False,
                'issues': [f'No specialization rules found for agent type: {agent_type}'],
                'suggestions': ['Define specialization rules for this agent type'],
                'confidence': 0.0
            })
            return validation_result
        
        rules = self.specialization_rules[agent_type]
        task_lower = task_description.lower()
        
        # Проверяем запрещенные задачи
        forbidden_issues = []
        for forbidden_pattern in rules.get('forbidden_tasks', []):
            if re.search(forbidden_pattern, task_lower):
                forbidden_issues.append(f"Forbidden task pattern matched: {forbidden_pattern}")
        
        if forbidden_issues:
            validation_result['valid'] = False
            validation_result['issues'].extend(forbidden_issues)
            validation_result['suggestions'].append(
                f"This task is not appropriate for {agent_type}. Consider reassigning to a more suitable agent."
            )
            validation_result['confidence'] = 0.1  # Очень низкая уверенность
        
        # Проверяем разрешенные задачи (менее строго)
        allowed_matches = []
        for allowed_pattern in rules.get('allowed_tasks', []):
            if re.search(allowed_pattern, task_lower):
                allowed_matches.append(allowed_pattern)
        
        if allowed_matches:
            # Повышаем уверенность, если есть совпадения с разрешенными задачами
            validation_result['confidence'] = min(1.0, 0.5 + len(allowed_matches) * 0.1)
        elif not forbidden_issues:
            # Если нет ни разрешенных, ни запрещенных задач, средняя уверенность
            validation_result['confidence'] = 0.5
            validation_result['issues'].append(
                f"Unclear task specialization match for {agent_type}"
            )
            validation_result['suggestions'].append(
                "Consider clarifying task requirements or reassigning to a specialist"
            )
        
        # Проверяем требуемые навыки (если есть)
        required_skills = rules.get('required_skills', [])
        if required_skills:
            skill_matches = []
            for skill in required_skills:
                if skill in task_lower:
                    skill_matches.append(skill)
            
            if skill_matches:
                # Повышаем уверенность, если есть совпадения по навыкам
                skill_confidence_boost = len(skill_matches) * 0.05
                validation_result['confidence'] = min(1.0, 
                    validation_result['confidence'] + skill_confidence_boost)
            elif not forbidden_issues:
                # Добавляем предупреждение, если нет совпадений по навыкам
                validation_result['issues'].append(
                    f"Missing required skills for {agent_type}: {required_skills}"
                )
        
        # Регистрируем проверку
        self._register_validation(agent_type, task_description, validation_result)
        
        return validation_result
    
    def find_suitable_agents(self, task_description: str, available_agents: List[str]) -> List[Tuple[str, float]]:
        """
        Найти подходящих агентов для задачи с оценкой подходящести
        """
        suitability_scores = []
        
        for agent_type in available_agents:
            # Сначала проверяем через правила специализаций
            validation = self.validate_task_assignment(agent_type, task_description)
            
            if validation['valid']:
                # Если задача подходит, оценка высокая
                score = validation['confidence']
            else:
                # Если задача не подходит, оценка очень низкая
                score = validation['confidence'] * 0.1  # Сильно снижаем оценку
            
            # Также учитываем компетентность из матрицы компетенций
            competency_scores = competency_matrix.get_task_similarity_scores(
                task_description, [agent_type]
            )
            competency_score = competency_scores.get(agent_type, 0.0)
            
            # Комбинируем оценки
            combined_score = (score * 0.7 + competency_score * 0.3)
            suitability_scores.append((agent_type, combined_score))
        
        # Сортируем по убыванию оценки
        suitability_scores.sort(key=lambda x: x[1], reverse=True)
        return suitability_scores
    
    def suggest_task_redistribution(self, current_assignments: Dict[str, List[str]], 
                                  available_agents: List[str]) -> Dict[str, Any]:
        """
        Предложить перераспределение задач для лучшего соответствия специализациям
        """
        redistribution_suggestions = {
            'suggested_changes': [],
            'conflicts_found': [],
            'improvements_possible': 0
        }
        
        for agent_type, tasks in current_assignments.items():
            for task in tasks:
                validation = self.validate_task_assignment(agent_type, task)
                
                if not validation['valid']:
                    # Задача не соответствует специализации агента
                    redistribution_suggestions['conflicts_found'].append({
                        'agent': agent_type,
                        'task': task,
                        'issues': validation['issues']
                    })
                    
                    # Ищем более подходящего агента
                    suitable_agents = self.find_suitable_agents(task, available_agents)
                    if suitable_agents and suitable_agents[0][1] > 0.3:
                        best_alternative_agent, best_score = suitable_agents[0]
                        if best_alternative_agent != agent_type:
                            redistribution_suggestions['suggested_changes'].append({
                                'from_agent': agent_type,
                                'to_agent': best_alternative_agent,
                                'task': task,
                                'confidence': best_score,
                                'reason': f"Better specialization match (confidence: {best_score:.2f})"
                            })
                            redistribution_suggestions['improvements_possible'] += 1
        
        return redistribution_suggestions
    
    def _register_validation(self, agent_type: str, task_description: str, 
                          validation_result: Dict[str, Any]):
        """
        Зарегистрировать результат проверки
        """
        validation_record = {
            'agent_type': agent_type,
            'task': task_description,
            'result': validation_result,
            'timestamp': self._get_current_timestamp()
        }
        
        task_hash = hash(f"{agent_type}_{task_description}")
        if task_hash not in self.violation_history:
            self.violation_history[task_hash] = []
        
        self.violation_history[task_hash].append(validation_record)
        
        # Ограничиваем историю последними 100 записями
        if len(self.violation_history[task_hash]) > 100:
            self.violation_history[task_hash] = self.violation_history[task_hash][-100:]
    
    def _get_current_timestamp(self) -> str:
        """
        Получить текущую временную метку
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_specialization_report(self) -> Dict[str, Any]:
        """
        Получить отчет по соблюдению специализаций
        """
        total_validations = 0
        valid_assignments = 0
        violations = []
        
        for task_validations in self.violation_history.values():
            total_validations += len(task_validations)
            for validation in task_validations:
                if validation['result']['valid']:
                    valid_assignments += 1
                else:
                    violations.append({
                        'agent': validation['agent_type'],
                        'task': validation['task'][:100] + '...',
                        'issues': validation['result']['issues']
                    })
        
        compliance_rate = valid_assignments / total_validations if total_validations > 0 else 1.0
        
        return {
            'total_validations': total_validations,
            'valid_assignments': valid_assignments,
            'violation_count': len(violations),
            'compliance_rate': compliance_rate,
            'violations': violations[:10],  # Показываем первые 10 нарушений
            'needs_attention': compliance_rate < 0.8
        }
    
    def enforce_strict_specialization(self, agent_type: str, task_description: str) -> bool:
        """
        Принудительно обеспечить строгое соблюдение специализаций
        """
        validation = self.validate_task_assignment(agent_type, task_description)
        
        if not validation['valid']:
            # Если задача не соответствует специализации, выбрасываем исключение
            raise ValueError(
                f"Task assignment violation for {agent_type}: {validation['issues'][0]}. "
                f"Suggestions: {validation['suggestions'][0]}"
            )
        
        return True  # Задача соответствует специализации
    
    def update_specialization_rules(self, agent_type: str, new_rules: Dict[str, Any]):
        """
        Обновить правила специализации для агента
        """
        self.specialization_rules[agent_type] = new_rules
        # В реальной системе здесь была бы логика сохранения правил

# Глобальная система контроля специализаций
specialization_control = SpecializationControlSystem()