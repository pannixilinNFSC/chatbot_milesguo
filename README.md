# chatbot_milesguo

This is a demonstration of using RAG + LLM to build a chatbot, written in Python with Jupyter Notebooks.  
author: pannixilin  
https://gettr.com/user/pannixilin1  


## 相对第一版的改进

RAG系统的通病是知识碎片化，由于所有的参考文本都是破碎的切片，即使检索召回率做到极限，仍然无法很好的回答问题。
本系统的改进
1. 在检索算法上做了精简，只使用BM25关键词检索的baseline。
2. 扩展了粗检索文档，再检索段落的多种检索路径，拓展检索内容的丰富度。此思路接近在RAG和Agentic Search之间找到一个中间状态。
3. 专注于document expansion，基于文本切片，扩展context和summary。解决参考文档碎片化的问题。
4. 并行使用query expansion替换sparse vector，不仅增加推理速度，降低推理成本，精度甚至高于使用vector search。理解用户意图扩展关键问法，比提高10%的召回率重要得多。
5. 放弃reranker，现代LLM的成本降低，LLM本身的性能又足以充当reranker。把所有找回文本扔给LLM，使reranker在RAG系统中不再必要。



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
Run `scripts/data_prepare.ipynb` to:
- Download text from https://gwins.org/
- Process and split text into chunks
- Generate summaries and titles
- Index documents in Elasticsearch

### Playground
Open `scripts/playground.ipynb` to:
- Explore Elasticsearch search functionality
- Test title search and chunk search
- Experiment with the two-step search system

### RAG Chatbot
The RAG system uses:
- **Two-step retrieval**: First searches document titles/summaries, then retrieves relevant chunks
- **Multi-model LLM**: Uses LiteLLM with fallback support (GPT-4o-mini, Gemini 2.0 Flash)
- **Async processing**: Supports asynchronous API calls for better performance

For detailed technical documentation about the RAG algorithm, workflow, document expansion techniques, and design decisions, see [docs/README_TECH.md](docs/README_TECH.md).

## Deployment

**Production Architecture:**
- **Frontend**: Static web frontend hosted on GitHub Pages (github.io)
- **Backend API**: Google Cloud Functions (2nd gen)
- **Database**: Elasticsearch Serverless
- **LLM**: Primary ChatGPT (GPT-4o-mini) with fallback to Gemini 2.0 Flash

**Recommended: Google Cloud Functions (2nd gen)**

The easiest way to deploy is using Google Cloud Functions. See [docs/README_GCLOUD_FUNCTIONS.md](docs/README_GCLOUD_FUNCTIONS.md) for deployment instructions.

The project includes `main.py` which contains the FastAPI app for Cloud Functions compatibility.

~~**Alternative deployment options (archived):**
- [archive/README_DOCKER.md](archive/README_DOCKER.md) - Docker deployment guide
- [archive/README_GCLOUD_RUN.md](archive/README_GCLOUD_RUN.md) - Google Cloud Run deployment guide~~

## Documentation

- [docs/README_TECH.md](docs/README_TECH.md) - Technical documentation and architecture details
- [docs/README_API.md](docs/README_API.md) - API endpoints and usage
- [docs/README_GCLOUD_FUNCTIONS.md](docs/README_GCLOUD_FUNCTIONS.md) - Google Cloud Functions deployment (recommended)
- [docs/README_TEST.md](docs/README_TEST.md) - Testing documentation
- [frontend/README_WEB.md](frontend/README_WEB.md) - Frontend documentation
- [archive/README_GCLOUD_RUN.md](archive/README_GCLOUD_RUN.md) - Google Cloud Run deployment (archived)
- [archive/README_DOCKER.md](archive/README_DOCKER.md) - Docker deployment guide (archived)

## Frontend (static)

The frontend is automatically deployed to GitHub Pages via GitHub Actions workflow (`.github/workflows/deploy.yml`). Every time code is merged to `main`, `master`, or `v2` branch, the frontend is automatically updated on GitHub Pages.

**Local Development:**
Open `frontend/index.html` in a browser, set the Cloud Functions base URL + function name, then start chatting.

*Important:* To avoid CORS blocking, make sure the backend has CORS enabled. Configure `CORS_ALLOW_ORIGINS` in your `.env` file (e.g., `CORS_ALLOW_ORIGINS=*` or specific origins like `CORS_ALLOW_ORIGINS=https://yourusername.github.io,file://`).

**Automatic Deployment:**
- The workflow triggers on push/merge to main/master/v2 branches
- Frontend files are automatically deployed to GitHub Pages
- Build timestamp and Git SHA are injected into the HTML

Note: browser calls require CORS. This repo enables CORS via FastAPI `CORSMiddleware` and supports configuring allowed origins with `CORS_ALLOW_ORIGINS` ("*" or comma-separated).

## Project Structure

```
chatbot_milesguo/
  main.py                    # FastAPI app entry point
  requirements.txt           # Dependencies
  env.example                # Environment variables template
  
  lib/                       # Core libraries
    rag/                     # RAG implementation
    llm/                     # LLM integration (LiteLLM)
    search/                  # Elasticsearch modules
    security/                # Security (CORS, auth, rate limiting)
    app_logger.py            # Logging utilities
  
  docs/                      # Documentation
    README_API.md            # API documentation
    README_TECH.md           # Technical documentation
    README_GCLOUD_FUNCTIONS.md  # Deployment guide
    README_TEST.md           # Testing guide
  
  frontend/                  # Frontend
    index.html               # Web UI
    README_WEB.md            # Frontend documentation
  
  scripts/                   # Scripts and notebooks
    data_prepare.ipynb       # Data preparation notebook
    playground.ipynb         # Exploration notebook
    deploy.sh                # Deployment script
  
  test/                      # Tests
  data_miles/                # Processed data (not in git)
  archive/                   # Legacy files
```

## Architecture

The system implements a **two-step RAG architecture**. For detailed architecture documentation, see [docs/README_TECH.md](docs/README_TECH.md).

## Advantages vs. Naive RAG

Compared to a naive RAG baseline (search all chunks globally → stuff top-k into the prompt), this system is designed to be more robust on large, noisy Chinese corpora:

- **Higher recall with less noise**: Two-step retrieval (document-level title/summary → chunk-level search within those documents) reduces the search space and helps prevent relevant chunks from being drowned out by global chunk noise.
- **Better semantic matching without embeddings**: Index-time document expansion (`doc_summary`) and chunk-level contextual descriptions (`context`) are included in Elasticsearch `multi_match` queries, improving matches even when exact keywords are missing from the chunk text.
- **More stable for short queries**: Optional query expansion for very short inputs improves search coverage and reduces “too vague to retrieve” failures.
- **Lower token waste**: Deduplication by `doc_id_chunk_id` prevents redundant chunks from being sent to the LLM, reducing prompt size and cost.
- **Good latency characteristics**: Searches are executed asynchronously in parallel (naive + two-step, across expanded queries), improving end-to-end response time under the same retrieval budget.
- **Simpler operations**: No embedding model, vector index, or reranker service to run and monitor—only Elasticsearch Serverless plus LLM calls (with model fallback).

### Technology Stack

- **Frontend**: Static web (hosted on GitHub Pages)
- **Backend**: Google Cloud Functions (FastAPI)
- **Search**: Elasticsearch Serverless
- **LLM**: LiteLLM with primary ChatGPT (GPT-4o-mini) and fallback Gemini 2.0 Flash
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
