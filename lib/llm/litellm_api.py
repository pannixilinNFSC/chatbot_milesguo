import litellm
from litellm import acompletion
from pydantic import BaseModel
import asyncio
import nest_asyncio
import os
import logging
from litellm import Router
import json
nest_asyncio.apply()
import tempfile
litellm.enable_json_schema_validation=True

# Suppress LiteLLM INFO logs
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("LiteLLM Router").setLevel(logging.WARNING)
# Also disable LiteLLM's verbose logging
litellm.set_verbose = False

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
            fallbacks=[{"gpt": ["gemini"]}, {"gemini":["gpt"]}],
            num_retries=1,
            max_fallbacks=1, 
        )
    return _router

async def call_llm_with_fallback(str1, 
                                 model_name = "gemini", 
                                 response_format=None
                                 ):
    router = get_litellm_fallback_router()
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
    
    # Parse JSON string when using structured output (response_format with json_schema)
    # litellm returns JSON string when using structured output, need to parse it
    if response_format and response_format.get("type") == "json_schema":
        try:
            return json.loads(x)
        except (json.JSONDecodeError, TypeError) as e:
            logging.warning(f"Failed to parse structured output as JSON: {e}. Returning raw string.")
            
    return x

async def call_llm_stream(str1, 
                         router=None, 
                         model_name="openai/gpt-4o", 
                         response_format=None, 
                         kwargs={}):
    """
    Stream LLM response as async generator yielding chunks.
    
    Yields:
        str: Content chunks from the LLM stream
    """
    acompletion1 = router.acompletion if router else acompletion
    stream = await acompletion1(
        model=model_name,
        messages=[{"role": "user", "content": str1}], 
        response_format=response_format,
        stream=True,
        **kwargs, 
    )
    
    async for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

async def call_llm_stream_with_fallback(str1, 
                                        model_name="gpt", 
                                        response_format=None):
    """
    Stream LLM response with fallback support.
    
    Yields:
        str: Content chunks from the LLM stream
    """
    router = get_litellm_fallback_router()
    kwargs = {"temperature": 0.0}
    
    try:
        async for chunk in call_llm_stream(
            str1, 
            router, 
            model_name, 
            response_format, 
            kwargs
        ):
            yield chunk
    except Exception as e:
        # If primary model fails, try fallback
        fallback_model = "gemini" if model_name == "gpt" else "gpt"
        logging.warning(f"Primary model {model_name} failed, trying fallback {fallback_model}: {e}")
        try:
            async for chunk in call_llm_stream(
                str1, 
                router, 
                fallback_model, 
                response_format, 
                kwargs
            ):
                yield chunk
        except Exception as fallback_error:
            logging.error(f"Both models failed: {fallback_error}")
            raise