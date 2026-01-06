import json


PROMPT_BASE = {
    "prompt1": """你是一个用于问答任务的助手。
请围绕给定的话题，对参考文本中与**该话题相关**的内容进行全面准确的总结和转述，忽略无关内容。

要求：
- 内容尽量丰富，语言风格风趣幽默，细节充分
- 总结并转述参考文本中与话题相关的内容
- 每句话都要有参考文档的依据，附带引用的序号，形如[2][3]等

**重要：命名实体匹配检查（最重要）**
在回答之前，你必须逐一检查每个参考文本中提到的命名实体（特别是人名）是否与话题中的命名实体完全一致。
- 如果参考文本中提到的人名、机构名称或其他命名实体与话题中的命名实体不一致，必须完全忽略该文本，不得在回答中引用或提及
- 严禁将不同的人名混淆，严禁将参考文本中错误的人名强行关联到话题中的人名
- 如果所有参考文本中的实体都与话题不匹配，你应该明确说明找不到相关信息，而不是强行使用错误的人名

其他注意事项：
1. 你不能对内容进行评价或表态
2. 如果参考文本中存在矛盾或冲突之处，请以时间较晚的内容为准
3. **禁止总结性结尾**：不要在回复的最后添加总结性陈词，如"综上所述"、"总之"、"总的来说"等。直接结束回答，不要添加任何总结性段落
4. 不用重复用户问答记录中的内容，尽量提供新的信息

话题是：
""",
    "prompt2": ""
}


def build_rag_prompt(query: str, 
                     search_results: list[dict], 
                     query_context: list[str]=[], 
                     prompt_before: str=None, 
                     prompt_after: str=None
    ) -> str:
    search_results_txt = json.dumps(search_results, ensure_ascii=False)
    
    if not prompt_before:
        prompt_before = PROMPT_BASE["prompt1"]
    if not prompt_after:
        prompt_after = PROMPT_BASE["prompt2"]
    
    prompt = f"""{prompt_before} 用户本次的话题是：{query} \n"""
    if query_context:
        prompt += f"""这是用户之前的问答记录：{query_context} \n"""
    prompt += f"""以下是参考文本: {search_results_txt} \n"""
    prompt += f"""{prompt_after}"""
    return prompt

