def build_prompt_entry(question, query_context):
    return f"""分析用户问题并分类：

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
扩展：一个人应具备哪些道德品格，如何加以实践与培养

对于前三种类型，expanded_queries 设为原问题。"""


def build_prompt_agentic(question, answer):
    return f"""评估答案质量并决定是否需要进一步检索：

用户问题：{question}

当前生成的答案：
{answer}

请评估答案是否充分回答了用户问题：

1. **valid_answer**：如果答案已经充分、准确、完整地回答了用户问题，则返回此状态
   - refined_queries 设为空数组
   - valid_search_indices 设为空数组

2. **refine_query**：如果答案不够充分、不准确、缺少关键信息，需要进一步检索，则返回此状态
   - 生成 1-3 个细化查询（refined_queries），这些查询应该：
     * 更聚焦于缺失或不足的信息
     * 每个查询 15 字以内
     * 避免与历史查询重复
   - 从答案中提取所有引用序号作为 valid_search_indices：
     * 答案中的引用格式为 [1][2] 等，提取其中的数字（如 "1", "2"）
     * 这些序号对应搜索结果的索引位置
     * 如果答案中没有引用标记，valid_search_indices 设为空数组

请严格按照 JSON Schema 格式返回结果。"""

def get_entry_response_format(agentic_config: dict):
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
    return entry_response_format

def get_agentic_response_format(agentic_config):
    k = agentic_config.get("max_query_expand_k", 1)
    
    agentic_schema = {
        "type": "object",
        "properties": {
            "type_state": {
                "type": "string",
                "enum": ["valid_answer", "refine_query"]
            },
            "refined_queries": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 0,
                "maxItems": k
            },
            "valid_search_indices": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of search index values that are mentioned in the answer"
            }
        },
        "required": ["type_state", "refined_queries", "valid_search_indices"]
    }
    agentic_response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "agentic_response_format",
            "schema": dict(agentic_schema)
        }
    }
    return agentic_response_format