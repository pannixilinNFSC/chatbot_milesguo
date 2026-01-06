# Agentic RAG Pipeline

## Overview

The Agentic RAG pipeline is a LangGraph-based workflow that intelligently routes user queries through different processing paths based on query classification and answer quality validation. It combines LLM-based intent classification, RAG (Retrieval-Augmented Generation) search, and iterative answer refinement to provide high-quality responses.

## Architecture

The workflow consists of 4 main nodes and 2 routing functions:

```
┌──────────────┐
│  __start__   │
└──────┬───────┘
       │
       ▼
┌────────────────────────┐
│        entry_llm       │
│ Intent & Quality Judge │
└──────┬─────────┬──────┘
       │         │
       │         │
       │         ▼
       │   ┌──────────────┐
       │   │ rag_search   │◄───────────────┐
       │   │ (Search KB)  │                │
       │   └──────┬───────┘                │
       │          │                        │
       │          ▼                        │
       │   ┌──────────────┐               │
       │   │ rag_reply    │               │
       │   │ (Generate)   │               │
       │   └──────┬───────┘               │
       │          │                        │
       │          ▼                        │
       │   ┌──────────────────┐           │
       │   │ reply_validation │           │
       │   │ Evidence Judge   │           │
       │   └──────┬────┬──────┘           │
       │          │    │                  │
       │          │    │                  │
       │          │    └──── Partial ──────┘
       │          │
       │          └──── Sufficient
       │
       ▼
┌──────────────┐
│   __end__    │
└──────────────┘
```

## Core Components

### `build_workflow()`

The main method that constructs and returns a LangGraph `StateGraph` instance.

**Location**: `lib.agentic.graph.AgenticGraph.build_workflow()`

**Returns**: `StateGraph[AgentState]` - A compiled workflow graph ready for execution

**Functionality**:
- Creates a `StateGraph` with `AgentState` as the state schema
- Adds 4 nodes: `entry_llm`, `rag_search`, `rag_reply`, `reply_validation`
- Sets `entry_llm` as the entry point
- Configures conditional routing after `entry_llm` and `reply_validation`
- Establishes linear flow: `rag_search` → `rag_reply` → `reply_validation`

**Usage**:
```python
from lib.agentic.graph import AgenticGraph

graph = AgenticGraph()
workflow = graph.build_workflow()
app = workflow.compile()
result = app.invoke({"question": "What is the capital of France?"})
```

### Nodes

#### 1. `entry_llm` (Entry LLM Node)
- **Function**: `lib.agentic.node.entry_llm_node`
- **Purpose**: Classifies user queries and generates direct answers for simple queries
- **Query Types**:
  - `"greeting"`: Casual conversation, returns friendly response
  - `"insult"`: Inappropriate language, returns professional response
  - `"unclear"`: Vague questions, returns clarification request
  - `"need_rag"`: Substantive questions requiring RAG search
- **Output**: Sets `query_type`, `answer`, and `expanded_queries` in state

#### 2. `rag_search` (RAG Search Node)
- **Function**: `lib.agentic.node.rag_search_node`
- **Purpose**: Performs knowledge base search using expanded queries
- **Behavior**: Increments `search_count` to track iterations
- **Output**: Updates `search_results` and `search_count` in state

#### 3. `rag_reply` (RAG Reply Node)
- **Function**: `lib.agentic.node.rag_reply_node`
- **Purpose**: Generates answer based on RAG search results
- **Behavior**: Uses search results to create comprehensive response
- **Output**: Updates `answer` in state

#### 4. `reply_validation` (Reply Validation Node)
- **Function**: `lib.agentic.node.reply_validation_node`
- **Purpose**: Validates answer quality and refines queries if needed
- **Validation States**:
  - `"valid_answer"`: Answer is sufficient, proceed to end
  - `"refine_query"`: Answer needs improvement, generate refined queries
- **Safety**: Enforces `max_iter` limit (default: 1, configurable via `agentic_config`) to prevent infinite loops
- **Output**: Updates `expanded_queries`, `historical_queries`, `answer`, and `search_results`

### Routing Functions

#### `route_after_entry`
- **Function**: `lib.agentic.edge.route_after_entry`
- **Location**: After `entry_llm` node
- **Logic**:
  - If `query_type == "need_rag"` → route to `rag_search`
  - Otherwise (greeting/insult/unclear) → route to `END`

#### `route_after_validation`
- **Function**: `lib.agentic.edge.route_after_validation`
- **Location**: After `reply_validation` node
- **Logic**:
  - If `search_count >= max_iter` (from `agentic_config`) or `len(expanded_queries) == 0` → route to `END`
  - Otherwise → route back to `rag_search` for refinement loop

## State Schema

The workflow uses `AgentState` (defined in `lib.agentic.config`):

```python
class AgentState(TypedDict):
    question: str                    # Initial user query
    query_context: List[str]         # Query context for RAG search
    answer: str                      # Final answer
    query_type: str                  # "greeting", "insult", "unclear", "need_rag"
    historical_queries: List[str]    # All queries used in search iterations
    expanded_queries: List[str]      # Next queries for RAG search
    search_results: List[dict]       # Search results for RAG answer generation
    search_count: int                # Number of RAG search iterations performed
    search_config: SearchConfig      # Search configuration (title_index, chunk_index, title_k, chunk_k)
    agentic_config: AgenticConfig    # Agentic configuration (max_iter, max_query_expand_k)
```

## Workflow Execution Flow

1. **Entry**: User query enters through `entry_llm` node
2. **Classification**: Query is classified into one of four types
3. **Routing Decision**:
   - **Simple queries** (greeting/insult/unclear): Direct answer → `END`
   - **RAG queries**: Proceed to RAG flow
4. **RAG Flow** (iterative):
   - **Search**: `rag_search` retrieves relevant information
   - **Generate**: `rag_reply` creates answer from search results
   - **Validate**: `reply_validation` evaluates answer quality
   - **Refine Loop**: If answer is insufficient, generate refined queries and loop back to search
   - **Termination**: Exit when answer is valid or `max_iter` is reached

## Example Usage

```python
from lib.agentic.graph import AgenticGraph
from lib.agentic.config import get_agent_state_default

# Build and compile the workflow
graph = AgenticGraph()
workflow = graph.build_workflow()
app = workflow.compile()

# Initialize state with default values
state = get_agent_state_default(
    chunk_index="miles_guo",
    title_k=3,
    chunk_k=10,
    max_iter=3,
    max_query_expand_k=1
)
state["question"] = "What is the capital of France?"

# Invoke with the state
result = app.invoke(state)

# Access the final answer
print(result["answer"])
```

## Implementation Details

- **Graph Library**: Built on LangGraph's `StateGraph`
- **State Management**: TypedDict-based state with type safety
- **Error Handling**: Fallback mechanisms in LLM calls (see `dummy_call_llm_with_fallback`)
- **Loop Prevention**: `search_count` tracking prevents infinite refinement loops
- **Query Refinement**: Invalid search results are filtered based on LLM feedback during validation