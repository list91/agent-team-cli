from dotenv import load_dotenv
from workflow import run_agent_workflow

def test_task8_detailed():
    """
    Detailed test for Task 8: Changelog generation utility
    Expected: Master should delegate to Researcher, BackendDev, Tester, DocWriter, DevOps
    """
    load_dotenv()
    
    session_id = "task8_detailed"
    user_request = """Разработай утилиту для генерации changelog из Git-истории и pull request'ов.
    CLI-инструмент `auto-changelog`, который:
    auto-changelog --repo-path ./my_project --from v1.0 --to v2.0 --output CHANGELOG.md
    → анализирует коммиты, PR-описания (через GitHub API), классифицирует изменения (feat/fix/docs), генерирует структурированный changelog.

    Делегирование:
    - Researcher: изучить conventional commits, GitHub API для получения PR-данных.
    - BackendDev: написать парсер коммитов + интеграцию с GitHub API (через токен).
    - Tester: проверить корректность классификации и обработку edge cases (merge commits, reverts).
    - DocWriter: шаблон CONTRIBUTING.md с правилами написания коммитов.
    - DevOpsAgent: добавить GitHub Action, который автоматически обновляет changelog при тегировании.

    Мастер проверяет:  
    - changelog соответствует conventional commits,  
    - нет утечки токена в логах,  
    - работает offline (если нет интернета — использует только локальные коммиты)."""
    
    print(f"=== TESTING TASK 8: Changelog Generation Tool ===")
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
    test_task8_detailed()