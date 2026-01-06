from typing import TypedDict, List, Literal
from langgraph.graph import END
from lib.agentic.config import AgentState


class Edge:
    """
    Edge class containing all routing functions for conditional edges in the workflow.
    Each method determines the next node based on the current state.
    """
    
    def route_after_entry(self, state: AgentState) -> str:
        """
        Route after entry_llm_node:
        - If greeting/insult/unclear: answer already generated, go to END
        - If need_rag: continue to RAG flow (rag_search_node)
        """
        query_type = state.get("query_type", "unclear")
        
        if query_type == "need_rag":
            return "rag_search"
        else:
            # greeting, insult, or unclear - answer already generated in first node
            return END

    def route_after_validation(self, state: AgentState) -> str:
        """
        Route after reply_validation_node:
        - If valid_answer or exceeded_limit: go to END (answer is ready)
        - If refine_query: loop back to rag_search_node for another iteration
        """
        agentic_config = state.get("agentic_config", {})
        max_search_count = agentic_config.get("max_search_count", 3)
        search_count = state.get("search_count", 0)
        exceeded_limit = search_count >= max_search_count
        
        # Check if we have search operations to execute (means we need to refine)
        search_ops = state.get("search_ops")
        
        if exceeded_limit or search_ops is None or len(search_ops) == 0:
            # No more search operations to execute, answer is ready
            return END
        else:
            # Need to refine, loop back to search
            return "rag_search"
