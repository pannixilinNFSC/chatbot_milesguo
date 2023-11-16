import json

def RAG_chatbot(txt_query, openai_client, txts_retrival):
    """
    k=3时token 4000左右，请求250次API成本1美金左右，成本和输入token数量，即和检索数量k成正比
    gpt-3.5-turbo-1106，是最新版3.5模型，最大token 16k
    需要试验其他开源LLM
    reference： https://openai.com/pricing#language-models
    """
    prompt = "\n\n".join([f"标题：{title}\n 正文：{txt}" for title, txt in txts_retrival])
    prompt = f"你需要先摘要并总结参考文本，总结郭文贵会如何回答以下问题：{txt_query} 以下是参考文本\n\n{txts_retrival}"
    
    response = openai_client.chat.completions.create(model="gpt-3.5-turbo-1106",
      messages=[{"role": "user", "content": prompt}])
    txt_response = json.loads(response.json())["choices"][0]["message"]["content"]
    return txt_response
