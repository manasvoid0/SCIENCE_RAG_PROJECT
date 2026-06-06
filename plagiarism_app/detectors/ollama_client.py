"""
ollama_client.py
================
A tiny helper that talks to your local Ollama server.

Every detector that needs AI goes through here, so there is ONE place that knows
the Ollama address. If you ever move Ollama to another machine or port, you only
change it here (or set the OLLAMA_HOST environment variable).

NOTE: Ollama does not need to be running while you build the project. These
functions only contact it when actually called (e.g. when a teacher runs an
analysis). Until then, nothing here touches the network.
"""

import os  # to read the optional OLLAMA_HOST environment variable
import json  # to parse the JSON that Qwen returns
import requests  # the library that sends HTTP requests to Ollama

# Base address of the Ollama server. Default is the standard local install.
# To override:  export OLLAMA_HOST=http://192.168.1.50:11434
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# The two models you already use in the RAG project.
CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def generate(prompt: str, temperature: float = 0.1) -> str:
    """
    Send a text prompt to the chat model (Qwen) and return its raw text reply.
    Low temperature = consistent, factual answers (good for scoring).
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,  # we want the whole answer at once, not word-by-word
            "options": {"temperature": temperature},
        },
        timeout=300,  # AI calls can be slow on first run; give it 5 minutes
    )
    response.raise_for_status()  # turn HTTP errors into clear Python exceptions
    return response.json()["response"]


def embed(text: str) -> list:
    """
    Turn a piece of text into a vector (list of numbers) using nomic-embed-text.
    Two texts with similar MEANING produce vectors that point the same way.
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def extract_json(raw: str) -> dict:
    """
    Qwen sometimes wraps its JSON answer in markdown fences like ```json ... ```.
    This strips that wrapper and parses the JSON safely.
    """
    text = raw.strip()
    if text.startswith("```"):
        # remove the opening fence (``` or ```json) and the closing fence
        text = text.split("```")[1]
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    return json.loads(text.strip())
