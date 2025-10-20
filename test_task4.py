from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task_4():
    """
    Testing task 4: Create a CLI tool for Python project audit and refactoring
    """
    load_dotenv()
    
    session_id = "test_task_4"
    user_request = "Создай CLI-инструмент для автоматического аудита и рефакторинга Python-проектов. Пользователь должен запустить утилиту как: pyrefactor --path ./my_project --fix-security --format-code --generate-report"
    
    print(f"Starting workflow for session: {session_id}")
    print(f"User request: {user_request}")
    print("-" * 50)
    
    result = run_agent_workflow(session_id, user_request)
    
    print("Final result:")
    print(f"Final decision: {result.get('final_decision', 'No decision')}")
    print(f"Review notes: {result.get('review_notes', 'No review notes')[:300]}...")
    print(f"Number of agent results: {len(result.get('agent_results', []))}")
    
    for i, agent_result in enumerate(result.get('agent_results', [])):
        print(f"  Agent {i+1}: {agent_result.get('agent_name', 'Unknown')}")
        print(f"    Task: {agent_result.get('task', 'No task')[:100]}...")
        print(f"    Result preview: {agent_result.get('result', 'No result')[:200]}...")
    
    return result

if __name__ == "__main__":
    test_task_4()