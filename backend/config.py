"""
Configuration management for the Diagnostic System.
Loads settings from environment variables and .env file.
"""
import os
from pathlib import Path
from typing import Optional

# Handle both pydantic v1 and v2 styles
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field

# Load .env file
from dotenv import load_dotenv

# Determine base directory
BASE_DIR = Path(__file__).parent.parent

load_dotenv(BASE_DIR / ".env")


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="mistral:7b", alias="OLLAMA_MODEL")
    
    # Groq Cloud
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    
    # Google AI
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", alias="GEMINI_MODEL")
    
    # Provider preference (ollama, groq, gemini)
    default_provider: str = Field(default="ollama", alias="DEFAULT_LLM_PROVIDER")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class APISettings(BaseSettings):
    """External API configuration."""
    use_external_apis: bool = Field(default=False, alias="USE_EXTERNAL_APIS")
    who_gho_api_url: str = Field(default="https://ghoapi.azureedge.net/api", alias="WHO_GHO_API_URL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class DiagnosticSettings(BaseSettings):
    """Diagnostic loop configuration."""
    confidence_threshold: float = Field(default=0.85, alias="CONFIDENCE_THRESHOLD")
    max_iterations: int = Field(default=10, alias="MAX_DIAGNOSTIC_ITERATIONS")
    default_budget_usd: float = Field(default=5000.0, alias="DEFAULT_BUDGET_USD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings:
    """Main application settings - uses simple class to avoid pydantic Path issues."""
    
    def __init__(self):
        self.app_name = "DDX Diagnostic System"
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Data paths - computed from base directory
        self.data_dir = BASE_DIR / "data"
        self.knowledge_dir = self.data_dir / "knowledge"
        self.epidemiology_dir = self.data_dir / "epidemiology"
        self.genomic_dir = self.data_dir / "genomic"
        self.vector_store_dir = self.data_dir / "vector_store"
        self.logs_dir = BASE_DIR / "logs"
        
        # Sub-settings (pydantic-based)
        self.llm = LLMSettings()
        self.api = APISettings()
        self.diagnostic = DiagnosticSettings()
        
        # Ensure directories exist
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
