# Task Management API

This is a REST API for managing tasks built with FastAPI.

## Features
- Create, Read, Update, and Delete (CRUD) operations for tasks
- FastAPI automatic documentation at `/docs`
- Pydantic model validation

## Endpoints

- `GET /` - Root endpoint
- `GET /tasks` - Get all tasks
- `GET /tasks/{{task_id}}` - Get a specific task
- `POST /tasks` - Create a new task
- `PUT /tasks/{{task_id}}` - Update a specific task
- `DELETE /tasks/{{task_id}}` - Delete a specific task

## Technologies Used
- FastAPI
- Pydantic
- Uvicorn (ASGI server)

## Running the Application

### Prerequisites
- Python 3.10+
- pip

### Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`

The API will be available at `http://localhost:8000`.

### Docker
Build and run with Docker:
```
docker build -t task-api .
docker run -p 8000:8000 task-api
```

## API Documentation
Auto-generated documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License
MIT
