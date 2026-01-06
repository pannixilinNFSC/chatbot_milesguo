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
    with patch("lib.search.elastic_mix.ElasticReadClientTitles") as title_cls, \
         patch("lib.search.elastic_mix.ElasticReadClientChunks") as chunk_cls:
        # Async clients so that awaited methods behave like real async calls
        title_client = AsyncMock()
        chunk_client = AsyncMock()
        title_cls.return_value = title_client
        chunk_cls.return_value = chunk_client

        # Default return values used by many tests
        chunk_client.search_chunks_naive = AsyncMock(return_value=[
            {"doc_id": "doc1", "chunk_id": "chunk1", "text": "test1", "score": 0.9}
        ])
        title_client.search_title_naive = AsyncMock(return_value=[
            {"doc_id": "doc1", "chunk_id": "chunk2", "text": "test2", "score": 0.8}
        ])
        
        from lib.search.elastic_mix import ElasticMix
        
        elastic_mix = ElasticMix()
        yield elastic_mix, title_client, chunk_client, title_cls, chunk_cls




@pytest.mark.asyncio
async def test_search_naive_delegates_to_elastic_2steps(elastic_mix_with_mocks):
    """Test that search_naive correctly delegates to chunk search client."""
    elastic_mix, _title_client, chunk_client, *_ = elastic_mix_with_mocks
    results = await elastic_mix.search_naive("test query", "chunk_index", chunk_k=5)
    
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk1"
    chunk_client.search_chunks_naive.assert_called_once_with(
        "test query", "chunk_index", k=5, doc_ids=None
    )


@pytest.mark.asyncio
async def test_search_2steps_delegates_to_elastic_2steps(elastic_mix_with_mocks):
    """Test that search_2steps correctly delegates to title and chunk clients."""
    elastic_mix, title_client, chunk_client, *_ = elastic_mix_with_mocks
    results = await elastic_mix.search_2steps(
        "test query", "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk1"
    title_client.search_title_naive.assert_called_once_with(
        "test query", "title_index", k=3
    )
    chunk_client.search_chunks_naive.assert_called_once_with(
        "test query", "chunk_index", k=5, doc_ids=["doc1"]
    )


@pytest.mark.asyncio
async def test_search_combines_naive_and_2steps_results(elastic_mix_with_mocks):
    """Test that search combines results from both search_naive and search_2steps."""
    elastic_mix, title_client, chunk_client, *_ = elastic_mix_with_mocks
    
    # Setup mocks to return different results for naive and 2-step paths.
    chunk_client.search_chunks_naive = AsyncMock(side_effect=[
        [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "naive1", "score": 0.9}],
        [{"doc_id": "doc2", "chunk_id": "chunk2", "text": "steps1", "score": 0.8}],
    ])
    title_client.search_title_naive = AsyncMock(return_value=[
        {"doc_id": "doc2", "chunk_id": "chunk2"}
    ])
    
    results = await elastic_mix.search(
        ["query1"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    assert len(results) == 2
    assert any(r["chunk_id"] == "chunk1" for r in results)
    assert any(r["chunk_id"] == "chunk2" for r in results)


@pytest.mark.asyncio
async def test_search_handles_multiple_queries(elastic_mix_with_mocks):
    """Test that search processes multiple queries in parallel."""
    elastic_mix, title_client, chunk_client, *_ = elastic_mix_with_mocks
    
    # Setup mocks to return different results for different calls
    # Use side_effect to return different values for each call
    # First two calls: naive search for query1 and query2
    # Next two calls: 2-step search for query1 and query2
    chunk_client.search_chunks_naive = AsyncMock(side_effect=[
        [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "naive1", "score": 0.9}],
        [{"doc_id": "doc3", "chunk_id": "chunk3", "text": "naive2", "score": 0.85}],
        [{"doc_id": "doc2", "chunk_id": "chunk2", "text": "steps1", "score": 0.8}],
        [{"doc_id": "doc4", "chunk_id": "chunk4", "text": "steps2", "score": 0.75}],
    ])
    title_client.search_title_naive = AsyncMock(side_effect=[
        [{"doc_id": "doc2", "chunk_id": "chunk2"}],
        [{"doc_id": "doc4", "chunk_id": "chunk4"}],
    ])
    
    results = await elastic_mix.search(
        ["query1", "query2"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    # Should have 2 queries * 2 search methods = 4 results
    assert len(results) == 4
    # 2 naive + 2 chunk searches in the second step
    assert chunk_client.search_chunks_naive.call_count == 4
    assert title_client.search_title_naive.call_count == 2


@pytest.mark.asyncio
async def test_search_deduplicates_results(elastic_mix_with_mocks):
    """Test that search deduplicates results by doc_id and chunk_id."""
    elastic_mix, title_client, chunk_client, *_ = elastic_mix_with_mocks
    
    # Setup mocks to return duplicate results
    chunk_client.search_chunks_naive = AsyncMock(side_effect=[
        [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "duplicate", "score": 0.9}],
        [{"doc_id": "doc1", "chunk_id": "chunk1", "text": "duplicate", "score": 0.8}],
    ])
    title_client.search_title_naive = AsyncMock(return_value=[
        {"doc_id": "doc1", "chunk_id": "chunk1"}
    ])
    
    results = await elastic_mix.search(
        ["query1"], "title_index", "chunk_index", title_k=3, chunk_k=5
    )
    
    # Should deduplicate to 1 result
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["chunk_id"] == "chunk1"



def test_deduplicate_search_results_preserves_critical_fields(elastic_mix_with_mocks):
    """Test that deduplicate_search_results preserves critical display fields."""
    elastic_mix, *_ = elastic_mix_with_mocks
    
    results = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "doc_title": "Title1", "index": "idx1", "score": 0.9, "text": "text1"},
        {"doc_id": "doc1", "chunk_id": "chunk2", "doc_title": "Title2", "index": "idx2", "score": 0.8, "text": "text2"},
    ]
    
    deduped = elastic_mix.postprocess_search_results(results)
    
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
    
    deduped = elastic_mix.postprocess_search_results(results)
    
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
    
    deduped = elastic_mix.postprocess_search_results(results)
    
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
    deduped = elastic_mix.postprocess_search_results(results)
    
    assert len(deduped) == 2


@pytest.mark.asyncio
async def test_search_neighbour_chunks_delegates_to_chunk_client(elastic_mix_with_mocks):
    """search_neighbour_chunks should delegate to chunk client's get_neighbour_chunks."""
    elastic_mix, _title_client, chunk_client, *_ = elastic_mix_with_mocks

    chunk_client.get_neighbour_chunks = AsyncMock(return_value=[
        {"doc_id": "doc1", "chunk_id": "c1"},
        {"doc_id": "doc1", "chunk_id": "c2"},
    ])

    results = await elastic_mix.search_neighbour_chunks(
        doc_id="doc1",
        chunk_id="c1",
        chunk_index="chunk_index",
        distance=2,
    )

    chunk_client.get_neighbour_chunks.assert_called_once_with(
        "chunk_index", "doc1", "c1", 2
    )
    assert len(results) == 2
    assert results[0]["chunk_id"] == "c1"


@pytest.mark.asyncio
async def test_search_ops_routes_to_all_operation_types(elastic_mix_with_mocks):
    """search_ops should route ops to the correct internal search methods and merge results."""
    elastic_mix, *_ = elastic_mix_with_mocks

    # Replace internal methods with async mocks
    elastic_mix.search_1step_and_2steps = AsyncMock(return_value=[
        {"doc_id": "doc1", "chunk_id": "g1"},
    ])
    elastic_mix.search_naive = AsyncMock(return_value=[
        {"doc_id": "doc2", "chunk_id": "d1"},
    ])
    elastic_mix.search_neighbour_chunks = AsyncMock(return_value=[
        {"doc_id": "doc3", "chunk_id": "n1"},
    ])

    ops = [
        {"type": "search_general", "query_list": ["q1"]},
        {"type": "search_doc", "query": "q2"},
        {"type": "search_neighbour_chunks", "doc_id": "doc3", "chunk_id": "n1"},
    ]

    results = await elastic_mix.search_ops(
        ops,
        title_index="titles",
        chunk_index="chunks",
        title_k=3,
        chunk_k=5,
    )

    # All three operations should have been called once
    assert elastic_mix.search_1step_and_2steps.await_count == 1
    assert elastic_mix.search_naive.await_count == 1
    assert elastic_mix.search_neighbour_chunks.await_count == 1
    # And results should be merged in order
    assert {r["chunk_id"] for r in results} == {"g1", "d1", "n1"}


def test_postprocess_search_results_adds_sequential_index(elastic_mix_with_mocks):
    """postprocess_search_results should add a 1-based sequential index field to each result."""
    elastic_mix, *_ = elastic_mix_with_mocks

    results = [
        {"doc_id": "d1", "chunk_id": "c1", "text": "a"},
        {"doc_id": "d2", "chunk_id": "c2", "text": "b"},
    ]

    deduped = elastic_mix.postprocess_search_results(results)

    assert [r["index"] for r in deduped] == [1, 2]

