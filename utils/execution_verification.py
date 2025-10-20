from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
import hashlib
import time
from datetime import datetime
import os

class ExecutionVerificationSystem:
    """
    Система подтверждения реального выполнения задач
    """
    
    def __init__(self):
        self.execution_records = {}
        self.verification_criteria = {
            'code_generation': {
                'required_files': ['.py'],
                'min_file_size': 100,
                'required_content_patterns': ['def ', 'return'],
                'forbidden_patterns': ['NEEDS_CLARIFICATION', 'TODO']
            },
            'documentation': {
                'required_files': ['.md', '.txt'],
                'min_file_size': 200,
                'required_content_patterns': ['#', '##'],
                'forbidden_patterns': ['TBD', 'To be determined']
            },
            'testing': {
                'required_files': ['.py', '.md'],
                'min_file_size': 150,
                'required_content_patterns': ['test_', 'assert'],
                'forbidden_patterns': ['placeholder', 'example']
            },
            'research': {
                'required_files': ['.md', '.txt'],
                'min_file_size': 300,
                'required_content_patterns': ['##', '###'],
                'forbidden_patterns': ['summary', 'placeholder']
            },
            'devops': {
                'required_files': ['.yml', '.yaml', 'Dockerfile'],
                'min_file_size': 50,
                'required_content_patterns': ['FROM', 'RUN'],
                'forbidden_patterns': ['example', 'template']
            }
        }
    
    def create_execution_record(self, session_id: str, agent_type: str, 
                              task_description: str) -> str:
        """
        Создать запись о начале выполнения задачи
        """
        record_id = hashlib.md5(f"{session_id}_{agent_type}_{task_description}_{time.time()}".encode()).hexdigest()[:12]
        
        self.execution_records[record_id] = {
            'session_id': session_id,
            'agent_type': agent_type,
            'task_description': task_description,
            'start_time': datetime.now().isoformat(),
            'status': 'started',
            'artifacts_before': self._get_workspace_artifacts(session_id),
            'verification_results': []
        }
        
        return record_id
    
    def verify_execution_completion(self, record_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверить завершение выполнения задачи
        """
        if record_id not in self.execution_records:
            return {
                'verified': False,
                'issues': ['Execution record not found'],
                'suggestions': ['Create execution record before completion']
            }
        
        record = self.execution_records[record_id]
        session_id = record['session_id']
        agent_type = record['agent_type']
        
        # Получаем текущие артефакты
        artifacts_after = self._get_workspace_artifacts(session_id)
        new_artifacts = self._find_new_artifacts(record['artifacts_before'], artifacts_after)
        
        # Проверяем реальное выполнение
        verification_results = []
        all_verified = True
        issues = []
        suggestions = []
        
        # Проверка 1: Наличие новых артефактов
        if not new_artifacts:
            issues.append('No new artifacts created')
            suggestions.append('Task should create at least one new artifact')
            all_verified = False
        else:
            # Проверяем качество новых артефактов
            for artifact in new_artifacts:
                artifact_path = f"./workspace/{session_id}/{artifact}"
                verification = self._verify_artifact_quality(artifact_path, agent_type)
                verification_results.append({
                    'artifact': artifact,
                    'verification': verification
                })
                
                if not verification['verified']:
                    all_verified = False
                    issues.extend(verification['issues'])
                    suggestions.extend(verification['suggestions'])
        
        # Проверка 2: Наличие реального содержания в результате
        result_content = result.get('result', '')
        if 'NEEDS_CLARIFICATION' in result_content or 'NEEDS_REDIRECT' in result_content:
            issues.append('Result contains placeholder text')
            suggestions.append('Replace placeholder text with actual implementation')
            all_verified = False
        
        # Проверка 3: Длина результата
        if len(result_content) < 50:
            issues.append('Result is too short')
            suggestions.append('Result should contain substantial content')
            all_verified = False
        
        # Обновляем запись
        record.update({
            'end_time': datetime.now().isoformat(),
            'status': 'completed',
            'artifacts_after': artifacts_after,
            'new_artifacts': new_artifacts,
            'verification_results': verification_results,
            'final_result': result
        })
        
        return {
            'verified': all_verified,
            'issues': issues,
            'suggestions': suggestions,
            'new_artifacts': new_artifacts,
            'verification_details': verification_results
        }
    
    def _get_workspace_artifacts(self, session_id: str) -> List[str]:
        """
        Получить список артефактов в рабочей директории
        """
        workspace_path = Path(f"./workspace/{session_id}")
        if not workspace_path.exists():
            return []
        
        artifacts = []
        for file_path in workspace_path.iterdir():
            if file_path.is_file():
                artifacts.append(file_path.name)
        
        return artifacts
    
    def _find_new_artifacts(self, before: List[str], after: List[str]) -> List[str]:
        """
        Найти новые артефакты
        """
        return list(set(after) - set(before))
    
    def _verify_artifact_quality(self, artifact_path: str, agent_type: str) -> Dict[str, Any]:
        """
        Проверить качество артефакта
        """
        try:
            path = Path(artifact_path)
            if not path.exists():
                return {
                    'verified': False,
                    'issues': ['Artifact file does not exist'],
                    'suggestions': ['Create the artifact file']
                }
            
            # Получаем критерии проверки для типа агента
            criteria = self.verification_criteria.get(agent_type, self.verification_criteria['documentation'])
            
            # Читаем содержимое
            content = path.read_text(encoding='utf-8')
            file_size = path.stat().st_size
            
            issues = []
            suggestions = []
            
            # Проверка размера файла
            if file_size < criteria.get('min_file_size', 50):
                issues.append(f'File too small: {file_size} bytes')
                suggestions.append(f'Add more content to reach minimum {criteria["min_file_size"]} bytes')
            
            # Проверка обязательных паттернов
            for pattern in criteria.get('required_content_patterns', []):
                if pattern not in content:
                    issues.append(f'Required pattern not found: {pattern}')
                    suggestions.append(f'Add content matching pattern: {pattern}')
            
            # Проверка запрещенных паттернов
            for pattern in criteria.get('forbidden_patterns', []):
                if pattern in content:
                    issues.append(f'Forbidden pattern found: {pattern}')
                    suggestions.append(f'Remove or replace forbidden pattern: {pattern}')
            
            # Проверка расширения файла
            required_extensions = criteria.get('required_files', [])
            file_extension = path.suffix.lower()
            if required_extensions and file_extension not in required_extensions:
                issues.append(f'Wrong file extension: {file_extension}')
                suggestions.append(f'Use one of required extensions: {required_extensions}')
            
            verified = len(issues) == 0
            
            return {
                'verified': verified,
                'issues': issues,
                'suggestions': suggestions,
                'file_size': file_size,
                'content_length': len(content)
            }
            
        except Exception as e:
            return {
                'verified': False,
                'issues': [f'Error verifying artifact: {str(e)}'],
                'suggestions': ['Fix file access issues']
            }
    
    def enforce_real_execution(self, agent_type: str, task_description: str, 
                              result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Принудительно обеспечить реальное выполнение задачи
        """
        # Создаем запись о выполнении
        record_id = self.create_execution_record(session_id, agent_type, task_description)
        
        # Проверяем завершение
        verification = self.verify_execution_completion(record_id, result)
        
        # Добавляем информацию о проверке в результат
        result['execution_verification'] = {
            'record_id': record_id,
            'verified': verification['verified'],
            'issues': verification['issues'],
            'suggestions': verification['suggestions'],
            'new_artifacts': verification['new_artifacts']
        }
        
        # Если проверка не пройдена, требуем повторное выполнение
        if not verification['verified']:
            result['requires_rework'] = True
            result['rework_reason'] = 'Execution not properly verified'
        
        return result
    
    def get_execution_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Получить сводку по выполнению задач в сессии
        """
        session_records = {
            rid: record for rid, record in self.execution_records.items()
            if record['session_id'] == session_id
        }
        
        total_tasks = len(session_records)
        completed_tasks = sum(1 for record in session_records.values() 
                             if record['status'] == 'completed')
        verified_tasks = 0
        total_artifacts = 0
        
        for record in session_records.values():
            if record.get('verification_results'):
                verified_count = sum(1 for vr in record['verification_results'] 
                                   if vr['verification']['verified'])
                if verified_count > 0:
                    verified_tasks += 1
            
            total_artifacts += len(record.get('new_artifacts', []))
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'verified_tasks': verified_tasks,
            'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'verification_rate': verified_tasks / total_tasks if total_tasks > 0 else 0,
            'total_artifacts': total_artifacts,
            'session_id': session_id
        }

# Глобальная система подтверждения выполнения
execution_verifier = ExecutionVerificationSystem()