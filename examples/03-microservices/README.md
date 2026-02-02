# 🏗️ Microservices Example

A complete microservices architecture example with 3 interacting services: Users, Orders, and Payments.

## Overview

This example demonstrates testing in a microservices environment where services communicate with each other via HTTP APIs. Perfect for learning how to test distributed systems and service dependencies.

### Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Users Service  │◄────►│  Orders Service │◄────►│ Payment Service │
│   (Port 5002)   │      │   (Port 5003)   │      │   (Port 5004)   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                        │                        │
        │                        │                        │
        └────────────────────────┴────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │    E2E Test Suite       │
                    │  (socialseed-e2e)       │
                    └─────────────────────────┘
```

## 📋 Services Description

### 1. Users Service (Port 5002)
**Responsibility**: User management and balance tracking

**Endpoints**:
- `GET /api/users` - List all users
- `GET /api/users/{id}` - Get user by ID
- `GET /api/users/{id}/balance` - Get user balance
- `POST /api/users/{id}/balance` - Update balance (used by Payment Service)
- `POST /api/users` - Create new user
- `GET /health` - Health check

**Database**: `users.db` (SQLite)

**Pre-loaded Data**: 3 users with balances:
- alice: $500.00
- bob: $300.00
- charlie: $150.00

### 2. Orders Service (Port 5003)
**Responsibility**: Order management

**Endpoints**:
- `GET /api/orders` - List all orders
- `POST /api/orders` - Create order (validates user via Users Service)
- `GET /api/orders/{id}` - Get order by ID
- `PUT /api/orders/{id}/status` - Update order status
- `GET /api/users/{id}/orders` - Get user's orders
- `GET /health` - Health check

**Dependencies**: Users Service

**Database**: `orders.db` (SQLite)

### 3. Payment Service (Port 5004)
**Responsibility**: Payment processing and balance management

**Endpoints**:
- `GET /api/payments` - List all payments
- `POST /api/payments` - Process payment (depends on Users & Orders)
- `GET /api/payments/{id}` - Get payment by ID
- `GET /api/users/{id}/payments` - Get user's payments
- `POST /api/refund` - Refund a payment
- `GET /health` - Health check

**Dependencies**: Users Service, Orders Service

**Database**: `payments.db` (SQLite)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd examples/03-microservices
pip install -r requirements.txt
```

### 2. Start Services

**Option A: Manual (one terminal per service)**

Terminal 1:
```bash
cd users-service
python users_api.py
```

Terminal 2:
```bash
cd orders-service
python orders_api.py
```

Terminal 3:
```bash
cd payment-service
python payment_api.py
```

**Option B: Background (single terminal)**
```bash
cd users-service && python users_api.py > /tmp/users.log 2>&1 &
cd orders-service && python orders_api.py > /tmp/orders.log 2>&1 &
cd payment-service && python payment_api.py > /tmp/payment.log 2>&1 &
```

### 3. Verify Services

```bash
# Check health of all services
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
```

### 4. Run E2E Tests

```bash
e2e run
```

Should show **3 services detected** with tests.

### ⚠️ Current Status (v0.1.0)

Test execution is in **placeholder mode**. The test modules will be detected but not fully executed until v0.2.0.

## 🔄 Service Dependencies

### Startup Order
1. **Users Service** (start first - no dependencies)
2. **Orders Service** (depends on Users Service)
3. **Payment Service** (depends on both Users and Orders)

### Communication Flow

**Create Order Flow**:
```
Client → Orders Service → Users Service (validate user)
                    ↓
              Order Created
```

**Payment Flow**:
```
Client → Payment Service → Orders Service (get order)
                    ↓
         Payment Service → Users Service (check/deduct balance)
                    ↓
              Payment Completed
                    ↓
         Payment Service → Orders Service (update status)
```

## 🧪 Testing Service Communication

### Test 1: Create Order (Service Communication)

```bash
# Create order for user alice (ID: 1)
curl -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "items": ["Laptop", "Mouse"],
    "total_amount": 999.99
  }'
```

**What happens**:
1. Orders Service receives request
2. Calls Users Service to validate user_id=1 exists
3. Creates order in orders.db
4. Returns order data

### Test 2: Process Payment (Multi-Service)

```bash
# Process payment for order
curl -X POST http://localhost:5004/api/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "user_id": 1
  }'
```

**What happens**:
1. Payment Service receives request
2. Calls Orders Service to get order details
3. Calls Users Service to get user balance
4. If sufficient funds, deducts balance via Users Service
5. Creates payment record
6. Updates order status via Orders Service
7. Returns payment confirmation

### Test 3: Check User Balance (After Payment)

```bash
curl http://localhost:5002/api/users/1/balance
```

Should show reduced balance after payment.

### Test 4: View User's Orders and Payments

```bash
# Get alice's orders
curl http://localhost:5003/api/users/1/orders

# Get alice's payments
curl http://localhost:5004/api/users/1/payments
```

## 📊 e2e.conf Configuration

The configuration defines all 3 services:

```yaml
services:
  users-service:
    base_url: http://localhost:5002
    required: true

  orders-service:
    base_url: http://localhost:5003
    required: true

  payment-service:
    base_url: http://localhost:5004
    required: true
```

## 🎓 Learning Outcomes

After this example, you'll understand:

1. ✅ Microservices architecture and communication
2. ✅ Service dependencies and startup order
3. ✅ HTTP-based service-to-service communication
4. ✅ Testing distributed systems
5. ✅ Health checks and service discovery
6. ✅ Transaction management across services
7. ✅ Circuit breaker patterns (basic)

## 🐛 Troubleshooting

### Services can't communicate

**Problem**: Orders Service can't reach Users Service
**Solution**: Ensure all services are running on correct ports:
- Users: 5002
- Orders: 5003
- Payment: 5004

### Port already in use

Change port in the service file:
```python
app.run(host='0.0.0.0', port=5005, debug=True)  # Use different port
```

Update `e2e.conf` accordingly.

### Database locked errors

Stop all services and delete .db files:
```bash
pkill -f users_api.py
pkill -f orders_api.py
pkill -f payment_api.py
rm -f users-service/users.db orders-service/orders.db payment-service/payments.db
```

Then restart services.

### Health check shows "unavailable"

This is normal if a dependent service hasn't started yet. Start services in order:
1. Users Service first
2. Orders Service second
3. Payment Service last

## 🐳 Docker Compose (Optional)

If you have Docker installed, you can use Docker Compose to run all services:

```yaml
# docker-compose.yml
version: '3.8'

services:
  users-service:
    build: ./users-service
    ports:
      - "5002:5002"

  orders-service:
    build: ./orders-service
    ports:
      - "5003:5003"
    depends_on:
      - users-service

  payment-service:
    build: ./payment-service
    ports:
      - "5004:5004"
    depends_on:
      - users-service
      - orders-service
```

Run with:
```bash
docker-compose up -d
```

## 📚 Next Steps

- Add authentication between services (API keys/JWT)
- Implement circuit breaker pattern
- Add message queue (RabbitMQ/Redis) for async processing
- Implement service mesh (Istio/Linkerd)
- Add distributed tracing (Jaeger/Zipkin)

## 🔗 Example Workflow

Complete e-commerce flow:

```bash
# 1. Check alice's initial balance
curl http://localhost:5002/api/users/1
# Shows: balance $500

# 2. Create order
curl -X POST http://localhost:5003/api/orders \
  -d '{"user_id": 1, "items": ["Phone"], "total_amount": 299.99}'
# Returns: order_id: 1

# 3. Process payment
curl -X POST http://localhost:5004/api/payments \
  -d '{"order_id": 1, "user_id": 1}'
# Deducts $299.99 from alice's balance

# 4. Check updated balance
curl http://localhost:5002/api/users/1/balance
# Shows: balance $200.01

# 5. Check order status
curl http://localhost:5003/api/orders/1
# Shows: status "confirmed"
```

---

**Happy Microservices Testing!** 🏗️
