import re
import json
from typing import Dict, Any

def clean_reddit_text(text: str) -> str:
    """Remove markdown e conteúdo irrelevante"""
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
    text = re.sub(r'\*\*|__|~~', '', text)  # Remove negrito/itálico
    return text.strip()

def load_config() -> Dict[str, Any]:
    with open('config.json') as f:
        return json.load(f)

def truncate_text(text: str, max_tokens: int = 3000) -> str:
    words = text.split()
    return ' '.join(words[:max_tokens])