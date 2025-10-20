from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import uuid
from datetime import datetime
import json
import asyncio

class AgentMicroservice(ABC):
    """
    Базовый класс микросервиса агента
    """
    
    def __init__(self, agent_type: str, service_id: str = None):
        self.agent_type = agent_type
        self.service_id = service_id or str(uuid.uuid4())
        self.status = 'initialized'
        self.capabilities = []
        self.health_check_endpoint = f'/health/{self.service_id}'
        self.task_endpoint = f'/task/{self.service_id}'
        
        # Регистрируем микросервис
        AgentServiceRegistry.register_service(self)
    
    @abstractmethod
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить задачу (абстрактный метод для реализации в подклассах)
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверить здоровье микросервиса
        """
        return {
            'service_id': self.service_id,
            'agent_type': self.agent_type,
            'status': self.status,
            'timestamp': datetime.now().isoformat(),
            'capabilities': self.capabilities,
            'health_status': 'healthy' if self.status != 'error' else 'unhealthy'
        }
    
    def update_status(self, new_status: str):
        """
        Обновить статус микросервиса
        """
        self.status = new_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Получить информацию о микросервисе
        """
        return {
            'service_id': self.service_id,
            'agent_type': self.agent_type,
            'status': self.status,
            'capabilities': self.capabilities,
            'endpoints': {
                'health': self.health_check_endpoint,
                'task': self.task_endpoint
            }
        }

class AgentServiceRegistry:
    """
    Реестр микросервисов агентов
    """
    
    _services = {}
    _service_discovery = {}
    
    @classmethod
    def register_service(cls, service: AgentMicroservice):
        """
        Зарегистрировать микросервис
        """
        cls._services[service.service_id] = service
        cls._update_service_discovery(service)
    
    @classmethod
    def _update_service_discovery(cls, service: AgentMicroservice):
        """
        Обновить информацию о службе в реестре обнаружения
        """
        if service.agent_type not in cls._service_discovery:
            cls._service_discovery[service.agent_type] = []
        
        # Добавляем или обновляем информацию о службе
        service_info = service.get_service_info()
        
        # Проверяем, существует ли уже такой сервис
        existing_services = [
            s for s in cls._service_discovery[service.agent_type] 
            if s['service_id'] == service.service_id
        ]
        
        if existing_services:
            # Обновляем существующую запись
            for i, existing in enumerate(cls._service_discovery[service.agent_type]):
                if existing['service_id'] == service.service_id:
                    cls._service_discovery[service.agent_type][i] = service_info
        else:
            # Добавляем новую запись
            cls._service_discovery[service.agent_type].append(service_info)
    
    @classmethod
    def get_available_services(cls, agent_type: str = None) -> List[Dict[str, Any]]:
        """
        Получить список доступных микросервисов
        """
        if agent_type:
            return cls._service_discovery.get(agent_type, [])
        else:
            # Возвращаем все сервисы
            all_services = []
            for services in cls._service_discovery.values():
                all_services.extend(services)
            return all_services
    
    @classmethod
    def get_service_by_id(cls, service_id: str) -> Optional[AgentMicroservice]:
        """
        Получить микросервис по ID
        """
        return cls._services.get(service_id)
    
    @classmethod
    def remove_service(cls, service_id: str):
        """
        Удалить микросервис из реестра
        """
        if service_id in cls._services:
            service = cls._services.pop(service_id)
            # Удаляем из реестра обнаружения
            if service.agent_type in cls._service_discovery:
                cls._service_discovery[service.agent_type] = [
                    s for s in cls._service_discovery[service.agent_type]
                    if s['service_id'] != service_id
                ]
    
    @classmethod
    def get_service_stats(cls) -> Dict[str, Any]:
        """
        Получить статистику по микросервисам
        """
        stats = {
            'total_services': len(cls._services),
            'services_by_type': {},
            'healthy_services': 0,
            'unhealthy_services': 0
        }
        
        # Считаем сервисы по типам
        for agent_type, services in cls._service_discovery.items():
            stats['services_by_type'][agent_type] = len(services)
        
        # Считаем здоровые и нездоровые сервисы
        for service in cls._services.values():
            if service.status != 'error':
                stats['healthy_services'] += 1
            else:
                stats['unhealthy_services'] += 1
        
        return stats

class ServiceOrchestrator:
    """
    Оркестратор микросервисов агентов
    """
    
    def __init__(self):
        self.active_tasks = {}
        self.task_results = {}
    
    async def dispatch_task(self, agent_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправить задачу подходящему микросервису
        """
        # Получаем доступные микросервисы для данного типа агента
        available_services = AgentServiceRegistry.get_available_services(agent_type)
        
        if not available_services:
            # Если нет доступных сервисов, создаем новый
            service = self._create_new_service(agent_type)
            available_services = [service.get_service_info()]
        
        # Выбираем лучший сервис (на основе нагрузки, здоровья и т.д.)
        best_service_info = self._select_best_service(available_services)
        
        if not best_service_info:
            raise Exception(f"No suitable service found for agent type: {agent_type}")
        
        # Получаем экземпляр сервиса
        service = AgentServiceRegistry.get_service_by_id(best_service_info['service_id'])
        
        if not service:
            raise Exception(f"Service instance not found: {best_service_info['service_id']}")
        
        # Создаем ID задачи
        task_id = str(uuid.uuid4())
        
        # Отправляем задачу сервису
        try:
            service.update_status('busy')
            result = await service.execute_task(task_data)
            service.update_status('ready')
            
            # Сохраняем результат
            self.task_results[task_id] = result
            
            return {
                'task_id': task_id,
                'result': result,
                'service_id': service.service_id,
                'status': 'completed'
            }
            
        except Exception as e:
            service.update_status('error')
            raise Exception(f"Task execution failed: {str(e)}")
    
    def _create_new_service(self, agent_type: str) -> AgentMicroservice:
        """
        Создать новый микросервис для агента
        """
        # Здесь должна быть логика создания нового микросервиса
        # В упрощенной версии создаем экземпляр соответствующего класса
        
        service_class = self._get_service_class(agent_type)
        if service_class:
            service = service_class()
            return service
        else:
            raise Exception(f"No service class found for agent type: {agent_type}")
    
    def _get_service_class(self, agent_type: str) -> Optional[type]:
        """
        Получить класс микросервиса по типу агента
        """
        # В реальной системе это будет более сложное сопоставление
        # Здесь упрощенная версия
        from utils.microservices import (
            ResearcherMicroservice, BackendDevMicroservice, 
            FrontendDevMicroservice, DocWriterMicroservice,
            TesterMicroservice, DevOpsMicroservice
        )
        
        service_mapping = {
            'researcher': ResearcherMicroservice,
            'backend_dev': BackendDevMicroservice,
            'frontend_dev': FrontendDevMicroservice,
            'doc_writer': DocWriterMicroservice,
            'tester': TesterMicroservice,
            'devops': DevOpsMicroservice
        }
        
        return service_mapping.get(agent_type)
    
    def _select_best_service(self, services: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Выбрать лучший микросервис из доступных
        """
        if not services:
            return None
        
        # Фильтруем здоровые сервисы
        healthy_services = [
            service for service in services 
            if service.get('health_status') == 'healthy'
        ]
        
        if not healthy_services:
            # Если нет здоровых сервисов, берем первый доступный
            return services[0] if services else None
        
        # Выбираем сервис с наименьшим количеством задач
        # В упрощенной версии просто берем первый здоровый
        return healthy_services[0]
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить результат задачи по ID
        """
        return self.task_results.get(task_id)
    
    async def health_check_all_services(self) -> Dict[str, Any]:
        """
        Проверить здоровье всех микросервисов
        """
        services = AgentServiceRegistry.get_available_services()
        health_results = []
        
        for service_info in services:
            service = AgentServiceRegistry.get_service_by_id(service_info['service_id'])
            if service:
                try:
                    health = await service.health_check()
                    health_results.append(health)
                except Exception as e:
                    health_results.append({
                        'service_id': service_info['service_id'],
                        'agent_type': service_info['agent_type'],
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'services_health': health_results,
            'registry_stats': AgentServiceRegistry.get_service_stats()
        }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """
        Получить статистику оркестратора
        """
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.task_results),
            'timestamp': datetime.now().isoformat()
        }

class LoadBalancer:
    """
    Балансировщик нагрузки для микросервисов
    """
    
    def __init__(self):
        self.service_loads = {}  # Следим за нагрузкой сервисов
    
    def update_service_load(self, service_id: str, load: int):
        """
        Обновить информацию о нагрузке сервиса
        """
        self.service_loads[service_id] = {
            'load': load,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_least_loaded_service(self, services: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Получить наименее загруженный сервис
        """
        if not services:
            return None
        
        # Фильтруем сервисы с известной нагрузкой
        loaded_services = []
        unloaded_services = []
        
        for service in services:
            service_id = service['service_id']
            if service_id in self.service_loads:
                loaded_services.append((service, self.service_loads[service_id]['load']))
            else:
                unloaded_services.append(service)
        
        # Если есть незагруженные сервисы, отдаем первый из них
        if unloaded_services:
            return unloaded_services[0]
        
        # Если все сервисы имеют нагрузку, отдаем наименее загруженный
        if loaded_services:
            return min(loaded_services, key=lambda x: x[1])[0]
        
        # Возвращаем первый доступный
        return services[0] if services else None

# Глобальные экземпляры
service_registry = AgentServiceRegistry()
service_orchestrator = ServiceOrchestrator()
load_balancer = LoadBalancer()

# Декоратор для регистрации микросервисов
def agent_microservice(agent_type: str):
    """
    Декоратор для регистрации микросервиса агента
    """
    def decorator(cls):
        # Автоматически регистрируем микросервис при создании
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # Вызываем оригинальный __init__
            original_init(self, *args, **kwargs)
            # Устанавливаем тип агента и ID
            self.agent_type = agent_type
            self.service_id = str(uuid.uuid4())
            # Регистрируем в реестре
            AgentServiceRegistry.register_service(self)
        
        cls.__init__ = new_init
        return cls
    
    return decorator