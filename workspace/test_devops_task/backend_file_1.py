name: CI/CD Pipeline

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest
        pip install bandit

    - name: Run tests
      run: |
        pytest

    - name: Run security scan
      run: |
        bandit -r .

  build_and_push:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_HUB_USERNAME }}
        password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}

    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.DOCKER_HUB_USERNAME }}/myapp:latest .
        docker push ${{ secrets.DOCKER_HUB_USERNAME }}/myapp:latest

  deploy:
    runs-on: ubuntu-latest
    needs: build_and_push

    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # Add deployment script or command here

  pre_commit:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Install pre-commit
      run: |
        pip install pre-commit
        pre-commit run --all-files
