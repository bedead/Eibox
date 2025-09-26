# Eibox

## Summary

Eibox (formerly ama.ai) is an intelligent system designed to completely handle emails. This assistant leverages AI to read, categorize, prioritize, and respond to emails, ensuring efficient email management. The goal is to reduce email overload and help users focus on important messages while automating routine tasks. The project is currently under development.

## Structure

- **app/**: Main application code
  - **api/**: API endpoints and routers
  - **core/**: Core configuration and middleware
  - **db/**: Database connections and repositories
  - **schemas/**: Pydantic models
  - **services/**: Business logic services
  - **utils/**: Utility functions
- **tests/**: Test directory (currently empty)
- **log_dump/**: Application logs
- **.github/**: GitHub workflows for CI/CD
- **venv/**: Python virtual environment

## Language & Runtime

**Language**: Python
**Version**: 3.11.9 (based on CI configuration)
**Package Manager**: pip

## Dependencies

**Main Dependencies**:

- fastapi: Web framework for building APIs
- uvicorn: ASGI server for FastAPI
- langchain: Framework for LLM applications
- groq: LLM provider client
- google-genai: Google Generative AI client
- pydantic: Data validation library
- redis: For caching and message broker
- APScheduler: Task scheduling
- google-api-python-client: Google API client

**Development Dependencies**:

- pytest: Testing framework
- pylint: Code linting
- pygount: Code metrics

## Build & Installation

```bash
# Create virtual environment
python -m venv venv
# Activate virtual environment (Windows)
.\venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Install development dependencies
pip install -r dev-requirements.txt
```

```bash
set API_ENVIRONMENT_TYPE=dev
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# or
fastapi run main:app
```

## API Structure

**Framework**: FastAPI
**Version**: v1
**Main Endpoints**:

- `/v1/auth`: Authentication endpoints
- `/v1/oauth`: OAuth integration with Gmail
- `/v1/chatbot`: WebSocket endpoints for chat functionality
- `/v1/cron`: Scheduler API endpoints (conditionally enabled)
- `/v1/test`: Testing endpoints

## Testing

**Framework**: pytest (E2E API Testing)
**Test Structure**: Comprehensive E2E test suite with mocked dependencies
**Configuration**:

- pytest.ini with coverage, timeout, and reporting settings
- conftest.py with fixtures and mocks for Redis, Google OAuth, and database operations
- Separate test files for different API endpoints and integration workflows

**Test Suites**:

- `test_auth_endpoints.py`: Authentication (register, login, update user data)
- `test_oauth_endpoints.py`: Gmail OAuth integration workflow
- `test_websocket_endpoints.py`: WebSocket chat functionality
- `test_utility_endpoints.py`: Health check and utility endpoints  
- `test_integration_workflows.py`: End-to-end user journeys and cross-endpoint interactions

**Run Commands**:

```bash
# Run all tests
pytest

# Run specific test suite
python tests/run_tests.py --suite auth
python tests/run_tests.py --suite oauth
python tests/run_tests.py --suite websocket
python tests/run_tests.py --suite integration

# Run with coverage and HTML report
python tests/run_tests.py --coverage --html-report

# Run tests in parallel
python tests/run_tests.py --parallel

# Install test dependencies
pip install -r tests/test_requirements.txt
```

**Test Features**:

- Mocked external dependencies (Redis, Google OAuth, database operations)
- WebSocket connection testing
- Concurrent user session testing
- Error handling and recovery testing
- Performance testing under simulated load
- Complete user onboarding workflow testing

## CI/CD

**Platform**: GitHub Actions
**Workflows**:

- pylint.yml: Runs linting on Python files
**Python Versions**: 3.10, 3.11
