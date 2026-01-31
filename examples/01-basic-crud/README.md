# Basic CRUD Example

This example demonstrates basic CRUD operations testing.

## Running the Example

```bash
cd examples/01-basic-crud
pip install -r requirements.txt
python api.py &
e2e run
```

## API Description

The example API provides:
- `POST /api/items` - Create item
- `GET /api/items` - List items
- `GET /api/items/{id}` - Get item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

## Tests Included

1. Create item test
2. List items test
3. Get item test
4. Update item test
5. Delete item test

See the `tests/` directory for implementation details.
