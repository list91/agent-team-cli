from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task10_simple():
    """
    Simple test for Task 10: Microservice stack generator
    """
    load_dotenv()
    
    session_id = "task10_simple"
    user_request = """Разработай CLI-инструмент для генерации полного стека микросервиса по описанию в YAML.
    Пользователь даёт service-spec.yaml:
    name: user-service
    language: python
    db: postgres
    auth: jwt
    endpoints:
      - path: /users
        method: GET
    → инструмент генерирует: FastAPI-сервис, Dockerfile, docker-compose.yml с БД, тесты, OpenAPI-спецификацию.

    Делегирование:
    - Researcher: собрать шаблоны для типовых микросервисов.
    - BackendDev: реализовать генератор кода на основе Jinja2-шаблонов.
    - FrontendDev: (опционально) сгенерировать Swagger UI как статику.
    - Tester: автогенерация unit-тестов для каждого эндпоинта.
    - DevOpsAgent: настроить health-checks, логирование, мониторинг (через Prometheus-аннотации).
    - DocWriter: README с инструкцией по запуску и кастомизации.

    Мастер проверяет: сервис поднимается через docker-compose up, все эндпоинты работают, структура соответствует best practices."""
    
    print(f"=== TESTING TASK 10: Microservice Generator ===")
    print(f"Session: {session_id}")
    print(f"Request length: {len(user_request)} chars")
    print("-" * 60)
    
    try:
        result = run_agent_workflow(session_id, user_request)
        
        print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
        print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
        
        print("\nAGENT RESULTS:")
        for i, agent_result in enumerate(result.get('agent_results', [])):
            agent_name = agent_result.get('agent_name', 'Unknown')
            task = agent_result.get('task', 'No task')
            
            print(f"  {i+1}. Agent: {agent_name}")
            print(f"     Task preview: {task[:100]}...")
            
        # Check for expected agents
        agent_names = [ar.get('agent_name', '') for ar in result.get('agent_results', [])]
        print(f"\nAGENTS USED: {set(agent_names)}")
        
        # Expected agents based on the requirement
        expected_agents = {'researcher', 'backend_dev', 'tester', 'doc_writer', 'devops', 'frontend_dev'}
        actual_agents = set(agent_names)
        
        print(f"EXPECTED AGENTS: {expected_agents}")
        print(f"ACTUAL AGENTS: {actual_agents}")
        print(f"MISSING AGENTS: {expected_agents - actual_agents}")
        print(f"EXTRA AGENTS: {actual_agents - expected_agents}")
        
        # Check workspace artifacts
        import os
        workspace_path = f"./workspace/{session_id}/"
        if os.path.exists(workspace_path):
            files = os.listdir(workspace_path)
            print(f"\nFILES IN WORKSPACE {workspace_path}: {files}")
        else:
            print(f"\nWORKSPACE {workspace_path} DOES NOT EXIST")
        
        return result
    except Exception as e:
        print(f"Error in test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task10_simple()