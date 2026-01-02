import keyword
from lib.llm.litellm_api import call_llm_with_fallback
from lib.app_logger import get_logger
import json

logger = get_logger(__name__)

class QueryExpander:
    def __init__(self):
        pass
    
    async def expand(self, 
                     query:str, 
                     query_context:list[str]=[], 
                     k:int=1
    ) -> list[str]:
        prompt = f"""
        猜测用户的提问意图，并给出一个更具体的查询问句，15个字以内。
        例如：
        用户提问：如何做好人
        扩展：一个人应具备哪些道德品格，如何加以实践与培养
        扩展：{k}个不同的查询问句
        以下是用户之前的问答记录：{query_context}
        用户当前提问：{query}
        """
        
        # Define JSON Schema with list length constraints
        # Use a more lenient maxItems to accommodate model responses
        json_schema = {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": k
                }
            },
            "required": ["queries"]
        }
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "query_expansion_schema",
                "schema": json_schema
            }
        }
        
        respond = await call_llm_with_fallback(prompt, 
                                               model_name="gemini", 
                                               response_format=response_format)
        
        logger.info("Respond: %s", respond)
        
        # Parse the structured response (litellm returns JSON string when using structured output)
        try:
            parsed_dict = json.loads(respond)
            return parsed_dict.get("queries", [])
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse structured output: {e}")
            return []
