from typing import Protocol, Dict, Any, List, Callable
from abc import abstractmethod
from pathlib import Path
import json

class AgentContract(Protocol):
    """
    Протокол контракта агента, определяющий обязательные методы и свойства
    """
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Тип агента (например, 'backend_dev', 'researcher', и т.д.)"""
        pass
    
    @property
    @abstractmethod
    def specialization_keywords(self) -> List[str]:
        """Ключевые слова, определяющие специализацию"""
        pass
    
    @abstractmethod
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Выполнить задачу и вернуть результат с обязательным созданием артефактов"""
        pass

class BaseAgentContract:
    """
    Базовая реализация контракта агента
    """
    
    def __init__(self, agent_type: str, session_id: str):
        self._agent_type = agent_type
        self.session_id = session_id
        
        # Словарь ключевых слов для каждой специализации
        self._specialization_keywords = {
            'researcher': ['research', 'study', 'analyze', 'examine', 'investigate', 'evaluate', 'gather information', 'best practices', 'find', 'explore'],
            'backend_dev': ['backend', 'server', 'api', 'flask', 'django', 'programming', 'code', 'implementation', 'backend', 'server-side'],
            'frontend_dev': ['frontend', 'ui', 'react', 'vue', 'html', 'css', 'client-side', 'interface', 'frontend'],
            'doc_writer': ['document', 'documentation', 'write', 'manual', 'guide', 'readme', 'usage', 'describe', 'explain'],
            'tester': ['test', 'testing', 'unit test', 'integration test', 'quality', 'checker', 'verify', 'validate', 'coverage'],
            'devops': ['docker', 'deploy', 'pipeline', 'ci/cd', 'infrastructure', 'kubernetes', 'dockerfile', 'install', 'setup', 'monitoring']
        }
    
    @property
    def agent_type(self) -> str:
        return self._agent_type
    
    @property
    def specialization_keywords(self) -> List[str]:
        return self._specialization_keywords.get(self._agent_type, [])
    
    def validate_task_assignment(self, task_description: str) -> bool:
        """
        Проверить, соответствует ли задача специализации агента
        """
        task_lower = task_description.lower()
        for keyword in self.specialization_keywords:
            if keyword.lower() in task_lower:
                return True
        return False
    
    def ensure_artifact_created(self, result: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """
        Обеспечить создание обязательного артефакта
        """
        # Проверяем, были ли созданы какие-либо файлы в рабочей директории
        workspace_path = Path(f"./workspace/{self.session_id}")
        files_created = list(workspace_path.glob("*")) if workspace_path.exists() else []
        
        if not files_created:
            # Если файлы не были созданы, создаем минимальный артефакт
            artifact_name = f"{self.agent_type}_output_{len(files_created) + 1}.txt"
            artifact_path = workspace_path / artifact_name
            artifact_path.write_text(f"Task: {task_description}\nAgent: {self.agent_type}\nResult: {result.get('result', 'No result provided')}")
            result['artifact_created'] = str(artifact_path)
        
        result['artifacts_count'] = len(files_created)
        return result

# Global registry for agent contracts
agent_contract_registry = {}

def register_agent_contract(agent_type: str, contract_class):
    """
    Зарегистрировать контракт для типа агента
    """
    agent_contract_registry[agent_type] = contract_class

def get_agent_contract(agent_type: str, session_id: str):
    """
    Получить экземпляр контракта для типа агента
    """
    if agent_type in agent_contract_registry:
        return agent_contract_registry[agent_type](session_id)
    else:
        raise ValueError(f"No contract registered for agent type: {agent_type}")