from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task7_detailed():
    """
    Detailed test for Task 7: Performance comparison system
    Expected: Master should delegate to Researcher, BackendDev, Tester, DevOps, DocWriter
    """
    load_dotenv()
    
    session_id = "task7_detailed"
    user_request = """Создай систему автоматического сравнения производительности двух версий Python-библиотеки.
    CLI-инструмент `perf-compare`, который:
    perf-compare --lib-name requests --old-version 2.28.0 --new-version 2.31.0 --benchmark-script ./benchmarks/http_load.py
    → генерирует отчёт `perf_diff.json` с метриками: время выполнения, потребление памяти, ошибки.

    Делегирование:
    - Researcher: найти best practices по бенчмаркингу Python (например, `pyperf`, `memory_profiler`).
    - BackendDev: реализовать `perf-compare` CLI с изоляцией версий через виртуальные окружения.
    - Tester: написать тесты на корректность замеров и обработку ошибок.
    - DevOpsAgent: создать Docker-образ с предустановленными инструментами профилирования.
    - DocWriter: документация по написанию кастомных benchmark-скриптов.

    Мастер проверяет:  
    - отчёт содержит числовые различия,  
    - обе версии запускаются в изолированных env,  
    - нет утечек между запусками."""
    
    print(f"=== TESTING TASK 7: Performance Comparison Tool ===")
    print(f"Session: {session_id}")
    print(f"Request length: {len(user_request)} chars")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print(f"\nFINAL DECISION: {result.get('final_decision', 'No decision')}")
    print(f"REVIEW NOTES preview: {result.get('review_notes', 'No review notes')[:200]}...")
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
    
    # Expected agents based on the requirement
    expected_agents = {'researcher', 'backend_dev', 'tester', 'devops', 'doc_writer'}
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
    test_task7_detailed()