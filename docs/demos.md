# Demo APIs Guide

This guide documents all the demo APIs available in socialseed-e2e for testing and learning purposes.

## Overview

The framework includes multiple demo APIs covering different protocols and use cases:

| Demo | Port | Protocol | Description |
|------|------|----------|-------------|
| REST API | 5000 | HTTP | Basic CRUD operations |
| Auth/JWT | 5003 | HTTP | JWT authentication |
| gRPC | 50051 | gRPC | gRPC service |
| WebSocket | 50052 | WS | Real-time messaging |
| E-commerce | 5004 | HTTP | Shopping cart, products |
| Chat | 5005 | HTTP | Messaging, rooms |
| Booking | 5006 | HTTP | Reservations |
| Notifications | 5007 | HTTP | Push, email, SMS |

## Installation

All demos are installed via the `install-demo` command:

```bash
# Initialize project (if needed)
e2e init my-project
cd my-project

# Install all demo APIs
e2e install-demo --force
```

This creates:
- API servers in `demos/`
- Test services in `services/`

## Running Demos

### REST Demo (Port 5000)

```bash
python demos/rest/api-rest-demo.py
```

**Endpoints:**
- `GET /health` - Health check
- `GET /api/users` - List users
- `POST /api/users` - Create user

### Auth/JWT Demo (Port 5003)

```bash
pip install pyjwt cryptography
python demos/auth/api-auth-demo.py
```

**Features:**
- JWT Bearer token authentication
- Default users: admin/admin123, user/user123

### gRPC Demo (Port 50051)

```bash
pip install grpcio grpcio-tools
python demos/grpc/api-grpc-demo.py
```

### WebSocket Demo (Port 50052)

```bash
pip install aiohttp
python demos/websocket/api-websocket-demo.py
```

### E-commerce Demo (Port 5004)

```bash
pip install fastapi uvicorn sqlalchemy
python demos/ecommerce/api-ecommerce-demo.py
```

**Features:**
- Product catalog
- Shopping cart
- Checkout flow
- Inventory management

**Endpoints:**
- `GET /api/products` - List products
- `POST /api/cart` - Add to cart
- `POST /api/checkout` - Process order
- `POST /api/payment` - Process payment

### Chat Demo (Port 5005)

```bash
python demos/chat/api-chat-demo.py
```

**Features:**
- User presence
- Chat rooms
- Messages and threads
- Reactions

**Endpoints:**
- `POST /api/auth` - Authenticate
- `GET /api/rooms` - List rooms
- `POST /api/messages` - Send message
- `POST /api/reactions` - Add reaction

### Booking Demo (Port 5006)

```bash
python demos/booking/api-booking-demo.py
```

**Features:**
- Service listing
- Availability checking
- Appointment booking
- Waitlist management

**Endpoints:**
- `GET /api/services` - List services
- `GET /api/availability` - Check availability
- `POST /api/appointments` - Create booking
- `POST /api/appointments/{id}/cancel` - Cancel

### Notifications Demo (Port 5007)

```bash
python demos/notifications/api_notifications_demo.py
```

**Features:**
- Multi-channel notifications (email, SMS, push, webhook)
- Notification templates
- Webhook registration
- Scheduled notifications

**Endpoints:**
- `POST /api/notifications` - Send notification
- `GET /api/notifications` - List notifications
- `POST /api/templates` - Create template
- `POST /api/webhooks` - Register webhook

## Testing with Demos

Each demo includes corresponding test services:

```bash
# Run tests for a specific demo
e2e run --service demo-api
e2e run --service ecommerce-demo
e2e run --service chat-demo
e2e run --service booking-demo
e2e run --service notifications-demo
```

## Service Pages

Each demo has a service page file in `services/<demo-name>/`:

```python
# services/ecommerce-demo/ecommerce_page.py
from socialseed_e2e.core import BasePage

class EcommercePage(BasePage):
    """Service page for e-commerce demo API."""
    
    def list_products(self, **kwargs):
        return self.get("/api/products", **kwargs)
    
    def add_to_cart(self, product_id, quantity=1, **kwargs):
        return self.post("/api/cart", json={"product_id": product_id, "quantity": quantity}, **kwargs)
```

## Extending Demos

To add a new demo:

1. Create API server template in `src/socialseed_e2e/templates/api_<name>_demo.py.template`
2. Create service page template in `src/socialseed_e2e/templates/<name>_service_page.py.template`
3. Add demo to `DEMO_SERVICES` in `src/socialseed_e2e/commands/install_demo_cmd.py`
4. Run `e2e install-demo --force` to generate files

## Dependencies

Some demos require additional dependencies:

```bash
# Core dependencies
pip install socialseed-e2e

# Optional for all HTTP demos
pip install fastapi uvicorn sqlalchemy

# Auth demo
pip install pyjwt cryptography

# gRPC demo
pip install grpcio grpcio-tools

# WebSocket demo
pip install aiohttp
```
