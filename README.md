# chatbot_milesguo

This is a demo of using RAG + LLM to build a chatbot.   
written in python jupyter notebook.  

1. download text on Miles Guo's speech
2. process the text
3. vectorize sentences by openai sentence-embedding ada 002
4. build simple vector search index by FAISS
5. Retrival Augmented Generation (RAG) by calling openai chatgpt-3.5 API. 

Installation:   
1. pip3 install -r requirements
2. write your openai API key to "openai_key.txt"

