import pytest
import asyncio
from unittest.mock import Mock, patch

@pytest.fixture
def mock_alpaca_client():
    with patch('alpaca.trading.client.TradingClient') as mock:
        yield mock

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()