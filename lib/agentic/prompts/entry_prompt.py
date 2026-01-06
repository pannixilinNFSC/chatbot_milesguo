def get_entry_prompt_and_format(question, query_context, agentic_config: dict):
    """
    Build entry prompt and response format together.
    
    Returns:
        tuple: (prompt, response_format)
    """
    prompt_entry = f"""分析用户问题并分类：

用户问题：{question}

用户之前的问答记录：{query_context}

分类规则：
- **greeting**：问候语或闲聊，生成友好回复作为 answer
- **insult**：不当言论，生成专业礼貌回应作为 answer
- **unclear**：问题模糊不明确，生成请求澄清的回复作为 answer
- **need_rag**：需要检索的实质性问题，生成 1-3 个扩展查询，answer 可为空

扩展查询生成方法（仅用于 need_rag）：
猜测用户的提问意图，并给出更具体的查询问句，15个字以内。
如果question中内容不全，则参考query_context中的内容进行扩展。
例如：
用户提问：如何做好人
扩展：["一个人应具备哪些道德品格", "如何加以实践与培养"]

对于前三种类型，expanded_queries 设为原问题。"""
    
    k = agentic_config.get("max_query_expand_k", 1)
    
    entry_schema = {
        "type": "object",
        "properties": {
            "expanded_queries": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": k
            },
            "query_type": {
                "type": "string",
                "enum": ["greeting", "insult", "unclear", "need_rag"]
            },
            "answer": {
                "type": "string",
            }
        },
        "required": ["query_type", "expanded_queries", "answer"]
    }

    entry_response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "entry_response_format",
            "schema": dict(entry_schema)
        }
    }
    
    return prompt_entry, entry_response_format

