#!/usr/bin/env python3
"""Test parser logic"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from agents.available.coder.agent import CoderAgent
import tempfile

resp = '''```python
# main.py
from fastapi import FastAPI

app = FastAPI()
```

```dockerfile
# Dockerfile
FROM python:3.11
```
'''

with tempfile.TemporaryDirectory() as tmpdir:
    scratchpad_path = Path(tmpdir) / "test.scratchpad.md"
    agent = CoderAgent(scratchpad_path)
    files = agent._parse_and_write_code_blocks(resp)
    print("Files created:", files)
    for f in files:
        p = Path(f)
        if p.exists():
            print(f"✓ {p.name} exists, size: {p.stat().st_size}")
        else:
            print(f"✗ {p.name} NOT FOUND")
