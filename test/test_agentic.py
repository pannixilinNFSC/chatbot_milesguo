"""
Unit tests for agentic workflow.
All external dependencies (LiteLLM, ElasticMix) are mocked.
Reproduces tests from scripts/agentic.ipynb
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from lib.agentic.config import get_agent_state_default
from lib.agentic.graph import AgenticGraph


@pytest.fixture
def mock_call_llm_with_fallback():
    """
    Mock implementation of call_llm_with_fallback.
    Returns appropriate format based on response_format parameter.
    
    Motivation: simulate LLM responses for different node types without calling actual LLM APIs.
    """
    async def _mock_llm(prompt, model_name, response_format):
        # Entry LLM node: classify query and generate response
        if response_format and response_format.get("json_schema", {}).get("name") == "entry_response_format":
            prompt_lower = prompt.lower()
            
            # Extract question from prompt
            question = ""
            if "用户问题：" in prompt:
                question = prompt.split("用户问题：")[1].split("\n")[0].strip()
            question_lower = question.lower()
            
            # Classify based on keywords in the question (not the entire prompt)
            if any(word in question_lower for word in ["hello", "hi", "hey", "greetings"]) or "how are you" in question_lower:
                return {
                    "query_type": "greeting",
                    "answer": "Hello! How can I help you today?",
                    "expanded_queries": [question] if question else []
                }
            elif any(word in question_lower for word in ["stupid", "idiot", "dumb", "hate"]):
                return {
                    "query_type": "insult",
                    "answer": "I'm here to help in a respectful manner. How can I assist you?",
                    "expanded_queries": [question] if question else []
                }
            elif "??" in question_lower or "i'm confused" in question_lower or "i am confused" in question_lower:
                return {
                    "query_type": "unclear",
                    "answer": "I'm not sure what you're asking. Could you please clarify your question?",
                    "expanded_queries": [question] if question else []
                }
            else:
                # Default to need_rag for substantive questions
                return {
                    "query_type": "need_rag",
                    "expanded_queries": [question] if question else ["What is the capital of France?"],
                    "answer": ""
                }
        
        # Validation node: evaluate answer quality
        elif response_format and response_format.get("json_schema", {}).get("name") == "agentic_response_format":
            return {
                "type_state": "valid_answer",
                "refined_queries": [],
                "valid_search_indices": [],
                "search_ops": []
            }
        
        # RAG reply node: structured response with answer and valid_search_indices
        elif response_format and response_format.get("json_schema", {}).get("name") == "rag_response_format":
            prompt_lower = prompt.lower()
            if "capital" in prompt_lower and "france" in prompt_lower:
                return {
                    "answer": "Based on the search results, the capital of France is Paris.",
                    "valid_search_indices": [1]  # Include index 1 as valid
                }
            elif "photosynthesis" in prompt_lower:
                return {
                    "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy, using carbon dioxide and water to produce glucose and oxygen.",
                    "valid_search_indices": [1]  # Include index 1 as valid
                }
            else:
                return {
                    "answer": "Based on the search results: answer",
                    "valid_search_indices": [1]  # Include index 1 as valid
                }
        
        # Plain text response (fallback, should not be used with structured output)
        else:
            prompt_lower = prompt.lower()
            if "capital" in prompt_lower and "france" in prompt_lower:
                return "Based on the search results, the capital of France is Paris."
            elif "photosynthesis" in prompt_lower:
                return "Photosynthesis is the process by which plants convert light energy into chemical energy, using carbon dioxide and water to produce glucose and oxygen."
            else:
                return "Based on the search results: answer"
    
    return _mock_llm


@pytest.fixture
def mock_elastic_mix():
    """
    Mock implementation of ElasticMix.
    Returns search results with index field.
    
    Motivation: simulate search operations without calling actual Elasticsearch.
    """
    class MockElasticMix:
        def __init__(self):
            pass
        
        async def search(self, query_list, title_index, chunk_index, title_k=3, chunk_k=10):
            # Return mock search results with index field
            search_results = []
            for i, query in enumerate(query_list):
                search_results.append({
                    "index": i + 1,
                    "_id": f"result_{i}",
                    "content": f"Search result for query: {query}",
                    "score": 0.9 - i * 0.1
                })
            return search_results
        
        async def search_ops(self, ops, title_index, chunk_index, title_k=3, chunk_k=10):
            """
            Mock implementation of search_ops.
            Processes a list of search operations and returns combined results.
            """
            search_results = []
            index_counter = 1
            
            for op in ops:
                op_type = op.get("type")
                if op_type == "search_general":
                    # Extract queries from query_list
                    query_list = op.get("query_list", [])
                    for query in query_list:
                        search_results.append({
                            "index": index_counter,
                            "_id": f"result_{index_counter}",
                            "content": f"Search result for query: {query}",
                            "score": 0.9 - (index_counter - 1) * 0.1
                        })
                        index_counter += 1
                elif op_type == "search_doc":
                    # Extract query and doc_ids
                    query = op.get("query", "")
                    doc_ids = op.get("doc_ids", [])
                    search_results.append({
                        "index": index_counter,
                        "_id": f"result_{index_counter}",
                        "content": f"Search result for query: {query} in docs: {doc_ids}",
                        "score": 0.9 - (index_counter - 1) * 0.1
                    })
                    index_counter += 1
                elif op_type == "search_neighbour_chunks":
                    # Extract doc_id, chunk_id, distance
                    doc_id = op.get("doc_id", "")
                    chunk_id = op.get("chunk_id", "")
                    distance = op.get("distance", 1)
                    search_results.append({
                        "index": index_counter,
                        "_id": f"result_{index_counter}",
                        "content": f"Neighbour chunks for doc: {doc_id}, chunk: {chunk_id}, distance: {distance}",
                        "score": 0.9 - (index_counter - 1) * 0.1
                    })
                    index_counter += 1
            
            return search_results
    
    return MockElasticMix


@pytest.fixture
def workflow_with_mocks(mock_call_llm_with_fallback, mock_elastic_mix):
    """
    Build a workflow with all external dependencies mocked.
    
    Motivation: avoid repeating the same patch boilerplate in every test.
    """
    with patch("lib.agentic.nodes.entry_llm_node.call_llm_with_fallback", side_effect=mock_call_llm_with_fallback), \
         patch("lib.agentic.nodes.rag_reply_node.call_llm_with_fallback", side_effect=mock_call_llm_with_fallback), \
         patch("lib.agentic.nodes.reply_validation_node.call_llm_with_fallback", side_effect=mock_call_llm_with_fallback), \
         patch("lib.agentic.node.ElasticMix", new=mock_elastic_mix):
        graph = AgenticGraph()
        workflow = graph.build_workflow()
        app = workflow.compile()
        yield app


@pytest.mark.asyncio
async def test_1_need_rag_path_france(workflow_with_mocks):
    """Test case 1: need_rag path - RAG flow (France question)"""
    state = get_agent_state_default()
    state["question"] = "What is the capital of France?"
    
    result = await workflow_with_mocks.ainvoke(state)
    
    assert result.get('query_type') == 'need_rag'
    assert result.get('answer') != ''
    assert result.get('search_count', 0) == 1
    assert isinstance(result.get('expanded_queries', []), list)


@pytest.mark.asyncio
async def test_2_greeting_path(workflow_with_mocks):
    """Test case 2: greeting path - direct answer"""
    state = get_agent_state_default()
    state["question"] = "Hello, how are you?"
    
    result = await workflow_with_mocks.ainvoke(state)
    
    assert result.get('query_type') == 'greeting'
    assert result.get('answer') == "Hello! How can I help you today?"
    assert result.get('search_count', 0) == 0


@pytest.mark.asyncio
async def test_3_insult_path(workflow_with_mocks):
    """Test case 3: insult path - direct answer"""
    state = get_agent_state_default()
    state["question"] = "You are stupid!"
    
    result = await workflow_with_mocks.ainvoke(state)
    
    assert result.get('query_type') == 'insult'
    assert result.get('answer') == "I'm here to help in a respectful manner. How can I assist you?"
    assert result.get('search_count', 0) == 0


@pytest.mark.asyncio
async def test_4_unclear_path(workflow_with_mocks):
    """Test case 4: unclear path - direct answer"""
    state = get_agent_state_default()
    state["question"] = "I'm confused??"
    
    result = await workflow_with_mocks.ainvoke(state)
    
    assert result.get('query_type') == 'unclear'
    assert result.get('answer') == "I'm not sure what you're asking. Could you please clarify your question?"
    assert result.get('search_count', 0) == 0


@pytest.mark.asyncio
async def test_5_need_rag_path_photosynthesis(workflow_with_mocks):
    """Test case 5: need_rag path - another RAG question (photosynthesis)"""
    state = get_agent_state_default()
    state["question"] = "How does photosynthesis work?"
    
    result = await workflow_with_mocks.ainvoke(state)
    
    assert result.get('query_type') == 'need_rag'
    assert result.get('answer') != ''
    assert result.get('search_count', 0) == 1
    assert isinstance(result.get('expanded_queries', []), list)


@pytest.mark.asyncio
async def test_summary_path_comparison(workflow_with_mocks):
    """Summary: Compare all paths"""
    test_cases = [
        ("need_rag (France)", "What is the capital of France?", "need_rag", True),
        ("greeting", "Hello, how are you?", "greeting", False),
        ("insult", "You are stupid!", "insult", False),
        ("unclear", "I'm confused??", "unclear", False),
        ("need_rag (photosynthesis)", "How does photosynthesis work?", "need_rag", True),
    ]
    
    results = []
    for name, question, expected_type, expect_rag in test_cases:
        state = get_agent_state_default()
        state["question"] = question
        result = await workflow_with_mocks.ainvoke(state)
        results.append((name, result, expected_type, expect_rag))
    
    # Verify all results
    for name, result, expected_type, expect_rag in results:
        assert result.get('query_type') == expected_type, f"Failed for {name}"
        search_count = result.get('search_count', 0)
        if expect_rag:
            assert search_count > 0, f"Expected RAG flow for {name}"
        else:
            assert search_count == 0, f"Expected direct answer for {name}"

