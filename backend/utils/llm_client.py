"""
Unified LLM client supporting multiple backends.
Supports Ollama (local), Groq Cloud, and Google AI (Gemini).
"""
import os
from typing import Optional, AsyncGenerator
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Unified LLM client that abstracts provider differences.
    Supports automatic fallback from local to cloud providers.
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.provider = provider or settings.llm.default_provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Optional[BaseChatModel] = None
        
        # Set model based on provider
        if model:
            self.model = model
        else:
            self.model = self._get_default_model()
        
        logger.info(f"Initializing LLM client: provider={self.provider}, model={self.model}")
    
    def _get_default_model(self) -> str:
        """Get default model for the current provider."""
        match self.provider:
            case "ollama":
                return settings.llm.ollama_model
            case "groq":
                return settings.llm.groq_model
            case "gemini":
                return settings.llm.gemini_model
            case _:
                return settings.llm.ollama_model
    
    def _create_client(self) -> BaseChatModel:
        """Create the appropriate LLM client based on provider."""
        match self.provider:
            case "ollama":
                logger.debug(f"Creating Ollama client: {settings.llm.ollama_base_url}")
                return ChatOllama(
                    model=self.model,
                    base_url=settings.llm.ollama_base_url,
                    temperature=self.temperature,
                    num_predict=self.max_tokens
                )
            
            case "groq":
                if not settings.llm.groq_api_key:
                    raise ValueError("GROQ_API_KEY not set in environment")
                
                from langchain_groq import ChatGroq
                logger.debug("Creating Groq client")
                return ChatGroq(
                    model=self.model,
                    api_key=settings.llm.groq_api_key,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            case "gemini":
                if not settings.llm.google_api_key:
                    raise ValueError("GOOGLE_API_KEY not set in environment")
                
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.debug("Creating Gemini client")
                return ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=settings.llm.google_api_key,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            
            case _:
                raise ValueError(f"Unknown provider: {self.provider}")
    
    @property
    def client(self) -> BaseChatModel:
        """Lazy-load the LLM client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            json_mode: If True, instruct the model to return JSON
            
        Returns:
            The generated response text
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if json_mode:
            prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        messages.append(HumanMessage(content=prompt))
        
        logger.debug(f"Generating response with {len(messages)} messages")
        
        try:
            response = await self.client.ainvoke(messages)
            logger.debug(f"Response received: {len(response.content)} chars")
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """Synchronous version of generate."""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if json_mode:
            prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        messages.append(HumanMessage(content=prompt))
        
        logger.debug(f"Generating response (sync) with {len(messages)} messages")
        
        try:
            response = self.client.invoke(messages)
            logger.debug(f"Response received: {len(response.content)} chars")
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


class LLMClientFactory:
    """Factory for creating LLM clients with different configurations."""
    
    @staticmethod
    def create_local() -> LLMClient:
        """Create a client using local Ollama."""
        return LLMClient(provider="ollama")
    
    @staticmethod
    def create_fast() -> LLMClient:
        """Create a fast cloud client (Gemini)."""
        return LLMClient(provider="gemini")
    
    @staticmethod
    def create_reasoning() -> LLMClient:
        """Create a high-reasoning client (Groq with large model)."""
        return LLMClient(provider="groq")
    
    @staticmethod
    def create_with_fallback() -> LLMClient:
        """
        Create a client that tries local first, falls back to cloud.
        Currently returns local client - fallback logic can be added.
        """
        try:
            client = LLMClient(provider="ollama")
            # Test connection
            return client
        except Exception as e:
            logger.warning(f"Ollama not available, falling back to Groq: {e}")
            return LLMClient(provider="groq")


# Default client instance
def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """Get an LLM client instance."""
    return LLMClient(provider=provider)
