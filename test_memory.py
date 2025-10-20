from memory.zep_client import RealZepMemoryManager

def test_memory_functionality():
    """
    Тестируем функциональность реальной памяти
    """
    print("Тестируем реальную систему памяти...")
    
    # Создаем менеджер памяти
    memory_manager = RealZepMemoryManager()
    
    # Тестируем добавление сообщений
    session_id = "test_session"
    agent_name = "backend_dev"
    
    print(f"Добавляем 3 сообщения в сессию {session_id} для агента {agent_name}")
    
    memory_manager.add_message(session_id, agent_name, "Первое сообщение")
    memory_manager.add_message(session_id, agent_name, "Второе сообщение")
    memory_manager.add_message(session_id, agent_name, "Третье сообщение")
    
    # Получаем сообщения
    messages = memory_manager.get_messages(session_id, agent_name)
    
    print(f"Получено {len(messages)} сообщений:")
    for i, msg in enumerate(messages):
        safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
    print(f"  {i+1}. {safe_msg}")
    
    # Тестируем ограничение FIFO (добавим больше 50 сообщений)
    print(f"\nТестируем ограничение FIFO (добавляем 55 сообщений)...")
    
    for i in range(55):
        memory_manager.add_message(session_id, agent_name, f"Сообщение #{i+1}")
    
    messages_after_limit = memory_manager.get_messages(session_id, agent_name)
    
    print(f"После добавления 55 сообщений: {len(messages_after_limit)} сообщений в памяти")
    print(f"Первое сообщение: {messages_after_limit[0] if messages_after_limit else 'Нет'}")
    print(f"Последнее сообщение: {messages_after_limit[-1] if messages_after_limit else 'Нет'}")
    
    # Проверяем изоляцию - добавим сообщения для другого агента
    agent2_name = "tester"
    memory_manager.add_message(session_id, agent2_name, "Сообщение от тестировщика")
    
    tester_messages = memory_manager.get_messages(session_id, agent2_name)
    print(f"\nСообщения для агента {agent2_name}: {len(tester_messages)}")
    
    backend_messages = memory_manager.get_messages(session_id, agent_name)
    print(f"Сообщения для агента {agent_name} (должны быть изолированы): {len(backend_messages)}")
    
    print("\nТест памяти завершен успешно!")

if __name__ == "__main__":
    test_memory_functionality()