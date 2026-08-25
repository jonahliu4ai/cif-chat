import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "deepseek"),
    
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com",
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    },
    
    "deepseek-siliconflow": {
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "base_url": "https://api.siliconflow.cn/v1",
        "model": os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V4-Flash"),
    },

    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": None,
        "model": "gpt-4o",
    },
    
    "custom": {
        "api_key": os.getenv("CUSTOM_API_KEY", ""),
        "base_url": os.getenv("CUSTOM_BASE_URL", ""),
        "model": os.getenv("CUSTOM_MODEL", ""),
    },
}


def get_llm_config():
    provider = LLM_CONFIG["provider"]
    config = LLM_CONFIG.get(provider, {})
    return provider, config
