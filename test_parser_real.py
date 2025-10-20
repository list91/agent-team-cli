import json
import re

response = '{"agents": [{"agent": "coder", "description": "create hello.py"}]}I\'ll help you create a hello.py file. Let me write a simple Python script that prints "Hello, World!".'

print("Testing JSON parser with real qwen response...")
print(f"Response: {response[:100]}...")

# Strategy 2: Find all potential JSON objects by balancing braces
potential_jsons = []
brace_count = 0
start_idx = None

for i, char in enumerate(response):
    if char == '{':
        if brace_count == 0:
            start_idx = i
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0 and start_idx is not None:
            potential_jsons.append(response[start_idx:i+1])
            start_idx = None

print(f"\nFound {len(potential_jsons)} potential JSON objects")

for i, json_str in enumerate(potential_jsons):
    print(f"\nCandidate {i+1}: {json_str[:100]}...")
    try:
        parsed = json.loads(json_str)
        print(f"✅ Valid JSON! Keys: {list(parsed.keys())}")
        if 'agents' in parsed:
            print(f"   agents field present: {parsed['agents']}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
