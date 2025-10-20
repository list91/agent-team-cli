#!/usr/bin/env python3
"""
Echo Agent - a simple test agent that writes its task to scratchpad and returns it.
This agent demonstrates the basic MSP contract.
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scratchpad import Scratchpad


def main():
    parser = argparse.ArgumentParser(description="Echo Agent - MSP Test Agent")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--scratchpad-path", required=True, help="Path to scratchpad file")
    parser.add_argument("--max-scratchpad-chars", type=int, default=8192, help="Max scratchpad characters")
    parser.add_argument("--allowed-tools", default="", help="Comma-separated list of allowed tools")
    parser.add_argument("--clarification-endpoint", help="HTTP endpoint for clarification requests")
    
    args = parser.parse_args()
    
    # Parse task
    task = json.loads(args.task)
    description = task.get("description", "")
    
    # Initialize scratchpad
    scratchpad = Scratchpad(Path(args.scratchpad_path), max_chars=args.max_scratchpad_chars)
    
    # Write initial status to scratchpad
    scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Echo Agent started\n")
    scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Task: {description}\n")
    
    # Simulate some work
    scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Processing task...\n")
    time.sleep(1)
    
    # Write response to scratchpad
    response = f"Echo: {description}"
    scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Response: {response}\n")
    
    # Prepare result
    result = {
        "status": "success",
        "result": {"response": response},
        "produced_files": []
    }
    
    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()