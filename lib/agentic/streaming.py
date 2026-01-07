"""
Streaming execution support for Agentic RAG workflow.
Uses LangGraph's native astream() method for graph execution.
"""
from typing import AsyncGenerator, Dict, Any, TYPE_CHECKING
from lib.agentic.config import AgentState

if TYPE_CHECKING:
    from langgraph.graph import CompiledGraph

async def agentic_rag_stream(
    graph: "CompiledGraph",
    initial_state: AgentState,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream Agentic RAG workflow execution using LangGraph's native astream().
    
    This function uses graph.astream() to execute the workflow and converts
    LangGraph stream events into the expected format for the frontend.
    
    Args:
        graph: Compiled LangGraph workflow
        initial_state: Initial AgentState dictionary
        
    Yields:
        dict: Streaming chunks with type and data fields:
            - type: "status" | "content" | "done" | "error"
            - data: chunk data
    """
    try:
        # Enable streaming in state
        streaming_state = {**initial_state, "enable_streaming": True}
        
        # Track current state and accumulated content
        final_state = streaming_state.copy()
        accumulated_content = ""
        entry_llm_completed = False
        last_reply_iteration = -1  # Track which iteration of rag_reply we're on
        
        # Stream graph execution with updates and custom events
        async for chunk in graph.astream(
            streaming_state,
            stream_mode=["updates", "custom"],
        ):
            # Handle different stream modes
            # When multiple modes are specified, chunks come as tuples (mode, data)
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
                
                if mode == "updates":
                    # Handle node updates
                    if isinstance(data, dict):
                        for node_name, node_state in data.items():
                            # Merge state updates into final state
                            final_state.update(node_state)
                            
                            # Emit status for node execution
                            node_status_map = {
                                "entry_llm": "classifying",
                                "rag_search": "searching",
                                "rag_reply": "generating",
                                "reply_validation": "validating",
                            }
                            status = node_status_map.get(node_name, "processing")
                            
                            # Get iteration count for search node
                            search_count = final_state.get("search_count", 0)
                            iteration_data = {"status": status, "node": node_name}
                            if node_name == "rag_search" and search_count > 0:
                                iteration_data["iteration"] = search_count
                            
                            # Reset accumulated content when a new rag_reply iteration starts
                            if node_name == "rag_reply":
                                current_reply_iteration = search_count  # rag_reply follows rag_search
                                if current_reply_iteration > last_reply_iteration:
                                    # New iteration started, clear previous content
                                    accumulated_content = ""
                                    last_reply_iteration = current_reply_iteration
                                    # Send reset signal to frontend
                                    yield {
                                        "type": "content_reset",
                                        "data": {"iteration": current_reply_iteration}
                                    }
                            
                            yield {
                                "type": "status",
                                "data": iteration_data
                            }
                            
                            # Handle entry_llm completion
                            if node_name == "entry_llm" and not entry_llm_completed:
                                entry_llm_completed = True
                                query_type = final_state.get("query_type", "")
                                answer = final_state.get("answer", "")
                                
                                # If not need_rag, return direct answer immediately
                                if query_type != "need_rag" and answer:
                                    yield {
                                        "type": "content",
                                        "data": answer
                                    }
                                    # Will return early after emitting done event
                                    accumulated_content = answer
                
                elif mode == "custom":
                    # Handle custom streaming events (from rag_reply_node)
                    if isinstance(data, dict):
                        event_type = data.get("type")
                        event_data = data.get("data")
                        
                        if event_type == "content_chunk":
                            # Stream content chunk from rag_reply_node
                            chunk_text = event_data if isinstance(event_data, str) else str(event_data)
                            accumulated_content += chunk_text
                            yield {
                                "type": "content",
                                "data": chunk_text
                            }
            
            elif isinstance(chunk, dict):
                # Single stream mode (updates only) - direct node updates
                for node_name, node_state in chunk.items():
                    final_state.update(node_state)
        
        # Emit final result
        # Use accumulated content if available, otherwise use final state answer
        final_content = accumulated_content if accumulated_content else final_state.get("answer", "")
        yield {
            "type": "done",
            "data": {
                "content": final_content,
                "search_results": final_state.get("search_results", []),
                "historical_search_ops": final_state.get("historical_search_ops", []),
                "query_type": final_state.get("query_type", ""),
                "search_count": final_state.get("search_count", 0),
            }
        }
        
    except Exception as e:
        yield {
            "type": "error",
            "data": {"error": str(e)}
        }
        raise

