from dotenv import load_dotenv
from workflow import run_agent_workflow

if __name__ == "__main__":
    load_dotenv()
    
    session_id = "todo_mvp_test_123"
    user_request = "Создай MVP REST API для управления задачами (To-Do) с аутентификацией и документацией"
    
    print(f"Запускаю тест для сессии: {session_id}")
    print(f"Запрос пользователя: {user_request}")
    print("-" * 60)
    
    result = run_agent_workflow(session_id, user_request)
    
    print("Результаты выполнения:")
    print(f"Решение мастера: {result.get('master_decision', 'Нет данных')[:300]}...")
    print(f"Делегированные задачи: {len(result.get('delegated_tasks', []))}")
    
    for i, task in enumerate(result.get('delegated_tasks', [])):
        print(f"  Задача {i+1}: {task.get('agent', 'N/A')} - {task.get('task', 'N/A')[:100]}...")
    
    print(f"Результаты агентов: {len(result.get('agent_results', []))}")
    
    for i, agent_result in enumerate(result.get('agent_results', [])):
        print(f"  Результат {i+1}:")
        print(f"    Агент: {agent_result.get('agent_name', 'N/A')}")
        print(f"    Задача: {agent_result.get('task', 'N/A')[:100]}...")
        print(f"    Результат: {agent_result.get('result', 'N/A')[:200]}...")
        
    print(f"Окончательное решение: {result.get('final_decision', 'Нет данных')}")
    print(f"Заметки по ревью: {result.get('review_notes', 'Нет данных')[:500]}...")
    
    # Проверка наличия файлов в workspace
    import os
    workspace_path = f"./workspace/{session_id}"
    if os.path.exists(workspace_path):
        files = os.listdir(workspace_path)
        print(f"Файлы в workspace/{session_id}: {files}")
    else:
        print(f"Директория workspace/{session_id} не найдена")