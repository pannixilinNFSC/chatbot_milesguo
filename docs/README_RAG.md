# RAG System Technical Documentation

This document provides detailed technical documentation about the RAG (Retrieval-Augmented Generation) system implementation.

## RAG System Workflow

The RAG system follows a comprehensive workflow to process user queries and generate accurate responses:

1. **Query Expansion** (Optional)
   - If the user query is too short (< 5 characters), the system uses LLM (Gemini) to expand the query
   - Generates additional related queries to improve search coverage
   - Example: "好人" → ["一个人应具备哪些道德品格，如何加以实践与培养"]

2. **Parallel Search Execution**
   - For each query (original + expanded queries), the system performs two types of searches in parallel:
     - **Naive Search**: Directly searches all chunks in the chunk index using Elasticsearch
     - **Two-Step Search**: 
       - Step 1: Searches document titles/summaries to identify relevant documents (top `title_k` documents)
       - Step 2: Searches chunks only within the identified documents (top `chunk_k` chunks)
   - All searches are executed asynchronously for optimal performance

3. **Result Deduplication**
   - Removes duplicate chunks based on unique `doc_id_chunk_id` combinations
   - Prevents redundant information from being passed to the LLM, reducing token costs

4. **Context Assembly**
   - Combines all unique search results into a JSON format
   - Each result includes: `doc_id`, `chunk_id`, `text`, `context`, `doc_title`, `doc_summary`

5. **LLM Generation**
   - Constructs a prompt with:
     - Pre-defined system prompt (from `prompt.py`)
     - User query
     - Retrieved context (search results)
     - Post-prompt instructions
   - Calls LLM (GPT-4o-mini with Gemini fallback) to generate the final answer
   - Returns the response along with search results and prompt for transparency

**Key Features:**
- **Document Expansion**: Enriches chunks with document summaries, titles, and contextual descriptions to improve semantic retrieval without vector embeddings
- **Hybrid Search Strategy**: Combines naive and two-step search for comprehensive coverage
- **Query Expansion**: Improves search quality for short queries
- **Async Processing**: Parallel execution of multiple searches for faster response times
- **Cost Optimization**: Deduplication reduces token usage in LLM calls
- **Fallback Mechanism**: Automatic fallback between GPT and Gemini models for reliability

## Document Expansion

The system employs multiple document expansion techniques to enhance retrieval quality by enriching chunks with additional contextual information:

1. **Document Summary (`doc_summary`)**
   - Generated at the document level using LLM (via `SummaryExtractor`)
   - Provides high-level semantic understanding of the entire document
   - Used in both title index and chunk index for better matching
   - In chunk search, `doc_summary` is included in multi-match queries to help retrieve relevant chunks even when the exact query terms don't appear in the chunk text
   - Weight: `doc_summary^2` in title search (higher weight for document-level relevance)

2. **Document Title (`doc_title`)**
   - Extracted from documents to provide concise document identification
   - Used in title index for document-level filtering
   - Included in chunk search results to provide document context to the LLM

3. **Chunk Context (`context`)**
   - Generated per-chunk using LLM (via `ContextGenerator`)
   - Combines document summary, current chunk, and adjacent chunks (default: ±2 chunks) to create contextual descriptions
   - Provides semantic context that helps bridge gaps between query intent and chunk content
   - Used in chunk search multi-match queries alongside chunk text and document summary
   - Helps retrieve chunks that are semantically relevant but may not contain exact query keywords

**Search Field Configuration:**
- **Chunk Search**: Uses `multi_match` query across `text^2`, `doc_summary`, and `context` fields
  - `text` field has weight 2 (highest priority for exact matches)
  - `doc_summary` and `context` provide semantic expansion
- **Title Search**: Uses `multi_match` query across `doc_summary^2` and `doc_title` fields
  - `doc_summary` has weight 2 (primary relevance signal)
  - `doc_title` provides additional matching surface

**Benefits:**
- Improves recall by capturing semantic relationships beyond keyword matching
- Reduces dependency on exact term matching
- Provides richer context to LLM for better answer generation
- Maintains search efficiency with Elasticsearch BM25 scoring

## Design Decisions: Why Not Sparse Vector Hybrid Search and Reranker?

The system intentionally uses **BM25-based lexical search** (Elasticsearch's default) instead of hybrid sparse/dense vector search and reranking.

### Commercial Practice Evidence

Based on commercial practice:
- **Sparse Vector** can improve recall@5 by approximately 10%. However, Chinese Sparse Encoder models are more expensive and are typically trained on general text corpora, making them unreliable on domain-specific corpora like this one.
- **Reranker** can provide an additional 10% improvement in recall@5 when applied to 20 candidates. However, a good reranker model is as expensive as an LLM. While it might seem more cost-efficient to use a reranker to filter candidates before sending to the LLM generator, modern LLMs such as Gemini 2.0 Flash are extremely cheap, making it more economical to send all retrieved text directly to the LLM generator.

### Key Reasons

1. **Cost Efficiency**
   - Sparse Vector and Reranker add inference-time costs during query processing
   - Current approach uses only Elasticsearch Serverless, minimizing infrastructure and operational costs
   - Document expansion (see above) only increases costs during data preparation, making it more cost-effective for high query volumes

2. **Chinese Language Support**
   - Most high-quality sparse retrieval models (SPLADE, ColBERT) are primarily trained on English data
   - Limited availability and quality of Chinese-specific sparse retrieval models
   - BM25 works well with Elasticsearch's built-in Chinese analyzer, providing good out-of-the-box performance

3. **Simplicity and Maintainability**
   - BM25 is well-understood, stable, and requires minimal configuration
   - No need to manage embedding models, vector indices, or reranker services
   - Easier to debug and optimize search behavior

4. **Performance Characteristics**
   - BM25 provides fast, deterministic search results
   - No additional latency from embedding generation or reranking steps
   - Two-step search strategy (title → chunks) already provides effective filtering

**Trade-offs:**
- Estimated ~20% lower recall@10 compared to using Sparse Vector + Reranker
- Relies more on keyword matching, though mitigated by document expansion
- Prioritizes cost efficiency and stability over maximum recall performance

## Architecture

The system implements a **two-step RAG architecture**:

1. **Document-level search**: Searches document titles and summaries to identify relevant documents
2. **Chunk-level search**: Retrieves specific chunks from the identified documents
3. **LLM generation**: Uses multi-model LLM (with fallback) to generate answers based on retrieved chunks

### Technology Stack

- **Search**: Elasticsearch Serverless
- **LLM**: LiteLLM (supports OpenAI GPT-4o-mini, Google Gemini 2.0 Flash)
- **Text Processing**: LangChain text splitters
- **Data Processing**: Python with Jupyter Notebooks

