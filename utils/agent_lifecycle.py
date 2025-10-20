from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import uuid
import threading
import time
from abc import ABC, abstractmethod

class AgentLifecycleManager:
    """
    Менеджер жизненного цикла агентов
    """
    
    def __init__(self):
        self.agents = {}
        self.agent_states = {}
        self.lifecycle_events = []
        self.agent_pools = {}
        
        # Инициализируем систему управления жизненным циклом
        self._initialize_lifecycle_management()
    
    def _initialize_lifecycle_management(self):
        """
        Инициализировать систему управления жизненным циклом
        """
        # Определяем состояния агентов
        self.agent_states = {
            'idle': 'Agent is ready but not currently processing tasks',
            'active': 'Agent is currently processing a task',
            'paused': 'Agent is temporarily paused',
            'terminated': 'Agent has been terminated',
            'error': 'Agent encountered an error',
            'restarting': 'Agent is restarting after an error'
        }
        
        # Определяем события жизненного цикла
        self.lifecycle_events = [
            'agent_created',
            'agent_started',
            'agent_paused',
            'agent_resumed',
            'agent_terminated',
            'agent_error',
            'agent_restart_initiated',
            'agent_restarted'
        ]
        
        # Инициализируем пулы агентов
        self.agent_pools = {
            'researcher_pool': [],
            'backend_dev_pool': [],
            'frontend_dev_pool': [],
            'doc_writer_pool': [],
            'tester_pool': [],
            'devops_pool': []
        }
    
    def create_agent(self, agent_type: str, session_id: str) -> str:
        """
        Создать нового агента
        """
        agent_id = str(uuid.uuid4())
        
        # Создаем запись агента
        agent_record = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'state': 'idle',
            'last_state_change': datetime.now().isoformat(),
            'task_history': [],
            'performance_metrics': {},
            'error_count': 0,
            'restart_count': 0,
            'pool_assignment': None
        }
        
        # Сохраняем агента
        self.agents[agent_id] = agent_record
        
        # Добавляем агента в соответствующий пул
        pool_name = f"{agent_type}_pool"
        if pool_name in self.agent_pools:
            self.agent_pools[pool_name].append(agent_id)
            agent_record['pool_assignment'] = pool_name
        
        # Записываем событие создания агента
        self._record_lifecycle_event(agent_id, 'agent_created', {
            'agent_type': agent_type,
            'session_id': session_id
        })
        
        return agent_id
    
    def start_agent(self, agent_id: str) -> bool:
        """
        Запустить агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Проверяем, может ли агент быть запущен
        if agent['state'] in ['idle', 'paused']:
            agent['state'] = 'active'
            agent['last_state_change'] = datetime.now().isoformat()
            
            # Записываем событие запуска агента
            self._record_lifecycle_event(agent_id, 'agent_started', {
                'previous_state': agent['state'],
                'new_state': 'active'
            })
            
            return True
        
        return False
    
    def pause_agent(self, agent_id: str) -> bool:
        """
        Приостановить агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Проверяем, может ли агент быть приостановлен
        if agent['state'] == 'active':
            agent['state'] = 'paused'
            agent['last_state_change'] = datetime.now().isoformat()
            
            # Записываем событие приостановки агента
            self._record_lifecycle_event(agent_id, 'agent_paused', {
                'previous_state': 'active',
                'new_state': 'paused'
            })
            
            return True
        
        return False
    
    def resume_agent(self, agent_id: str) -> bool:
        """
        Возобновить работу агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Проверяем, может ли агент быть возобновлен
        if agent['state'] == 'paused':
            agent['state'] = 'active'
            agent['last_state_change'] = datetime.now().isoformat()
            
            # Записываем событие возобновления агента
            self._record_lifecycle_event(agent_id, 'agent_resumed', {
                'previous_state': 'paused',
                'new_state': 'active'
            })
            
            return True
        
        return False
    
    def terminate_agent(self, agent_id: str, reason: str = None) -> bool:
        """
        Завершить работу агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Обновляем состояние агента
        agent['state'] = 'terminated'
        agent['last_state_change'] = datetime.now().isoformat()
        agent['termination_reason'] = reason
        
        # Удаляем агента из пула
        if agent['pool_assignment']:
            pool = self.agent_pools.get(agent['pool_assignment'], [])
            if agent_id in pool:
                pool.remove(agent_id)
        
        # Записываем событие завершения агента
        self._record_lifecycle_event(agent_id, 'agent_terminated', {
            'previous_state': agent['state'],
            'new_state': 'terminated',
            'reason': reason
        })
        
        return True
    
    def handle_agent_error(self, agent_id: str, error_details: Dict[str, Any]) -> bool:
        """
        Обработать ошибку агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Обновляем состояние агента
        agent['state'] = 'error'
        agent['last_state_change'] = datetime.now().isoformat()
        agent['error_count'] += 1
        agent['last_error'] = error_details
        
        # Записываем событие ошибки агента
        self._record_lifecycle_event(agent_id, 'agent_error', {
            'previous_state': agent['state'],
            'new_state': 'error',
            'error_details': error_details
        })
        
        # Проверяем, нужно ли перезапускать агента
        if agent['error_count'] <= 3:  # Максимум 3 перезапуска
            return self.restart_agent(agent_id)
        
        return False
    
    def restart_agent(self, agent_id: str) -> bool:
        """
        Перезапустить агента после ошибки
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Проверяем, можно ли перезапустить агента
        if agent['state'] in ['error', 'terminated']:
            # Обновляем состояние агента
            agent['state'] = 'restarting'
            agent['last_state_change'] = datetime.now().isoformat()
            agent['restart_count'] += 1
            
            # Записываем событие инициации перезапуска
            self._record_lifecycle_event(agent_id, 'agent_restart_initiated', {
                'previous_state': agent['state'],
                'new_state': 'restarting',
                'restart_count': agent['restart_count']
            })
            
            # Симулируем перезапуск (в реальной системе это будет фактический перезапуск)
            time.sleep(1)  # Имитация времени перезапуска
            
            # Обновляем состояние после перезапуска
            agent['state'] = 'idle'
            agent['last_state_change'] = datetime.now().isoformat()
            agent['last_error'] = None  # Очищаем последнюю ошибку
            
            # Добавляем агента обратно в пул
            if agent['pool_assignment']:
                self.agent_pools[agent['pool_assignment']].append(agent_id)
            
            # Записываем событие перезапуска
            self._record_lifecycle_event(agent_id, 'agent_restarted', {
                'previous_state': 'restarting',
                'new_state': 'idle',
                'restart_successful': True
            })
            
            return True
        
        return False
    
    def assign_task_to_agent(self, agent_id: str, task: Dict[str, Any]) -> bool:
        """
        Назначить задачу агенту
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Проверяем, может ли агент принимать задачи
        if agent['state'] == 'idle':
            # Обновляем состояние агента
            agent['state'] = 'active'
            agent['last_state_change'] = datetime.now().isoformat()
            
            # Добавляем задачу в историю
            task_record = {
                'task_id': str(uuid.uuid4()),
                'task': task,
                'assigned_at': datetime.now().isoformat(),
                'completed_at': None,
                'status': 'assigned'
            }
            
            agent['task_history'].append(task_record)
            
            # Записываем событие назначения задачи
            self._record_lifecycle_event(agent_id, 'task_assigned', {
                'task_id': task_record['task_id'],
                'task_description': task.get('task', '')[0:100] + '...' if len(task.get('task', '')) > 100 else task.get('task', ''),
                'agent_state_changed_to': 'active'
            })
            
            return True
        
        return False
    
    def complete_agent_task(self, agent_id: str, task_id: str, result: Dict[str, Any]) -> bool:
        """
        Завершить задачу агента
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # Находим задачу в истории
        for task_record in agent['task_history']:
            if task_record['task_id'] == task_id:
                # Обновляем запись задачи
                task_record['completed_at'] = datetime.now().isoformat()
                task_record['status'] = 'completed'
                task_record['result'] = result
                
                # Обновляем состояние агента
                agent['state'] = 'idle'
                agent['last_state_change'] = datetime.now().isoformat()
                
                # Записываем событие завершения задачи
                self._record_lifecycle_event(agent_id, 'task_completed', {
                    'task_id': task_id,
                    'task_result_preview': str(result)[:200] + '...' if len(str(result)) > 200 else str(result),
                    'agent_state_changed_to': 'idle'
                })
                
                return True
        
        return False
    
    def _record_lifecycle_event(self, agent_id: str, event_type: str, 
                              event_data: Dict[str, Any]):
        """
        Записать событие жизненного цикла агента
        """
        event_record = {
            'event_id': str(uuid.uuid4()),
            'agent_id': agent_id,
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.lifecycle_events.append(event_record)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Получить статус агента
        """
        if agent_id not in self.agents:
            return {
                'agent_id': agent_id,
                'status': 'not_found',
                'error': 'Agent not found'
            }
        
        agent = self.agents[agent_id]
        
        return {
            'agent_id': agent_id,
            'agent_type': agent['agent_type'],
            'session_id': agent['session_id'],
            'current_state': agent['state'],
            'last_state_change': agent['last_state_change'],
            'task_count': len(agent['task_history']),
            'error_count': agent['error_count'],
            'restart_count': agent['restart_count'],
            'pool_assignment': agent['pool_assignment'],
            'status_timestamp': datetime.now().isoformat()
        }
    
    def get_agent_pool_status(self, agent_type: str) -> Dict[str, Any]:
        """
        Получить статус пула агентов
        """
        pool_name = f"{agent_type}_pool"
        
        if pool_name not in self.agent_pools:
            return {
                'pool_name': pool_name,
                'status': 'not_found',
                'error': 'Agent pool not found'
            }
        
        pool_agents = self.agent_pools[pool_name]
        agent_statuses = []
        
        for agent_id in pool_agents:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent_statuses.append({
                    'agent_id': agent_id,
                    'state': agent['state'],
                    'task_count': len(agent['task_history']),
                    'error_count': agent['error_count']
                })
        
        return {
            'pool_name': pool_name,
            'total_agents': len(pool_agents),
            'active_agents': len([agent for agent in agent_statuses if agent['state'] == 'active']),
            'idle_agents': len([agent for agent in agent_statuses if agent['state'] == 'idle']),
            'error_agents': len([agent for agent in agent_statuses if agent['state'] == 'error']),
            'agent_statuses': agent_statuses,
            'pool_timestamp': datetime.now().isoformat()
        }
    
    def get_lifecycle_report(self, agent_id: str = None, 
                           hours: int = 24) -> Dict[str, Any]:
        """
        Получить отчет о жизненном цикле агентов
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if agent_id:
            # Получаем отчет для конкретного агента
            agent_events = [
                event for event in self.lifecycle_events
                if event['agent_id'] == agent_id and 
                datetime.fromisoformat(event['timestamp']) > cutoff_time
            ]
            
            return {
                'report_type': 'agent_specific',
                'agent_id': agent_id,
                'events_count': len(agent_events),
                'events': agent_events,
                'report_period_hours': hours,
                'report_timestamp': datetime.now().isoformat()
            }
        else:
            # Получаем общий отчет по всем агентам
            recent_events = [
                event for event in self.lifecycle_events
                if datetime.fromisoformat(event['timestamp']) > cutoff_time
            ]
            
            # Группируем события по типам
            event_types = {}
            for event in recent_events:
                event_type = event['event_type']
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            # Получаем статусы всех агентов
            agent_statuses = {}
            for agent_id, agent in self.agents.items():
                agent_statuses[agent_id] = agent['state']
            
            return {
                'report_type': 'system_wide',
                'total_events': len(recent_events),
                'event_distribution': event_types,
                'agent_states': agent_statuses,
                'active_agents': len([agent for agent in self.agents.values() if agent['state'] == 'active']),
                'idle_agents': len([agent for agent in self.agents.values() if agent['state'] == 'idle']),
                'error_agents': len([agent for agent in self.agents.values() if agent['state'] == 'error']),
                'terminated_agents': len([agent for agent in self.agents.values() if agent['state'] == 'terminated']),
                'report_period_hours': hours,
                'report_timestamp': datetime.now().isoformat()
            }
    
    def cleanup_terminated_agents(self, older_than_hours: int = 72) -> Dict[str, Any]:
        """
        Очистить завершенных агентов, которые существуют дольше указанного времени
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleaned_agents = []
        
        agents_to_remove = []
        for agent_id, agent in self.agents.items():
            if agent['state'] == 'terminated':
                termination_time = datetime.fromisoformat(agent.get('last_state_change', agent['created_at']))
                if termination_time < cutoff_time:
                    agents_to_remove.append(agent_id)
                    cleaned_agents.append(agent_id)
        
        # Удаляем агентов
        for agent_id in agents_to_remove:
            del self.agents[agent_id]
        
        # Удаляем агентов из пулов
        for pool_name, pool_agents in self.agent_pools.items():
            self.agent_pools[pool_name] = [
                agent_id for agent_id in pool_agents 
                if agent_id not in agents_to_remove
            ]
        
        return {
            'cleanup_performed': True,
            'agents_cleaned_up': len(cleaned_agents),
            'cleaned_agent_ids': cleaned_agents,
            'cleanup_timestamp': datetime.now().isoformat()
        }
    
    def scale_agent_pool(self, agent_type: str, target_count: int) -> Dict[str, Any]:
        """
        Масштабировать пул агентов до целевого количества
        """
        pool_name = f"{agent_type}_pool"
        
        if pool_name not in self.agent_pools:
            return {
                'scaling_successful': False,
                'error': f'Unknown agent pool: {pool_name}'
            }
        
        current_agents = len(self.agent_pools[pool_name])
        
        if target_count > current_agents:
            # Создаем новых агентов
            agents_created = []
            for i in range(target_count - current_agents):
                agent_id = self.create_agent(agent_type, 'system_scaling')
                agents_created.append(agent_id)
            
            return {
                'scaling_successful': True,
                'action': 'scale_up',
                'agents_created': len(agents_created),
                'agent_ids': agents_created,
                'new_pool_size': len(self.agent_pools[pool_name]),
                'scaling_timestamp': datetime.now().isoformat()
            }
        elif target_count < current_agents:
            # Завершаем лишних агентов
            agents_to_terminate = self.agent_pools[pool_name][target_count:]
            agents_terminated = []
            
            for agent_id in agents_to_terminate:
                if self.terminate_agent(agent_id, 'scaling_down'):
                    agents_terminated.append(agent_id)
            
            # Обновляем пул
            self.agent_pools[pool_name] = self.agent_pools[pool_name][:target_count]
            
            return {
                'scaling_successful': True,
                'action': 'scale_down',
                'agents_terminated': len(agents_terminated),
                'agent_ids': agents_terminated,
                'new_pool_size': len(self.agent_pools[pool_name]),
                'scaling_timestamp': datetime.now().isoformat()
            }
        else:
            # Ничего не меняем
            return {
                'scaling_successful': True,
                'action': 'no_change',
                'current_pool_size': current_agents,
                'scaling_timestamp': datetime.now().isoformat()
            }
    
    def get_performance_metrics(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Получить метрики производительности агентов
        """
        if agent_id:
            # Получаем метрики для конкретного агента
            if agent_id not in self.agents:
                return {
                    'metrics_available': False,
                    'error': 'Agent not found'
                }
            
            agent = self.agents[agent_id]
            return {
                'agent_id': agent_id,
                'agent_type': agent['agent_type'],
                'task_completion_rate': self._calculate_task_completion_rate(agent),
                'error_rate': self._calculate_error_rate(agent),
                'uptime_percentage': self._calculate_uptime_percentage(agent),
                'average_task_duration': self._calculate_average_task_duration(agent),
                'metrics_timestamp': datetime.now().isoformat()
            }
        else:
            # Получаем агрегированные метрики для всех агентов
            all_metrics = []
            
            for agent_id, agent in self.agents.items():
                agent_metrics = {
                    'agent_id': agent_id,
                    'agent_type': agent['agent_type'],
                    'task_completion_rate': self._calculate_task_completion_rate(agent),
                    'error_rate': self._calculate_error_rate(agent),
                    'uptime_percentage': self._calculate_uptime_percentage(agent),
                    'average_task_duration': self._calculate_average_task_duration(agent)
                }
                all_metrics.append(agent_metrics)
            
            # Рассчитываем агрегированные метрики
            if all_metrics:
                avg_completion_rate = sum(m['task_completion_rate'] for m in all_metrics) / len(all_metrics)
                avg_error_rate = sum(m['error_rate'] for m in all_metrics) / len(all_metrics)
                avg_uptime = sum(m['uptime_percentage'] for m in all_metrics) / len(all_metrics)
                avg_task_duration = sum(m['average_task_duration'] for m in all_metrics) / len(all_metrics)
            else:
                avg_completion_rate = 0.0
                avg_error_rate = 0.0
                avg_uptime = 0.0
                avg_task_duration = 0.0
            
            return {
                'metrics_available': True,
                'total_agents_monitored': len(all_metrics),
                'average_completion_rate': avg_completion_rate,
                'average_error_rate': avg_error_rate,
                'average_uptime_percentage': avg_uptime,
                'average_task_duration': avg_task_duration,
                'agent_metrics': all_metrics,
                'metrics_timestamp': datetime.now().isoformat()
            }
    
    def _calculate_task_completion_rate(self, agent: Dict[str, Any]) -> float:
        """
        Рассчитать процент завершения задач агентом
        """
        task_history = agent.get('task_history', [])
        if not task_history:
            return 1.0  # По умолчанию считаем 100% завершение для новых агентов
        
        completed_tasks = sum(1 for task in task_history if task['status'] == 'completed')
        return completed_tasks / len(task_history)
    
    def _calculate_error_rate(self, agent: Dict[str, Any]) -> float:
        """
        Рассчитать процент ошибок агента
        """
        error_count = agent.get('error_count', 0)
        task_count = len(agent.get('task_history', []))
        
        if task_count == 0:
            return 0.0  # Нет задач - нет ошибок
        
        return error_count / task_count
    
    def _calculate_uptime_percentage(self, agent: Dict[str, Any]) -> float:
        """
        Рассчитать процент времени работы агента
        """
        created_at = datetime.fromisoformat(agent['created_at'])
        now = datetime.now()
        total_time = (now - created_at).total_seconds()
        
        if total_time == 0:
            return 1.0  # По умолчанию считаем 100% uptime
        
        # Рассчитываем время в состоянии "terminated" или "error"
        inactive_time = 0
        last_state_change = datetime.fromisoformat(agent['last_state_change'])
        
        if agent['state'] in ['terminated', 'error']:
            inactive_time = (now - last_state_change).total_seconds()
        
        uptime_percentage = 1.0 - (inactive_time / total_time)
        return max(0.0, min(1.0, uptime_percentage))  # Ограничиваем диапазон от 0.0 до 1.0
    
    def _calculate_average_task_duration(self, agent: Dict[str, Any]) -> float:
        """
        Рассчитать среднюю продолжительность выполнения задач
        """
        task_history = agent.get('task_history', [])
        completed_tasks = [task for task in task_history if task['status'] == 'completed']
        
        if not completed_tasks:
            return 0.0  # Нет завершенных задач
        
        total_duration = 0.0
        for task in completed_tasks:
            assigned_at = datetime.fromisoformat(task['assigned_at'])
            completed_at = datetime.fromisoformat(task['completed_at'])
            duration = (completed_at - assigned_at).total_seconds()
            total_duration += duration
        
        return total_duration / len(completed_tasks)

# Глобальный менеджер жизненного цикла агентов
agent_lifecycle_manager = AgentLifecycleManager()