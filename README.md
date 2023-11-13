# chatbot_milesguo

This is a demonstration of using RAG + LLM to build a chatbot, written in a Python Jupyter Notebook.  


Installation:   
1. pip3 install -r requirements
2. write your openai API key to "openai_key.txt"
3. install and run jupyter notebook
4. open main.ipynb

The process involves:  

Downloading text from Miles Guo's speeches from https://gwins.org/  
Processing and sllit the text.  
Vectorizing sentences using OpenAI's sentence-embedding model 'ada 002'.  
Building a simple vector search index with FAISS.  
Performing Retrival Augmented Generation (RAG) by making calls to the OpenAI ChatGPT-3.5 API.  
