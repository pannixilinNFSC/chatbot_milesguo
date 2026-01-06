import json


def get_agentic_prompt_and_format(question, answer, search_results, agentic_config):
    """
    Build agentic prompt and response format together.
    
    Returns:
        tuple: (prompt, response_format)
    """
    search_results_txt = json.dumps(search_results, ensure_ascii=False)
    prompt_agentic = f"""评估答案质量并决定是否需要进一步检索：

用户问题：{question}

当前生成的答案：
{answer}

已经找到的用于生成答案的搜索结果：
{search_results_txt}

请评估答案是否充分回答了用户问题：

1. **valid_answer**：如果答案已经充分、准确、完整地回答了用户问题，则返回此状态
   - refined_queries 设为空数组
   - valid_search_indices 设为空数组
   - search_ops 设为空数组

2. **refine_query**：如果答案不够充分、不准确、缺少关键信息，需要进一步检索，则返回此状态
   - 生成 1-3 个细化查询（refined_queries），这些查询应该：
     * 更聚焦于缺失或不足的信息
     * 每个查询 15 字以内
     * 避免与历史查询重复
   - 从答案中提取所有引用序号作为 valid_search_indices：
     * 答案中的引用格式为 [1][2] 等，提取其中的数字（如 "1", "2"）
     * 这些序号对应搜索结果的索引位置
     * 如果答案中没有引用标记，valid_search_indices 设为空数组
   - 生成 search_ops 数组，每个元素是一个搜索操作对象：
     * 类型可以是 "search_general"（通用搜索，需要 query_list 字段）
     * 类型可以是 "search_doc"（文档内搜索，需要 query 和 doc_ids 字段）
     * 类型可以是 "search_neighbour_chunks"（邻近块搜索，需要 doc_id、chunk_id、distance 字段）
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
                            "description": "Required for search_general type"
                        },
                        "query": {
                            "type": "string",
                            "description": "Required for search_doc type"
                        },
                        "doc_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required for search_doc type"
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
        "required": ["type_state", "refined_queries", "valid_search_indices", "search_ops"]
    }
    agentic_response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "agentic_response_format",
            "schema": dict(agentic_schema)
        }
    }
    
    return prompt_agentic, agentic_response_format

