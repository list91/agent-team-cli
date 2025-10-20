#!/usr/bin/env python3
"""Debug parser"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.llm_client import create_llm_client_from_config
from src.fallbacks import get_fallback_config

config = get_fallback_config()
client = create_llm_client_from_config(config)

resp = client.generate('', 'Task: Create a FastAPI service\n\nGenerate production-ready code')

blocks = resp.split('```')
print(f'Total blocks: {len(blocks)}')

for i, block in enumerate(blocks):
    print(f'\nBlock {i}:')
    lines = block.split('\n')[:3]
    for j, line in enumerate(lines):
        print(f'  Line {j}: {repr(line)}')
