# Dashboard Issues

## Issue 001: Variables & Environment Support

**Priority:** HIGH  
**Status:** IN PROGRESS  
**Estimate:** 3 hours

### Description
Add support for environment variables that can be used in requests, similar to Postman. This allows users to switch between dev/staging/prod environments easily.

### Requirements

#### Data Model
```python
# stored in dashboard.db
class Environment:
    id: int
    name: str  # "Development", "Staging", "Production"
    variables: dict  # {"base_url": "http://localhost:5000", "api_key": "xxx"}
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### UI Requirements
- Dropdown to select environment in header
- "Manage Environments" button opens modal
- Environment variables shown as key-value pairs
- Variable substitution in URL: `{{base_url}}/api/users`
- Variable substitution in body, headers

#### API Endpoints
- `GET /api/environments` - List all environments
- `POST /api/environments` - Create environment
- `PUT /api/environments/{id}` - Update environment
- `DELETE /api/environments/{id}` - Delete environment
- `POST /api/environments/{id}/activate` - Set active environment

#### Variable Syntax
- `{{variable_name}}` - Replace with environment variable
- Support in: URL, Headers, Body, Params

#### Example Usage
```
Environment: Production
Variables:
  - base_url: https://api.example.com
  - api_key: sk_live_xxx

Request:
  URL: {{base_url}}/users
  → becomes: https://api.example.com/users
```

### Acceptance Criteria
1. Can create/edit/delete environments
2. Can switch between environments
3. Variables are substituted in requests
4. Active environment persists across sessions
5. Visual indicator of active environment in header

---

## Issue 002: Import from OpenAPI/Postman

**Priority:** HIGH  
**Status:** PENDING  
**Estimate:** 4 hours

### Description
Import API definitions from OpenAPI 3.x or Postman collections and automatically generate test requests.

### Requirements

#### Supported Formats
- OpenAPI 3.0/3.1 (JSON/YAML)
- Postman Collection v2.1

#### Import Process
1. User uploads file or pastes URL
2. System parses and validates
3. User selects which endpoints to import
4. Requests are created in dashboard

#### UI Components
- Import button in sidebar
- Drag-and-drop file upload
- URL input for remote specs
- Preview list of discovered endpoints
- Checkbox selection for what to import

#### API Endpoints
- `POST /api/import/openapi` - Parse OpenAPI spec
- `POST /api/import/postman` - Parse Postman collection

#### Data Storage
```python
class ImportedRequest:
    id: int
    name: str
    method: str  # GET, POST, etc.
    path: str
    import_source: str  # "openapi" or "postman"
    original_spec: dict
    created_at: datetime
```

### Acceptance Criteria
1. Can import OpenAPI 3.0 JSON
2. Can import OpenAPI 3.0 YAML
3. Can import Postman collection
4. Imported requests appear in sidebar
5. Can execute imported requests

---

## Issue 003: Request History Panel

**Priority:** HIGH  
**Status:** PENDING  
**Estimate:** 2 hours

### Description
Enhance the existing history feature to show detailed request/response pairs with timestamps, similar to Postman's history.

### Requirements

#### UI Layout
- Tab in main panel: "History"
- List of recent requests (last 100)
- Each entry shows: method, URL, status, time
- Click to reload request into editor

#### Data Model (extend existing)
```python
class RequestHistory:
    id: int
    timestamp: datetime
    method: str
    url: str
    headers: dict
    body: str
    response_status: int
    response_body: str
    response_headers: dict
    duration_ms: int
    environment_id: int  # which env was active
```

#### Features
- Search/filter by URL, method, status
- Clear history button
- Export history to JSON
- Click to restore request

#### API Endpoints
- `GET /api/history` - List with pagination
- `GET /api/history/{id}` - Get details
- `DELETE /api/history` - Clear all
- `DELETE /api/history/{id}` - Delete single

### Acceptance Criteria
1. History shows all executed requests
2. Can click to reload request
3. Can search/filter history
4. Can clear history
5. Persists across sessions

---

## Issue 004: Collections (Suites)

**Priority:** MEDIUM  
**Status:** PENDING  
**Estimate:** 3 hours

### Description
Group requests into named collections (folders) for organization, similar to Postman collections.

### Requirements

#### Data Model
```python
class Collection:
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

class CollectionRequest:
    id: int
    collection_id: int
    request_id: int
    order: int  # for sorting within collection
```

#### UI Components
- Collections section in sidebar (above individual requests)
- Create/rename/delete collections
- Drag-drop requests into collections
- Expand/collapse collection

#### Features
- Collection-level variables (override global)
- Run all requests in collection
- Export collection

### Acceptance Criteria
1. Can create/rename/delete collections
2. Can add requests to collections
3. Collections persist across sessions
4. Can run all in collection

---

## Issue 005: Code Snippet Generation

**Priority:** MEDIUM  
**Status:** PENDING  
**Estimate:** 2 hours

### Description
Generate code snippets (cURL, Python, JavaScript, etc.) from the current request, similar to Postman's code generator.

### Requirements

#### Supported Languages
- cURL
- Python (requests)
- JavaScript (fetch)
- Java (OkHttp)
- Go

#### UI
- Tab in main panel: "Code"
- Dropdown to select language
- Syntax-highlighted code output
- Copy button

#### Implementation
```python
LANGUAGE_TEMPLATES = {
    "curl": 'curl -X {{method}} "{{url}}" \\\n  -H "Content-Type: application/json"',
    "python": "import requests\n\nresponse = requests.{{method.lower()}}(\n    \"{{url}}\"\n)",
    # ...
}
```

### Acceptance Criteria
1. Generates valid cURL command
2. Generates valid Python requests code
3. Generates valid JavaScript fetch code
4. Copy button works
5. Updates when request changes

---

## Issue 006: Dark/Light Theme Toggle

**Priority:** LOW  
**Status:** PENDING  
**Estimate:** 1 hour

### Description
Add theme toggle for dark/light mode.

### Requirements

- Toggle in header
- Save preference in localStorage
- CSS variables for theming
- Smooth transition between themes

### Acceptance Criteria
1. Can toggle between dark/light
2. Preference persists
3. All UI elements properly themed

---

## Issue 007: Keyboard Shortcuts

**Priority:** LOW  
**Status:** PENDING  
**Estimate:** 2 hours

### Description
Add keyboard shortcuts for common actions.

### Shortcuts
- `Ctrl+Enter` / `Cmd+Enter` - Send request
- `Ctrl+S` / `Cmd+S` - Save request
- `Ctrl+N` / `Cmd+N` - New request
- `Ctrl+D` / `Cmd+D` - Duplicate request
- `Ctrl+,` - Open settings
- `Esc` - Close modals

### Acceptance Criteria
1. All shortcuts work
2. Shortcuts displayed in tooltips
3. Can disable shortcuts in settings

---

## Issue 008: WebSocket Testing Support

**Priority:** LOW  
**Status:** PENDING  
**Estimate:** 4 hours

### Description
Add support for testing WebSocket connections, similar to how HTTP requests work.

### Requirements

#### UI
- Method selector: WebSocket
- URL input for WS endpoint
- Connect/Disconnect buttons
- Message input for sending
- Message log panel

#### Features
- Connect to WS endpoint
- Send text/binary messages
- Display incoming messages
- Connection status indicator

### Acceptance Criteria
1. Can connect to WS endpoint
2. Can send messages
3. Can see incoming messages
4. Connection status shown

---

## Issue 009: Response Visualization

**Priority:** LOW  
**Status:** PENDING  
**Estimate:** 2 hours

### Description
Add response body visualization for common formats (JSON, XML, HTML, Images).

### Features

#### JSON
- Collapsible tree view
- Search within JSON
- Copy path

#### HTML
- Preview rendered HTML (sandboxed iframe)
- View source

#### Images
- Display image preview
- Show dimensions

### Acceptance Criteria
1. JSON shown as collapsible tree
2. HTML rendered in preview
3. Images displayed inline
4. Binary shown as hex dump

---

## Issue 010: Request/Response Comparison

**Priority:** LOW  
**Status:** PENDING  
**Estimate:** 3 hours

### Description
Compare two requests/responses side by side, useful for regression testing.

### Features
- Select two history entries
- Side-by-side diff view
- Highlight differences
- Merge capabilities (for body)

### Acceptance Criteria
1. Can select two requests
2. Differences highlighted
3. Can navigate between diffs
