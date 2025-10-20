from main import query_ollama
from prompts import PROMPTS

def test_prompt(prompt_name, test_input):
    print(f"\n=== Тестирование промпта: {prompt_name} ===")
    prompt = PROMPTS[prompt_name].replace("<*^$YOURPROMPT$^*>", test_input)
    print("\nЗапрос к Llama...")
    response = query_ollama(prompt)
    print("\nОтвет:")
    print(response)
    print("\n" + "="*50)

# Тестовые данные для каждого промпта
test_cases = {
    "explain_code": """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
""",

    "code_review": """
def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
""",

    "generate_docs": """
def calculate_discount(price, customer_type):
    if customer_type == 'vip':
        return price * 0.8
    elif customer_type == 'regular':
        return price * 0.95
    return price
""",

    "generate_tests": """
def divide_numbers(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""",

    "fix_bug": """
def factorial(n):
    if n == 0:
        return 0
    return n * factorial(n-1)
""",

    "optimize_code": """
def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates
""",

    "design_api": "Создать API для системы управления задачами (todo list) с возможностью создания, удаления и обновления задач",

    "optimize_query": """
SELECT * FROM orders o 
JOIN customers c ON c.id = o.customer_id 
JOIN products p ON p.id = o.product_id 
WHERE o.created_at > '2023-01-01'
""",

    "security_review": """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    if user:
        return create_session(user)
    return None
""",

    "refactor_code": """
def process_data(data):
    result = []
    for item in data:
        if item['type'] == 'A':
            val = item['value'] * 2
            if val > 100:
                result.append(val)
        elif item['type'] == 'B':
            val = item['value'] / 2
            if val > 50:
                result.append(val)
    return result
""",

    "error_handling": """
def read_config(filename):
    f = open(filename)
    data = f.read()
    config = json.loads(data)
    f.close()
    return config
""",

    "complete_code": """
class ShoppingCart:
    def __init__(self):
        self.items = {}
        
    def add_item(self, item_id, quantity):
""",

    "design_architecture": "Спроектировать систему онлайн-бронирования для небольшой сети отелей",

    "result cmd command": """
C:\\Users\\user>python script.py
Starting process...
Loading dependencies...
Process completed successfully.
Exit code: 0
"""
}

def test_streaming_response():
    print("\nTesting streaming response with a complex question...")
    prompt = """Please write a detailed explanation of how neural networks work. 
    Break it down into multiple paragraphs and include technical details."""
    
    print("Starting response (you should see it appear gradually):\n")
    result = query_ollama(prompt)
    print(f"\nResponse status: {result}")

if __name__ == "__main__":
    # Тестируем каждый промпт
    for prompt_name, test_input in test_cases.items():
        test_prompt(prompt_name, test_input)
    test_streaming_response()
