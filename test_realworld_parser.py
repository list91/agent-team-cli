#!/usr/bin/env python
"""Test JSON parsing with real qwen output"""

# Real qwen output (stdout only, no stderr)
real_qwen_output = '''{"agents": [{"agent": "coder"}]}I'll help you continue with the Qwen Code setup.'''

print("Testing JSON parser with REAL qwen stdout...")
print(f"Input length: {len(real_qwen_output)}")
print(f"Input: {real_qwen_output[:100]}...")

# Import the actual parser from llm_client
import sys
sys.path.insert(0, '.')
from src.llm_client import LLMClient

# Create a mock client just to test the parser
class MockProvider:
    def generate(self, *args, **kwargs):
        return real_qwen_output

client = LLMClient("mock")
client.provider = MockProvider()

# Test the internal JSON parser
result = client._parse_json_response(real_qwen_output)

print("\n=== RESULT ===")
print(result)

if isinstance(result, dict) and 'agents' in result:
    print("\n✅ SUCCESS! Parser extracted the JSON correctly!")
    print(f"   Found agents: {result['agents']}")
else:
    print("\n❌ FAIL! Parser did not extract JSON")
    if isinstance(result, dict) and 'error' in result:
        print(f"   Error: {result['error']}")
