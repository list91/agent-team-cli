#!/usr/bin/env python3
"""
MSP Orchestrator CLI entry point
Usage: ./msp-run --task "Create a REST API with FastAPI"
"""
import sys
import argparse
import json
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.master.master import run_master


def main():
    parser = argparse.ArgumentParser(description="MSP Orchestrator CLI")
    parser.add_argument("--task", required=True, help="Task description in natural language")
    parser.add_argument("--workdir", default=".", help="Working directory (default: current directory)")
    
    args = parser.parse_args()
    
    # Convert workdir to absolute path
    workdir = Path(args.workdir).resolve()
    
    # Create workdir if it doesn't exist
    workdir.mkdir(parents=True, exist_ok=True)
    
    # Prepare task for master
    task_data = {
        "description": args.task,
        "context": {
            "workdir": str(workdir)
        }
    }
    
    # Run the master orchestrator
    result = run_master(task_data, workdir)
    
    if result["status"] == "success":
        print("Task completed successfully!")
        if "produced_files" in result:
            print(f"Files produced: {result['produced_files']}")
    else:
        print(f"Task failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()