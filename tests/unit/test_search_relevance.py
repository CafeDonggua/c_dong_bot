from dongdong_bot.lib.search_schema import SearchResponse
from dongdong_bot.main import _search_result_relevant


def test_search_relevance_detects_related_result():
    response = SearchResponse(
        summary="台灣新核能政策近期有多項討論。",
        bullets=["台灣能源轉型", "核能議題升溫"],
        sources=[],
    )
    assert _search_result_relevant("台灣新核能", response) is True


def test_search_relevance_detects_unrelated_result():
    response = SearchResponse(
        summary="OpenAI 是一家人工智慧公司。",
        bullets=["產品包含 ChatGPT", "與核能無直接關係"],
        sources=[],
    )
    assert _search_result_relevant("台灣新核能", response) is False
