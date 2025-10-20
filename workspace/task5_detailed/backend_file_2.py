import yaml
import subprocess
import os

def load_config(config_path='ci.config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def run_stage(stage, config):
    image = config.get('image', 'python:3.8')
    command = config.get('command', '')
    
    if not command:
        print(f"No command specified for stage: {stage}")
        return
    
    volume_mount = f"{os.getcwd()}:/workspace"
    docker_command = f"docker run --rm -v {volume_mount} {image} /bin/sh -c '{command}'"
    
    print(f"Running stage: {stage}")
    result = subprocess.run(docker_command, shell=True)
    
    if result.returncode != 0:
        print(f"Stage {stage} failed with exit code {result.returncode}")
        exit(result.returncode)

def main():
    config = load_config()
    
    for stage, stage_config in config.items():
        run_stage(stage, stage_config)

if __name__ == "__main__":
    main()
