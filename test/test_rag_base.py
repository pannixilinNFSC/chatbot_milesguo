"""
Unit tests for RAGBase class.
All external dependencies (Elasticsearch, LiteLLM) are mocked.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json


@pytest.fixture
def mock_prompt_base():
    """Mock prompt.py PROMPT_BASE content."""
    return {
        "prompt1": "Test prompt before",
        "prompt2": "Test prompt after"
    }

@pytest.fixture
def rag_with_mocks(mock_prompt_base):
    """
    Build a RAGBase with all external dependencies mocked.

    Motivation: avoid repeating the same patch boilerplate in every test.
    """
    # Mock router before any imports that might trigger it
    mock_router = AsyncMock()
    with patch("lib.llm.litellm_api.get_litellm_fallback_router", return_value=mock_router), \
         patch("lib.rag.rag_prompt.PROMPT_BASE", mock_prompt_base), \
         patch("lib.rag.rag_base.ElasticMix") as elastic_cls, \
         patch("lib.rag.rag_base.QueryExpander") as expander_cls:
        elastic_mix = AsyncMock()
        elastic_mix.search.return_value = [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "test"}]
        elastic_cls.return_value = elastic_mix

        expander = AsyncMock()
        expander.expand.return_value = ["expanded query"]
        expander_cls.return_value = expander

        from lib.rag.rag_base import RAGBase

        rag = RAGBase()
        yield rag, elastic_mix, expander, elastic_cls, expander_cls


def test_init_sets_prompt_and_deps(rag_with_mocks):
    rag, _elastic, _expander, elastic_cls, expander_cls = rag_with_mocks
    assert rag.prompt_before == "Test prompt before"
    assert rag.prompt_after == "Test prompt after"
    elastic_cls.assert_called_once()
    expander_cls.assert_called_once()


@pytest.mark.asyncio
async def test_search_expands_for_short_query(rag_with_mocks):
    rag, _elastic, expander, *_ = rag_with_mocks
    _results, expanded = await rag.search("test", title_index="test_titles", chunk_index="test_chunks", title_k=3, chunk_k=10, query_expand_k=1)
    assert expanded == ["expanded query"]
    expander.expand.assert_called_once()


@pytest.mark.asyncio
async def test_chat_calls_llm_and_returns_prompt(rag_with_mocks):
    rag, _elastic, _expander, *_ = rag_with_mocks
    with patch("lib.rag.rag_base.call_llm_with_fallback", new_callable=AsyncMock, return_value="Test LLM response") as llm:
        result = await rag.chat("test query", title_index="test_titles", chunk_index="test_chunks", title_k=3, chunk_k=10, query_expand_k=0)

    assert result["content"] == "Test LLM response"
    assert isinstance(result["search_results"], list)
    assert isinstance(result["prompt"], str)
    assert "test query" in result["prompt"]
    llm.assert_called_once()

