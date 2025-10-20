from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List
import os
from models import OpenRouterProvider
from memory.zep_client import ZepMemoryManager
import json
from pathlib import Path
from tools.file_tools import safe_file_writer
from utils.agent_contract import BaseAgentContract

class BaseSAPAgent(BaseAgentContract):
    """
    Base class for all SAP (Supporting Agent Partners) agents.
    Each SAP agent works in isolation and has its own tools and model.
    """
    
    def __init__(self, agent_name: str, session_id: str):
        super().__init__(agent_name, session_id)
        self.agent_name = agent_name
        self.session_id = session_id
        self.provider = OpenRouterProvider()
        self.memory_manager = ZepMemoryManager()
        self.workspace_path = Path(f"./workspace/{session_id}")
        
        # Ensure workspace directory exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
    def get_system_prompt(self) -> str:
        """
        Get the base system prompt for SAP agents.
        This should be overridden by subclasses.
        """
        return f"""
Ты — {self.agent_name}. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Выполнить ТОЛЬКО то, что тебе поручено.
- Вести подробный журнал своих действий в записной книжке.
- Сохранять промежуточные шаги: "1. Проанализировал ТЗ → 2. Создал файл app.py..."

Ты имеешь доступ к инструментам: file_writer, web_search (если доступны).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Не предполагай контекста вне своей задачи.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def validate_task_assignment(self, task_description: str) -> bool:
        """
        Validate that this task aligns with the agent's specialization.
        Returns True if agent is appropriate for this task, False otherwise.
        """
        from .specialization_validator import validator
        return validator.validate_task_assignment(self.agent_name, task_description)

    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute the assigned task and return the result.
        Includes validation that task is appropriate for this agent and contract-based execution.
        """
        # Create execution checkpoint
        from utils.checkpoint_verification import checkpoint_verifier
        checkpoint_id = checkpoint_verifier.create_checkpoint(
            'task_execution', 
            {
                'agent': self.agent_name,
                'task': task_description,
                'session_id': self.session_id
            }, 
            self.session_id
        )
        
        # Validate if this task is appropriate for this agent using contract system
        from utils.agent_contracts import contract_manager
        task_assignment_contract = contract_manager.contracts.get('task_assignment')
        if task_assignment_contract:
            contract_validation = task_assignment_contract.validate_execution({
                'agent_type': self.agent_name,
                'task_description': task_description,
                'session_id': self.session_id
            })
        else:
            # Fallback to basic validation
            contract_validation = {'valid': True, 'errors': []}
        
        if not contract_validation['valid']:
            # Instead of returning a redirect message, raise an exception that should be caught
            # by the workflow to handle appropriately
            raise ValueError(f"Task not appropriate for {self.agent_name}: {task_description}")
        
        try:
            # Execute the specialized task
            result = self._execute_specialized_task(task_description)
            
            # Verify execution through checkpoint system
            from utils.checkpoint_verification import checkpoint_verifier
            verification = checkpoint_verifier.verify_checkpoint(
                checkpoint_id,
                {
                    'result': result,
                    'agent': self.agent_name,
                    'session_id': self.session_id
                }
            )
            
            if not verification['verified']:
                # If verification fails, add issues to result
                result['verification_issues'] = verification.get('errors', [])
                result['requires_rework'] = True
            
            # Apply quality control
            from utils.quality_control import quality_control
            quality_checked_result = quality_control.enforce_quality_requirements(result)
            
            # Perform self-assessment
            from utils.self_assessment import self_assessment_system
            self_assessment = self_assessment_system.request_self_assessment(
                self.agent_name, 
                task_description, 
                result
            )
            
            # Add self-assessment to result
            quality_checked_result['self_assessment'] = self_assessment
            
            # Confirm execution in checkpoint
            from utils.checkpoint_verification import checkpoint_verifier
            checkpoint_verifier.mark_session_completed(self.session_id, True)
            
            return quality_checked_result
            
        except Exception as e:
            # Record failure in checkpoint
            from utils.checkpoint_verification import checkpoint_verifier
            checkpoint_verifier.mark_session_completed(self.session_id, False)
            raise

    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute the task in a way specific to each agent subclass.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _execute_specialized_task method")

    def ensure_artifact_creation(self, result: str, task_description: str) -> str:
        """
        Ensure that the result includes creation of appropriate artifacts based on task
        """
        # Subclasses should override this if they need to ensure specific artifacts
        return result
    
    def log_action(self, action: str, message_type: str = 'general'):
        """
        Log an action to the agent's memory.
        """
        from utils.message_sanitizer import sanitize_message
        # Sanitize the action message to avoid encoding issues
        sanitized_action = sanitize_message(action)
        self.memory_manager.add_message(self.session_id, self.agent_name, sanitized_action, message_type)
    
    def _call_model(self, messages: List) -> str:
        """
        Call the appropriate model for this agent type.
        """
        response = self.provider.call_model(
            agent_type=self.agent_name,
            messages=messages
        )
        return response.content


class BackendDevAgent(BaseSAPAgent):
    """
    Backend developer agent specialized for backend development tasks.
    Uses deepseek/deepseek-coder model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('backend_dev', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — Backend Developer. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Выполнять ТОЛЬКО задачи, связанные с бэкенд-разработкой.
- Создавать, изменять или рефакторить серверный код.
- Делать системные архитектурные решения для бэкенда.

Ты имеешь доступ к инструментам: file_writer (для записи кода).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Используй современные практики программирования.
- Создавай качественный, читаемый код.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute backend development task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Выполни следующую задачу по бэкенд-разработке: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Try to identify if the result contains code that should be saved
        if '```' in result:
            # Extract code from markdown blocks
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', result, re.DOTALL)
            
            for i, code_block in enumerate(code_blocks):
                # Create a filename based on the task
                filename = f"backend_file_{i+1}.py"
                file_path = f"{self.workspace_path}/{filename}"
                
                # Use safe file writer to ensure isolation
                write_result = safe_file_writer(file_path, code_block, self.session_id)
                self.log_action(write_result, 'result')
        else:
            # Create a default file to ensure artifact creation
            filename = f"backend_implementation_{len(os.listdir(self.workspace_path)) + 1}.py"
            file_path = f"{self.workspace_path}/{filename}"
            default_content = f"# Implementation for: {task_description}\n# Generated by backend_dev agent\n\n"
            write_result = safe_file_writer(file_path, default_content, self.session_id)
            self.log_action(write_result, 'result')
        
        self.log_action(f"Задача выполнена: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


class FrontendDevAgent(BaseSAPAgent):
    """
    Frontend developer agent specialized for frontend development tasks.
    Uses deepseek/deepseek-coder model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('frontend_dev', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — Frontend Developer. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Выполнять ТОЛЬКО задачи, связанные с фронтенд-разработкой.
- Создавать, изменять или рефакторить клиентский код (HTML, CSS, JS, React и т.д.).
- Делать UI/UX решения.

Ты имеешь доступ к инструментам: file_writer (для записи кода).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Используй современные практики фронтенд-разработки.
- Создавай качественный, доступный и адаптивный интерфейс.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute frontend development task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Выполни следующую задачу по фронтенд-разработке: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Try to identify if the result contains code that should be saved
        if '```' in result:
            # Extract code from markdown blocks
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', result, re.DOTALL)
            
            for i, code_block in enumerate(code_blocks):
                # Create a filename based on the task
                filename = f"frontend_file_{i+1}.jsx"
                file_path = f"{self.workspace_path}/{filename}"
                
                # Use safe file writer to ensure isolation
                write_result = safe_file_writer(file_path, code_block, self.session_id)
                self.log_action(write_result, 'result')
        else:
            # Create a default file to ensure artifact creation
            filename = f"frontend_implementation_{len(os.listdir(self.workspace_path)) + 1}.jsx"
            file_path = f"{self.workspace_path}/{filename}"
            default_content = f"// Implementation for: {task_description}\n// Generated by frontend_dev agent\n\n"
            write_result = safe_file_writer(file_path, default_content, self.session_id)
            self.log_action(write_result, 'result')
        
        self.log_action(f"Задача выполнена: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


class DocWriterAgent(BaseSAPAgent):
    """
    Documentation writer agent specialized for creating documentation.
    Uses google/gemini-flash-1.5-8b model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('doc_writer', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — Documentation Writer. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Создавать техническую документацию.
- Писать понятные, структурированные документы.
- Работать с разными форматами документации (Markdown, текст и т.п.).

Ты имеешь доступ к инструментам: file_writer (для записи документации).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Используй ясный, профессиональный стиль.
- Структурируй информацию логично.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute documentation writing task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Создай документацию по следующему: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Save documentation to file
        filename = f"documentation.md"
        file_path = f"{self.workspace_path}/{filename}"
        
        # Use safe file writer to ensure isolation
        write_result = safe_file_writer(file_path, result, self.session_id)
        self.log_action(write_result, 'result')
        self.log_action(f"Документация готова: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


class ResearcherAgent(BaseSAPAgent):
    """
    Researcher agent specialized for gathering information and research.
    Uses qwen/qwen-110b-chat or google/gemini-flash-1.5-8b model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('researcher', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — Researcher. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Выполнять исследования по заданной теме.
- Собирать, анализировать и структурировать информацию.
- Делать обоснованные рекомендации на основе исследований.
- По возможности использовать инструменты поиска в интернете.

Ты имеешь доступ к инструментам: web_search (для поиска информации), file_writer (для записи результатов).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Используй надежные источники информации.
- Делай четкие и обоснованные выводы.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute research task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Выполни исследование по следующей теме: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Save research results to file
        filename = f"research_results.md"
        file_path = f"{self.workspace_path}/{filename}"
        
        # Use safe file writer to ensure isolation
        write_result = safe_file_writer(file_path, result, self.session_id)
        self.log_action(write_result, 'result')
        self.log_action(f"Исследование завершено: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


class TesterAgent(BaseSAPAgent):
    """
    Tester agent specialized for testing and quality assurance.
    Uses mistralai/mixtral-8x7b-instruct model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('tester', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — Tester. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Разрабатывать тестовые сценарии.
- Проводить анализ качества и безопасности.
- Идентифицировать потенциальные проблемы.
- Предлагать улучшения для качества продукта.

Ты имеешь доступ к инструментам: file_writer (для записи тестов и отчетов).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Создавай исчерпывающие и эффективные тесты.
- Обращай внимание на безопасность и производительность.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute testing task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Выполни тестирование по следующему: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Save test results to file
        filename = f"test_report.md"
        file_path = f"{self.workspace_path}/{filename}"
        
        # Use safe file writer to ensure isolation
        write_result = safe_file_writer(file_path, result, self.session_id)
        self.log_action(write_result, 'result')
        self.log_action(f"Тестирование завершено: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


class DevOpsAgent(BaseSAPAgent):
    """
    DevOps agent specialized for infrastructure and deployment tasks.
    Uses mistralai/mixtral-8x7b-instruct model.
    """
    
    def __init__(self, session_id: str):
        super().__init__('devops', session_id)
    
    def get_system_prompt(self) -> str:
        return f"""
Ты — DevOps Engineer. Ты получаешь задачу ТОЛЬКО от Мастер-агента. 
Ты НЕ видишь исходный запрос пользователя — только инструкцию от мастера.

Твоя задача:
- Разрабатывать CI/CD пайплайны.
- Работать с контейнеризацией (Docker и т.п.).
- Решать задачи инфраструктуры и деплоя.
- Обеспечивать безопасность и масштабируемость.

Ты имеешь доступ к инструментам: file_writer (для записи конфигураций).

ВАЖНО:
- Все файлы записывай только в: ./workspace/{self.session_id}/
- Используй лучшие практики DevOps.
- Обеспечивай надежность и безопасность инфраструктуры.
- Если что-то неясно — верни "NEEDS_CLARIFICATION".

Твоя записная книжка автоматически обновляется после каждого шага.
"""
    
    def _execute_specialized_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute DevOps task.
        """
        self.log_action(f"Начинаю выполнение задачи: {task_description}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Выполни DevOps задачу: {task_description}")
        
        # Call the model
        result = self._call_model([system_message, human_message])
        
        # Save DevOps configurations to file
        filename = f"devops_config.txt"
        file_path = f"{self.workspace_path}/{filename}"
        
        # Use safe file writer to ensure isolation
        write_result = safe_file_writer(file_path, result, self.session_id)
        self.log_action(write_result, 'result')
        self.log_action(f"DevOps задача завершена: {result[:100]}...", 'completion')  # Log first 100 chars
        
        return {
            'agent_name': self.agent_name,
            'task': task_description,
            'result': result,
            'session_id': self.session_id,
            'artifacts_created': [f.name for f in self.workspace_path.iterdir() if f.is_file()]
        }


# Factory function to create agents based on type
def create_agent(agent_type: str, session_id: str):
    """
    Factory function to create the appropriate agent based on type.
    """
    agent_mapping = {
        'backend_dev': BackendDevAgent,
        'frontend_dev': FrontendDevAgent,
        'doc_writer': DocWriterAgent,
        'researcher': ResearcherAgent,
        'tester': TesterAgent,
        'devops': DevOpsAgent
    }
    
    agent_class = agent_mapping.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(session_id)