from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List
from models import OpenRouterProvider
from memory.zep_client import ZepMemoryManager
from utils.competency_matrix import competency_matrix
from utils.task_auction import task_auction
from utils.specialization_control import specialization_control
from utils.routing_system import routing_system
import json

class MasterOrchestrator:
    """
    Master orchestrator agent that coordinates other specialized agents.
    Uses google/gemini-flash-1.5-8b model and has no tools.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.provider = OpenRouterProvider()
        self.memory_manager = ZepMemoryManager()
        self.agent_type = 'master'
        
        # Store the list of available agents and their purposes
        self.available_agents = {
            'researcher': 'Research and gather information',
            'backend_dev': 'Backend development',
            'frontend_dev': 'Frontend development',
            'doc_writer': 'Documentation',
            'tester': 'Testing and quality assurance',
            'devops': 'DevOps and infrastructure'
        }
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the Master orchestrator.
        """
        return f"""
Ты — Мастер-агент (Project Orchestrator). Твоя единственная задача — анализировать запрос пользователя, 
декомпозировать его на подзадачи и делегировать их подходящим специализированным сап-агентам. 

ДОСТУПНЫЕ САП-АГЕНТЫ И ИХ СПЕЦИАЛИЗАЦИИ:
- researcher: Исследования, анализ существующих решений, сбор информации
- backend_dev: Разработка бэкенд-компонентов, программирование
- frontend_dev: Разработка фронтенд-компонентов
- doc_writer: Создание документации, технических описаний
- tester: Тестирование, написание тестов, проверка качества
- devops: Инфраструктура, DevOps-инструменты, автоматизация

Ты НЕ ИМЕЕШЬ ПРАВА:
- Писать код
- Редактировать файлы
- Искать в интернете
- Генерировать документацию
- Выполнять любые действия вне планирования и делегирования

Ты ДОЛЖЕН:
1. Понять суть задачи.
2. Проанализировать, какие этапы/части есть в задаче.
3. Для КАЖДОГО этапа определить наиболее подходящего сап-агента по специализации.
4. Сформулировать ЧЁТКУЮ, АТОМИЧНУЮ подзадачу для КАЖДОГО агента.
5. ВЕРНУТЬ структурированный список: {{"agent": "agent_type", "task": "task_description"}} для КАЖДОЙ подзадачи.
6. После получения результатов от САП-агентов, проанализировать их и принять решение: УТВЕРДИТЬ или ЗАПРОСИТЬ ДОРАБОТКУ.

ВАЖНО: НЕ отправляй одну большую задачу одному агенту. РАЗДЕЛЯЙ на специализированные подзадачи.

Ты работаешь в рамках сессии {self.session_id}. Вся твоя память хранится в изолированной записной книжке.
"""
    
    def execute(self, user_request: str) -> Dict[str, Any]:
        """
        Execute the master orchestrator logic: analyze request and delegate to appropriate agents.
        """
        # Add the user request to memory
        self.memory_manager.add_message(self.session_id, 'master', f"USER REQUEST: {user_request}", 'task')
        
        # Prepare messages for the LLM
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Analyze this request and delegate tasks: {user_request}")
        
        # Call the model using OpenRouter provider
        response = self.provider.call_model(
            agent_type=self.agent_type,
            messages=[system_message, human_message]
        )
        
        # Add response to memory
        self.memory_manager.add_message(self.session_id, 'master', f"MODEL RESPONSE: {response.content}", 'planning')
        
        # Process the response to extract required agents and tasks
        tasks = self._parse_tasks(response.content)
        
        # Используем систему маршрутизации для улучшенного распределения задач
        routed_tasks = self._route_tasks_improved(tasks, user_request)
        
        return {
            'user_request': user_request,
            'delegated_tasks': routed_tasks,
            'session_id': self.session_id,
            'master_decision': response.content
        }
    
    def _route_tasks_improved(self, tasks: List[Dict[str, str]], user_request: str) -> List[Dict[str, str]]:
        """
        Улучшенная маршрутизация задач с использованием систем балансировки и контроля специализаций
        """
        from utils.load_balancer import load_balancer
        from utils.routing_system import routing_system
        from utils.specialization_control import specialization_control
        
        routed_tasks = []
        already_assigned_agents = []
        
        # Если нет задач, создаем базовую задачу
        if not tasks:
            # Сначала анализируем запрос пользователя для создания задач
            analysis_tasks = self._analyze_user_request_for_tasks(user_request)
            tasks = analysis_tasks
        
        for task in tasks:
            agent_type = task.get('agent', 'backend_dev')
            task_description = task.get('task', '')
            
            # Используем систему маршрутизации для определения лучшего агента
            best_agent = routing_system.route_task(task_description, list(self.available_agents.keys()), self.session_id)
            
            # Проверяем соответствие специализации
            validation = specialization_control.validate_task_assignment(best_agent, task_description)
            
            if not validation['valid']:
                # Если задача не соответствует специализации, находим более подходящего агента
                suitable_agents = specialization_control.find_suitable_agents(
                    task_description, 
                    list(self.available_agents.keys())
                )
                
                if suitable_agents:
                    # Берем первого подходящего агента
                    best_agent = suitable_agents[0][0]
                else:
                    # Если не найдено подходящих агентов, используем балансировку нагрузки
                    best_agent = load_balancer.assign_task_to_agent(
                        task_description, 
                        list(self.available_agents.keys()), 
                        self.session_id
                    )
            
            # Добавляем задачу с правильным агентом
            routed_tasks.append({
                'agent': best_agent,
                'task': task_description
            })
            
            already_assigned_agents.append(best_agent)
        
        return routed_tasks
    
    def _analyze_user_request_for_tasks(self, user_request: str) -> List[Dict[str, str]]:
        """
        Анализировать запрос пользователя для создания списка задач
        """
        # Используем LLM для декомпозиции запроса на задачи
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=f"Decompose this user request into specific tasks for different specialized agents: {user_request}")
        
        # Вызываем модель для декомпозиции
        response = self.provider.call_model(
            agent_type=self.agent_type,
            messages=[system_message, human_message]
        )
        
        # Парсим ответ на задачи
        tasks = self._parse_tasks(response.content)
        return tasks
    
    def _parse_tasks(self, response_content: str) -> List[Dict[str, str]]:
        """
        Parse the LLM response to extract tasks for delegation.
        Expects structured format like: {"agent": "agent_type", "task": "task_description"}
        """
        import json
        import re
        
        tasks = []
        
        # Try to find JSON-like structures in the response
        # Look for patterns like {"agent": "...", "task": "..."} or similar
        json_pattern = r'\{[^}]*"agent"[^}]*:[^}]*"task"[^}]*\}'
        matches = re.findall(json_pattern, response_content, re.DOTALL)
        
        for match in matches:
            try:
                # Clean up the match to make it valid JSON
                cleaned_match = match.strip().replace('\\', '')
                task_dict = json.loads(cleaned_match)
                
                if 'agent' in task_dict and 'task' in task_dict:
                    tasks.append({
                        'agent': task_dict['agent'],
                        'task': task_dict['task']
                    })
            except:
                # If JSON parsing fails, try simple pattern matching
                agent_match = re.search(r'"?agent"?\s*:\s*"?([a-zA-Z_]+)"?', match)
                task_match = re.search(r'"?task"?\s*:\s*"?([^"]+)"?', match)
                
                if agent_match and task_match:
                    tasks.append({
                        'agent': agent_match.group(1),
                        'task': task_match.group(1)
                    })
        
        # If no JSON structures found, try looking for structured text format
        if not tasks:
            # Look for patterns like "Agent: type, Task: description"
            lines = response_content.split('\n')
            for line in lines:
                line = line.strip()
                if 'Agent:' in line and 'Task:' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        agent_part = parts[0].replace('Agent:', '').strip()
                        task_part = parts[1].replace('Task:', '').strip()
                        
                        tasks.append({
                            'agent': agent_part,
                            'task': task_part
                        })
        
        # If still no tasks found, check if response contains clear task breakdown
        if not tasks:
            # Look for numbered lists indicating different tasks
            numbered_task_pattern = r'\d+\.\s*\*\*?([^*]+?)\*\*?\s*[-:]?\s*(.*?)(?=\d+\.|$)'
            matches = re.findall(numbered_task_pattern, response_content, re.DOTALL)
            
            for match in matches:
                description = match[1].strip()
                
                # Try to infer agent type based on task content
                agent_type = self._infer_agent_type(description)
                
                tasks.append({
                    'agent': agent_type,
                    'task': f"{match[0].strip()}: {description}"
                })
        
        # Validate agent types to ensure they're from our available agents
        valid_agents = set(self.available_agents.keys())  # Use available agents instead of hardcoded list
        validated_tasks = []
        
        for task in tasks:
            agent_type = task.get('agent', '').strip().lower()
            if agent_type in valid_agents:
                validated_tasks.append({
                    'agent': agent_type,
                    'task': task.get('task', '')
                })
        
        return validated_tasks

    def _infer_agent_type(self, task_description: str, already_assigned: List[str] = None) -> str:
        """
        Infer the appropriate agent type based on task description
        Uses the specialization validator for dynamic classification
        """
        from agents.specialization_validator import validator
        available_agents = list(self.available_agents.keys())
        return validator.find_appropriate_agent(task_description, available_agents, already_assigned) or 'backend_dev'

    def review_results(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Review the results from SAP agents and make approval decision.
        Includes validation that results came from appropriate agents.
        Now uses contract-based validation.
        """
        # Add agent results to memory for review
        for result in agent_results:
            agent_name = result.get('agent_name', 'unknown')
            task_result = result.get('result', 'no result')
            self.memory_manager.add_message(self.session_id, 'master', f"REVIEWING {agent_name}: {task_result}", 'result')
        
        # Create a review prompt with the results and contract-based validation
        review_content = f"""
        Here are the results from the agents for the original request:
        {json.dumps(agent_results, indent=2)}
        
        Contract-based validation results:
        - All agents executed tasks within their contractual obligations: {self._validate_contract_compliance(agent_results)}
        - Quality metrics for all results: {self._calculate_aggregate_quality_metrics(agent_results)}
        - Self-assessment results: {self._collect_self_assessments(agent_results)}
        
        Please review these results and decide if they are sufficient to approve or if more work is needed.
        Respond with either APPROVE or REQUEST_CHANGES, followed by your reasoning.
        """
        
        system_message = SystemMessage(content=self.get_system_prompt())
        human_message = HumanMessage(content=review_content)
        
        # Call the model for review
        response = self.provider.call_model(
            agent_type=self.agent_type,
            messages=[system_message, human_message]
        )
        
        # Add review to memory
        self.memory_manager.add_message(self.session_id, 'master', f"REVIEW RESULT: {response.content}", 'review')
        
        # Determine approval status
        decision = 'APPROVE' if 'APPROVE' in response.content.upper() else 'REQUEST_CHANGES'
        
        return {
            'decision': decision,
            'review_notes': response.content,
            'agent_results': agent_results
        }
    
    def _validate_contract_compliance(self, agent_results: List[Dict[str, Any]]) -> bool:
        """
        Validate that all agents complied with their contractual obligations
        """
        from utils.agent_contracts import contract_manager
        
        for result in agent_results:
            agent_name = result.get('agent_name', 'unknown')
            task_description = result.get('task', '')
            
            # Validate contract compliance for each result
            contract_validation = contract_manager.validate_contract_execution(
                'task_assignment',
                {
                    'agent_type': agent_name,
                    'task_description': task_description,
                    'session_id': self.session_id
                }
            )
            
            if not contract_validation['valid']:
                return False
        
        return True
    
    def _calculate_aggregate_quality_metrics(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate quality metrics for all results
        """
        from utils.quality_metrics import quality_metrics
        
        aggregate_metrics = {
            'total_results': len(agent_results),
            'average_quality_score': 0.0,
            'quality_issues_count': 0,
            'high_quality_results': 0,
            'needs_improvement_results': 0
        }
        
        total_quality_score = 0.0
        issues_count = 0
        high_quality_count = 0
        needs_improvement_count = 0
        
        for result in agent_results:
            quality_score = result.get('quality_validation', {}).get('quality_score', 0.5)
            requires_rework = result.get('requires_rework', False)
            
            total_quality_score += quality_score
            
            if quality_score >= 0.8:
                high_quality_count += 1
            elif quality_score < 0.5:
                needs_improvement_count += 1
            
            if requires_rework:
                issues_count += 1
        
        if agent_results:
            aggregate_metrics['average_quality_score'] = total_quality_score / len(agent_results)
            aggregate_metrics['quality_issues_count'] = issues_count
            aggregate_metrics['high_quality_results'] = high_quality_count
            aggregate_metrics['needs_improvement_results'] = needs_improvement_count
        
        return aggregate_metrics
    
    def _collect_self_assessments(self, agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Collect self-assessment results from all agents
        """
        self_assessments = []
        
        for result in agent_results:
            self_assessment = result.get('self_assessment', {})
            if self_assessment:
                self_assessments.append({
                    'agent_name': result.get('agent_name', 'unknown'),
                    'self_assessment': self_assessment
                })
        
        return self_assessments