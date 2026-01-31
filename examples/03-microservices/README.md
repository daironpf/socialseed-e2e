# Microservices Example

This example demonstrates testing multiple interacting microservices.

## Running the Example

```bash
cd examples/03-microservices
docker-compose up -d
# or run services manually
python service_a.py &
python service_b.py &
e2e run
```

## Architecture

- **Service A**: User management
- **Service B**: Order processing
- Communication via HTTP API

## Tests Included

1. Create user in Service A
2. Create order in Service B (references user)
3. Verify order in Service A
4. End-to-end workflow test

## Key Concepts

- Multi-service configuration
- Service dependencies
- Orchestrated testing

See the `tests/` directory for implementation details.
