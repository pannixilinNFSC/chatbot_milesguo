import litellm
from litellm import acompletion
from pydantic import BaseModel
import asyncio
import nest_asyncio
import os
from litellm import Router
nest_asyncio.apply()
import tempfile
litellm.enable_json_schema_validation=True

# Create a single shared router instance to avoid callback limit issues
_router = None

def get_litellm_fallback_router():
    """Get or create a shared router instance"""
    global _router
    if _router is None:
        _router = Router(
            model_list=[
                #{
                #    "model_name": "claude", 
                #    "litellm_params": {
                #        "model": "anthropic/claude-3-haiku-20240307"}
                #}, 
                {
                    "model_name": "gpt",
                    "litellm_params": {
                        "model": "openai/gpt-4o-mini", 
                    }
                },
                {
                    "model_name": "gemini",
                    "litellm_params": {
                        "model": "gemini/gemini-2.0-flash-001", 
                    }
                }
            ],
            fallbacks=[{"gpt": ["gemini"]}, {"gemini":["gpt"]}]
        )
    return _router

async def call_llm_with_fallback(str1, response_format=None):
    router = get_litellm_fallback_router()
    model_name = "gemini"
    kwargs = {"temperature": 0.0}
    result = await call_llm(
        str1, 
        router, 
        model_name, 
        response_format, 
        kwargs
    )
    return result

async def call_llm(str1, 
                   router=None, 
                   model_name="openai/gpt-4o", 
                   response_format=None, 
                   kwargs={}):
    acompletion1 = router.acompletion if router else acompletion
    response = await acompletion1(
        model=model_name,
        messages=[{"role": "user", "content": str1}], 
        response_format=response_format, 
        **kwargs, 
    )
    x = response.choices[0].message.content
    return x