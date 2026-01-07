from lib.agentic.config import AgentState
from lib.agentic.prompts import get_rag_prompt_and_format
from lib.llm.litellm_api import call_llm_with_fallback, call_llm_stream_with_fallback
from contextlib import contextmanager
import re


@contextmanager
def _get_stream_writer():
    """
    Context manager to get stream writer if available.
    Returns None if not in LangGraph execution context.
    """
    try:
        from langgraph.utils import get_stream_writer
        writer = get_stream_writer()
        yield writer
    except (ImportError, RuntimeError, AttributeError, TypeError):
        # Not in LangGraph execution context or writer not available
        yield None


def _extract_indices_from_answer(answer: str) -> set[int]:
    """
    Extract index references from answer text (e.g., [1][2] -> {1, 2}).
    
    Args:
        answer: Answer text that may contain index references like [1][2]
        
    Returns:
        set: Set of integer indices found in the answer
    """
    # Match patterns like [1], [2], [1][2], etc.
    # This regex finds all [number] patterns
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, answer)
    indices = {int(m) for m in matches}
    return indices


async def _generate_answer_with_streaming(
    prompt_rag: str,
    rag_response_format: dict,
    writer
) -> tuple[str, set]:
    """
    Generate answer with streaming support.
    
    First streams the LLM response for real-time output, then gets structured output
    to filter search results based on valid indices.
    
    Args:
        prompt_rag: RAG prompt for LLM
        rag_response_format: Structured response format for filtering
        writer: Stream writer for custom events (from LangGraph)
        
    Returns:
        tuple: (answer, valid_indices) where valid_indices is a set of valid search result indices
    """
    # Stream LLM response if stream writer is available
    full_answer = ""
    async for chunk in call_llm_stream_with_fallback(prompt_rag, model_name="gpt", response_format=None):
        full_answer += chunk
        # Send custom streaming event
        try:
            writer.write({
                "type": "content_chunk",
                "data": chunk
            })
        except Exception:
            # Ignore errors if writer is not properly configured
            pass
    
    # After streaming, get structured output to filter search results
    # Extract indices from the streamed answer (what user actually sees) first
    streamed_indices = _extract_indices_from_answer(full_answer)
    
    try:
        llm_output = await call_llm_with_fallback(prompt_rag, model_name="gpt", response_format=rag_response_format)
        structured_indices = set(llm_output.get("valid_search_indices", []))
        
        # Merge indices: combine structured output indices with indices found in streamed answer
        # This ensures that if the streamed answer mentions [1][2], those sources are kept
        # even if structured output didn't capture them correctly
        valid_indices = structured_indices | streamed_indices
        
        # Use streamed answer (what user actually saw) as the final answer
        # This ensures consistency between what's displayed and what's filtered
        answer = full_answer
    except Exception:
        # Fallback: use streamed answer and extract indices from it
        answer = full_answer
        valid_indices = streamed_indices
    
    return answer, valid_indices


async def rag_reply_node(state: AgentState) -> AgentState:
    """
    Third node (second LLM node): Generate answer based on RAG search results.
    
    This node uses the search results from rag_search_node to generate a comprehensive
    answer to the user's query. It supports streaming output when enable_streaming is True
    in state and a stream writer is available.
    
    The generated answer is stored in state and may be validated in subsequent nodes
    to ensure it adequately addresses the user's question.
    """
    question = state.get("question", "")
    search_results = state.get("search_results", [])
    agentic_config = state.get("agentic_config", {})
    enable_streaming = state.get("enable_streaming", False)
    
    # Get prompt and response format
    prompt_rag, rag_response_format = get_rag_prompt_and_format(question, search_results, agentic_config)
    
    # Use streaming if enabled and writer is available
    if enable_streaming:
        with _get_stream_writer() as writer:
            if writer is not None:
                # Use streaming function for real-time output
                answer, valid_indices = await _generate_answer_with_streaming(
                    prompt_rag, rag_response_format, writer
                )
            else:
                # Fallback to non-streaming execution if writer not available
                llm_output = await call_llm_with_fallback(prompt_rag, model_name="gpt", response_format=rag_response_format)
                answer = llm_output["answer"]
                structured_indices = set(llm_output.get("valid_search_indices", []))
                # Also extract indices from answer text to ensure consistency
                answer_indices = _extract_indices_from_answer(answer)
                valid_indices = structured_indices | answer_indices
    else:
        # Non-streaming execution (default)
        llm_output = await call_llm_with_fallback(prompt_rag, model_name="gpt", response_format=rag_response_format)
        answer = llm_output["answer"]
        structured_indices = set(llm_output.get("valid_search_indices", []))
        # Also extract indices from answer text to ensure consistency
        answer_indices = _extract_indices_from_answer(answer)
        valid_indices = structured_indices | answer_indices
    
    # Filter search results: keep only those with indices mentioned in answer
    # valid_search_indices contains reference numbers from answer (e.g., "1", "2" from [1][2])
    filtered_search_results = [
        result for result in search_results 
        if result.get("index") in valid_indices
    ] if valid_indices else search_results
    
    return {
        **state,
        "answer": answer,
        "search_results": filtered_search_results,
    }

