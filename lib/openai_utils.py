import openai
from openai import OpenAI # API v1.2

with open("openai_key.txt", "r") as f:
    openai_key = f.read().strip()
    openai_client = OpenAI(api_key=openai_key)
