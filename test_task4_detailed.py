from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task4_detailed():
    """
    Detailed test for Task 4: Create CLI tool for Python project audit and refactoring
    Expected: Master should delegate to Researcher, BackendDev, Tester, DocWriter, DevOps
    """
    load_dotenv()
    
    session_id = "task4_detailed"
    user_request = """Создай CLI-инструмент для автоматического аудита и рефакторинга Python-проектов. 
    Пользователь должен запустить утилиту как: pyrefactor --path ./my_project --fix-security --format-code --generate-report
    
    Что должен сделать мастер-агент:
    Делегировать Researcher:
    Изучить best practices по статическому анализу Python (bandit, ruff, pylint, semgrep).
    Собрать список типовых уязвимостей и anti-patterns.
    
    Делегировать BackendDev:
    Написать CLI-приложение на Python (с использованием click или typer).
    Реализовать модули:
    security_scanner (на основе bandit-like логики),
    code_formatter (через ruff --fix),
    dependency_checker (анализ requirements.txt на CVE).
    
    Делегировать Tester:
    Написать unit-тесты для каждого модуля.
    Создать интеграционные тесты: запуск pyrefactor на тестовом проекте и проверка изменений.
    
    Делегировать DocWriter:
    Написать README.md с примерами использования.
    Сгенерировать USAGE.md с описанием всех флагов.
    
    Делегировать DevOpsAgent:
    Создать Dockerfile для запуска pyrefactor без установки зависимостей.
    Добавить GitHub Actions workflow для CI (запуск тестов при пуше).
    
    Мастер проверяет:
    CLI работает в консоли без ошибок,
    отчёт генерируется в refactor_report.json,
    Docker-образ собирается и запускается."""
    
    print(f"=== TESTING TASK 4: Detailed ===")
    print(f"Session: {session_id}")
    print(f"Request: {user_request[:100]}...")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
    print(f"REVIEW NOTES: {result.get('review_notes', 'No review notes')[:200]}...")
    print(f"NUMBER OF AGENT RESULTS: {len(result.get('agent_results', []))}")
    
    print("\nAGENT RESULTS:")
    for i, agent_result in enumerate(result.get('agent_results', [])):
        agent_name = agent_result.get('agent_name', 'Unknown')
        task = agent_result.get('task', 'No task')
        result_content = agent_result.get('result', 'No result')
        
        print(f"  {i+1}. Agent: {agent_name}")
        print(f"     Task preview: {task[:100]}...")
        print(f"     Result preview: {result_content[:200]}...")
        print(f"     Result length: {len(result_content)} chars")
        print()
    
    # Check for expected agents
    agent_names = [ar.get('agent_name', '') for ar in result.get('agent_results', [])]
    print(f"AGENTS USED: {set(agent_names)}")
    
    # Expected agents based on the requirement: researcher, backend_dev, tester, doc_writer, devops
    expected_agents = {'researcher', 'backend_dev', 'tester', 'doc_writer', 'devops'}
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

if __name__ == "__main__":
    test_task4_detailed()