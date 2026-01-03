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
         patch("lib.rag.rag_base.PROMPT_BASE", mock_prompt_base), \
         patch("lib.rag.rag_base.Elastic2Steps") as elastic_cls, \
         patch("lib.rag.rag_base.QueryExpander") as expander_cls:
        elastic = AsyncMock()
        elastic.search_naive.return_value = [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "test"}]
        elastic.search_2steps.return_value = [{"doc_id": "doc1", "chunk_id": "chunk2", "text": "test2"}]
        elastic_cls.return_value = elastic

        expander = AsyncMock()
        expander.expand.return_value = ["expanded query"]
        expander_cls.return_value = expander

        from lib.rag.rag_base import RAGBase

        rag = RAGBase(title_index="test_titles", chunk_index="test_chunks")
        yield rag, elastic, expander, elastic_cls, expander_cls


def test_init_sets_prompt_and_deps(rag_with_mocks):
    rag, _elastic, _expander, elastic_cls, expander_cls = rag_with_mocks
    assert rag.prompt_before == "Test prompt before"
    assert rag.prompt_after == "Test prompt after"
    elastic_cls.assert_called_once_with("test_titles", "test_chunks")
    expander_cls.assert_called_once()


@pytest.mark.asyncio
async def test_search_expands_for_short_query(rag_with_mocks):
    rag, _elastic, expander, *_ = rag_with_mocks
    _results, expanded = await rag.search("test", title_k=3, chunk_k=10, expand_query=True)
    assert expanded == ["expanded query"]
    expander.expand.assert_called_once()


def test_deduplicate_search_results_removes_duplicate_ids(rag_with_mocks):
    rag, *_ = rag_with_mocks
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "text1"},
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "text1"},
        {"doc_id": "doc1", "chunk_id": "chunk2", "text": "text2"},
    ]
    deduped = rag.deduplicate_search_results(results)
    assert len(deduped) == 2


@pytest.mark.asyncio
async def test_chat_calls_llm_and_returns_prompt(rag_with_mocks):
    rag, _elastic, _expander, *_ = rag_with_mocks
    with patch("lib.rag.rag_base.call_llm_with_fallback", return_value="Test LLM response") as llm:
        content, search_results, prompt = await rag.chat("test query", title_k=3, chunk_k=10, expand_query=False)

    assert content == "Test LLM response"
    assert isinstance(search_results, list)
    assert isinstance(prompt, str)
    assert "test query" in prompt
    llm.assert_called_once()

