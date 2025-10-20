from typing import Dict, List, Any, Optional, Callable, Protocol
from abc import ABC, abstractmethod
import json
import hashlib
from datetime import datetime
import uuid

class AgentContract(Protocol):
    """
    Протокол контракта между агентами
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        """
        Получить спецификацию контракта
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Проверить входные данные на соответствие контракту
        """
        pass
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Проверить выходные данные на соответствие контракту
        """
        pass
    
    def execute_with_contract(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить задачу с проверкой контракта
        """
        pass

class ContractManager:
    """
    Менеджер контрактов между агентами
    """
    
    def __init__(self):
        self.contracts = {}
        self.contract_history = {}
        self.violations = []
        
        # Инициализируем стандартные контракты
        self._initialize_standard_contracts()
    
    def _initialize_standard_contracts(self):
        """
        Инициализировать стандартные контракты
        """
        self.contracts.update({
            'task_assignment': TaskAssignmentContract(),
            'task_execution': TaskExecutionContract(),
            'result_delivery': ResultDeliveryContract(),
            'quality_assurance': QualityAssuranceContract(),
            'artifact_creation': ArtifactCreationContract(),
            'progress_reporting': ProgressReportingContract()
        })
    
    def create_contract(self, contract_type: str, parties: List[str], 
                       terms: Dict[str, Any]) -> str:
        """
        Создать новый контракт между агентами
        """
        contract_id = str(uuid.uuid4())
        
        contract_data = {
            'contract_id': contract_id,
            'contract_type': contract_type,
            'parties': parties,
            'terms': terms,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'signatures': {}
        }
        
        # Сохраняем контракт
        self.contracts[contract_id] = contract_data
        
        # Регистрируем в истории
        if contract_type not in self.contract_history:
            self.contract_history[contract_type] = []
        
        self.contract_history[contract_type].append(contract_data)
        
        return contract_id
    
    def sign_contract(self, contract_id: str, party: str, signature: str) -> bool:
        """
        Подписать контракт участником
        """
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        
        # Проверяем, что участник входит в число сторон контракта
        if party not in contract['parties']:
            return False
        
        # Добавляем подпись
        contract['signatures'][party] = {
            'signature': signature,
            'signed_at': datetime.now().isoformat()
        }
        
        return True
    
    def validate_contract_execution(self, contract_id: str, 
                                   execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверить выполнение контракта
        """
        if contract_id not in self.contracts:
            return {
                'valid': False,
                'errors': ['Contract not found'],
                'contract_id': contract_id
            }
        
        contract = self.contracts[contract_id]
        
        # Проверяем, является ли контракт словарем или объектом
        if isinstance(contract, dict):
            contract_type = contract.get('contract_type', contract_id)
        elif hasattr(contract, 'get_contract_specification'):
            # Это объект контракта, получаем спецификацию
            try:
                spec = contract.get_contract_specification()
                contract_type = spec.get('contract_type', contract_id)
            except:
                contract_type = contract_id
        else:
            # Неизвестный формат контракта
            contract_type = contract_id
        
        # Получаем спецификацию контракта
        if contract_type in self.contracts:
            contract_spec = self.contracts[contract_type]
            if hasattr(contract_spec, 'validate_execution'):
                try:
                    validation_result = contract_spec.validate_execution(execution_data)
                    return validation_result
                except Exception as e:
                    return {
                        'valid': False,
                        'errors': [f'Validation error: {str(e)}'],
                        'contract_id': contract_id
                    }
        
        # Если нет специфической валидации, используем базовую
        return self._basic_contract_validation(contract, execution_data)
    
    def _basic_contract_validation(self, contract: Dict[str, Any], 
                                 execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Базовая проверка выполнения контракта
        """
        errors = []
        
        # Проверяем обязательные поля из условий контракта
        terms = contract.get('terms', {})
        required_fields = terms.get('required_fields', [])
        
        for field in required_fields:
            if field not in execution_data:
                errors.append(f'Missing required field: {field}')
        
        # Проверяем типы данных
        field_types = terms.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in execution_data:
                actual_value = execution_data[field]
                if not self._validate_type(actual_value, expected_type):
                    errors.append(f'Invalid type for field {field}: expected {expected_type}, got {type(actual_value)}')
        
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'errors': errors,
            'contract_id': contract['contract_id'],
            'validation_performed_at': datetime.now().isoformat()
        }
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """
        Проверить тип значения
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict,
            'datetime': str  # ISO формат даты
        }
        
        expected_python_type = type_mapping.get(expected_type, str)
        return isinstance(value, expected_python_type)
    
    def record_contract_violation(self, contract_id: str, 
                                 violating_party: str, 
                                 violation_details: Dict[str, Any]):
        """
        Записать нарушение контракта
        """
        violation_record = {
            'contract_id': contract_id,
            'violating_party': violating_party,
            'violation_details': violation_details,
            'recorded_at': datetime.now().isoformat(),
            'violation_id': str(uuid.uuid4())
        }
        
        self.violations.append(violation_record)
    
    def get_contract_status(self, contract_id: str) -> Dict[str, Any]:
        """
        Получить статус контракта
        """
        if contract_id not in self.contracts:
            return {
                'status': 'not_found',
                'error': 'Contract not found'
            }
        
        contract = self.contracts[contract_id]
        
        return {
            'contract_id': contract_id,
            'contract_type': contract['contract_type'],
            'status': contract['status'],
            'parties': contract['parties'],
            'signatures': list(contract['signatures'].keys()),
            'created_at': contract['created_at'],
            'terms_summary': self._summarize_terms(contract.get('terms', {}))
        }
    
    def _summarize_terms(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать краткое описание условий контракта
        """
        summary = {}
        
        if 'required_fields' in terms:
            summary['required_fields_count'] = len(terms['required_fields'])
        
        if 'field_types' in terms:
            summary['field_types_count'] = len(terms['field_types'])
        
        if 'deadlines' in terms:
            summary['has_deadlines'] = True
        
        return summary
    
    def get_violation_report(self, contract_id: str = None) -> List[Dict[str, Any]]:
        """
        Получить отчет о нарушениях контрактов
        """
        if contract_id:
            return [v for v in self.violations if v['contract_id'] == contract_id]
        else:
            return self.violations
    
    def enforce_contract_compliance(self, contract_id: str) -> bool:
        """
        Принудительно обеспечить соблюдение контракта
        """
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        
        # Проверяем, все ли стороны подписали контракт
        required_signatures = set(contract['parties'])
        actual_signatures = set(contract['signatures'].keys())
        
        missing_signatures = required_signatures - actual_signatures
        
        if missing_signatures:
            # Записываем нарушение
            self.record_contract_violation(
                contract_id,
                'contract_system',
                {
                    'type': 'missing_signatures',
                    'missing_parties': list(missing_signatures),
                    'description': f'Missing signatures from parties: {missing_signatures}'
                }
            )
            return False
        
        return True
    
    def terminate_contract(self, contract_id: str, reason: str = None) -> bool:
        """
        Расторгнуть контракт
        """
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        contract['status'] = 'terminated'
        contract['termination_reason'] = reason
        contract['terminated_at'] = datetime.now().isoformat()
        
        return True

# Базовые контракты

class TaskAssignmentContract:
    """
    Контракт на назначение задач
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'task_assignment',
            'required_fields': ['agent_type', 'task_description', 'session_id', 'deadline'],
            'field_types': {
                'agent_type': 'string',
                'task_description': 'string',
                'session_id': 'string',
                'deadline': 'datetime'
            },
            'validation_rules': [
                'agent_type_must_be_valid',
                'task_description_must_not_be_empty',
                'deadline_must_be_future'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['agent_type', 'task_description', 'session_id', 'deadline']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['assignment_status', 'assigned_at']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем обязательные поля
        if 'agent_type' not in execution_data:
            errors.append('Missing agent_type')
        
        if 'task_description' not in execution_data or not execution_data['task_description']:
            errors.append('Empty or missing task_description')
        
        if 'deadline' in execution_data:
            try:
                deadline = datetime.fromisoformat(execution_data['deadline'])
                if deadline < datetime.now():
                    errors.append('Deadline must be in the future')
            except ValueError:
                errors.append('Invalid deadline format')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class TaskExecutionContract:
    """
    Контракт на выполнение задач
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'task_execution',
            'required_fields': ['agent_type', 'task_description', 'result', 'artifacts_created'],
            'field_types': {
                'agent_type': 'string',
                'task_description': 'string',
                'result': 'string',
                'artifacts_created': 'list'
            },
            'validation_rules': [
                'result_must_not_contain_placeholders',
                'artifacts_must_be_list',
                'execution_must_have_content'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['agent_type', 'task_description']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['result', 'artifacts_created', 'completed_at']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем, что результат не содержит placeholder-текстов
        result = execution_data.get('result', '')
        forbidden_patterns = ['NEEDS_CLARIFICATION', 'TODO', 'FIXME', 'placeholder']
        
        for pattern in forbidden_patterns:
            if pattern in result:
                errors.append(f'Forbidden pattern in result: {pattern}')
        
        # Проверяем, что артефакты являются списком
        artifacts = execution_data.get('artifacts_created', [])
        if not isinstance(artifacts, list):
            errors.append('artifacts_created must be a list')
        
        # Проверяем, что есть реальное содержание результата
        if len(result) < 20:
            errors.append('Result content is too short')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class ResultDeliveryContract:
    """
    Контракт на доставку результатов
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'result_delivery',
            'required_fields': ['sender', 'recipient', 'result_data', 'delivery_timestamp'],
            'field_types': {
                'sender': 'string',
                'recipient': 'string',
                'result_data': 'dict',
                'delivery_timestamp': 'datetime'
            },
            'validation_rules': [
                'sender_must_be_valid_agent',
                'recipient_must_be_valid_agent',
                'result_data_must_be_dict'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['sender', 'recipient', 'result_data']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['delivery_status', 'acknowledged_at']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем, что отправитель и получатель не совпадают
        sender = execution_data.get('sender', '')
        recipient = execution_data.get('recipient', '')
        
        if sender == recipient and sender:  # Если оба заданы и совпадают
            errors.append('Sender and recipient cannot be the same')
        
        # Проверяем, что данные результата являются словарем
        result_data = execution_data.get('result_data', {})
        if not isinstance(result_data, dict):
            errors.append('result_data must be a dictionary')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class QualityAssuranceContract:
    """
    Контракт на обеспечение качества
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'quality_assurance',
            'required_fields': ['artifacts', 'quality_score', 'issues_found', 'verification_timestamp'],
            'field_types': {
                'artifacts': 'list',
                'quality_score': 'float',
                'issues_found': 'list',
                'verification_timestamp': 'datetime'
            },
            'validation_rules': [
                'quality_score_must_be_between_0_and_1',
                'artifacts_must_be_list',
                'issues_found_must_be_list'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['artifacts', 'quality_score']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['verification_result', 'approved_at']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем диапазон оценки качества
        quality_score = execution_data.get('quality_score', 0.0)
        if not (0.0 <= quality_score <= 1.0):
            errors.append('quality_score must be between 0.0 and 1.0')
        
        # Проверяем, что артефакты и проблемы являются списками
        artifacts = execution_data.get('artifacts', [])
        issues_found = execution_data.get('issues_found', [])
        
        if not isinstance(artifacts, list):
            errors.append('artifacts must be a list')
        
        if not isinstance(issues_found, list):
            errors.append('issues_found must be a list')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class ArtifactCreationContract:
    """
    Контракт на создание артефактов
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'artifact_creation',
            'required_fields': ['artifact_name', 'artifact_type', 'content', 'created_at'],
            'field_types': {
                'artifact_name': 'string',
                'artifact_type': 'string',
                'content': 'string',
                'created_at': 'datetime'
            },
            'validation_rules': [
                'artifact_name_must_not_be_empty',
                'artifact_type_must_be_valid',
                'content_must_have_minimum_length'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['artifact_name', 'artifact_type', 'content']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['creation_status', 'artifact_path']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем, что имя артефакта не пустое
        artifact_name = execution_data.get('artifact_name', '')
        if not artifact_name or not artifact_name.strip():
            errors.append('artifact_name cannot be empty')
        
        # Проверяем, что содержание имеет минимальную длину
        content = execution_data.get('content', '')
        if len(content) < 10:
            errors.append('content must be at least 10 characters long')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class ProgressReportingContract:
    """
    Контракт на отчет о прогрессе
    """
    
    def get_contract_specification(self) -> Dict[str, Any]:
        return {
            'contract_type': 'progress_reporting',
            'required_fields': ['session_id', 'progress_percentage', 'current_step', 'total_steps', 'report_timestamp'],
            'field_types': {
                'session_id': 'string',
                'progress_percentage': 'float',
                'current_step': 'integer',
                'total_steps': 'integer',
                'report_timestamp': 'datetime'
            },
            'validation_rules': [
                'progress_percentage_must_be_between_0_and_100',
                'current_step_must_not_exceed_total_steps',
                'session_id_must_be_valid'
            ]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ['session_id', 'progress_percentage', 'current_step', 'total_steps']
        return all(field in input_data for field in required_fields)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        required_fields = ['report_status', 'acknowledged_at']
        return all(field in output_data for field in required_fields)
    
    def validate_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Проверяем диапазон процента прогресса
        progress_percentage = execution_data.get('progress_percentage', 0.0)
        if not (0.0 <= progress_percentage <= 100.0):
            errors.append('progress_percentage must be between 0.0 and 100.0')
        
        # Проверяем согласованность шагов
        current_step = execution_data.get('current_step', 0)
        total_steps = execution_data.get('total_steps', 1)
        
        if current_step > total_steps:
            errors.append('current_step cannot exceed total_steps')
        
        # Проверяем ID сессии
        session_id = execution_data.get('session_id', '')
        if not session_id or not session_id.strip():
            errors.append('session_id cannot be empty')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# Глобальный менеджер контрактов
contract_manager = ContractManager()