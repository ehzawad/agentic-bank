import pytest

from chatbot.config import settings


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: live Claude API tests (slow, costs money)")


def pytest_collection_modifyitems(config, items):
    if not settings.anthropic_api_key:
        skip = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
