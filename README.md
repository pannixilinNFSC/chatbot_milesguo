# chatbot_milesguo

This is a demonstration of using RAG + LLM to build a chatbot, written in Python with Jupyter Notebooks.  
author: pannixilin  
https://gettr.com/user/pannixilin1  

## Installation

1. Install Python libraries: `pip install -r requirements.txt`
2. Set up API keys:
   - Copy `env.example` to `.env`
   - Add your API keys:
     - `OPENAI_API_KEY`: For OpenAI API access
     - `GOOGLE_API_KEY`: For Google/Gemini API access (optional)
     - `ELASTIC_URL`: Elasticsearch server URL
     - `ELASTIC_API_KEY`: Elasticsearch API key
3. Set up Elasticsearch: The project uses Elasticsearch Serverless for document indexing and search
4. Prepare data: Run `data_prepare.ipynb` to download and process the data

## Usage

### Data Preparation
Run `data_prepare.ipynb` to:
- Download text from https://gwins.org/
- Process and split text into chunks
- Generate summaries and titles
- Index documents in Elasticsearch

### Playground
Open `playground.ipynb` to:
- Explore Elasticsearch search functionality
- Test title search and chunk search
- Experiment with the two-step search system

### RAG Chatbot
The RAG system uses:
- **Two-step retrieval**: First searches document titles/summaries, then retrieves relevant chunks
- **Multi-model LLM**: Uses LiteLLM with fallback support (GPT-4o-mini, Gemini 2.0 Flash)
- **Async processing**: Supports asynchronous API calls for better performance

For detailed technical documentation about the RAG algorithm, workflow, document expansion techniques, and design decisions, see [README_TECH.md](README_TECH.md).

## Deployment

**Recommended: Google Cloud Functions (2nd gen)**

The easiest way to deploy is using Google Cloud Functions. See [README_GCLOUD_FUNCTIONS.md](README_GCLOUD_FUNCTIONS.md) for deployment instructions.

The project includes `main_gcf.py` which wraps the FastAPI app from `server.py` for Cloud Functions compatibility.

**Alternative deployment options (archived):**
- [archive/README_DOCKER.md](archive/README_DOCKER.md) - Docker deployment guide
- [archive/README_GCLOUD_RUN.md](archive/README_GCLOUD_RUN.md) - Google Cloud Run deployment guide

## Documentation

- [README_TECH.md](README_TECH.md) - Technical documentation and architecture details
- [README_API.md](README_API.md) - API endpoints and usage
- [README_GCLOUD_FUNCTIONS.md](README_GCLOUD_FUNCTIONS.md) - Google Cloud Functions deployment (recommended)
- [archive/README_GCLOUD_RUN.md](archive/README_GCLOUD_RUN.md) - Google Cloud Run deployment (archived)
- [archive/README_DOCKER.md](archive/README_DOCKER.md) - Docker deployment guide (archived)

## Project Structure

```
chatbot_milesguo/
  data_prepare.ipynb        # Data preparation notebook
  playground.ipynb           # Exploration notebook
  prompt.json                # Prompt templates
  requirements.txt           # Dependencies
  
  lib/
    rag/                     # RAG implementation
    llm/                     # LLM integration (LiteLLM)
    search/                  # Elasticsearch modules
    data/                    # Data processing modules
  
  data_miles/                # Processed data (not in git)
  archive/                   # Legacy files
```

## Architecture

The system implements a **two-step RAG architecture**. For detailed architecture documentation, see [README_TECH.md](README_TECH.md).

## Advantages vs. Naive RAG

Compared to a naive RAG baseline (search all chunks globally → stuff top-k into the prompt), this system is designed to be more robust on large, noisy Chinese corpora:

- **Higher recall with less noise**: Two-step retrieval (document-level title/summary → chunk-level search within those documents) reduces the search space and helps prevent relevant chunks from being drowned out by global chunk noise.
- **Better semantic matching without embeddings**: Index-time document expansion (`doc_summary`) and chunk-level contextual descriptions (`context`) are included in Elasticsearch `multi_match` queries, improving matches even when exact keywords are missing from the chunk text.
- **More stable for short queries**: Optional query expansion for very short inputs improves search coverage and reduces “too vague to retrieve” failures.
- **Lower token waste**: Deduplication by `doc_id_chunk_id` prevents redundant chunks from being sent to the LLM, reducing prompt size and cost.
- **Good latency characteristics**: Searches are executed asynchronously in parallel (naive + two-step, across expanded queries), improving end-to-end response time under the same retrieval budget.
- **Simpler operations**: No embedding model, vector index, or reranker service to run and monitor—only Elasticsearch Serverless plus LLM calls (with model fallback).

### Technology Stack

- **Search**: Elasticsearch Serverless
- **LLM**: LiteLLM (supports OpenAI GPT-4o-mini, Google Gemini 2.0 Flash)
- **Text Processing**: LangChain text splitters
- **Data Processing**: Python with Jupyter Notebooks  



网站声明

欢迎访问[爆料革命文库内容问答机器人]（以下简称"本网站"）！

网站目的：
本网站旨在通过数据检索和聊天机器人的形式帮助用户理解和检索以[郭文贵]先生直播的字幕内容为核心的，爆料革命和新中国联邦的2000万字核心文本。
1.为战友提供易于访问和理解的信息，以促进知识的传播和共享。
2.方便路人快速了解关于 爆料革命/新中国联邦/郭文贵先生 的核心信息。

代码开源：
本网站所有代码全部开源
https://github.com/pannixilinNFSC/chatbot_milesguo

数据来源：
本网站的全部数据内容来自于：https://gwins.org/ 数据版权归原网站所有。

外部工具：
本网站调用elastic serverless 作为检索数据库
本网站调用openai chatgpt-4o-mini 作为文本生成模型。

免责声明：
本网站的内容仅供信息和参考之用，不构成法律、医疗、金融或其他专业建议。读者在使用本网站提供的信息时应谨慎，自行承担风险。本网站不对因使用本站内容而引发的任何后果承担责任。

隐私政策：
本网站尊重用户隐私，不会收集和分析用户ip地址和输入文本等信息。

作者信息：
本网站的内容由[盘尼西林]编写。此网站的解释权归个人所有。

联系方式：
如果您有任何问题、建议或意见，欢迎通过以下方式与我联系：
- 社交媒体: https://gettr.com/user/pannixilin1

变更通知：
本网站声明的内容可能随时发生变更，变更后的声明将在本网站上公布。请定期查看以获取最新信息。
感谢您访问本网站，我们希望您能在这里找到有用的资源和信息！

[2026-01-01]
