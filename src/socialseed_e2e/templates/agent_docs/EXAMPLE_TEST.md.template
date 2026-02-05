# Ejemplo Completo de Test Generado

Este archivo sirve como referencia "Gold Standard" de lo que se espera generar.

**IMPORTANT PRINCIPLES:**
- NO relative imports (from ..x import y) - use absolute imports from `services.xxx.data_schema`
- Always use `by_alias=True` when serializing Pydantic models
- Handle authentication headers manually (no `update_headers` method)
- Use `do_*` prefix for methods to avoid name conflicts with attributes

Supongamos una API de Tareas (TODOs).

## 1. services/todo_app/data_schema.py

```python
from pydantic import BaseModel, Field
from typing import Optional

class TodoItem(BaseModel):
    id: Optional[str] = None
    title: str
    completed: bool = False

    class Config:
        populate_by_name = True

ENDPOINTS = {
    "list": "/todos",
    "create": "/todos",
    "get": "/todos/{id}",
    "update": "/todos/{id}",
    "delete": "/todos/{id}"
}
```

## 2. services/todo_app/todo_app_page.py

```python
from socialseed_e2e.core.base_page import BasePage
from playwright.sync_api import APIResponse, APIRequestContext
from services.todo_app.data_schema import TodoItem, ENDPOINTS

class TodoAppPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.created_todo_id = None  # Estado compartido
        self.auth_token = None

    def do_create_todo(self, item: TodoItem) -> APIResponse:
        """Create a new todo item."""
        return self.post(
            ENDPOINTS["create"],
            data=item.model_dump(by_alias=True, exclude={"id"})
        )

    def do_get_todo(self, todo_id: str) -> APIResponse:
        """Retrieve a todo by ID."""
        path = ENDPOINTS["get"].format(id=todo_id)
        return self.get(path)

    def do_delete_todo(self, todo_id: str) -> APIResponse:
        """Delete a todo by ID."""
        path = ENDPOINTS["delete"].format(id=todo_id)
        return self.delete(path)

    def do_authenticate(self, token: str) -> None:
        """Set authentication token manually."""
        self.auth_token = token
        # Manually handle headers - don't use update_headers()
        self.headers = {**self.headers, "Authorization": f"Bearer {token}"}
```

## 3. services/todo_app/modules/01_create_todo.py

```python
from services.todo_app.data_schema import TodoItem
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.todo_app.todo_app_page import TodoAppPage

def run(page: 'TodoAppPage'):
    print("STEP: Create Todo")

    new_todo = TodoItem(title="Learn SocialSeed E2E", completed=False)

    response = page.do_create_todo(new_todo)
    assert response.ok, f"Failed to create todo: {response.status} - {response.text()}"

    data = response.json()
    assert data["title"] == new_todo.title, f"Title mismatch: expected {new_todo.title}, got {data.get('title')}"
    assert "id" in data, "No 'id' field in response"

    # Guardar ID para el siguiente paso
    page.created_todo_id = data["id"]
    print(f"✓ Created Todo with ID: {page.created_todo_id}")
```

## 4. services/todo_app/modules/02_get_todo.py

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.todo_app.todo_app_page import TodoAppPage

def run(page: 'TodoAppPage'):
    print("STEP: Get Todo")

    # Recuperar ID del paso anterior
    todo_id = page.created_todo_id
    assert todo_id, "No created_todo_id found from previous step"

    response = page.do_get_todo(todo_id)
    assert response.ok, f"Failed to get todo: {response.status} - {response.text()}"

    data = response.json()
    assert data["id"] == todo_id, f"ID mismatch: expected {todo_id}, got {data.get('id')}"
    print("✓ Todo retrieved successfully")
```

## 5. services/todo_app/modules/03_authenticated_request.py

```python
from services.todo_app.data_schema import TodoItem
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.todo_app.todo_app_page import TodoAppPage

def run(page: 'TodoAppPage'):
    print("STEP: Authenticated Request Example")

    # Perform authentication and store token
    auth_response = page.post("/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert auth_response.ok, f"Authentication failed: {auth_response.status}"

    token = auth_response.json().get("token")
    assert token, "No token in authentication response"

    # Manually set the authentication token
    page.do_authenticate(token)

    # Now make authenticated request
    new_todo = TodoItem(title="Authenticated Todo", completed=False)

    # Use by_alias=True when serializing
    response = page.do_create_todo(new_todo)
    assert response.ok, f"Failed to create todo: {response.status} - {response.text()}"

    print("✓ Authenticated request successful")
```
