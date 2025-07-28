# Tests Directory
This directory contains unit and integration tests for the AI Assistant.

## Running Tests:
```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=.
```

## Test Structure:
- `test_api/` - API endpoint tests
- `test_agents/` - Agent logic tests  
- `test_scraping/` - Web scraping tests
- `conftest.py` - Test configuration and fixtures