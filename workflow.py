from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from agents.master import MasterOrchestrator
from agents.sap_agents import create_agent
from memory.zep_client import ZepMemoryManager
from agents.specialization_validator import validator
from utils.competency_matrix import competency_matrix
from utils.task_auction import task_auction
from utils.specialization_control import specialization_control
from utils.load_balancer import load_balancer
from utils.self_assessment import self_assessment_system
from utils.execution_verification import execution_verifier
from utils.quality_control import quality_control
from utils.intelligent_control import intelligent_control
from utils.checkpoint_verification import checkpoint_verifier
from utils.quality_metrics import quality_metrics
from utils.microservice_architecture import service_orchestrator
from utils.agent_contracts import contract_manager
from utils.self_learning import self_learning_system
from utils.multilevel_architecture import multi_level_architecture
import json

class AgentState(TypedDict):
    """
    State structure for the agent workflow
    """
    session_id: str
    user_request: str
    master_decision: str
    delegated_tasks: List[Dict[str, str]]
    agent_results: List[Dict[str, Any]]
    final_decision: str
    review_notes: str
    current_task_index: int  # Track which task we're currently processing
    all_tasks_completed: bool  # Flag to check if all tasks are done
    iteration_count: int  # Track number of iterations to prevent infinite loops
    max_iterations: int  # Maximum allowed iterations

def master_node(state: AgentState) -> Dict[str, Any]:
    """
    Master orchestrator node: analyzes request and delegates tasks
    Now uses multilevel architecture for enhanced task processing with proper agent specialization
    """
    session_id = state['session_id']
    user_request = state['user_request']
    
    # Use multilevel architecture for complex task processing
    import asyncio
    # Run the async multilevel execution in a synchronous context
    try:
        multilevel_result = asyncio.run(multi_level_architecture.execute_task_multilevel({
            'task_description': user_request,
            'session_id': session_id
        }))
    except Exception as e:
        # If multilevel execution fails, fall back to traditional approach
        print(f"Multilevel execution failed, falling back to traditional approach: {str(e)}")
        master = MasterOrchestrator(session_id)
        result = master.execute(user_request)
        delegated_tasks = result['delegated_tasks']
        master_decision = result['master_decision']
        
        delegated_tasks_count = len(delegated_tasks)
        
        return {
            'delegated_tasks': delegated_tasks,
            'master_decision': master_decision,
            'current_task_index': 0,
            'all_tasks_completed': delegated_tasks_count == 0,
            'iteration_count': 0,
            'max_iterations': delegated_tasks_count * 5 if delegated_tasks_count > 0 else 30,  # Increased safeguard against infinite loops
            'completion_percentage': 0.0
        }
    
    # Extract tasks from multilevel analysis
    delegated_tasks = multilevel_result.get('execution_context', {}).get('levels_results', {}).get('analysis', {}).get('plan', {}).get('tasks', [])
    
    # Convert to format expected by workflow with proper agent assignment
    converted_tasks = []
    for task in delegated_tasks:
        agent_type = task.get('agent', 'backend_dev')
        task_description = task.get('task', task.get('description', task.get('name', 'Unnamed task')))
        
        # Validate agent type to ensure it's from our available agents
        try:
            master = MasterOrchestrator(session_id)
            available_agents = list(master.available_agents.keys())
            
            # If agent type not in available agents, find the most suitable one
            if agent_type not in available_agents:
                from utils.specialization_control import specialization_control
                suitable_agents = specialization_control.find_suitable_agents(
                    task_description, 
                    available_agents
                )
                
                if suitable_agents:
                    # Take the first suitable agent
                    agent_type = suitable_agents[0][0]
                else:
                    # Default to backend_dev if no suitable agent found
                    agent_type = 'backend_dev'
        except Exception as e:
            # If validation fails, default to backend_dev
            agent_type = 'backend_dev'
        
        converted_tasks.append({
            'agent': agent_type,
            'task': task_description
        })
    
    # If no tasks from multilevel analysis, fall back to traditional approach
    if not converted_tasks:
        master = MasterOrchestrator(session_id)
        result = master.execute(user_request)
        converted_tasks = result['delegated_tasks']
        master_decision = result['master_decision']
    else:
        master_decision = "Tasks delegated through multilevel architecture"
    
    delegated_tasks_count = len(converted_tasks)
    
    return {
        'delegated_tasks': converted_tasks,
        'master_decision': master_decision,
        'current_task_index': 0,
        'all_tasks_completed': delegated_tasks_count == 0,
        'iteration_count': 0,
        'max_iterations': delegated_tasks_count * 5 if delegated_tasks_count > 0 else 30,  # Increased safeguard against infinite loops
        'completion_percentage': 0.0
    }

def validate_specialization_node(state: AgentState) -> Dict[str, Any]:
    """
    Валидационный узел, проверяющий соответствие задач специализациям агентов
    """
    delegated_tasks = state.get('delegated_tasks', [])
    validated_tasks = []
    
    # Получаем доступных агентов из мастер-агента
    master = MasterOrchestrator(state['session_id'])
    available_agents = list(master.available_agents.keys())
    
    # Список уже назначенных агентов для предотвращения дублирования
    assigned_agents = []
    
    # Проверяем и, при необходимости, корректируем задачи
    for task_info in delegated_tasks:
        agent_type = task_info.get('agent', 'backend_dev')
        task_description = task_info.get('task', '')
        
        # Проверяем, соответствует ли агент задаче
        if not validator.validate_task_assignment(agent_type, task_description):
            # Находим наиболее подходящего агента, учитывая уже назначенных
            correct_agent = validator.find_appropriate_agent(task_description, available_agents, assigned_agents)
            if correct_agent:
                # Обновляем агента в задаче
                validated_tasks.append({
                    'agent': correct_agent,
                    'task': task_description
                })
                assigned_agents.append(correct_agent)
                print(f"REASSIGNED: Task '{task_description[:50]}...' reassigned from {agent_type} to {correct_agent}")
            else:
                # Если не найден подходящий агент, оставляем как есть
                validated_tasks.append(task_info)
                assigned_agents.append(agent_type)
        else:
            validated_tasks.append(task_info)
            assigned_agents.append(agent_type)
    
    return {
        'delegated_tasks': validated_tasks
    }

def check_tasks_condition(state: AgentState) -> str:
    """
    Conditional node to check if all tasks have been processed
    Includes max iterations to prevent infinite loops and task completion tracking
    """
    delegated_tasks = state.get('delegated_tasks', [])
    current_index = state.get('current_task_index', 0)
    max_iterations = state.get('max_iterations', len(delegated_tasks) * 3 if delegated_tasks else 30)  # Prevent infinite loops
    iteration_count = state.get('iteration_count', 0)
    agent_results = state.get('agent_results', [])
    
    # Check if all tasks have been processed or if we've exceeded max iterations
    if current_index >= len(delegated_tasks) or iteration_count >= max_iterations:
        if iteration_count >= max_iterations:
            print(f"Max iterations ({max_iterations}) reached, stopping to prevent infinite loop")
        return "done"
    else:
        # Still have tasks to process
        return "continue"

def update_iteration_count(state: AgentState) -> Dict[str, Any]:
    """
    Update the iteration counter and track task completion progress
    """
    current_iteration = state.get('iteration_count', 0)
    delegated_tasks = state.get('delegated_tasks', [])
    agent_results = state.get('agent_results', [])
    
    # Calculate completion percentage
    tasks_sent = len(delegated_tasks)
    results_received = len(agent_results)
    completion_percentage = (results_received / tasks_sent * 100) if tasks_sent > 0 else 0
    
    # Log progress every 5 iterations
    if (current_iteration + 1) % 5 == 0:
        print(f"Iteration {current_iteration + 1}: {results_received}/{tasks_sent} tasks completed ({completion_percentage:.1f}%)")
    
    return {
        'iteration_count': current_iteration + 1,
        'completion_percentage': completion_percentage
    }

def sap_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    SAP agent node: executes individual tasks delegated by master
    Processes one task at a time for proper agent specialization
    Now includes comprehensive quality control, verification, and loop prevention
    """
    session_id = state['session_id']
    delegated_tasks = state.get('delegated_tasks', [])
    current_index = state.get('current_task_index', 0)
    agent_results = state.get('agent_results', [])
    iteration_count = state.get('iteration_count', 0)
    max_iterations = state.get('max_iterations', len(delegated_tasks) * 3 if delegated_tasks else 30)
    
    # Check for infinite loop prevention
    if iteration_count >= max_iterations:
        print(f"Max iterations ({max_iterations}) reached, stopping SAP agent processing")
        return {
            'agent_results': agent_results,
            'current_task_index': current_index
        }
    
    # Check if all tasks have been processed
    if current_index >= len(delegated_tasks):
        return {
            'agent_results': agent_results,
            'current_task_index': current_index
        }
    
    results = []
    
    # Process the current task only
    if current_index < len(delegated_tasks):
        task_info = delegated_tasks[current_index]
        agent_type = task_info.get('agent', 'backend_dev')
        task = task_info.get('task', '')
        
        if task:
            try:
                agent = create_agent(agent_type, session_id)
                result = agent.execute_task(task)
                
                # Validate result through quality control system
                quality_validation = quality_control.validate_result_quality(
                    result, 
                    agent_type, 
                    task, 
                    session_id
                )
                
                if not quality_validation['valid']:
                    # If quality validation fails, request rework
                    result['requires_rework'] = True
                    result['quality_issues'] = quality_validation.get('issues', [])
                
                # Log the result
                results.append(result)
                
                print(f"Completed task for agent {agent_type}: {task[:100]}...")
            except ValueError as e:
                # Handle specialization mismatch - find appropriate agent using load balancer
                if "not appropriate for" in str(e) or "NEEDS_REDIRECT_TO_SPECIALIST" in str(e):
                    from agents.sap_agents import create_agent as create_agent_func
                    
                    task_description = task
                    # Get available agents from master
                    master = MasterOrchestrator(session_id)
                    available_agents = list(master.available_agents.keys())
                    
                    # Find the most appropriate agent for this task using load balancer
                    correct_agent_type = load_balancer.assign_task_to_agent(
                        task_description, 
                        available_agents, 
                        session_id
                    )
                    
                    # Check if this is a new agent (prevent infinite loops)
                    if correct_agent_type and correct_agent_type != agent_type:
                        try:
                            correct_agent = create_agent_func(correct_agent_type, session_id)
                            result = correct_agent.execute_task(task_description)
                            
                            # Validate result through quality control system
                            quality_validation = quality_control.validate_result_quality(
                                result, 
                                correct_agent_type, 
                                task_description, 
                                session_id
                            )
                            
                            if not quality_validation['valid']:
                                result['requires_rework'] = True
                                result['quality_issues'] = quality_validation.get('issues', [])
                            
                            # Log with corrected agent
                            results.append(result)
                            
                            print(f"Reassigned and completed task for agent {correct_agent_type}: {task_description[:100]}...")
                        except Exception as correct_e:
                            print(f"Error executing reassigned task for agent {correct_agent_type}: {str(correct_e)}")
                            results.append({
                                'agent_name': correct_agent_type,
                                'task': task_description,
                                'result': f"Error after reassignment: {str(correct_e)}",
                                'session_id': session_id,
                                'requires_rework': True,
                                'error_details': str(correct_e)
                            })
                    else:
                        # If no appropriate agent found or same agent, return error
                        results.append({
                            'agent_name': agent_type,
                            'task': task,
                            'result': f"Error: No appropriate agent found for task. Original error: {str(e)}",
                            'session_id': session_id,
                            'requires_rework': True,
                            'error_details': str(e)
                        })
                else:
                    # Handle other value errors
                    results.append({
                        'agent_name': agent_type,
                        'task': task,
                        'result': f"ValueError: {str(e)}",
                        'session_id': session_id,
                        'requires_rework': True,
                        'error_details': str(e)
                    })
            except Exception as e:
                print(f"Error executing task for agent {agent_type}: {str(e)}")
                
                # Add error result to maintain consistency
                results.append({
                    'agent_name': agent_type,
                    'task': task,
                    'result': f"Error: {str(e)}",
                    'session_id': session_id,
                    'requires_rework': True,
                    'error_details': str(e)
                })
    
    # Update current task index
    new_index = current_index + 1 if results else current_index
    
    return {
        'agent_results': agent_results + results,
        'current_task_index': new_index
        # iteration count is updated by separate node
    }

def review_node(state: AgentState) -> Dict[str, Any]:
    """
    Review node: master reviews SAP agent results and makes final decision
    """
    session_id = state['session_id']
    agent_results = state.get('agent_results', [])
    
    master = MasterOrchestrator(session_id)
    review_result = master.review_results(agent_results)
    
    return {
        'final_decision': review_result['decision'],
        'review_notes': review_result['review_notes']
    }

def check_master_decision(state: AgentState) -> str:
    """
    Conditional node to check master's decision
    """
    delegated_tasks = state.get('delegated_tasks', [])
    
    if len(delegated_tasks) > 0:
        return "delegate"
    else:
        return "approve"

def check_review_decision(state: AgentState) -> str:
    """
    Conditional node to check review decision
    """
    final_decision = state.get('final_decision', '').upper()
    
    if 'APPROVE' in final_decision:
        return "approve"
    else:
        return "rework"

def quality_control_node(state: AgentState) -> Dict[str, Any]:
    """
    Quality control node: verifies the quality of all agent results
    """
    agent_results = state.get('agent_results', [])
    session_id = state['session_id']
    
    # Apply quality control to all results
    quality_checked_results = []
    for result in agent_results:
        agent_type = result.get('agent_name', 'unknown')
        task_description = result.get('task', '')
        
        # Validate result quality
        quality_validation = quality_control.validate_result_quality(
            result, 
            agent_type, 
            task_description, 
            session_id
        )
        
        # Add quality information to result
        result['quality_validation'] = quality_validation
        quality_checked_results.append(result)
    
    return {
        'agent_results': quality_checked_results
    }

def checkpoint_verification_node(state: AgentState) -> Dict[str, Any]:
    """
    Checkpoint verification node: verifies that all execution checkpoints are valid
    """
    agent_results = state.get('agent_results', [])
    session_id = state['session_id']
    
    # Verify all checkpoints
    checkpoint_verifications = []
    for result in agent_results:
        checkpoint_id = result.get('checkpoint_id')
        if checkpoint_id:
            verification = checkpoint_verifier.verify_checkpoint(
                checkpoint_id,
                {
                    'result': result,
                    'session_id': session_id
                }
            )
            checkpoint_verifications.append(verification)
    
    return {
        'checkpoint_verifications': checkpoint_verifications
    }

def self_assessment_node(state: AgentState) -> Dict[str, Any]:
    """
    Self-assessment node: allows agents to assess their own performance
    """
    agent_results = state.get('agent_results', [])
    session_id = state['session_id']
    
    # Request self-assessment from all agents
    self_assessments = []
    for result in agent_results:
        agent_type = result.get('agent_name', 'unknown')
        task_description = result.get('task', '')
        
        # Request self-assessment
        self_assessment = self_assessment_system.request_self_assessment(
            agent_type,
            task_description,
            result
        )
        
        # Add self-assessment to result
        result['self_assessment'] = self_assessment
        self_assessments.append(self_assessment)
    
    return {
        'agent_results': agent_results,
        'self_assessments': self_assessments
    }

def create_agent_workflow():
    """
    Create the main workflow graph with conditional logic for multiple agents
    Implements multilevel architecture with proper task delegation and completion tracking
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("master", master_node)
    workflow.add_node("validation", validate_specialization_node)
    workflow.add_node("sap_agent", sap_agent_node)
    workflow.add_node("review", review_node)
    workflow.add_node("quality_control", quality_control_node)
    workflow.add_node("checkpoint_verification", checkpoint_verification_node)
    workflow.add_node("self_assessment", self_assessment_node)
    workflow.add_node("update_iteration", update_iteration_count)
    
    # Set entry point
    workflow.set_entry_point("master")
    
    # Define edges
    workflow.add_edge("master", "validation")
    workflow.add_edge("validation", "sap_agent")
    workflow.add_edge("sap_agent", "update_iteration")
    
    # Add conditional edge from update_iteration
    workflow.add_conditional_edges(
        "update_iteration",
        check_tasks_condition,
        {
            "continue": "sap_agent",  # Loop back to process next task
            "done": "quality_control"  # Move to quality control when all tasks are done
        }
    )
    
    # Quality control leads to checkpoint verification
    workflow.add_edge("quality_control", "checkpoint_verification")
    
    # Checkpoint verification leads to self-assessment
    workflow.add_edge("checkpoint_verification", "self_assessment")
    
    # Self-assessment leads to review
    workflow.add_edge("self_assessment", "review")
    
    # Add conditional edge from review
    workflow.add_conditional_edges(
        "review",
        check_review_decision,
        {
            "approve": END,
            "rework": "master"  # Send back to master for re-delegation
        }
    )
    
    # Compile the graph with increased recursion limit to prevent early termination
    app = workflow.compile(config={'recursion_limit': 50})
    return app

def run_agent_workflow(session_id: str, user_request: str):
    """
    Run the complete agent workflow with proper initialization and state management
    """
    app = create_agent_workflow()
    
    initial_state = {
        'session_id': session_id,
        'user_request': user_request,
        'master_decision': '',
        'delegated_tasks': [],
        'agent_results': [],
        'final_decision': '',
        'review_notes': '',
        'current_task_index': 0,
        'all_tasks_completed': False,
        'iteration_count': 0,
        'max_iterations': 30,  # Increased limit to prevent early termination
        'completion_percentage': 0.0
    }
    
    final_state = app.invoke(initial_state)
    return final_state

# Example usage function
def run_example():
    """
    Example function to demonstrate the workflow
    """
    session_id = "test_session_123"
    user_request = "Create a health endpoint for the API"
    
    print(f"Starting workflow for session: {session_id}")
    print(f"User request: {user_request}")
    print("-" * 50)
    
    result = run_agent_workflow(session_id, user_request)
    
    print("Final result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    run_example()