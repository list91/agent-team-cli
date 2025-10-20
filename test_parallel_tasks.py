import sys
import os
import threading
from dotenv import load_dotenv
from workflow import run_agent_workflow

def run_session(session_id: str, task: str, results: dict, index: int):
    """
    Function to run a single session in a thread
    """
    load_dotenv()
    
    try:
        print(f"Thread {index}: Starting session {session_id} with task")
        
        result = run_agent_workflow(session_id, task)
        
        results[index] = {
            'session_id': session_id,
            'success': True,
            'result': result
        }
        
        print(f"Thread {index}: Completed session {session_id}")
    except Exception as e:
        print(f"Thread {index}: Error in session {session_id}: {str(e)}")
        results[index] = {
            'session_id': session_id,
            'success': False,
            'error': str(e)
        }

def test_parallel_tasks():
    """
    Testing all three tasks running in parallel to check isolation
    """
    load_dotenv()
    
    print("Testing parallel execution of all three tasks to check isolation:")
    
    # Define tasks for each session
    task_4 = "Создай CLI-инструмент для автоматического аудита и рефакторинга Python-проектов. Пользователь должен запустить утилиту как: pyrefactor --path ./my_project --fix-security --format-code --generate-report"
    task_5 = "Разработай систему локального CI/CD для команды разработчиков на базе CLI и Docker. Пользователь хочет локальный аналог GitHub Actions, который запускается из терминала и выполняет этапы: lint -> test -> build -> report."
    task_6 = "Создай утилиту для безопасного управления секретами в CLI-проектах. Инструмент vault-cli, который шифрует .env-файлы с помощью мастер-пароля и позволяет безопасно хранить их в Git."
    
    # Dictionary to store results from each thread
    results = {}
    
    # Create threads for each session
    thread_4 = threading.Thread(target=run_session, args=("session_4", task_4, results, 0))
    thread_5 = threading.Thread(target=run_session, args=("session_5", task_5, results, 1))
    thread_6 = threading.Thread(target=run_session, args=("session_6", task_6, results, 2))
    
    # Start all threads
    thread_4.start()
    thread_5.start()
    thread_6.start()
    
    # Wait for all threads to complete
    thread_4.join()
    thread_5.join()
    thread_6.join()
    
    # Check results
    success_4 = results[0]['success']
    success_5 = results[1]['success']
    success_6 = results[2]['success']
    
    print(f"Session 4 (Task 4) success: {success_4}")
    print(f"Session 5 (Task 5) success: {success_5}")
    print(f"Session 6 (Task 6) success: {success_6}")
    
    if success_4 and success_5 and success_6:
        print("SUCCESS: All sessions completed successfully - isolation test passed")
        
        # Check final decisions
        for i in range(3):
            decision = results[i]['result'].get('final_decision', 'No decision')
            print(f"Session {i+4} final decision: {decision}")
        
        return True
    else:
        print("FAILURE: One or more sessions failed - isolation test failed")
        for i, session_id in enumerate(['session_4', 'session_5', 'session_6']):
            if not results[i].get('success', False):
                print(f"  Session {session_id} error: {results[i].get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    test_parallel_tasks()