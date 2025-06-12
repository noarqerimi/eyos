# NewStore to Hail API Integration

This project integrates NewStore's Order Lifecycle webhooks with eyos' Hail API for real-time transaction processing.

## Architecture Overview

The integration follows an event-driven architecture with the following components:

1. **Webhook Receiver**: FastAPI endpoints that receive NewStore order events via webhooks
2. **Data Transformer**: Service that transforms NewStore data format to Hail API format
3. **Hail API Client**: Service that sends transformed data to the Hail API with retry logic
4. **Queue Processor**: In-memory queue (simulating a message broker) for asynchronous processing

### Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  NewStore   │    │   Webhook   │    │   Queue     │    │   Hail API  │
│   System    │───▶│  Receiver   │───▶│  Processor  │───▶│   Client    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                  │
                          ▼                  ▼                  ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │  Signature  │    │    Data     │    │  Retry &    │
                   │  Validation │    │ Transformer │    │Error Handling│
                   └─────────────┘    └─────────────┘    └─────────────┘
```

### Key Features

- **Async Processing**: Uses FastAPI's async capabilities and background tasks
- **Retry Logic**: Implements exponential backoff with jitter for API failures
- **Validation**: Validates incoming webhooks (signature and payload)
- **Modular Design**: Clear separation of concerns with dedicated modules
- **Testing**: Comprehensive test coverage for core components
- **Extensibility**: Easy to extend for new event types or API versions

## How to Run

### Prerequisites

- Python 3.9+
- [Rye](https://rye-up.com/) (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies with Rye:
   ```bash
   rye sync
   ```

3. Run the development server:
   ```bash
   rye run dev
   ```

4. The API will be available at http://localhost:8000

### Available Scripts

The project includes several Rye scripts for common tasks:

- `rye run dev` - Start the development server with hot reload
- `rye run start` - Start the server in production mode
- `rye run test` - Run all tests
- `rye run test-cov` - Run tests with coverage report
- `rye run simulate` - Simulate a webhook event using the default payload
- `rye run simulate-newstore` - Simulate a NewStore webhook event
- `rye run client-example` - Run the example API client
- `rye run pre-commit run -a` - Run pre-commit



### API Endpoints

- `POST /webhooks/newstore`: Main webhook endpoint for receiving NewStore events
- `POST /webhooks/newstore/simulate`: Development endpoint for simulating webhook events
- `POST /mock/hail/events/v2/transaction/`: Mock Hail API endpoint for testing

## Examples

The project includes example code in the `examples/` directory:

- `api_client.py` - An example client that demonstrates how to interact with the API programmatically

To run the example client:
```bash
rye run client-example
```

## Assumptions and Limitations

### Assumptions

1. **NewStore Webhooks**: The solution assumes NewStore sends webhooks for completed orders with a specific JSON structure.
2. **Hail API**: The solution assumes the Hail API expects transactions in the format provided in the sample payload.
3. **Signature Validation**: A mock implementation is provided, but would need to be updated with the actual signature format used by NewStore.
4. **Data Mapping**: Several assumptions are made in mapping data between the systems, which would need to be validated with actual business requirements.

### Limitations

1. **In-Memory Queue**: Uses an in-memory queue for simplicity. In production, this would be replaced with a proper message broker like RabbitMQ or Kafka.
2. **Limited Event Types**: Currently only supports the `order.completed` event type.
3. **Minimal Error Recovery**: Basic retry logic is implemented, but a production system would need more sophisticated error recovery (dead letter queues, monitoring, etc.).
4. **No Persistence**: Events are not persisted, so if the service crashes, in-flight events might be lost.

## Future Improvements

1. **Message Broker**: Replace the in-memory queue with a proper message broker
2. **Persistence**: Add a database to track event processing status
3. **Monitoring**: Add metrics and monitoring for system health
4. **Versioning**: Implement explicit API versioning for both webhook and Hail API endpoints
5. **Encryption**: Add support for encrypted payloads
6. **Multiple Tenants**: Enhance to support multiple tenants with different configurations
7. **Contract Testing**: Add contract tests to validate against API specifications
8. **Deployment**: Add containerization and deployment configurations
