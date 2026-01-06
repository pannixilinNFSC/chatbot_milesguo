import json


def get_agentic_prompt_and_format(
        question: str, 
        answer: str, 
        search_results: list[dict], 
        historical_search_ops: list[dict], 
        agentic_config: dict = None):
    """
    Build agentic prompt and response format together.
    
    Returns:
        tuple: (prompt, response_format)
    """
    search_results_txt = json.dumps(search_results, ensure_ascii=False)
    prompt_agentic = f"""评估答案质量并决定是否需要进一步检索：

用户问题：{question}

之前的历史操作：{historical_search_ops}

已经找到的有用的生成答案的搜索结果：
{search_results_txt}

当前生成的答案：
{answer}

请评估答案是否充分回答了用户问题：

1. **valid_answer**：如果答案已经充分、准确、完整地回答了用户问题，则返回此状态
   - refined_queries 设为空数组
   - valid_search_indices 设为空数组
   - search_ops 设为空数组

2. **refine_query**：如果答案不够充分、不准确、缺少关键信息，需要尝试对潜在的缺失的信息进一步检索，则返回此状态
   - 生成 search_ops 数组，包含一个或多个元素，每个元素是一个搜索操作对象：
     * 类型可以是 "search_general"（通用搜索，需要 query_list 字段）
     * 类型可以是 "search_doc"（对于摘要显示值得深入挖掘的文档再次搜索，需要 query_list 和 doc_id 字段）
     * 类型可以是 "search_neighbour_chunks"（对于内容不全的chunk，进行邻近块搜索，需要 doc_id、chunk_id、distance 字段）
     * 根据细化查询的内容，选择合适的搜索类型

请严格按照 JSON Schema 格式返回结果。"""
    
    k = agentic_config.get("max_query_expand_k", 1)
    
    agentic_schema = {
        "type": "object",
        "properties": {
            "type_state": {
                "type": "string",
                "enum": ["valid_answer", "refine_query"]
            },
            "search_ops": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["search_general", "search_doc", "search_neighbour_chunks"]
                        },
                        "query_list": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required for search_general type",
                            "minItems": 1,
                            "maxItems": 3
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "Required for search_neighbour_chunks type"
                        },
                        "chunk_id": {
                            "type": "string",
                            "description": "Required for search_neighbour_chunks type"
                        },
                        "distance": {
                            "type": "integer",
                            "description": "Required for search_neighbour_chunks type"
                        }
                    },
                    "required": ["type"]
                },
                "minItems": 0
            }
        },
        "required": ["type_state", "search_ops"]
    }
    agentic_response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "agentic_response_format",
            "schema": dict(agentic_schema)
        }
    }
    
    return prompt_agentic, agentic_response_format

