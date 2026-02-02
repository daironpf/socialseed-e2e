# 🛍️ Basic CRUD Example

A complete working example of basic CRUD operations using socialseed-e2e with a Flask API and SQLite backend.

## Overview

This example demonstrates:
- **Create**: POST /api/items
- **Read**: GET /api/items (list) and GET /api/items/{id} (single)
- **Update**: PUT /api/items/{id}
- **Delete**: DELETE /api/items/{id}

## 📁 Project Structure

```
01-basic-crud/
├── api.py                           # Flask API with SQLite
├── requirements.txt                 # Python dependencies
├── e2e.conf                         # socialseed-e2e configuration
├── services/
│   └── items-api/
│       ├── items_api_page.py       # Service page class
│       ├── data_schema.py          # Pydantic models
│       └── modules/
│           ├── 01_create_item.py   # Create tests
│           ├── 02_list_items.py    # List tests
│           ├── 03_get_item.py      # Get single item tests
│           ├── 04_update_item.py   # Update tests
│           └── 05_delete_item.py   # Delete tests
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API

```bash
python api.py
```

The API will start on http://localhost:5000 with the following endpoints:
- `POST /api/items` - Create item
- `GET /api/items` - List items (with pagination & search)
- `GET /api/items/{id}` - Get single item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item
- `GET /health` - Health check

### 3. Verify Test Discovery

In a new terminal (from the example directory):

```bash
e2e run
```

You should see output showing that **5 tests** are detected and ready:

```
🚀 socialseed-e2e v0.1.0
══════════════════════════════════════════════════

📋 Configuración: e2e.conf
🌍 Environment: dev

    Servicios Encontrados
┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Servicio  ┃ Tests ┃ Estado ┃
┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ items-api │ 5     │ Ready  │
└───────────┴───────┴────────┘
```

### ⚠️ Important Note

**Test execution is currently in placeholder mode** (v0.1.0). The test modules are fully implemented and detected, but the actual test runner will be implemented in v0.2.0.

**What's working:**
- ✅ Complete test module examples (5 tests)
- ✅ Test discovery and listing
- ✅ API with all CRUD endpoints
- ✅ Service Page implementation
- ✅ Data schemas with validation

**Coming in v0.2.0:**
- 🚧 Full test execution with `e2e run`
- 🚧 Test results reporting
- 🚧 HTML reports

### Manual Testing

You can test the API manually using curl commands (see below) or by importing the test modules into your own Python scripts.

## 📋 Step-by-Step Tutorial

### Step 1: Explore the API

The Flask API (`api.py`) provides a simple items inventory system with:
- SQLite database (auto-created as `items.db`)
- JSON request/response format
- Error handling and validation
- Pagination and search support

### Step 2: Service Page Class

The `ItemsApiPage` class (`services/items-api/items_api_page.py`) extends `BasePage` and provides methods for each CRUD operation:

```python
# Create
response = items_api.create_item(
    name="Laptop",
    price=999.99,
    description="High-performance laptop",
    quantity=10
)

# List
response = items_api.list_items(page=1, limit=10)

# Get
response = items_api.get_item(1)

# Update
response = items_api.update_item(1, price=899.99)

# Delete
response = items_api.delete_item(1)
```

### Step 3: Test Modules

Each test module in `services/items-api/modules/` tests a specific operation:

1. **01_create_item.py** - Tests creating items and validation
2. **02_list_items.py** - Tests listing with pagination and search
3. **03_get_item.py** - Tests retrieving single items and 404 handling
4. **04_update_item.py** - Tests partial and full updates
5. **05_delete_item.py** - Tests deletion and verification

### Step 4: Data Schemas

Pydantic models in `data_schema.py` define the data structures:
- `ItemCreate` - Fields required for creation
- `ItemUpdate` - Optional fields for updates
- `Item` - Complete item representation
- `ItemListResponse` - Paginated list response

## 🧪 Running Tests

### Current Status (v0.1.0)

Test execution is currently in **placeholder mode**. While all 5 test modules are complete and will be detected:

```bash
cd examples/01-basic-crud
e2e run
# Shows: items-api | 5 | Ready
```

The actual test runner execution will be implemented in v0.2.0. Until then, you can:

1. **Study the test examples** - Learn from the 5 complete test implementations
2. **Test manually** - Use the curl examples below
3. **Import into your code** - Use the test modules as reference

### View Test Modules

All test modules are functional and demonstrate best practices:

```bash
# View test implementations
ls -la services/items-api/modules/
cat services/items-api/modules/01_create_item.py
```

### Manual Testing

You can verify the API works correctly using curl:

## 🔍 API Endpoints

### Health Check
```bash
curl http://localhost:5000/health
```

### Create Item
```bash
curl -X POST http://localhost:5000/api/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","price":99.99,"quantity":5}'
```

### List Items
```bash
# List all
curl http://localhost:5000/api/items

# With pagination
curl "http://localhost:5000/api/items?page=1&limit=5"

# With search
curl "http://localhost:5000/api/items?search=laptop"
```

### Get Single Item
```bash
curl http://localhost:5000/api/items/1
```

### Update Item
```bash
curl -X PUT http://localhost:5000/api/items/1 \
  -H "Content-Type: application/json" \
  -d '{"price":89.99}'
```

### Delete Item
```bash
curl -X DELETE http://localhost:5000/api/items/1
```

## 📝 Writing Your Own Tests

To add a new test:

1. Create a new file in `services/items-api/modules/`
2. Name it with prefix (e.g., `06_bulk_operations.py`)
3. Implement the `run()` function:

```python
from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: 'ItemsApiPage') -> APIResponse:
    """Your test description."""
    print("Starting my test...")

    # Your test code here
    response = items_api.create_item(name="Test", price=10.00)
    items_api.assert_status(response, 201)

    print("✅ Test passed!")
    return response
```

## 🐛 Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```python
# Edit api.py and change the port
app.run(host='0.0.0.0', port=5001, debug=True)
```

Then update `e2e.conf`:

```yaml
services:
  items-api:
    base_url: http://localhost:5001
```

### Database Issues

To reset the database:

```bash
rm items.db
python api.py  # Will recreate with empty schema
```

### Import Errors

Make sure socialseed-e2e is installed:

```bash
pip install socialseed-e2e
# or in development mode:
pip install -e /path/to/socialseed-e2e
```

## 🎓 Learning Outcomes

After working through this example, you'll understand:

1. ✅ How to structure a socialseed-e2e test project
2. ✅ How to create a Service Page class with CRUD methods
3. ✅ How to write test modules with the `run()` function
4. ✅ How to use assertions and handle responses
5. ✅ How to share state between tests
6. ✅ How to configure e2e.conf for your API

## 📚 Next Steps

- Try modifying the tests to add validation scenarios
- Add new endpoints to the API and corresponding tests
- Explore the other examples in the `examples/` directory
- Read the full documentation at [../../docs/](../../docs/)

## 💡 Key Concepts Demonstrated

- **Service Page Pattern**: Encapsulating API interactions in a class
- **Test Modules**: Independent test files with `run()` entry point
- **Assertions**: Using `assert_status()`, `assert_json()` helpers
- **State Sharing**: Storing data in service page attributes
- **Cleanup**: Managing test data with `created_items` list
- **Pagination**: Testing list endpoints with pagination params
- **Error Handling**: Testing 404 and validation error scenarios

---

**Happy Testing!** 🚀
