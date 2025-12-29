"""
LLM integrations for the Nurture Layer.
Uses OpenAI API directly for chat completions.
"""
import requests
from openai import OpenAI
from typing import Optional


class OllamaClient:
    """Ollama client for local models (fallback option)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        self.base_url = base_url
        self.model = model
    
    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, messages: list) -> str:
        """Generate response from Ollama model."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response with optional system prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)


# Global Ollama client
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client(model: str = "mistral") -> OllamaClient:
    """Get or create Ollama client."""
    global _ollama_client
    if _ollama_client is None or _ollama_client.model != model:
        _ollama_client = OllamaClient(model=model)
    return _ollama_client


class LLMClient:
    """OpenAI API client for chat completions."""
    
    DEFAULT_MODEL = "gpt-4o"  # Latest GPT model
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self.model = self.DEFAULT_MODEL
        
        if api_key:
            self.set_api_key(api_key)
    
    def set_api_key(self, api_key: str):
        """Set or update the OpenAI API key."""
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def is_configured(self) -> bool:
        """Check if API key is set."""
        return self.client is not None and self.api_key is not None
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using OpenAI API.
        
        Args:
            prompt: The user/context prompt
            system_prompt: Optional system prompt override
        
        Returns:
            Generated text response
        """
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def generate_with_history(
        self, 
        messages: list,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response with conversation history.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system_prompt: Optional system prompt
        
        Returns:
            Generated text response
        """
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")
        
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def chat(self, messages: list) -> str:
        """
        Generate a response from raw messages array.
        
        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": str}
        
        Returns:
            Generated text response
        """
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content


# Session-based client storage
_session_clients: dict[str, LLMClient] = {}


def get_client(session_id: str) -> Optional[LLMClient]:
    """Get client for session."""
    return _session_clients.get(session_id)


def set_client(session_id: str, api_key: str) -> LLMClient:
    """Create or update client for session."""
    client = LLMClient(api_key)
    _session_clients[session_id] = client
    return client


def remove_client(session_id: str):
    """Remove client for session."""
    if session_id in _session_clients:
        del _session_clients[session_id]
