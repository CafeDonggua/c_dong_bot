import os

import pytest
from openai import NotFoundError, PermissionDeniedError

from dongdong_bot.config import SEARCH_MODEL
from dongdong_bot.lib.search_client import SearchClient


def test_real_web_search_keyword():
    if os.getenv("REAL_SEARCH_TEST", "").strip() not in {"1", "true", "yes", "on"}:
        pytest.skip("Set REAL_SEARCH_TEST=1 to run live web search test.")
    api_key = os.getenv("OPENAI_SEARCH_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Missing OPENAI_SEARCH_API_KEY or OPENAI_API_KEY for live test.")
    model = os.getenv("SEARCH_MODEL", "").strip() or SEARCH_MODEL
    client = SearchClient(api_key=api_key, model=model)

    try:
        response = client.search_keyword("Example Domain")
    except (NotFoundError, PermissionDeniedError):
        pytest.skip("Search model not available for this API key.")

    assert response.sources, "Expected at least one source URL from web search."
