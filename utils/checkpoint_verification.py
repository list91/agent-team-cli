from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import hashlib
import json

class CheckpointVerificationSystem:
    """
    Система верификации контрольных точек выполнения задач
    """
    
    def __init__(self):
        self.checkpoints = {}
        self.verifications = {}
        self.validation_rules = {}
        
        # Инициализируем систему
        self._initialize_validation_rules()
    
    def _initialize_validation_rules(self):
        """
        Инициализировать правила валидации контрольных точек
        """
        self.validation_rules = {
            'task_assignment': {
                'required_fields': ['agent_type', 'task_description', 'session_id'],
                'validation_functions': [
                    self._validate_agent_type,
                    self._validate_task_description,
                    self._validate_session_id
                ]
            },
            'task_execution': {
                'required_fields': ['agent_type', 'task_description', 'result', 'artifacts_created'],
                'validation_functions': [
                    self._validate_execution_result,
                    self._validate_artifacts,
                    self._validate_completion_status
                ]
            },
            'quality_check': {
                'required_fields': ['quality_score', 'issues_found', 'suggestions'],
                'validation_functions': [
                    self._validate_quality_score,
                    self._validate_issues_and_suggestions
                ]
            },
            'progress_update': {
                'required_fields': ['progress_percentage', 'current_step', 'total_steps'],
                'validation_functions': [
                    self._validate_progress_values,
                    self._validate_step_consistency
                ]
            }
        }
    
    def create_checkpoint(self, checkpoint_type: str, data: Dict[str, Any], 
                         session_id: str) -> str:
        """
        Создать контрольную точку
        """
        # Генерируем уникальный ID контрольной точки
        checkpoint_id = self._generate_checkpoint_id(checkpoint_type, data, session_id)
        
        # Создаем запись контрольной точки
        checkpoint_record = {
            'id': checkpoint_id,
            'type': checkpoint_type,
            'data': data,
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'verifications': []
        }
        
        # Сохраняем контрольную точку
        self.checkpoints[checkpoint_id] = checkpoint_record
        
        # Выполняем начальную валидацию
        initial_validation = self._perform_initial_validation(checkpoint_type, data)
        if not initial_validation['valid']:
            checkpoint_record['status'] = 'validation_failed'
            checkpoint_record['validation_errors'] = initial_validation['errors']
        
        return checkpoint_id
    
    def _generate_checkpoint_id(self, checkpoint_type: str, data: Dict[str, Any], 
                              session_id: str) -> str:
        """
        Сгенерировать уникальный ID контрольной точки
        """
        # Создаем хэш из комбинации параметров
        hash_input = f"{checkpoint_type}_{json.dumps(data, sort_keys=True)}_{session_id}_{datetime.now().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def _perform_initial_validation(self, checkpoint_type: str, 
                                   data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить начальную валидацию контрольной точки
        """
        if checkpoint_type not in self.validation_rules:
            return {
                'valid': False,
                'errors': [f'Unknown checkpoint type: {checkpoint_type}']
            }
        
        rules = self.validation_rules[checkpoint_type]
        errors = []
        
        # Проверяем наличие обязательных полей
        for field in rules['required_fields']:
            if field not in data:
                errors.append(f'Missing required field: {field}')
        
        # Выполняем функции валидации
        for validation_func in rules['validation_functions']:
            try:
                validation_result = validation_func(data)
                if not validation_result['valid']:
                    errors.extend(validation_result['errors'])
            except Exception as e:
                errors.append(f'Validation function error: {str(e)}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def verify_checkpoint(self, checkpoint_id: str, 
                         verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Верифицировать контрольную точку
        """
        if checkpoint_id not in self.checkpoints:
            return {
                'verified': False,
                'errors': ['Checkpoint not found']
            }
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        # Выполняем верификацию
        verification_result = self._perform_verification(
            checkpoint['type'], 
            checkpoint['data'], 
            verification_data
        )
        
        # Сохраняем результат верификации
        verification_record = {
            'timestamp': datetime.now().isoformat(),
            'result': verification_result,
            'verification_data': verification_data
        }
        
        checkpoint['verifications'].append(verification_record)
        
        # Обновляем статус контрольной точки
        if verification_result['verified']:
            checkpoint['status'] = 'verified'
        else:
            checkpoint['status'] = 'verification_failed'
            checkpoint['verification_errors'] = verification_result.get('errors', [])
        
        return verification_result
    
    def _perform_verification(self, checkpoint_type: str, checkpoint_data: Dict[str, Any], 
                            verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить верификацию контрольной точки
        """
        errors = []
        
        # Проверяем реальное содержание результата
        result_content = checkpoint_data.get('result', '')
        if 'NEEDS_CLARIFICATION' in result_content or 'TODO' in result_content:
            errors.append('Result contains placeholder text')
        
        # Проверяем наличие реальных артефактов
        artifacts = checkpoint_data.get('artifacts_created', [])
        if not artifacts:
            errors.append('No artifacts created')
        else:
            # Проверяем качество артефактов
            artifact_issues = self._verify_artifacts_quality(artifacts, 
                                                           checkpoint_data.get('session_id', ''))
            errors.extend(artifact_issues)
        
        # Проверяем объем результата
        if len(result_content) < 50:
            errors.append('Result content is too short')
        
        # Проверяем данные верификации
        if verification_data:
            verification_issues = self._validate_verification_data(verification_data)
            errors.extend(verification_issues)
        
        verified = len(errors) == 0
        
        return {
            'verified': verified,
            'errors': errors,
            'confidence': 1.0 - min(1.0, len(errors) * 0.2)  # Простая оценка уверенности
        }
    
    def _verify_artifacts_quality(self, artifacts: List[str], session_id: str) -> List[str]:
        """
        Проверить качество артефактов
        """
        issues = []
        
        for artifact in artifacts:
            # В реальной системе здесь будет проверка содержимого артефакта
            # Сейчас используем простую проверку
            
            # Проверяем имя файла
            if 'placeholder' in artifact.lower():
                issues.append(f'Artifact name contains placeholder: {artifact}')
            
            # Проверяем расширение
            if '.' not in artifact:
                issues.append(f'Artifact has no extension: {artifact}')
        
        return issues
    
    def _validate_verification_data(self, verification_data: Dict[str, Any]) -> List[str]:
        """
        Проверить данные верификации
        """
        errors = []
        
        # Базовые проверки
        if 'timestamp' not in verification_data:
            errors.append('Missing timestamp in verification data')
        
        if 'verifier' not in verification_data:
            errors.append('Missing verifier information')
        
        return errors
    
    def get_checkpoint_status(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Получить статус контрольной точки
        """
        if checkpoint_id not in self.checkpoints:
            return {
                'status': 'not_found',
                'error': 'Checkpoint ID not found'
            }
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        return {
            'id': checkpoint_id,
            'type': checkpoint['type'],
            'status': checkpoint['status'],
            'created_at': checkpoint['created_at'],
            'session_id': checkpoint['session_id'],
            'verifications_count': len(checkpoint['verifications']),
            'validation_errors': checkpoint.get('validation_errors', []),
            'verification_errors': checkpoint.get('verification_errors', [])
        }
    
    def get_session_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Получить все контрольные точки для сессии
        """
        session_checkpoints = []
        
        for checkpoint_id, checkpoint in self.checkpoints.items():
            if checkpoint['session_id'] == session_id:
                session_checkpoints.append({
                    'id': checkpoint_id,
                    'type': checkpoint['type'],
                    'status': checkpoint['status'],
                    'created_at': checkpoint['created_at'],
                    'verifications_count': len(checkpoint['verifications'])
                })
        
        return session_checkpoints
    
    def validate_checkpoint_integrity(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Проверить целостность контрольной точки
        """
        if checkpoint_id not in self.checkpoints:
            return {
                'integrity_valid': False,
                'errors': ['Checkpoint not found']
            }
        
        checkpoint = self.checkpoints[checkpoint_id]
        errors = []
        
        # Проверяем структуру контрольной точки
        required_fields = ['id', 'type', 'data', 'session_id', 'created_at', 'status']
        for field in required_fields:
            if field not in checkpoint:
                errors.append(f'Missing required field in checkpoint structure: {field}')
        
        # Проверяем тип контрольной точки
        if checkpoint['type'] not in self.validation_rules:
            errors.append(f'Invalid checkpoint type: {checkpoint["type"]}')
        
        # Проверяем данные
        if not isinstance(checkpoint['data'], dict):
            errors.append('Checkpoint data must be a dictionary')
        
        # Проверяем дату создания
        try:
            datetime.fromisoformat(checkpoint['created_at'])
        except ValueError:
            errors.append('Invalid timestamp format')
        
        integrity_valid = len(errors) == 0
        
        return {
            'integrity_valid': integrity_valid,
            'errors': errors,
            'checkpoint_id': checkpoint_id
        }
    
    # Функции валидации для разных типов контрольных точек
    
    def _validate_agent_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить тип агента"""
        errors = []
        agent_type = data.get('agent_type', '')
        
        if not agent_type:
            errors.append('Agent type is empty')
        elif not isinstance(agent_type, str):
            errors.append('Agent type must be a string')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_task_description(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить описание задачи"""
        errors = []
        task_description = data.get('task_description', '')
        
        if not task_description:
            errors.append('Task description is empty')
        elif len(task_description) < 10:
            errors.append('Task description is too short')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_session_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить ID сессии"""
        errors = []
        session_id = data.get('session_id', '')
        
        if not session_id:
            errors.append('Session ID is empty')
        elif not isinstance(session_id, str):
            errors.append('Session ID must be a string')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_execution_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить результат выполнения"""
        errors = []
        result = data.get('result', '')
        
        if not result:
            errors.append('Execution result is empty')
        elif len(result) < 20:
            errors.append('Execution result is too short')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_artifacts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить артефакты"""
        errors = []
        artifacts = data.get('artifacts_created', [])
        
        if not isinstance(artifacts, list):
            errors.append('Artifacts must be a list')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_completion_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить статус завершения"""
        errors = []
        # В данном случае проверка может быть пустой
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_quality_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить оценку качества"""
        errors = []
        quality_score = data.get('quality_score', 0.0)
        
        if not isinstance(quality_score, (int, float)):
            errors.append('Quality score must be a number')
        elif not (0.0 <= quality_score <= 1.0):
            errors.append('Quality score must be between 0.0 and 1.0')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_issues_and_suggestions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить проблемы и предложения"""
        errors = []
        issues = data.get('issues_found', [])
        suggestions = data.get('suggestions', [])
        
        if not isinstance(issues, list):
            errors.append('Issues must be a list')
        
        if not isinstance(suggestions, list):
            errors.append('Suggestions must be a list')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_progress_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить значения прогресса"""
        errors = []
        progress = data.get('progress_percentage', 0)
        current_step = data.get('current_step', 0)
        total_steps = data.get('total_steps', 1)
        
        if not isinstance(progress, (int, float)):
            errors.append('Progress percentage must be a number')
        elif not (0 <= progress <= 100):
            errors.append('Progress percentage must be between 0 and 100')
        
        if not isinstance(current_step, int) or current_step < 0:
            errors.append('Current step must be a non-negative integer')
        
        if not isinstance(total_steps, int) or total_steps <= 0:
            errors.append('Total steps must be a positive integer')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_step_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверить согласованность шагов"""
        errors = []
        current_step = data.get('current_step', 0)
        total_steps = data.get('total_steps', 1)
        
        if current_step > total_steps:
            errors.append('Current step cannot exceed total steps')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику верификации
        """
        total_checkpoints = len(self.checkpoints)
        verified_checkpoints = 0
        failed_verifications = 0
        validation_failures = 0
        
        for checkpoint in self.checkpoints.values():
            if checkpoint['status'] == 'verified':
                verified_checkpoints += 1
            elif checkpoint['status'] == 'verification_failed':
                failed_verifications += 1
            elif checkpoint['status'] == 'validation_failed':
                validation_failures += 1
        
        return {
            'total_checkpoints': total_checkpoints,
            'verified_checkpoints': verified_checkpoints,
            'failed_verifications': failed_verifications,
            'validation_failures': validation_failures,
            'verification_rate': verified_checkpoints / total_checkpoints if total_checkpoints > 0 else 0,
            'failure_rate': (failed_verifications + validation_failures) / total_checkpoints if total_checkpoints > 0 else 0
        }
    
    def mark_session_completed(self, session_id: str, success: bool = True):
        """
        Пометить сессию как завершенную
        """
        # Обновляем статус всех контрольных точек в сессии
        for checkpoint_id, checkpoint in self.checkpoints.items():
            if checkpoint.get('session_id') == session_id:
                if success:
                    checkpoint['status'] = 'completed_success'
                    checkpoint['completion_status'] = 'success'
                else:
                    checkpoint['status'] = 'completed_failure'
                    checkpoint['completion_status'] = 'failed'
                checkpoint['completed_at'] = datetime.now().isoformat()
        
        # Добавляем запись о завершении сессии
        completion_record = {
            'session_id': session_id,
            'completion_status': 'success' if success else 'failed',
            'completed_at': datetime.now().isoformat(),
            'total_checkpoints_in_session': len([cp for cp in self.checkpoints.values() if cp.get('session_id') == session_id])
        }
        
        # Сохраняем запись о завершении (можно использовать отдельную структуру)
        if not hasattr(self, 'session_completions'):
            self.session_completions = {}
        
        self.session_completions[session_id] = completion_record
        
        return completion_record

# Глобальная система верификации контрольных точек
checkpoint_verifier = CheckpointVerificationSystem()