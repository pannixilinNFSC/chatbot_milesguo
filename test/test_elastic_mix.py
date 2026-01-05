"""
Unit tests for ElasticMix class.
All external dependencies (Elasticsearch) are mocked.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import copy


@pytest.fixture
def elastic_mix_with_mocks():
    """
    Build an ElasticMix with all external dependencies mocked.

    Motivation: avoid repeating the same patch boilerplate in every test.
    """
    with patch("lib.search.elastic_mix.Elastic2Steps") as elastic_cls:
        elastic_2steps = AsyncMock()
        elastic_2steps.search_naive.return_value = [
            {"doc_id": "doc1", "chunk_id": "chunk1", "text": "test1", "score": 0.9}
        ]
        elastic_2steps.search_2steps.return_value = [
            {"doc_id": "doc1", "chunk_id": "chunk2", "text": "test2", "score": 0.8}
        ]
        elastic_cls.return_value = elastic_2steps

        from lib.search.elastic_mix import ElasticMix

        elastic_mix = ElasticMix()
        yield elastic_mix, elastic_2steps, elastic_cls




@pytest.mark.asyncio
async def test_search_naive_delegates_to_elastic_2steps(elastic_mix_with_mocks):
    """Test that search_naive correctly delegates to Elastic2Steps."""
    elastic_mix, elastic_2steps, _ = elastic_mix_with_mocks
    results = await elastic_mix.search_naive("test query", "chunk_index", chunk_k=5)
    
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk1"
    elastic_2steps.search_naive.assert_called_once_with("test query", "chunk_index", k=5)


@pytest.mark.asyncio
async def test_search_2steps_delegates_to_elastic_2steps(elastic_mix_with_mocks):
    """Test that search_2steps correctly delegates to Elastic2Steps."""
    elastic_mix, elastic_2steps, _ = elastic_mix_with_mocks
    results = await elastic_mix.search_2steps(
        "test query", "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk2"
    elastic_2steps.search_2steps.assert_called_once_with(
        "test query", "title_index", "chunk_index", title_k=3, chunk_k=5
    )


@pytest.mark.asyncio
async def test_search_combines_naive_and_2steps_results(elastic_mix_with_mocks):
    """Test that search combines results from both search_naive and search_2steps."""
    elastic_mix, elastic_2steps, _ = elastic_mix_with_mocks
    
    # Setup mocks to return different results
    elastic_2steps.search_naive.return_value = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "naive1", "score": 0.9}
    ]
    elastic_2steps.search_2steps.return_value = [
        {"doc_id": "doc2", "chunk_id": "chunk2", "text": "steps1", "score": 0.8}
    ]
    
    results = await elastic_mix.search(
        ["query1"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    assert len(results) == 2
    assert any(r["chunk_id"] == "chunk1" for r in results)
    assert any(r["chunk_id"] == "chunk2" for r in results)


@pytest.mark.asyncio
async def test_search_handles_multiple_queries(elastic_mix_with_mocks):
    """Test that search processes multiple queries in parallel."""
    elastic_mix, elastic_2steps, _ = elastic_mix_with_mocks
    
    # Setup mocks to return different results for different calls
    # Use side_effect to return different values for each call
    elastic_2steps.search_naive.side_effect = [
        [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "naive1", "score": 0.9}],
        [{"doc_id": "doc3", "chunk_id": "chunk3", "text": "naive2", "score": 0.85}]
    ]
    elastic_2steps.search_2steps.side_effect = [
        [{"doc_id": "doc2", "chunk_id": "chunk2", "text": "steps1", "score": 0.8}],
        [{"doc_id": "doc4", "chunk_id": "chunk4", "text": "steps2", "score": 0.75}]
    ]
    
    results = await elastic_mix.search(
        ["query1", "query2"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    # Should have 2 queries * 2 search methods = 4 results
    assert len(results) == 4
    assert elastic_2steps.search_naive.call_count == 2
    assert elastic_2steps.search_2steps.call_count == 2


@pytest.mark.asyncio
async def test_search_deduplicates_results(elastic_mix_with_mocks):
    """Test that search deduplicates results by doc_id and chunk_id."""
    elastic_mix, elastic_2steps, _ = elastic_mix_with_mocks
    
    # Setup mocks to return duplicate results
    elastic_2steps.search_naive.return_value = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "duplicate", "score": 0.9}
    ]
    elastic_2steps.search_2steps.return_value = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "duplicate", "score": 0.8}
    ]
    
    results = await elastic_mix.search(
        ["query1"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    # Should deduplicate to 1 result
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk1"


def test_deduplicate_search_results_removes_duplicate_ids(elastic_mix_with_mocks):
    """Test that deduplicate_search_results removes results with duplicate doc_id+chunk_id."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "text1", "score": 0.9},
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "text1", "score": 0.8},
        {"doc_id": "doc1", "chunk_id": "chunk2", "text": "text2", "score": 0.7},
    ]
    
    deduped = elastic_mix.deduplicate_search_results(results)
    
    assert len(deduped) == 2
    assert deduped[0]["chunk_id"] == "chunk1"
    assert deduped[1]["chunk_id"] == "chunk2"


def test_deduplicate_search_results_preserves_critical_fields(elastic_mix_with_mocks):
    """Test that deduplicate_search_results preserves critical display fields."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "doc_title": "Title1", "index": "idx1", "score": 0.9, "text": "text1"},
        {"doc_id": "doc1", "chunk_id": "chunk2", "doc_title": "Title2", "index": "idx2", "score": 0.8, "text": "text2"},
    ]
    
    deduped = elastic_mix.deduplicate_search_results(results)
    
    assert len(deduped) == 2
    for result in deduped:
        assert "doc_id" in result
        assert "chunk_id" in result
        assert "doc_title" in result
        assert "index" in result
        assert "score" in result


def test_deduplicate_search_results_removes_duplicate_field_values(elastic_mix_with_mocks):
    """Test that deduplicate_search_results removes duplicate field values from later results."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "unique1", "metadata": {"key": "value1"}},
        {"doc_id": "doc2", "chunk_id": "chunk2", "text": "unique1", "metadata": {"key": "value1"}},
    ]
    
    deduped = elastic_mix.deduplicate_search_results(results)
    
    assert len(deduped) == 2
    # First result should keep all fields
    assert "text" in deduped[0]
    assert "metadata" in deduped[0]
    # Second result should have duplicate fields removed
    assert "text" not in deduped[1]
    assert "metadata" not in deduped[1]


def test_deduplicate_search_results_handles_json_serialization(elastic_mix_with_mocks):
    """Test that deduplicate_search_results handles complex nested structures via JSON serialization."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "nested": {"a": 1, "b": [1, 2, 3]}},
        {"doc_id": "doc2", "chunk_id": "chunk2", "nested": {"a": 1, "b": [1, 2, 3]}},
    ]
    
    deduped = elastic_mix.deduplicate_search_results(results)
    
    assert len(deduped) == 2
    # Second result should have the duplicate nested field removed
    assert "nested" not in deduped[1]


def test_deduplicate_search_results_handles_non_serializable_fields(elastic_mix_with_mocks):
    """Test that deduplicate_search_results gracefully handles non-serializable field values."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    # Create a non-serializable object (function)
    def non_serializable():
        pass
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "text1"},
        {"doc_id": "doc2", "chunk_id": "chunk2", "text": "text2", "func": non_serializable},
    ]
    
    # Should not raise an exception
    deduped = elastic_mix.deduplicate_search_results(results)
    
    assert len(deduped) == 2

