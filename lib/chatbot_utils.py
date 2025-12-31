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
        json2 = [{i+1: f"Title: {title}\n Content: {txt}" for i, (title, txt) in enumerate(txts_retrival)}]
        json1 = {"reply": txt_response, 
                "retrieval": json2, 
                "prompt": txt_prompt, 
                "declaration": self.declaration}
        json1 = json.dumps(json1, indent=4, ensure_ascii=False)
        return json1

def RAG_chatbot(txt_query, openai_client, txts_retrival, 
                prompt1="You need to comprehensively summarize all reference texts and summarize the answer to the following question:", 
               prompt2="The following are reference texts\n\n"):
    """
    RAG-style chatbot: concatenate retrieved passages and ask the chat model to answer.

    Cost/limits notes (rough, depends heavily on prompt + retrieval size):
    - When k=3, tokens can be ~4k; cost scales with input tokens and retrieval count k.
    - Model context window depends on the selected model.
    - Consider experimenting with other open-source LLMs if you want to avoid API cost.
    - Reference: https://openai.com/pricing#language-models
    """
    txts_retrival = "\n\n".join([f"Title: {title}\n Content: {txt}\n" for title, txt in txts_retrival])
    prompt = f"{prompt1} {txt_query} {prompt2} "
    response = openai_client.chat.completions.create(model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt + txts_retrival}])
    txt_response = json.loads(response.json())["choices"][0]["message"]["content"]
    return txt_response, prompt
