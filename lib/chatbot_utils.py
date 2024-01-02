import os
import json

class ChatbotClient(object):
    def __init__(self, work_dir, openai_client):
        prompt_path = os.path.join(work_dir, "prompt.json")
        declaration_path = os.path.join(work_dir, "declaration.txt")
        with open(prompt_path, "r") as f:
            self.default_prompt = json.load(f)
        with open(declaration_path, "r") as f:
            self.declaration = f.read()
        self.openai_client = openai_client
            
    def __call__(self, txt_query, txts_retrival, prompt1=None, prompt2=None):
        if prompt1 is None:
            prompt1 = self.default_prompt["prompt1"]
        if prompt2 is None:
            prompt2 = self.default_prompt["prompt2"]
        txt_response, txt_prompt = RAG_chatbot(txt_query, self.openai_client, txts_retrival, 
                prompt1=prompt1, prompt2=prompt2)
        json2 = [{i+1: f"题目：{title}\n 正文：{txt}" for i, (title, txt) in enumerate(txts_retrival)}]
        json1 = {"reply": txt_response, 
                "retrieval": json2, 
                "prompt": txt_prompt, 
                "declaration": self.declaration}
        json1 = json.dumps(json1, indent=4, ensure_ascii=False)
        return json1

def RAG_chatbot(txt_query, openai_client, txts_retrival, 
                prompt1="你需要全面地摘要并总结a所有参考文本，并总结对以下问题的回答：", 
               prompt2="以下是参考文本\n\n"):
    """
    k=3时token 4000左右，请求250次API成本1美金左右，成本和输入token数量，即和检索数量k成正比
    gpt-3.5-turbo-1106，是最新版3.5模型，最大token 16k
    需要试验其他开源LLM
    reference： https://openai.com/pricing#language-models
    """
    txts_retrival = "\n\n".join([f"标题：{title}\n 正文：{txt}\n" for title, txt in txts_retrival])
    prompt = f"{prompt1} {txt_query} {prompt2} "
    response = openai_client.chat.completions.create(model="gpt-3.5-turbo-1106",
        messages=[{"role": "user", "content": prompt + txts_retrival}])
    txt_response = json.loads(response.json())["choices"][0]["message"]["content"]
    return txt_response, prompt
