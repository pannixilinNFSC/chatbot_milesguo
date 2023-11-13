# chatbot_milesguo

This is a demonstration of using RAG + LLM to build a chatbot, written in a Python Jupyter Notebook.  

The process involves:  

Downloading text from Miles Guo's speeches from https://gwins.org/  
Processing and sllit the text.  
Vectorizing sentences using OpenAI's sentence-embedding model 'ada 002'.  
Building a simple vector search index with FAISS.  
Performing Retrival Augmented Generation (RAG) by making calls to the OpenAI ChatGPT-3.5 API.  
