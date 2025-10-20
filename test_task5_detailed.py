from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task5_detailed():
    """
    Detailed test for Task 5: Local CI/CD system
    Expected: Master should delegate to Researcher, BackendDev, DevOps, Tester, DocWriter
    """
    load_dotenv()
    
    session_id = "task5_detailed"
    user_request = """Разработай систему локального CI/CD для команды разработчиков на базе CLI и Docker. 
    Пользователь хочет локальный аналог GitHub Actions, который запускается из терминала и выполняет этапы: lint -> test -> build -> report.
    
    Что должен сделать мастер-агент:
    Делегировать Researcher:
    Изучить структуру .github/workflows и аналоги (например, taskfile, just, make).
    Определить минимальный набор этапов для Python/JS проектов.
    
    Делегировать BackendDev:
    Написать local-ci.py — скрипт, который читает ci.config.yaml и последовательно запускает этапы в изолированных Docker-контейнерах.
    Поддержка этапов: lint, test, build, notify.
    
    Делегировать DevOpsAgent:
    Создать базовые Docker-образы: ci-python, ci-node.
    Реализовать монтирование кода в контейнеры через volume.
    
    Делегировать Tester:
    Написать end-to-end тест: запуск local-ci run на тестовом репозитории → проверка exit code и логов.
    
    Делегировать DocWriter:
    Написать GETTING_STARTED.md с примером ci.config.yaml.
    Документация по кастомизации этапов.
    
    Мастер проверяет:
    Система запускается одной командой local-ci run,
    Каждый этап изолирован в своём контейнере,
    При падении тестов — весь pipeline останавливается с кодом 1."""
    
    print(f"=== TESTING TASK 5: Detailed ===")
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
    
    # Expected agents based on the requirement: researcher, backend_dev, devops, tester, doc_writer
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
    test_task5_detailed()