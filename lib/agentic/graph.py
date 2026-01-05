from langgraph.graph import StateGraph, END
from lib.agentic.config import AgentState


class AgenticGraph:
    """
    Graph class for building the agentic RAG workflow.
    Manages the workflow graph construction with nodes and edges.
    """
    
    def __init__(self, node=None, edge=None):
        """
        Initialize the Graph with Node and Edge instances.
        
        Args:
            node: Node instance (optional, creates default if not provided)
            edge: Edge instance (optional, creates default if not provided)
        """
        from lib.agentic.node import Node as NodeClass
        from lib.agentic.edge import Edge as EdgeClass
        
        self.node = node if node is not None else NodeClass()
        self.edge = edge if edge is not None else EdgeClass()
    
    def build_workflow(self) -> StateGraph:
        """
        Build and return the complete workflow graph.
        
        Returns:
            StateGraph: A compiled workflow graph ready for execution
        """
        workflow = StateGraph(AgentState)

        # Add nodes with correct function names
        workflow.add_node("entry_llm", self.node.entry_llm_node)
        workflow.add_node("rag_search", self.node.rag_search_node)
        workflow.add_node("rag_reply", self.node.rag_reply_node)
        workflow.add_node("reply_validation", self.node.reply_validation_node)

        # Set entry point
        workflow.set_entry_point("entry_llm")

        # Add conditional edge from entry_llm_node
        workflow.add_conditional_edges(
            "entry_llm",
            self.edge.route_after_entry,
            {
                "rag_search": "rag_search",
                END: END
            }
        )

        # RAG flow: search -> reply -> validation
        workflow.add_edge("rag_search", "rag_reply")
        workflow.add_edge("rag_reply", "reply_validation")

        # Conditional edge after validation: either END or loop back to search
        workflow.add_conditional_edges(
            "reply_validation",
            self.edge.route_after_validation,
            {
                "rag_search": "rag_search",
                END: END
            }
        )
        return workflow

