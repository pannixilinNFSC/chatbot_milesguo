import json

def RAG_chatbot(txt_query, openai_client, txts_retrival, 
                prompt1="你需要全面地摘要并总结a所有参考文本，并总结对以下问题的回答：", 
               prompt2="以下是参考文本\n\n"):
    """
    k=3时token 4000左右，请求250次API成本1美金左右，成本和输入token数量，即和检索数量k成正比
    gpt-3.5-turbo-1106，是最新版3.5模型，最大token 16k
    需要试验其他开源LLM
    reference： https://openai.com/pricing#language-models
    """
    txts_retrival = "\n\n".join([f"标题：{title}\n 正文：{txt}" for title, txt in txts_retrival])
    prompt = f"{prompt1} {txt_query} {prompt2} {txts_retrival}"
    response = openai_client.chat.completions.create(model="gpt-3.5-turbo-1106",
        messages=[{"role": "user", "content": prompt}])
    txt_response = json.loads(response.json())["choices"][0]["message"]["content"]
    return txt_response
